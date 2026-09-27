"""Data models for Student Progress & Analytics (Phase 09).

Master Plan Section 18:
Covers all 14 canonical dimensions exposed from authoritative SLR data:
1. overall mastery
2. topic mastery
3. concept heatmap
4. recent sessions
5. recent activity
6. weak areas
7. misconceptions
8. accuracy trends
9. mastery trends
10. question-type performance
11. review due
12. recommendations (strictly policy-generated)
13. session summary
14. learning streak
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TopicMastery:
    topic_id: str
    topic_name: str
    concept_count: int
    mastery_score: float
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HeatmapNode:
    concept_id: str
    concept_name: str
    domain: str
    mastery_score: float
    confidence: float
    status: str  # NEW, LEARNING, PRACTICING, PROFICIENT, MASTERED, REVIEW_DUE
    color: str  # Hex color code for UI
    is_review_due: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WeakArea:
    concept_id: str
    concept_name: str
    mastery_score: float
    mastery_gap: float
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AccuracyTrendPoint:
    timestamp: str
    accuracy: float
    event_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MasteryTrendPoint:
    timestamp: str
    mastery: float
    event_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuestionTypeMetric:
    question_type: str
    attempts: int
    correct: int
    accuracy: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewDueItem:
    concept_id: str
    concept_name: str
    due_at: str
    overdue_days: int
    current_mastery: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningStreak:
    current_streak_days: int
    longest_streak_days: int
    active_days_last_30: int
    last_active_date: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionSummary:
    session_id: str
    concept_id: str
    status: str
    questions_attempted: int
    accuracy: float
    duration_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudentProgressReport:
    """Canonical 14-dimension Student Learning Progress Report."""
    student_id: str
    course_id: str
    generated_at: str = field(default_factory=_now_iso)

    # 1. Overall Mastery
    overall_mastery: float = 0.50

    # 2. Topic Mastery
    topic_mastery: List[TopicMastery] = field(default_factory=list)

    # 3. Concept Heatmap
    concept_heatmap: List[HeatmapNode] = field(default_factory=list)

    # 4. Recent Sessions
    recent_sessions: List[Dict[str, Any]] = field(default_factory=list)

    # 5. Recent Activity
    recent_activity: List[Dict[str, Any]] = field(default_factory=list)

    # 6. Weak Areas
    weak_areas: List[WeakArea] = field(default_factory=list)

    # 7. Misconceptions
    misconceptions: List[Dict[str, Any]] = field(default_factory=list)

    # 8. Accuracy Trends
    accuracy_trends: List[AccuracyTrendPoint] = field(default_factory=list)

    # 9. Mastery Trends
    mastery_trends: List[MasteryTrendPoint] = field(default_factory=list)

    # 10. Question-Type Performance
    question_type_performance: Dict[str, QuestionTypeMetric] = field(default_factory=dict)

    # 11. Review Due
    review_due: List[ReviewDueItem] = field(default_factory=list)

    # 12. Policy-driven Recommendations (No free-form LLM text)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # 13. Session Summary
    session_summary: Optional[SessionSummary] = None

    # 14. Learning Streak
    learning_streak: LearningStreak = field(
        default_factory=lambda: LearningStreak(0, 0, 0, "")
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "generated_at": self.generated_at,
            "overall_mastery": round(self.overall_mastery, 4),
            "topic_mastery": [t.to_dict() for t in self.topic_mastery],
            "concept_heatmap": [h.to_dict() for h in self.concept_heatmap],
            "recent_sessions": self.recent_sessions,
            "recent_activity": self.recent_activity,
            "weak_areas": [w.to_dict() for w in self.weak_areas],
            "misconceptions": self.misconceptions,
            "accuracy_trends": [a.to_dict() for a in self.accuracy_trends],
            "mastery_trends": [m.to_dict() for m in self.mastery_trends],
            "question_type_performance": {
                k: v.to_dict() for k, v in self.question_type_performance.items()
            },
            "review_due": [r.to_dict() for r in self.review_due],
            "recommendations": self.recommendations,
            "session_summary": self.session_summary.to_dict() if self.session_summary else None,
            "learning_streak": self.learning_streak.to_dict(),
        }
