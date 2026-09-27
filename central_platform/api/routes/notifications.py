"""Gayatri AI Platform — Notifications API Endpoints (Phase 02)."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter
from central_platform.api.schemas import ApiResponse, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse[List[NotificationResponse]])
async def list_notifications(recipient_id: str = "usr-current-01"):
    """Retrieve notifications for user."""
    return ApiResponse(
        ok=True,
        data=[
            NotificationResponse(
                notification_id="notif-01",
                recipient_id=recipient_id,
                channel="in_app",
                title="Pedagogical Directive Updated",
                message="Teacher Sharma added a new directive for thermodynamics.",
                created_at="2026-09-27T10:00:00Z",
                is_read=False,
            )
        ],
    )
