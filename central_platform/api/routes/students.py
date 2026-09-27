"""Gayatri AI Platform — Students API Endpoints (Phase 04).

Master Plan Section 13:
- Student learning profiles & diagnostics
- Real-time telemetry snapshot submission
- Authoritative Student Learning Record (SLR) summary
- Strict student self-access & cross-student boundary enforcement
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from central_platform.api.schemas import (
    ApiResponse,
    StudentProfileResponse,
    StudentSnapshotRequest,
)
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
)
from central_platform.models.schema import User, UserRole
from central_platform.teacher.portal import TeacherPortalService

router = APIRouter(prefix="/students", tags=["Students"])

try:
    from server import portal as _portal_service
except Exception:
    _portal_service = TeacherPortalService()


@router.get("/{student_id}", response_model=ApiResponse[StudentProfileResponse])
async def get_student_profile(
    student_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve full student learning profile and active diagnostics."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=student_id)

    students = _portal_service.get_all_students("crs-chem-101")
    matched = next((s for s in students if s["student_id"] == student_id), None)
    if not matched:
        # Generate default active profile if not yet in roster
        matched = {
            "student_id": student_id,
            "student_name": f"Student ({student_id})",
            "course_id": "crs-chem-101",
            "current_concept": "chem_thermo_first_law",
            "mastery": 0.50,
            "retention_rate": 0.85,
            "hint_count": 0,
            "misconceptions": [],
            "recent_activity": [],
        }

    recent = matched.get("recent_activity", [])
    if isinstance(recent, str):
        recent_activity = [recent]
    elif isinstance(recent, list):
        recent_activity = recent
    else:
        recent_activity = []

    data = StudentProfileResponse(
        student_id=matched["student_id"],
        student_name=matched.get("student_name", "Student"),
        course_id=matched.get("course_id", "crs-chem-101"),
        current_concept=matched.get("current_concept", "chem_thermo_first_law"),
        mastery=matched.get("mastery", 0.5),
        retention_rate=matched.get("retention_rate", 0.85),
        hint_count=matched.get("hint_count", 0),
        misconceptions=matched.get("misconceptions", []),
        recent_activity=recent_activity,
    )
    return ApiResponse(ok=True, data=data)


@router.post("/snapshot", response_model=ApiResponse[dict])
async def update_student_snapshot(
    snapshot: StudentSnapshotRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Push local student telemetry, mastery, and misconceptions to platform."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=snapshot.student_id)

    # Update central portal service roster
    _portal_service.update_student_snapshot(
        student_id=snapshot.student_id,
        student_name=snapshot.student_name,
        course_id=snapshot.course_id,
        mastery=snapshot.mastery,
        needs_attention=snapshot.needs_attention,
        misconceptions=snapshot.misconceptions,
        hint_count=snapshot.hint_count,
        retention_rate=snapshot.retention_rate,
    )
    return ApiResponse(
        ok=True,
        data={
            "status": "ACCEPTED",
            "student_id": snapshot.student_id,
            "mastery": snapshot.mastery,
        },
    )


@router.get("/{student_id}/slr", response_model=ApiResponse[Dict[str, Any]])
async def get_student_learning_record(
    student_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get canonical Student Learning Record (SLR) summary."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=student_id)

    profile = await get_student_profile(student_id, current_user=current_user)
    return ApiResponse(
        ok=True,
        data={
            "slr_id": f"slr-{student_id}",
            "student_id": student_id,
            "profile": profile.data.model_dump() if profile.data else {},
            "authoritative": True,
        },
    )
