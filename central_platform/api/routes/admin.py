"""Gayatri AI Platform — Admin API Endpoints (Phase 02)."""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from central_platform.api.schemas import ApiResponse

router = APIRouter(prefix="/admin", tags=["Administration"])

_KILL_SWITCH = {"active": False, "reason": ""}


@router.get("/organizations", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_organizations():
    """List all registered educational organizations."""
    return ApiResponse(
        ok=True,
        data=[
            {
                "org_id": "org-central",
                "name": "Central Academy",
                "tier": "ENTERPRISE",
                "student_quota": 500,
                "created_at": "2026-09-01T00:00:00Z",
            }
        ],
    )


@router.get("/system-health", response_model=ApiResponse[Dict[str, Any]])
async def get_system_health():
    """Get system resource and services status."""
    return ApiResponse(
        ok=True,
        data={
            "api_server": "ONLINE",
            "database": "ONLINE",
            "ai_gateway": "ONLINE",
            "sync_service": "ONLINE",
            "kill_switch": _KILL_SWITCH["active"],
        },
    )


@router.post("/kill-switch", response_model=ApiResponse[Dict[str, Any]])
async def toggle_kill_switch(active: bool, reason: str = ""):
    """Admin emergency AI kill switch control."""
    _KILL_SWITCH["active"] = active
    _KILL_SWITCH["reason"] = reason
    return ApiResponse(ok=True, data={"kill_switch_active": active, "reason": reason})
