"""Gayatri AI Platform — Tutoring Sessions API Endpoints (Phase 02)."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException, status
from central_platform.api.schemas import ApiResponse, SessionResponse, SessionStartRequest

router = APIRouter(prefix="/sessions", tags=["Sessions"])

_ACTIVE_SESSIONS = {}


@router.post("/start", response_model=ApiResponse[SessionResponse], status_code=status.HTTP_201_CREATED)
async def start_session(req: SessionStartRequest):
    """Start an interactive adaptive tutoring session for a student."""
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
async def get_session(session_id: str):
    """Get active session details."""
    sess = _ACTIVE_SESSIONS.get(session_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return ApiResponse(ok=True, data=sess)
