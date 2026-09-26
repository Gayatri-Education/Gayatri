"""Unit and simulation test suite for Student Identity and Sync (Phase 4)."""

import pytest
from central_platform.sync.manager import SyncEvent, SyncManager


def test_device_binding_and_authorization():
    sync_mgr = SyncManager()
    sync_mgr.bind_device("device_laptop_1", "student_42")

    assert sync_mgr.get_bound_student("device_laptop_1") == "student_42"
    assert sync_mgr.get_bound_student("unregistered_device") is None

    # Valid event queueing
    event = SyncEvent(
        event_id="evt_001",
        student_id="student_42",
        device_id="device_laptop_1",
        event_type="quiz_attempt",
        payload={"score": 100},
    )
    assert sync_mgr.queue_offline_event(event) is True

    # Unauthorized device event should raise PermissionError
    unauthorized_event = SyncEvent(
        event_id="evt_002",
        student_id="student_42",
        device_id="unregistered_device",
        event_type="quiz_attempt",
        payload={"score": 50},
    )
    with pytest.raises(PermissionError):
        sync_mgr.queue_offline_event(unauthorized_event)


def test_offline_sync_idempotency_and_reconciliation():
    sync_mgr = SyncManager()
    sync_mgr.bind_device("device_tab_1", "student_99")

    e1 = SyncEvent("evt_101", "student_99", "device_tab_1", "assessment", {"result": "pass"})
    e2 = SyncEvent("evt_102", "student_99", "device_tab_1", "assessment", {"result": "pass"})

    sync_mgr.queue_offline_event(e1)
    sync_mgr.queue_offline_event(e2)

    # First sync execution
    res1 = sync_mgr.process_sync()
    assert res1["synced"] == 2
    assert res1["duplicates"] == 0

    # Re-submitting duplicate event e1
    sync_mgr.queue_offline_event(e1)
    res2 = sync_mgr.process_sync()
    assert res2["synced"] == 0
    assert res2["duplicates"] == 1
