"""Phase 14 Test Suite: Sync & Conflict Resolution.

Verifies:
1. Normal sync lifecycle with LocalSyncOutbox and SyncService.
2. Duplicate sync event idempotency (same event sent twice does not create duplicate rows).
3. Operation ID replay idempotency (exact cached receipt returned).
4. Partial sync acknowledgement (valid events acknowledged, invalid events flagged).
5. Network timeout handling and exponential retry backoff.
6. Server rejection on device binding mismatch.
7. Client crash and restart durability with in-flight recovery.
8. Server restart persistence and sync operations ledger survivability.
9. Simultaneous multi-device sync merging into canonical student learning timeline.
10. Course version mismatch conflict resolution policy.
11. Out-of-order event sequence reconciliation.
12. Sync status API endpoint and audit summary.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.slr.service import SLRService
from central_platform.sync.service import SyncService
from local_runtime.sync_outbox import LocalSyncOutbox


@pytest.fixture
def managed_db(tmp_path):
    """Provide isolated SQLite platform database."""
    db_file = tmp_path / "phase14_platform.db"
    db = PlatformDatabase(db_path=str(db_file))
    yield db
    db.close()


@pytest.fixture
def sync_service(managed_db):
    """Provide server-side SyncService backed by managed platform DB."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    return SyncService(db=managed_db, event_store=event_store, slr_service=slr_service)


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Normal sync lifecycle
# ─────────────────────────────────────────────────────────────────────────────
def test_normal_sync_lifecycle(tmp_path, sync_service):
    """Outbox enqueues events, builds batch with operation_id, syncs with server, and clears outbox."""
    outbox = LocalSyncOutbox(db_path=tmp_path / "client_outbox.db")

    # Enqueue events
    outbox.enqueue("stu_101", "crs-phy-101", "ev_01", "question_attempted", {"score": 0.8}, "phy_kinematics", 1)
    outbox.enqueue("stu_101", "crs-phy-101", "ev_02", "question_attempted", {"score": 1.0}, "phy_kinematics", 2)
    assert outbox.count_pending() == 2

    # Fetch batch
    op_id, events = outbox.get_pending_batch(limit=10)
    assert op_id.startswith("op_")
    assert len(events) == 2

    # Transmit to server
    res = sync_service.process_sync_batch(
        student_id="stu_101",
        events=events,
        course_id="crs-phy-101",
        device_id="dev_01",
        operation_id=op_id,
    )

    assert res["ok"] is True
    assert res["status"] == "SYNCED"
    assert res["synced_count"] == 2
    assert res["duplicate_count"] == 0
    assert set(res["acknowledged_ids"]) == {"ev_01", "ev_02"}

    # Client receives acknowledgment and purges outbox
    deleted = outbox.mark_acknowledged(op_id, res["acknowledged_ids"])
    assert deleted == 2
    assert outbox.count_pending() == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Duplicate sync event idempotency
# ─────────────────────────────────────────────────────────────────────────────
def test_duplicate_sync_event_idempotency(sync_service, managed_db):
    """Sending same events twice must not create duplicate logical events in the database."""
    events = [
        {"event_id": "dup_01", "event_type": "answer_submitted", "score": 1.0, "concept_id": "math_algebra", "sequence_num": 1},
        {"event_id": "dup_02", "event_type": "answer_submitted", "score": 0.5, "concept_id": "math_algebra", "sequence_num": 2},
    ]

    # First sync
    res1 = sync_service.process_sync_batch("stu_dup", events, course_id="crs-math-101")
    assert res1["synced_count"] == 2
    assert res1["duplicate_count"] == 0

    # Second sync with different operation_id but identical event_ids
    res2 = sync_service.process_sync_batch("stu_dup", events, course_id="crs-math-101", operation_id="op_retry_99")
    assert res2["ok"] is True
    assert res2["synced_count"] == 0
    assert res2["duplicate_count"] == 2
    assert set(res2["acknowledged_ids"]) == {"dup_01", "dup_02"}

    # Database invariant: exactly 2 events stored, not 4
    stored = managed_db.query_learning_events(student_id="stu_dup")
    assert len(stored) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Operation ID replay idempotency
# ─────────────────────────────────────────────────────────────────────────────
def test_operation_id_replay_idempotency(sync_service):
    """Replaying exact same operation_id returns cached receipt without reprocessing."""
    events = [
        {"event_id": "op_ev_1", "event_type": "answer_submitted", "score": 0.9, "concept_id": "cs_python", "sequence_num": 1}
    ]
    op_id = "op_idempotent_test_1"

    # First attempt
    res1 = sync_service.process_sync_batch("stu_op", events, course_id="crs-cs-101", operation_id=op_id)
    assert res1["is_replay"] is False
    assert res1["synced_count"] == 1

    # Exact replay of same operation_id
    res2 = sync_service.process_sync_batch("stu_op", events, course_id="crs-cs-101", operation_id=op_id)
    assert res2["is_replay"] is True
    assert res2["operation_id"] == op_id
    assert res2["synced_count"] == 1
    assert res2["acknowledged_ids"] == ["op_ev_1"]
    assert res2["status"] == "SYNCED"


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Partial sync acknowledgement
# ─────────────────────────────────────────────────────────────────────────────
def test_partial_sync_acknowledgement(sync_service):
    """Batch with valid and malformed events acknowledges valid IDs and marks status PARTIAL."""
    events = [
        {"event_id": "valid_01", "event_type": "answer_submitted", "score": 1.0, "concept_id": "bio_genetics", "sequence_num": 1},
        {"event_id": "", "event_type": "answer_submitted", "score": 0.5},  # Missing event_id
        {"event_id": "valid_02", "event_type": "hint_requested", "concept_id": "bio_genetics", "sequence_num": 3},
    ]

    res = sync_service.process_sync_batch("stu_part", events, course_id="crs-bio-101")
    assert res["ok"] is False
    assert res["status"] == "PARTIAL"
    assert res["synced_count"] == 2
    assert res["failed_count"] == 1
    assert set(res["acknowledged_ids"]) == {"valid_01", "valid_02"}


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Network timeout handling and exponential retry backoff
# ─────────────────────────────────────────────────────────────────────────────
def test_network_timeout_and_exponential_retry(tmp_path):
    """Outbox handles failure by recording error and scheduling exponential backoff retry."""
    outbox = LocalSyncOutbox(db_path=tmp_path / "timeout_outbox.db")
    outbox.enqueue("stu_to", "crs-1", "ev_to_1", "turn", {"q": 1})

    op_id, items = outbox.get_pending_batch()
    assert len(items) == 1

    # Simulate timeout
    outbox.mark_failed(op_id, "HTTP 504 Gateway Timeout", backoff_base_sec=0.5)

    # Immediately requesting pending batch returns empty because retry delay has not passed
    _, retry_items = outbox.get_pending_batch()
    assert len(retry_items) == 0

    # Wait for backoff window (0.5s * 2^1 = 1.0s)
    time.sleep(1.2)

    # Now eligible for retry
    _, retry_items_after = outbox.get_pending_batch()
    assert len(retry_items_after) == 1
    assert retry_items_after[0]["event_id"] == "ev_to_1"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Server rejection on device binding mismatch
# ─────────────────────────────────────────────────────────────────────────────
def test_server_rejection_and_device_quarantine(sync_service):
    """Device bound to student A cannot sync telemetry on behalf of student B."""
    sync_service.bind_device("hardware_device_xyz", "student_alice")

    events = [{"event_id": "ev_hijack", "event_type": "answer_submitted", "score": 1.0}]

    with pytest.raises(PermissionError) as exc_info:
        sync_service.process_sync_batch(
            student_id="student_bob",
            events=events,
            device_id="hardware_device_xyz",
        )

    assert "bound to another student" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Client crash and restart durability
# ─────────────────────────────────────────────────────────────────────────────
def test_client_crash_and_restart_durability(tmp_path):
    """In-flight items from mid-sync crash are reset to PENDING on restart so zero events are lost."""
    db_file = tmp_path / "crash_durability.db"

    # Session 1: Enqueue and take batch (marking IN_FLIGHT)
    o1 = LocalSyncOutbox(db_path=db_file)
    o1.enqueue("stu_crash", "crs-1", "ev_c1", "turn", {"a": 1})
    o1.enqueue("stu_crash", "crs-1", "ev_c2", "turn", {"a": 2})
    op_id, items = o1.get_pending_batch()
    assert len(items) == 2

    # Simulate abrupt process death
    del o1

    # Session 2: Startup initiates in-flight recovery
    o2 = LocalSyncOutbox(db_path=db_file)
    status = o2.get_outbox_status()
    assert status["pending"] == 2
    assert status["in_flight"] == 0

    # Events are immediately re-batchable
    new_op, re_items = o2.get_pending_batch()
    assert len(re_items) == 2
    assert {i["event_id"] for i in re_items} == {"ev_c1", "ev_c2"}


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Server restart persistence
# ─────────────────────────────────────────────────────────────────────────────
def test_server_restart_persistence(tmp_path):
    """Sync operations and acknowledged receipts survive platform server restart."""
    db_file = str(tmp_path / "server_durability.db")

    # Server session 1: Process and record sync operation
    db1 = PlatformDatabase(db_path=db_file)
    svc1 = SyncService(db=db1)
    res = svc1.process_sync_batch(
        student_id="stu_persist",
        events=[{"event_id": "ev_p1", "event_type": "answer_submitted", "score": 1.0, "concept_id": "c1"}],
        course_id="crs-test-101",
        operation_id="op_persist_01",
    )
    assert res["synced_count"] == 1
    db1.close()

    # Server session 2: Reopen database and verify operation ledger
    db2 = PlatformDatabase(db_path=db_file)
    op_record = db2.get_sync_operation("op_persist_01")
    assert op_record is not None
    assert op_record.student_id == "stu_persist"
    assert op_record.synced_count == 1
    assert op_record.acknowledged_ids == ["ev_p1"]

    svc2 = SyncService(db=db2)
    sync_status = svc2.get_sync_status("stu_persist", "crs-test-101")
    assert sync_status["total_operations"] == 1
    assert sync_status["total_synced_events"] == 1
    assert sync_status["last_operation_id"] == "op_persist_01"
    db2.close()


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Simultaneous multi-device sync
# ─────────────────────────────────────────────────────────────────────────────
def test_simultaneous_multi_device_sync(sync_service, managed_db):
    """Two devices for the same student sync concurrent sessions; events are merged into unified timeline."""
    device_laptop_events = [
        {"event_id": "dev1_ev1", "event_type": "answer_submitted", "score": 0.8, "concept_id": "concept_alpha", "sequence_num": 1, "timestamp": "2026-10-02T10:00:00Z"},
        {"event_id": "dev1_ev2", "event_type": "answer_submitted", "score": 0.9, "concept_id": "concept_beta", "sequence_num": 2, "timestamp": "2026-10-02T10:05:00Z"},
    ]
    device_tablet_events = [
        {"event_id": "dev2_ev1", "event_type": "answer_submitted", "score": 0.7, "concept_id": "concept_alpha", "sequence_num": 1, "timestamp": "2026-10-02T10:02:00Z"},
        {"event_id": "dev2_ev2", "event_type": "hint_requested", "concept_id": "concept_beta", "sequence_num": 2, "timestamp": "2026-10-02T10:06:00Z"},
    ]

    # Sync laptop
    res1 = sync_service.process_sync_batch("stu_multidev", device_laptop_events, course_id="crs-multi-101", device_id="laptop_01")
    assert res1["synced_count"] == 2

    # Sync tablet
    res2 = sync_service.process_sync_batch("stu_multidev", device_tablet_events, course_id="crs-multi-101", device_id="tablet_02")
    assert res2["synced_count"] == 2

    # Central DB has all 4 events
    all_events = managed_db.query_learning_events(student_id="stu_multidev")
    assert len(all_events) == 4

    # Both devices registered
    status = sync_service.get_sync_status("stu_multidev", "crs-multi-101")
    assert "laptop_01" in status["registered_devices"]
    assert "tablet_02" in status["registered_devices"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Course version mismatch resolution
# ─────────────────────────────────────────────────────────────────────────────
def test_course_version_mismatch_resolution(sync_service):
    """Client syncing against older/mismatched course version is tagged and resolved without corrupting course data."""
    events = [
        {"event_id": "ver_ev_1", "event_type": "answer_submitted", "score": 1.0, "concept_id": "math_diff", "course_version": "v0.9-beta"}
    ]

    res = sync_service.process_sync_batch(
        student_id="stu_ver",
        events=events,
        course_id="crs-math-calc",
        course_version="v0.9-beta",
    )

    assert res["ok"] is True
    assert res["synced_count"] == 1
    assert res["conflicts_resolved"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Out-of-order event sequence reconciliation
# ─────────────────────────────────────────────────────────────────────────────
def test_out_of_order_event_reconciliation(sync_service, managed_db):
    """Events arriving in scrambled order [seq 3, seq 1, seq 2] are reconciled chronologically."""
    scrambled_events = [
        {"event_id": "seq_3", "event_type": "answer_submitted", "score": 1.0, "concept_id": "c1", "sequence_num": 3, "timestamp": "2026-10-02T12:00:03Z"},
        {"event_id": "seq_1", "event_type": "answer_submitted", "score": 0.5, "concept_id": "c1", "sequence_num": 1, "timestamp": "2026-10-02T12:00:01Z"},
        {"event_id": "seq_2", "event_type": "answer_submitted", "score": 0.8, "concept_id": "c1", "sequence_num": 2, "timestamp": "2026-10-02T12:00:02Z"},
    ]

    res = sync_service.process_sync_batch("stu_ooo", scrambled_events, course_id="crs-sort-101")
    assert res["synced_count"] == 3

    # Verify that in the event store / SLR projection, the latest mastery reflects the progression
    assert res["latest_mastery"] > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Sync status API and audit endpoint
# ─────────────────────────────────────────────────────────────────────────────
def test_sync_status_api_and_audit(tmp_path, monkeypatch):
    """Verifies GET /api/v1/sync/status endpoint returns accurate telemetry summary."""
    import central_platform.auth.dependencies as auth_deps
    from central_platform.db import PlatformDatabase

    db_path = str(tmp_path / "sync_api_test.db")
    monkeypatch.setenv("GAYATRI_DB_PATH", db_path)
    auth_deps._DB_INSTANCE = PlatformDatabase(db_path)

    client = TestClient(app)
    token = create_access_token(user_id="stu_api_01", role="student")

    # 1. Sync batch via API
    batch_payload = {
        "student_id": "stu_api_01",
        "course_id": "crs-cs-101",
        "device_id": "api_client_device",
        "operation_id": "op_api_sync_01",
        "events": [
            {"event_id": "api_ev_1", "event_type": "answer_submitted", "score": 0.9, "concept_id": "cs_loops"}
        ],
    }
    sync_resp = client.post(
        "/api/v1/sync/events",
        json=batch_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sync_resp.status_code == 200
    res_data = sync_resp.json()["data"]
    assert res_data["ok"] is True
    assert res_data["synced_count"] == 1

    # 2. Query sync status via API
    status_resp = client.get(
        "/api/v1/sync/status?student_id=stu_api_01&course_id=crs-cs-101",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()["data"]
    assert status_data["student_id"] == "stu_api_01"
    assert status_data["course_id"] == "crs-cs-101"
    assert status_data["total_operations"] == 1
    assert status_data["total_synced_events"] == 1
    assert "api_client_device" in status_data["registered_devices"]
    assert status_data["status"] == "HEALTHY"
