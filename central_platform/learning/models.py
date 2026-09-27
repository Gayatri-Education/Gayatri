"""Data models for the Central Platform Learning Engine Bridge (Phase 07).

Master Plan Section 16:
- Student action payloads
- Engine action results with pedagogical routing, updated mastery, and SLR
- Backtest history representations
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.slr.models import AuthoritativeSLR, SLRAlert, SLRRecommendation


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StudentActionPayload:
    """Action submitted by a student or tutor adapter."""
    concept_id: str
    action_type: str = "answer_submitted"  # "answer_submitted", "hint_requested", "misconception_exhibited", "concept_reviewed"
    course_id: Optional[str] = "crs-chem-101"
    session_id: Optional[str] = None
    turn_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answer: Optional[str] = None
    correctness: Optional[str] = None  # "correct", "partially_correct", "incorrect", "uncertain"
    score: Optional[float] = None
    hint_level: int = 0
    difficulty: Optional[float] = None  # 1.0 to 5.0 or 0.2 to 1.0
    response_time_ms: Optional[float] = None
    misconception_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineActionResult:
    """Canonical result of the connected learning engine pipeline."""
    event_id: str
    student_id: str
    concept_id: str
    course_id: str
    mastery_score: float
    mastery_delta: float
    difficulty_level: int  # 1 to 5
    difficulty_label: str  # "Recall", "Basic", "Standard", "Multi-step", "Advanced"
    next_review_at: str  # ISO timestamp
    pedagogical_action: str  # "MASTERED", "REMEDIATE_PREREQUISITE", "EXPLAIN_CONCEPT", "TEST_AND_HINT", "CHALLENGE_QUESTION"
    target_concept: str
    pedagogical_reason: str
    recommended_mode: str = "QUESTION"  # "SUMMARY", "REMEDIATE", "EXPLAIN", "QUESTION"
    misconception: Optional[Dict[str, Any]] = None
    candidate_concepts: List[Dict[str, Any]] = field(default_factory=list)
    slr: Optional[AuthoritativeSLR] = None
    recommendations: List[SLRRecommendation] = field(default_factory=list)
    alerts: List[SLRAlert] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        def _dump(item: Any) -> Any:
            if hasattr(item, "to_dict"):
                return item.to_dict()
            if hasattr(item, "model_dump"):
                return item.model_dump()
            if hasattr(item, "dict"):
                return item.dict()
            return item

        res = {
            "event_id": self.event_id,
            "student_id": self.student_id,
            "concept_id": self.concept_id,
            "course_id": self.course_id,
            "mastery_score": round(self.mastery_score, 4),
            "mastery_delta": round(self.mastery_delta, 4),
            "difficulty_level": self.difficulty_level,
            "difficulty_label": self.difficulty_label,
            "next_review_at": self.next_review_at,
            "pedagogical_action": self.pedagogical_action,
            "target_concept": self.target_concept,
            "pedagogical_reason": self.pedagogical_reason,
            "recommended_mode": self.recommended_mode,
            "misconception": self.misconception,
            "candidate_concepts": self.candidate_concepts,
            "recommendations": [_dump(r) for r in self.recommendations],
            "alerts": [_dump(a) for a in self.alerts],
            "timestamp": self.timestamp,
        }
        if self.slr is not None:
            res["slr"] = self.slr.to_dict()
        return res

