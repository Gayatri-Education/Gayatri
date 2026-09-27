"""Gayatri AI Platform — Synchronization API Endpoints (Phase 08).

Master Plan Section 17:
- Real network synchronization pipeline
- Server-side validation and device authorization
- Idempotency & deduplication filter via LearningEventStore
- Out-of-order event sequence reconciliation
- Permanent storage in central PostgreSQL/SQLite database
- Canonical SLR projection update immediately post-sync
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from central_platform.api.schemas import (
    ApiResponse,
    BatchSyncEventsRequest,
    BatchSyncEventsResponse,
)
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
)
from central_platform.models.schema import User
from central_platform.sync.manager import SyncEvent, SyncManager
from central_platform.sync.service import SyncService

router = APIRouter(prefix="/sync", tags=["Sync"])

_sync_service = SyncService()

try:
    from server import sync_manager as _sync_manager
except Exception:
    _sync_manager = SyncManager()


@router.post("/events", response_model=ApiResponse[BatchSyncEventsResponse])
async def sync_events(
    batch: BatchSyncEventsRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Batch synchronize offline/local student events with central platform."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=batch.student_id)

    # Process through authoritative central sync service
    result = _sync_service.process_sync_batch(
        student_id=batch.student_id,
        events=batch.events,
    )

    # Keep backward compatibility with legacy in-memory manager
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
        try:
            _sync_manager.record_event(sync_ev)
        except Exception:
            pass
        count += 1

    return ApiResponse(
        ok=result["ok"],
        data=BatchSyncEventsResponse(
            ok=result["ok"],
            synced_count=result["synced_count"],
            duplicate_count=result["duplicate_count"],
            failed_count=result["failed_count"],
            acknowledged_ids=result["acknowledged_ids"],
            status=result["status"],
            latest_mastery=result["latest_mastery"],
            server_timestamp=result["server_timestamp"],
        ),
    )
