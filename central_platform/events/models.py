"""Pydantic schemas and serialization models for central learning events (Phase 05).

Master Plan Section 14:
- Ingestion models with rigorous event_type validation
- Batch ingestion support
- Query filtering schemas
- Event replay projection structures
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from central_platform.events.types import LearningEventType


class LearningEventIngest(BaseModel):
    """Authoritative learning event ingestion contract (Section 14)."""
    event_id: str = Field(..., min_length=1, description="Globally unique event identifier")
    student_id: str = Field(..., min_length=1, description="Student subject identifier")
    organization_id: str = Field(default="org-default", description="Tenant organization scope")
    course_id: str = Field(default="crs-chem-101", description="Academic course scope")
    session_id: str = Field(..., min_length=1, description="Session identifier")
    event_type: LearningEventType = Field(..., description="One of the 20 canonical event types")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp",
    )
    source: str = Field(default="student_desktop", description="Source subsystem")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific metadata")
    schema_version: str = Field(default="1.0.0", description="Event contract version")

    # Additional turn-level fields supported for compatibility
    turn_id: Optional[str] = Field(default=None)
    concept_id: Optional[str] = Field(default=None)
    correctness: Optional[str] = Field(default=None)
    hint_used: Optional[int] = Field(default=None)
    difficulty: Optional[float] = Field(default=None)
    score: Optional[float] = Field(default=None)
    misconception_code: Optional[str] = Field(default=None)

    @field_validator("event_type", mode="before")
    @classmethod
    def validate_canonical_event_type(cls, v: Any) -> LearningEventType:
        if isinstance(v, LearningEventType):
            return v
        if isinstance(v, str):
            try:
                return LearningEventType(v)
            except ValueError:
                raise ValueError(
                    f"Invalid event_type '{v}'. Must be one of the 20 canonical types: "
                    f"{[e.value for e in LearningEventType]}"
                )
        raise ValueError("event_type must be a valid string or LearningEventType enum")

    def model_post_init(self, __context: Any) -> None:
        """Consolidate root fields into payload dictionary for uniform downstream consumption."""
        if self.turn_id and "turn_id" not in self.payload:
            self.payload["turn_id"] = self.turn_id
        if self.concept_id and "concept_id" not in self.payload:
            self.payload["concept_id"] = self.concept_id
        if self.correctness and "correctness" not in self.payload:
            self.payload["correctness"] = self.correctness
        if self.hint_used is not None and "hint_used" not in self.payload:
            self.payload["hint_used"] = self.hint_used
        if self.difficulty is not None and "difficulty" not in self.payload:
            self.payload["difficulty"] = self.difficulty
        if self.score is not None and "score" not in self.payload:
            self.payload["score"] = self.score
        if self.misconception_code and "misconception_code" not in self.payload:
            self.payload["misconception_code"] = self.misconception_code


class BatchLearningEventIngest(BaseModel):
    """Batch ingestion payload for high-throughput sync."""
    events: List[LearningEventIngest] = Field(..., min_length=1)


class LearningEventFilter(BaseModel):
    """Query parameters for filtering event stream."""
    student_id: Optional[str] = None
    organization_id: Optional[str] = None
    course_id: Optional[str] = None
    session_id: Optional[str] = None
    event_type: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)


class ReplayProjectionResult(BaseModel):
    """Projected pedagogical state resulting from chronological event replay."""
    student_id: str
    organization_id: str
    total_events: int
    current_mastery: float
    concept_mastery: Dict[str, float] = Field(default_factory=dict)
    concepts_introduced: List[str]
    concepts_mastered: List[str]
    active_misconceptions: List[str]
    recovered_misconceptions: List[str]
    questions_attempted: int
    questions_correct: int
    hints_used: int
    teacher_instructions_count: int
    last_event_timestamp: Optional[str] = None
