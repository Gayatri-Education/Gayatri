"""Gayatri AI Platform — Synchronization API Endpoints (Phase 02)."""
from __future__ import annotations

from fastapi import APIRouter
from central_platform.api.schemas import ApiResponse, BatchSyncEventsRequest, BatchSyncEventsResponse
from central_platform.sync.manager import SyncManager, SyncEvent

router = APIRouter(prefix="/sync", tags=["Sync"])

try:
    from server import sync_manager as _sync_manager
except Exception:
    _sync_manager = SyncManager()


@router.post("/events", response_model=ApiResponse[BatchSyncEventsResponse])
async def sync_events(batch: BatchSyncEventsRequest):
    """Batch synchronize offline/local student events with central platform."""
    count = 0
    for ev in batch.events:
        sync_ev = SyncEvent(
            event_id=ev.get("event_id", f"sync-{count}"),
            student_id=batch.student_id,
            device_id=ev.get("device_id", f"device-{batch.student_id}"),
            event_type=ev.get("event_type", "turn_completed"),
            payload=ev,
            timestamp=ev.get("timestamp", ""),
        )
        _sync_manager.record_event(sync_ev)
        count += 1

    return ApiResponse(
        ok=True,
        data=BatchSyncEventsResponse(
            ok=True,
            synced_count=count,
            failed_count=0,
            status="SYNCED",
        ),
    )
