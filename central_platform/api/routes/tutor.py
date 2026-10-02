"""Gayatri AI Platform — Generic Tutor Orchestrator REST Routes (Phase 10).

Exposes the course-independent 16-step tutoring lifecycle over HTTP REST.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from central_platform.auth.dependencies import get_current_user_optional, get_db
from central_platform.courses.service import CourseNotFoundError
from central_platform.db import PlatformDatabase
from central_platform.models.schema import User
from central_platform.tutor.orchestrator import (
    EnrollmentError,
    GenericTutorOrchestrator,
    TutorTurnRequest,
    TutorTurnResult,
)

logger = logging.getLogger("gayatri.api.routes.tutor")

router = APIRouter(prefix="/tutor", tags=["Tutor Orchestrator"])


class TutorTurnApiRequest(BaseModel):
    """REST request body for submitting a course tutoring turn."""
    student_id: str = Field(..., description="Student unique identifier")
    session_id: str = Field(..., description="Active session unique identifier")
    course_id: str = Field(..., description="Target course unique identifier")
    message: Optional[str] = Field(None, description="Student query or message")
    student_input: Optional[str] = Field(None, description="Alternative alias for student query")
    course_version_id: Optional[str] = Field(None, description="Optional pinned course version")
    class_id: Optional[str] = Field(None, description="Optional class/cohort identifier")
    concept_id: Optional[str] = Field(None, description="Optional target concept identifier")
    max_tokens: int = Field(512, ge=1, le=4096, description="Max generation tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    preferred_provider: Optional[str] = Field(None, description="Requested provider")
    preferred_model: Optional[str] = Field(None, description="Requested model")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation turns")


class TutorTurnApiResponse(BaseModel):
    """REST response body for a completed tutoring turn."""
    turn_id: str
    session_id: str
    student_id: str
    course_id: str
    concept_id: str
    response_text: str
    pedagogical_action: str
    validation_passed: bool
    state_committed: bool
    rag_sources_used: List[str] = Field(default_factory=list)
    tools_invoked: List[str] = Field(default_factory=list)
    teacher_instructions_applied: int = 0
    latency_ms: float = 0.0
    provider_used: str = "local"
    model_used: str = "default"
    status: str = "SUCCESS"
    validation_issues: List[Dict[str, Any]] = Field(default_factory=list)
    applied_instruction_ids: List[str] = Field(default_factory=list)
    contributed_source_ids: List[str] = Field(default_factory=list)
    contributed_chunk_ids: List[str] = Field(default_factory=list)
    provenance_records: List[Dict[str, Any]] = Field(default_factory=list)
    ok: bool = True
    assistant_text: Optional[str] = None


@router.post("/turn", response_model=TutorTurnApiResponse)
async def submit_tutor_turn(
    req: TutorTurnApiRequest,
    db: PlatformDatabase = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> TutorTurnApiResponse:
    query_text = req.message or req.student_input or ""
    if not query_text.strip():
        raise HTTPException(status_code=400, detail="Missing message or student_input text.")

    try:
        orchestrator = GenericTutorOrchestrator(db=db)
        turn_req = TutorTurnRequest(
            student_id=req.student_id,
            session_id=req.session_id,
            course_id=req.course_id,
            message=query_text,
            course_version_id=req.course_version_id,
            class_id=req.class_id,
            concept_id=req.concept_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            preferred_provider=req.preferred_provider,
            preferred_model=req.preferred_model,
            conversation_history=req.conversation_history,
        )
        res: TutorTurnResult = orchestrator.execute_turn(turn_req)
        turn_dict = res.to_dict()
        turn_dict["ok"] = (res.status == "SUCCESS")
        turn_dict["assistant_text"] = res.response_text
        return TutorTurnApiResponse(**turn_dict)

    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except EnrollmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error in tutor turn endpoint: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tutoring turn execution failed.")
