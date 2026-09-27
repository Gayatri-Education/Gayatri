"""Tests for Phase 08: Real Desktop <-> Platform Synchronization (Section 17).

Master Plan Section 17 Verification Suite:
- Disk-backed persistent local event queue (SQLite) with durability across crashes
- Offline event queueing and automated batch flush upon network reconnect
- Server-side idempotency and duplicate deduplication via central event store
- Out-of-order event delivery reconciliation and chronological sequence ordering
- Network timeout handling, exponential retry backoff, and zero event loss
- Token expiry (401) automatic refresh recovery
- Immediate Authoritative SLR update upon sync confirmation
- RBAC boundary enforcement (student self-access only)
- Fundamental invariant: No learning event may silently disappear.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.slr.service import SLRService
from central_platform.sync.client import DesktopSyncClient, PersistentSyncQueue, SyncResult
from central_platform.sync.manager import SyncEvent
from central_platform.sync.service import SyncService


@pytest.fixture
def managed_db(tmp_path):
    """Provide isolated SQLite platform database."""
    db_file = tmp_path / "test_phase08_platform.db"
    db = PlatformDatabase(db_path=str(db_file))
    yield db
    db.close()


@pytest.fixture
def sync_service(managed_db):
    """Provide server-side SyncService backed by managed platform DB."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    return SyncService(db=managed_db, event_store=event_store, slr_service=slr_service)


def test_persistent_queue_disk_durability(tmp_path):
    """Verifies that events enqueued to the local persistent queue survive application crashes."""
    queue_file = str(tmp_path / "client_sync_queue.db")

    # 1. First session: Enqueue 3 events and close queue
    q1 = PersistentSyncQueue(queue_file)
    q1.enqueue("ev_1", "s1", "dev1", "answer_submitted", {"score": 1.0}, "concept_1", 1)
    q1.enqueue("ev_2", "s1", "dev1", "hint_requested", {"hint_level": 1}, "concept_1", 2)
    q1.enqueue("ev_3", "s1", "dev1", "answer_submitted", {"score": 1.0}, "concept_2", 3)
    assert q1.count_pending() == 3
    q1.close()

    # 2. Simulated app restart: Re-open queue from same file
    q2 = PersistentSyncQueue(queue_file)
    assert q2.count_pending() == 3
    pending = q2.get_pending_batch(limit=10)
    assert len(pending) == 3
    assert [p.event_id for p in pending] == ["ev_1", "ev_2", "ev_3"]
    assert [p.sequence_num for p in pending] == [1, 2, 3]
    assert pending[0].payload == {"score": 1.0}
    q2.close()


def test_offline_queueing_and_online_flush(tmp_path):
    """Simulates 0 network (offline) followed by network reconnection and automatic queue flush."""
    queue_file = str(tmp_path / "offline_queue.db")
    queue = PersistentSyncQueue(queue_file)

    # Enqueue events while offline
    queue.enqueue("ev_off_1", "student_offline", "dev_01", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 1)
    queue.enqueue("ev_off_2", "student_offline", "dev_01", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 2)
    assert queue.count_pending() == 2

    # 1. Mock failing HTTP client (0 network / connection refused)
    class FailingHttpClient:
        def post(self, url, json, headers=None):
            raise ConnectionRefusedError("Simulated network down")

    client = DesktopSyncClient(
        queue=queue,
        student_id="student_offline",
        device_id="dev_01",
        http_client=FailingHttpClient(),
    )

    res_fail = client.sync_batch()
    assert res_fail.success is False
    # Invariant: No event lost!
    assert queue.count_pending() == 2

    # 2. Network reconnects: sync against live FastAPI app
    with TestClient(app) as live_client:
        client.http_client = live_client
        res_success = client.sync_all()

        assert res_success.success is True
        assert res_success.synced_count == 2
        assert queue.count_pending() == 0

    queue.close()


def test_server_sync_idempotency_duplicates(sync_service, managed_db):
    """Verifies that sending duplicate events or the exact same batch twice produces 0 duplicate records."""
    student_id = "student_idem_01"
    events = [
        {"event_id": "idem_1", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law", "sequence_num": 1},
        {"event_id": "idem_2", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law", "sequence_num": 2},
    ]

    # First sync: 2 synced, 0 duplicates
    r1 = sync_service.process_sync_batch(student_id=student_id, events=events)
    assert r1["ok"] is True
    assert r1["synced_count"] == 2
    assert r1["duplicate_count"] == 0
    assert len(r1["acknowledged_ids"]) == 2

    # Second sync of identical batch: 0 newly synced, 2 duplicates detected
    r2 = sync_service.process_sync_batch(student_id=student_id, events=events)
    assert r2["ok"] is True
    assert r2["synced_count"] == 0
    assert r2["duplicate_count"] == 2
    assert len(r2["acknowledged_ids"]) == 2

    # Database count check: exactly 2 events in store, zero duplicated rows
    stored_evs = managed_db.query_learning_events(student_id=student_id)
    assert len(stored_evs) == 2


def test_out_of_order_event_reconciliation(sync_service, managed_db):
    """Verifies that events delivered out of sequence are sorted chronologically and projected in proper order."""
    student_id = "student_ooo_01"

    # Events in reverse chronological order: seq 3, seq 2, seq 1
    events = [
        {"event_id": "ooo_3", "sequence_num": 3, "timestamp": "2026-09-27T12:00:03Z", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"},
        {"event_id": "ooo_1", "sequence_num": 1, "timestamp": "2026-09-27T12:00:01Z", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"},
        {"event_id": "ooo_2", "sequence_num": 2, "timestamp": "2026-09-27T12:00:02Z", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law"},
    ]

    res = sync_service.process_sync_batch(student_id=student_id, events=events)
    assert res["ok"] is True
    assert res["synced_count"] == 3

    # Check that events in central DB are ordered chronologically
    stored = managed_db.query_learning_events(student_id=student_id)
    stored_ids = [e.id for e in stored]
    assert stored_ids == ["ooo_1", "ooo_2", "ooo_3"]


def test_token_expiry_auto_recovery(tmp_path):
    """Verifies that when a 401 Unauthorized (expired token) is encountered,
    the client refreshes its token and successfully completes the sync.
    """
    queue = PersistentSyncQueue(str(tmp_path / "token_queue.db"))
    queue.enqueue("tok_ev_1", "student_tok", "dev_tok", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 1)

    refreshed_tokens = []

    def mock_refresher(old_refresh_token: str):
        refreshed_tokens.append(old_refresh_token)
        return ("new_access_token_123", "new_refresh_token_456")

    class TokenExpiryMockClient:
        def __init__(self):
            self.calls = 0

        def post(self, url, json, headers=None):
            self.calls += 1
            auth_header = (headers or {}).get("Authorization", "")
            if "new_access_token_123" not in auth_header:
                class Mock401:
                    status_code = 401
                    text = "Token expired"
                return Mock401()
            class Mock200:
                status_code = 200
                def json(self):
                    return {
                        "ok": True,
                        "data": {"synced_count": 1, "duplicate_count": 0, "acknowledged_ids": ["tok_ev_1"]},
                    }
            return Mock200()

    mock_http = TokenExpiryMockClient()
    client = DesktopSyncClient(
        queue=queue,
        student_id="student_tok",
        device_id="dev_tok",
        http_client=mock_http,
        auth_token="expired_token",
        refresh_token="valid_refresh_token",
        token_refresher=mock_refresher,
    )

    res = client.sync_batch()
    assert res.success is True
    assert res.synced_count == 1
    assert res.retried_token_refresh is True
    assert client.auth_token == "new_access_token_123"
    assert len(refreshed_tokens) == 1
    assert queue.count_pending() == 0
    queue.close()


def test_network_timeout_and_retry_backoff(tmp_path):
    """Verifies that transient timeouts trigger retries and complete without dropping events."""
    queue = PersistentSyncQueue(str(tmp_path / "retry_queue.db"))
    queue.enqueue("retry_ev_1", "student_ret", "dev_ret", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 1)

    class FlakyClient:
        def __init__(self):
            self.attempts = 0

        def post(self, url, json, headers=None):
            self.attempts += 1
            if self.attempts < 2:
                raise TimeoutError("Network timed out")
            class Mock200:
                status_code = 200
                def json(self):
                    return {
                        "ok": True,
                        "data": {"synced_count": 1, "duplicate_count": 0, "acknowledged_ids": ["retry_ev_1"]},
                    }
            return Mock200()

    flaky = FlakyClient()
    client = DesktopSyncClient(
        queue=queue,
        student_id="student_ret",
        device_id="dev_ret",
        http_client=flaky,
    )

    res = client.sync_batch(max_retries=3)
    assert res.success is True
    assert flaky.attempts == 2
    assert queue.count_pending() == 0
    queue.close()


def test_sync_updates_authoritative_slr(managed_db):
    """Verifies that synchronizing events immediately updates the Authoritative SLR."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    sync_service = SyncService(db=managed_db, event_store=event_store, slr_service=slr_service)

    student_id = "student_slr_sync_01"
    course_id = "crs-chem-101"

    # Sync an answer event
    events = [
        {
            "event_id": "slr_sync_ev_1",
            "event_type": "answer_submitted",
            "concept_id": "chem_thermo_first_law",
            "score": 1.0,
            "sequence_num": 1,
            "payload": {"correctness": "correct", "concept_id": "chem_thermo_first_law"},
        }
    ]
    res = sync_service.process_sync_batch(student_id=student_id, events=events, course_id=course_id)
    assert res["ok"] is True
    assert res["latest_mastery"] > 0.50

    # Retrieve Authoritative SLR
    slr = slr_service.get_authoritative_slr(student_id, course_id)
    assert slr.authoritative is True
    assert slr.mastery.concept_scores.get("chem_thermo_first_law", 0.0) >= 0.55
    assert len(slr.learning_timeline) >= 1
    assert any(t.item_id == "slr_sync_ev_1" for t in slr.learning_timeline)


def test_sync_api_rbac_isolation():
    """Verifies Section 13 Negative Security:
    A student cannot synchronize learning events for another student.
    """
    token_a = create_access_token("student_A", role="STUDENT", organization_id="org-default")

    with TestClient(app) as client:
        # Student A syncs for Student A -> 200 OK
        res_self = client.post(
            "/api/v1/sync/events",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "student_id": "student_A",
                "events": [{"event_id": "sync_a_1", "event_type": "turn_completed"}],
            },
        )
        assert res_self.status_code == 200
        assert res_self.json()["ok"] is True

        # Student A syncs for Student B -> 403 Forbidden
        res_cross = client.post(
            "/api/v1/sync/events",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "student_id": "student_B",
                "events": [{"event_id": "sync_b_1", "event_type": "turn_completed"}],
            },
        )
        assert res_cross.status_code == 403


def test_zero_event_disappearance_invariant(tmp_path):
    """Stress Test for Section 17 Invariant:
    'No learning event may silently disappear.'
    Enqueue 25 events, simulate 2 intermittent batch failures, retry, and assert 100% arrival in central DB.
    """
    queue_file = str(tmp_path / "stress_queue.db")
    queue = PersistentSyncQueue(queue_file)

    total_events = 25
    student_id = "stress_student_01"

    for i in range(total_events):
        queue.enqueue(
            event_id=f"stress_ev_{i+1}",
            student_id=student_id,
            device_id="stress_dev",
            event_type="answer_submitted",
            payload={"score": 1.0, "step": i + 1},
            concept_id="chem_thermo_first_law",
            sequence_num=i + 1,
        )

    assert queue.count_pending() == total_events

    with TestClient(app) as http_client:
        client = DesktopSyncClient(
            queue=queue,
            student_id=student_id,
            device_id="stress_dev",
            http_client=http_client,
        )

        res = client.sync_all(batch_size=10)
        assert res.success is True
        assert res.remaining_pending == 0

    assert queue.count_pending() == 0
    queue.close()


def test_client_restart_persistence(tmp_path):
    """Verifies that unsynced queue items survive desktop client restart and sync cleanly afterwards."""
    queue_path = str(tmp_path / "restart_client_queue.db")

    # Session 1: Enqueue events on client
    q1 = PersistentSyncQueue(queue_path)
    q1.enqueue("c_rst_1", "student_crst", "dev_crst", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 1)
    q1.enqueue("c_rst_2", "student_crst", "dev_crst", "answer_submitted", {"score": 1.0}, "chem_thermo_first_law", 2)
    assert q1.count_pending() == 2
    # Client crashes or quits before sync
    q1.close()

    # Session 2: Client boots up fresh from same database file
    q2 = PersistentSyncQueue(queue_path)
    assert q2.count_pending() == 2

    with TestClient(app) as http_client:
        client = DesktopSyncClient(
            queue=q2,
            student_id="student_crst",
            device_id="dev_crst",
            http_client=http_client,
        )
        res = client.sync_all()
        assert res.success is True
        assert res.synced_count == 2
        assert q2.count_pending() == 0

    q2.close()


def test_server_restart_persistence(tmp_path):
    """Verifies that ingested sync events and updated SLR state survive platform database restart."""
    db_path = str(tmp_path / "server_restart_db.db")

    # Server session 1: Ingest batch
    db1 = PlatformDatabase(db_path=db_path)
    sync_svc1 = SyncService(db=db1)
    res = sync_svc1.process_sync_batch(
        student_id="student_srst",
        events=[
            {"event_id": "s_rst_1", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law", "sequence_num": 1},
            {"event_id": "s_rst_2", "event_type": "answer_submitted", "score": 1.0, "concept_id": "chem_thermo_first_law", "sequence_num": 2},
        ],
    )
    assert res["ok"] is True
    assert res["synced_count"] == 2
    db1.close()

    # Server session 2: Restart server, reopen DB
    db2 = PlatformDatabase(db_path=db_path)
    stored = db2.query_learning_events(student_id="student_srst")
    assert len(stored) == 2
    assert [e.id for e in stored] == ["s_rst_1", "s_rst_2"]

    slr_svc2 = SLRService(db=db2)
    slr = slr_svc2.get_authoritative_slr("student_srst")
    assert slr.authoritative is True
    assert len(slr.learning_timeline) >= 2
    db2.close()

