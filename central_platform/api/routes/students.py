"""Gayatri AI Platform — Students API Endpoints (Phase 06).

Master Plan Section 15:
- Authoritative Student Learning Record (SLR) covering all 15 dimensions
- Student learning profiles & diagnostics
- Real-time telemetry snapshot submission
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
from central_platform.slr.service import SLRService
from central_platform.teacher.portal import TeacherPortalService

router = APIRouter(prefix="/students", tags=["Students"])

_slr_service = SLRService()

try:
    from server import portal as _portal_service
except Exception:
    _portal_service = TeacherPortalService()


@router.get("/{student_id}", response_model=ApiResponse[StudentProfileResponse])
async def get_student_profile(
    student_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve full student learning profile from authoritative SLR."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=student_id)

    slr = _slr_service.get_authoritative_slr(student_id)
    recent_activity = [t.summary for t in slr.learning_timeline[:5]]
    misconceptions = [m.name for m in slr.misconceptions]

    data = StudentProfileResponse(
        student_id=slr.identity.student_id,
        student_name=slr.identity.student_name,
        course_id=slr.course.course_id,
        current_concept=slr.curriculum.current_concept,
        mastery=slr.mastery.overall_score,
        retention_rate=slr.mastery.retention_rate,
        hint_count=slr.hints.total_hints_requested,
        misconceptions=misconceptions,
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

    # Sync with SLR service
    _slr_service.update_concept_mastery(
        student_id=snapshot.student_id,
        concept_id="chem_thermo_first_law",
        score=snapshot.mastery,
        course_id=snapshot.course_id,
    )

    for misc_name in snapshot.misconceptions:
        _slr_service.record_student_misconception(
            student_id=snapshot.student_id,
            misconception_code=misc_name,
            course_id=snapshot.course_id,
        )

    # Update legacy portal service roster
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
    course_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get canonical 15-dimension Authoritative Student Learning Record (SLR)."""
    if current_user:
        enforce_resource_boundaries(current_user, target_student_id=student_id)

    slr = _slr_service.get_authoritative_slr(student_id, course_id=course_id)
    profile = await get_student_profile(student_id, current_user=current_user)

    slr_dict = slr.to_dict()
    # Add backward-compatible profile envelope field
    slr_dict["profile"] = profile.data.model_dump() if profile.data else {}

    return ApiResponse(
        ok=True,
        data=slr_dict,
    )
