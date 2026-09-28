"""Authoritative domain models for Unified Assessment Platform (Phase 19).

Supports Question Bank, Diagnostic, Formative, Summative, Adaptive, Assignments,
Attempts, Rubric Scoring, AI-Assisted Grading, and Reassessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


from central_platform.models.schema import AssessmentType


class QuestionType(str, Enum):
    MCQ = "MCQ"
    NUMERICAL = "NUMERICAL"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"
    CODE = "CODE"
    MATCHING = "MATCHING"
    TRUE_FALSE = "TRUE_FALSE"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADING_PENDING = "grading_pending"
    GRADED = "graded"
    REVIEWED = "reviewed"
    ABANDONED = "abandoned"


@dataclass
class RubricCriterion:
    """Individual rubric criterion with weights and score descriptions."""
    criterion_id: str
    name: str
    description: str = ""
    max_points: float = 4.0
    weight: float = 1.0
    levels: Dict[str, str] = field(default_factory=dict)  # score (e.g. "4", "3", "2", "1", "0") -> description

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "name": self.name,
            "description": self.description,
            "max_points": self.max_points,
            "weight": self.weight,
            "levels": self.levels,
        }


@dataclass
class Rubric:
    """Multi-criterion grading rubric."""
    rubric_id: str
    title: str
    description: str = ""
    criteria: List[RubricCriterion] = field(default_factory=list)

    @property
    def total_max_points(self) -> float:
        return sum(c.max_points * c.weight for c in self.criteria)

    def to_dict(self) -> dict:
        return {
            "rubric_id": self.rubric_id,
            "title": self.title,
            "description": self.description,
            "criteria": [c.to_dict() for c in self.criteria],
            "total_max_points": self.total_max_points,
        }


@dataclass
class ItemGradingResult:
    """Grading result for a single question item."""
    item_id: str
    student_answer: Any
    is_correct: bool
    score: float
    max_marks: float
    percentage: float = 0.0
    criterion_scores: Dict[str, float] = field(default_factory=dict)
    feedback: str = ""
    misconception_code: Optional[str] = None
    ai_graded: bool = False
    ai_confidence: float = 1.0
    ai_rationale: str = ""
    teacher_adjusted: bool = False
    teacher_comment: str = ""

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "student_answer": self.student_answer,
            "is_correct": self.is_correct,
            "score": self.score,
            "max_marks": self.max_marks,
            "percentage": self.percentage,
            "criterion_scores": self.criterion_scores,
            "feedback": self.feedback,
            "misconception_code": self.misconception_code,
            "ai_graded": self.ai_graded,
            "ai_confidence": self.ai_confidence,
            "ai_rationale": self.ai_rationale,
            "teacher_adjusted": self.teacher_adjusted,
            "teacher_comment": self.teacher_comment,
        }


@dataclass
class AdaptiveState:
    """Internal state tracking for Computerized Adaptive Testing (CAT)."""
    current_difficulty: int = 1  # 1 to 5
    consecutive_correct: int = 0
    consecutive_incorrect: int = 0
    tested_concepts: List[str] = field(default_factory=list)
    remaining_concepts: List[str] = field(default_factory=list)
    items_administered: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "current_difficulty": self.current_difficulty,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_incorrect": self.consecutive_incorrect,
            "tested_concepts": self.tested_concepts,
            "remaining_concepts": self.remaining_concepts,
            "items_administered": self.items_administered,
            "history": self.history,
        }
