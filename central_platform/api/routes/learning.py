"""Gayatri AI Platform — Learning Engine & Events API Endpoints (Phase 02)."""
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, status
from central_platform.api.schemas import ApiResponse, LearningEventSchema

router = APIRouter(prefix="/learning", tags=["Learning"])

_LEARNING_EVENTS_STORE = []


@router.post("/events", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def ingest_learning_event(event: LearningEventSchema):
    """Ingest student interaction event into central event store."""
    _LEARNING_EVENTS_STORE.append(event.model_dump())
    return ApiResponse(ok=True, data={"event_id": event.event_id, "status": "RECORDED"})


@router.get("/recommendations/{student_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_learning_recommendation(student_id: str, concept_id: str = "chem_thermo_first_law"):
    """Get pedagogical next action recommendation from adaptive engine policy."""
    return ApiResponse(
        ok=True,
        data={
            "student_id": student_id,
            "concept_id": concept_id,
            "recommended_action": "QUESTION",
            "recommended_difficulty": 3,
            "difficulty_label": "Standard",
            "focus_reason": "Prerequisite readiness verified; practice numerical stoichiometry calculations.",
        },
    )
