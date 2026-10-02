"""Phase 08 Remediation Verification Test Suite: Offline Sync, Device Binding, Durable Idempotency.

Verifies:
1. SyncManager durable restart cycle (enqueue -> crash -> restart -> process once -> replay -> zero duplicates)
2. Device binding anti-hijacking security in SyncManager
3. Device binding persistence across server/database restarts
4. Event-level idempotency and database uniqueness
5. Operation-level replay idempotency with cached receipt
6. Out-of-order event sequence reconciliation and sequence gap detection
7. Device binding API endpoints (bind, list, cross-student rejection)
8. Multi-device sync merging into Authoritative SLR
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.slr.service import SLRService
from central_platform.sync.manager import SyncEvent, SyncManager
from central_platform.sync.service import SyncService


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 1: SyncManager Durable Restart Cycle
# ─────────────────────────────────────────────────────────────────────────────
def test_sync_manager_durable_restart_cycle(tmp_path):
    """Verifies Master Plan Section 13 Restart Test:
    1. queue event;
    2. kill process;
    3. restart;
    4. event still exists;
    5. process once;
    6. replay same event;
    7. no duplicate learning evidence.
    """
    db_file = str(tmp_path / "sync_manager_restart.db")

    # Step 1: Open session 1, bind device, queue event
    sm1 = SyncManager(db_path=db_file)
    sm1.bind_device("dev_restart_1", "student_rst")
    assert sm1.get_bound_student("dev_restart_1") == "student_rst"

    ev1 = SyncEvent(
        event_id="evt_durable_101",
        student_id="student_rst",
        device_id="dev_restart_1",
        event_type="question_attempted",
        payload={"score": 1.0, "concept_id": "chem_thermo_first_law"},
        sequence_num=1,
    )
    assert sm1.queue_offline_event(ev1) is True

    # Step 2: Kill process (close db connection)
    sm1.close()
    del sm1

    # Step 3 & 4: Restart process (new SyncManager instance on same DB file)
    sm2 = SyncManager(db_path=db_file)
    assert sm2.get_bound_student("dev_restart_1") == "student_rst"
    queued = sm2.get_queued_events()
    assert len(queued) == 1
    assert queued[0].event_id == "evt_durable_101"

    # Step 5: Process once
    res1 = sm2.process_sync()
    assert res1["synced"] == 1
    assert res1["duplicates"] == 0
    assert sm2.is_event_processed("evt_durable_101") is True

    # Step 6: Replay same event
    # queue_offline_event returns False because event is already processed
    assert sm2.queue_offline_event(ev1) is False
    res2 = sm2.process_sync()
    # Step 7: No duplicate learning evidence
    assert res2["synced"] == 0
    assert res2["duplicates"] == 1

    # Restart once more to verify processed status survives further restarts
    sm2.close()
    del sm2

    sm3 = SyncManager(db_path=db_file)
    assert sm3.is_event_processed("evt_durable_101") is True
    assert sm3.queue_offline_event(ev1) is False
    res3 = sm3.process_sync()
    assert res3["synced"] == 0
    assert res3["duplicates"] == 1
    sm3.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 2: Device Binding Anti-Hijacking in SyncManager
# ─────────────────────────────────────────────────────────────────────────────
def test_device_binding_anti_hijacking_sync_manager(tmp_path):
    """A device bound to student A cannot be hijacked by student B."""
    sm = SyncManager(db_path=str(tmp_path / "anti_hijack.db"))
    sm.bind_device("hardware_dev_007", "student_alice")

    # Attempting to rebind to student_bob without force raises PermissionError
    with pytest.raises(PermissionError) as exc_info:
        sm.bind_device("hardware_dev_007", "student_bob")
    assert "already bound to another student" in str(exc_info.value)

    # Queueing event claiming student_bob on alice's device raises PermissionError
    hijack_event = SyncEvent(
        event_id="ev_steal_1",
        student_id="student_bob",
        device_id="hardware_dev_007",
        event_type="question_attempted",
        payload={"score": 0.5},
    )
    with pytest.raises(PermissionError) as exc_info:
        sm.queue_offline_event(hijack_event)
    assert "Device is not bound to the specified student" in str(exc_info.value)

    # Calling record_event with student_bob also raises PermissionError
    with pytest.raises(PermissionError):
        sm.record_event(hijack_event)

    sm.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 3: Device Binding Persistence Across Server Restarts
# ─────────────────────────────────────────────────────────────────────────────
def test_device_binding_persistence_server_restart(tmp_path):
    """Device bindings in PlatformDatabase survive server restart and prevent hijacking."""
    db_file = str(tmp_path / "server_restart_device.db")

    # Server Session 1: Register device for Student Alice
    db1 = PlatformDatabase(db_path=db_file)
    svc1 = SyncService(db=db1)
    svc1.bind_device("dev_desktop_alpha", "student_alice")
    assert svc1.get_bound_student("dev_desktop_alpha") == "student_alice"
    db1.close()
    del db1, svc1

    # Server Session 2: Server restarts with fresh database connection
    db2 = PlatformDatabase(db_path=db_file)
    svc2 = SyncService(db=db2)

    # Verification: Device binding was restored from persistent storage
    assert svc2.get_bound_student("dev_desktop_alpha") == "student_alice"

    # Student Bob attempts to sync using Alice's device -> REJECT
    events = [
        {"event_id": "ev_bob_01", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"}
    ]
    with pytest.raises(PermissionError) as exc_info:
        svc2.process_sync_batch(
            student_id="student_bob",
            events=events,
            device_id="dev_desktop_alpha",
        )
    assert "bound to another student" in str(exc_info.value)

    # Student Alice can sync normally
    alice_events = [
        {"event_id": "ev_alice_01", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"}
    ]
    res_alice = svc2.process_sync_batch(
        student_id="student_alice",
        events=alice_events,
        device_id="dev_desktop_alpha",
    )
    assert res_alice["ok"] is True
    assert res_alice["synced_count"] == 1
    db2.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 4: Event-Level Idempotency and Database Uniqueness
# ─────────────────────────────────────────────────────────────────────────────
def test_event_level_idempotency_database_constraint(tmp_path):
    """Duplicate events are deduplicated at both DB and service level."""
    db_file = str(tmp_path / "idempotency_test.db")
    db = PlatformDatabase(db_path=db_file)
    svc = SyncService(db=db)

    student_id = "student_idem_test"
    events = [
        {"event_id": "ev_idem_101", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law", "sequence_num": 1},
        {"event_id": "ev_idem_102", "event_type": "answer_submitted", "score": 0.8, "concept_id": "chem_thermo_first_law", "sequence_num": 2},
    ]

    # Ingest batch
    res1 = svc.process_sync_batch(student_id=student_id, events=events)
    assert res1["synced_count"] == 2
    assert res1["duplicate_count"] == 0
    assert set(res1["acknowledged_ids"]) == {"ev_idem_101", "ev_idem_102"}

    # Resend same events in new batch
    res2 = svc.process_sync_batch(student_id=student_id, events=events)
    assert res2["synced_count"] == 0
    assert res2["duplicate_count"] == 2
    assert set(res2["acknowledged_ids"]) == {"ev_idem_101", "ev_idem_102"}

    # DB uniqueness: exactly 2 events exist
    stored = db.query_learning_events(student_id=student_id)
    assert len(stored) == 2
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 5: Operation-Level Replay Idempotency
# ─────────────────────────────────────────────────────────────────────────────
def test_operation_id_replay_idempotency(tmp_path):
    """Sending the exact same operation_id returns cached receipt with is_replay=True."""
    db = PlatformDatabase(db_path=str(tmp_path / "op_replay.db"))
    svc = SyncService(db=db)

    op_id = "op_replay_unique_123"
    events = [
        {"event_id": "ev_op_1", "event_type": "answer_submitted", "score": 0.95, "concept_id": "chem_thermo_first_law"}
    ]

    r1 = svc.process_sync_batch("stu_op", events, operation_id=op_id)
    assert r1["is_replay"] is False
    assert r1["synced_count"] == 1

    # Exact replay
    r2 = svc.process_sync_batch("stu_op", events, operation_id=op_id)
    assert r2["is_replay"] is True
    assert r2["operation_id"] == op_id
    assert r2["synced_count"] == 1
    assert r2["acknowledged_ids"] == ["ev_op_1"]
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 6: Out-of-Order Sequence Reconciliation and Gap Detection
# ─────────────────────────────────────────────────────────────────────────────
def test_out_of_order_sequence_and_gap_detection(tmp_path):
    """Scrambled events are reconciled chronologically and sequence gaps are reported."""
    db = PlatformDatabase(db_path=str(tmp_path / "gap_detect.db"))
    svc = SyncService(db=db)

    # Missing sequence numbers 3 and 4; delivered in scrambled order
    events = [
        {"event_id": "ev_seq_5", "sequence_num": 5, "timestamp": "2026-10-02T12:00:05Z", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"},
        {"event_id": "ev_seq_1", "sequence_num": 1, "timestamp": "2026-10-02T12:00:01Z", "event_type": "answer_submitted", "score": 0.6, "concept_id": "chem_thermo_first_law"},
        {"event_id": "ev_seq_6", "sequence_num": 6, "timestamp": "2026-10-02T12:00:06Z", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"},
        {"event_id": "ev_seq_2", "sequence_num": 2, "timestamp": "2026-10-02T12:00:02Z", "event_type": "answer_submitted", "score": 0.8, "concept_id": "chem_thermo_first_law"},
    ]

    res = svc.process_sync_batch("student_gaps", events)
    assert res["ok"] is True
    assert res["synced_count"] == 4

    # Events in database are ordered by timeline correctly
    stored = db.query_learning_events(student_id="student_gaps")
    assert [e.id for e in stored] == ["ev_seq_1", "ev_seq_2", "ev_seq_5", "ev_seq_6"]

    # Sequence gap detected between seq 2 and seq 5 (expected 3, received 5, gap_size 2)
    gaps = res.get("sequence_gaps", [])
    assert len(gaps) == 1
    assert gaps[0]["expected"] == 3
    assert gaps[0]["received"] == 5
    assert gaps[0]["gap_size"] == 2
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 7: Device Binding API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
def test_device_binding_api_endpoints(tmp_path, monkeypatch):
    """Verifies /api/v1/sync/devices/bind and /api/v1/sync/devices endpoints."""
    import central_platform.auth.dependencies as auth_deps

    db_path = str(tmp_path / "device_api.db")
    monkeypatch.setenv("GAYATRI_DB_PATH", db_path)
    test_db = PlatformDatabase(db_path)
    auth_deps._DB_INSTANCE = test_db

    token_alice = create_access_token(user_id="student_alice_api", role="student")
    token_bob = create_access_token(user_id="student_bob_api", role="student")

    with TestClient(app) as client:
        # 1. Alice binds her device
        res = client.post(
            "/api/v1/sync/devices/bind",
            json={
                "device_id": "macbook_pro_alice",
                "student_id": "student_alice_api",
                "device_name": "Alice's MacBook Pro",
            },
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["device_id"] == "macbook_pro_alice"
        assert res.json()["data"]["status"] == "ACTIVE"

        # 2. Alice lists her registered devices
        list_res = client.get(
            "/api/v1/sync/devices?student_id=student_alice_api",
            headers={"Authorization": f"Bearer {token_alice}"},
        )
        assert list_res.status_code == 200
        devices = list_res.json()["data"]
        assert len(devices) == 1
        assert devices[0]["device_id"] == "macbook_pro_alice"
        assert devices[0]["device_name"] == "Alice's MacBook Pro"

        # 3. Bob attempts to bind Alice's device to himself -> 403 Forbidden
        bob_hijack = client.post(
            "/api/v1/sync/devices/bind",
            json={
                "device_id": "macbook_pro_alice",
                "student_id": "student_bob_api",
                "device_name": "Bob's Claim",
            },
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert bob_hijack.status_code == 403

        # 4. Bob cannot list Alice's devices -> 403 Forbidden
        bob_list_alice = client.get(
            "/api/v1/sync/devices?student_id=student_alice_api",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert bob_list_alice.status_code == 403

    test_db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 8: Multi-Device Sync Merging into Authoritative SLR
# ─────────────────────────────────────────────────────────────────────────────
def test_multi_device_sync_merging_into_authoritative_slr(tmp_path):
    """Two authorized devices for the same student merge into a single canonical SLR."""
    db = PlatformDatabase(db_path=str(tmp_path / "multi_dev_slr.db"))
    svc = SyncService(db=db)

    student_id = "student_dual_device"
    course_id = "crs-chem-101"

    # Device 1 (phone) sends first answer
    phone_events = [
        {
            "event_id": "phone_ev_1",
            "device_id": "device_phone",
            "event_type": "answer_submitted",
            "concept_id": "chem_thermo_first_law",
            "score": 0.85,
            "sequence_num": 1,
            "timestamp": "2026-10-02T10:00:00Z",
            "payload": {"correctness": "correct", "concept_id": "chem_thermo_first_law"},
        }
    ]
    res1 = svc.process_sync_batch(student_id=student_id, events=phone_events, course_id=course_id, device_id="device_phone")
    assert res1["ok"] is True

    # Device 2 (laptop) sends second answer
    laptop_events = [
        {
            "event_id": "laptop_ev_1",
            "device_id": "device_laptop",
            "event_type": "answer_submitted",
            "concept_id": "chem_thermo_enthalpy",
            "score": 0.90,
            "sequence_num": 1,
            "timestamp": "2026-10-02T10:05:00Z",
            "payload": {"correctness": "correct", "concept_id": "chem_thermo_enthalpy"},
        }
    ]
    res2 = svc.process_sync_batch(student_id=student_id, events=laptop_events, course_id=course_id, device_id="device_laptop")
    assert res2["ok"] is True

    # Check sync status reflects both registered devices
    status = svc.get_sync_status(student_id=student_id, course_id=course_id)
    assert "device_phone" in status["registered_devices"]
    assert "device_laptop" in status["registered_devices"]
    assert status["total_synced_events"] == 2

    # Authoritative SLR reflects both concepts
    slr = svc.slr_service.get_authoritative_slr(student_id, course_id)
    assert slr.authoritative is True
    assert len(slr.learning_timeline) >= 2
    timeline_ids = [t.item_id for t in slr.learning_timeline]
    assert "phone_ev_1" in timeline_ids
    assert "laptop_ev_1" in timeline_ids

    db.close()
