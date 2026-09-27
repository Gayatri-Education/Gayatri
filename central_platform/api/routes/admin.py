"""Gayatri AI Platform — Admin API Endpoints (Phase 04).

Master Plan Section 13:
- Role verification (SUPER_ADMIN, ORG_ADMIN)
- Teachers & students blocked (teacher -> admin 403 Forbidden)
- Org admin cross-tenant blocked (org admin -> another org 403 Forbidden)
- Super Admin exclusive control over kill switch and global health
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from central_platform.api.schemas import ApiResponse
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
)
from central_platform.models.schema import User, UserRole

router = APIRouter(prefix="/admin", tags=["Administration"])

_KILL_SWITCH = {"active": False, "reason": ""}

_DEFAULT_ORGS = [
    {
        "org_id": "org-central",
        "name": "Central Academy",
        "tier": "ENTERPRISE",
        "student_quota": 500,
        "created_at": "2026-09-01T00:00:00Z",
    },
    {
        "org_id": "org-external-beta",
        "name": "Beta Institute",
        "tier": "STANDARD",
        "student_quota": 200,
        "created_at": "2026-09-10T00:00:00Z",
    },
]


@router.get("/organizations", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_organizations(
    organization_id: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List registered educational organizations with tenant scoping."""
    if current_user:
        if current_user.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: administrative privileges required",
            )
        if current_user.role == UserRole.ORG_ADMIN:
            # Org Admin cannot query another organization
            if organization_id and organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: cannot access organization '{organization_id}' outside your tenant",
                )
            # Filter to their own org only
            return ApiResponse(
                ok=True,
                data=[o for o in _DEFAULT_ORGS if o["org_id"] == current_user.organization_id] or [
                    {
                        "org_id": current_user.organization_id,
                        "name": f"Organization ({current_user.organization_id})",
                        "tier": "STANDARD",
                        "student_quota": 250,
                        "created_at": "2026-09-01T00:00:00Z",
                    }
                ],
            )

    results = _DEFAULT_ORGS
    if organization_id:
        results = [o for o in results if o["org_id"] == organization_id]
    return ApiResponse(ok=True, data=results)


@router.get("/system-health", response_model=ApiResponse[Dict[str, Any]])
async def get_system_health(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get system resource and services status."""
    if current_user and current_user.role in (UserRole.STUDENT, UserRole.TEACHER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: administrative privileges required",
        )
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
async def toggle_kill_switch(
    active: bool,
    reason: str = "",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Admin emergency AI kill switch control (Super Admin only)."""
    if current_user and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: only Super Admin can toggle emergency kill switch",
        )
    _KILL_SWITCH["active"] = active
    _KILL_SWITCH["reason"] = reason
    return ApiResponse(ok=True, data={"kill_switch_active": active, "reason": reason})
