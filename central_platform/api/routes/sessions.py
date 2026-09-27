"""Gayatri AI Platform — Tutoring Sessions API Endpoints (Phase 04).

Master Plan Section 13:
- Session initiation and lifecycle management
- Student session isolation (modified session_id -> 403 Forbidden)
- Payload identity spoofing defense (modified student_id -> 403 Forbidden)
"""
from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from central_platform.api.schemas import ApiResponse, SessionResponse, SessionStartRequest
from central_platform.auth.dependencies import (
    enforce_resource_boundaries,
    get_current_user_optional,
)
from central_platform.models.schema import User, UserRole

router = APIRouter(prefix="/sessions", tags=["Sessions"])

_ACTIVE_SESSIONS = {}


@router.post("/start", response_model=ApiResponse[SessionResponse], status_code=status.HTTP_201_CREATED)
async def start_session(
    req: SessionStartRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Start an interactive adaptive tutoring session for a student."""
    if current_user and current_user.role == UserRole.STUDENT:
        if req.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: student_id in request body does not match authenticated student",
            )

    sess_id = f"sess-{uuid.uuid4().hex[:8]}"
    resp = SessionResponse(
        session_id=sess_id,
        student_id=req.student_id,
        course_id=req.course_id,
        active_concept=req.initial_concept or "chem_thermo_first_law",
        status="ACTIVE",
    )
    _ACTIVE_SESSIONS[sess_id] = resp
    return ApiResponse(ok=True, data=resp)


@router.get("/{session_id}", response_model=ApiResponse[SessionResponse])
async def get_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get active session details."""
    sess = _ACTIVE_SESSIONS.get(session_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if current_user:
        enforce_resource_boundaries(current_user, target_session_student_id=sess.student_id)

    return ApiResponse(ok=True, data=sess)
