"""Gayatri AI Platform — Courses API Endpoints (Phase 02)."""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, status
from central_platform.api.schemas import ApiResponse, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

_COURSES = [
    CourseResponse(
        course_id="crs-chem-101",
        title="NCERT Class 11-12 Chemistry",
        description="Comprehensive physical and inorganic chemistry adaptive curriculum.",
        subject="Chemistry",
        grade_level="Class 11-12",
        total_concepts=18,
        version="v1.0",
    ),
    CourseResponse(
        course_id="crs-math-09",
        title="Grade 9 Mathematics",
        description="CBSE Grade 9 foundation mathematics.",
        subject="Mathematics",
        grade_level="Grade 9",
        total_concepts=14,
        version="v1.0",
    ),
]


@router.get("", response_model=ApiResponse[List[CourseResponse]])
async def list_courses():
    """List all available courses."""
    return ApiResponse(ok=True, data=_COURSES)


@router.get("/{course_id}", response_model=ApiResponse[CourseResponse])
async def get_course(course_id: str):
    """Get course metadata by course_id."""
    for c in _COURSES:
        if c.course_id == course_id:
            return ApiResponse(ok=True, data=c)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course {course_id} not found")
