"""Gayatri AI Platform — Enrollments API Endpoints (Phase 02)."""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, status
from central_platform.api.schemas import ApiResponse

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])

_ENROLLMENTS = [
    {"enrollment_id": "enr-01", "student_id": "student_001", "course_id": "crs-chem-101", "status": "ACTIVE"},
    {"enrollment_id": "enr-02", "student_id": "student_002", "course_id": "crs-chem-101", "status": "ACTIVE"},
    {"enrollment_id": "enr-03", "student_id": "student_003", "course_id": "crs-chem-101", "status": "ACTIVE"},
]


@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_enrollments(student_id: str = ""):
    """List course enrollments."""
    results = _ENROLLMENTS
    if student_id:
        results = [e for e in results if e["student_id"] == student_id]
    return ApiResponse(ok=True, data=results)
