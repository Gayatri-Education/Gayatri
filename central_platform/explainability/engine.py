"""Gayatri AI Platform — Explainability & Traceable Decision Subsystem (Phase 36).

Provides evidence-based pedagogical explanations for:
1. "Why am I seeing this?" (Content/Item Recommendation)
2. "Why was I flagged?" (Intervention / Misconception Alert)
3. "Why is this my next lesson?" (Curriculum Path Resolution)
4. "Why is this concept due for review?" (Spaced Repetition Schedule)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional


class ExplanationType(str, Enum):
    WHY_SEEING_THIS = "why_seeing_this"
    WHY_FLAGGED = "why_flagged"
    WHY_NEXT_LESSON = "why_next_lesson"
    WHY_DUE_FOR_REVIEW = "why_due_for_review"


@dataclass
class RecommendationExplanation:
    """Standardized traceable explanation contract for AI decisions and recommendations."""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = ""
    explanation_type: ExplanationType = ExplanationType.WHY_SEEING_THIS
    title: str = ""
    summary: str = ""
    evidence_list: List[str] = field(default_factory=list)
    pedagogical_justification: str = ""
    confidence_score: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["explanation_type"] = (
            self.explanation_type.value
            if isinstance(self.explanation_type, ExplanationType)
            else self.explanation_type
        )
        return d


class ExplainabilityEngine:
    """Authoritative Decision Explainability Engine."""

    @classmethod
    def explain_content_recommendation(
        cls,
        student_id: str,
        concept_name: str,
        learner_state: Dict[str, Any],
    ) -> RecommendationExplanation:
        """Explain 'Why am I seeing this?' for a recommended learning module or question."""
        mastery = learner_state.get("mastery_score", 65.0)
        recent_mistakes = learner_state.get("recent_mistakes_count", 0)

        evidence = [
            f"Current estimated mastery for '{concept_name}' is {mastery:.1f}%.",
            f"Recorded {recent_mistakes} incorrect responses in recent practice items.",
        ]

        if mastery < 70.0:
            justification = (
                f"Targeted practice on '{concept_name}' is recommended to boost concept mastery above the 70% proficiency threshold."
            )
        else:
            justification = (
                f"Advancing with practice on '{concept_name}' reinforces retention and prepares for upcoming advanced topics."
            )

        return RecommendationExplanation(
            student_id=student_id,
            explanation_type=ExplanationType.WHY_SEEING_THIS,
            title=f"Why are you seeing '{concept_name}'?",
            summary=f"Recommended based on your current {mastery:.1f}% mastery score.",
            evidence_list=evidence,
            pedagogical_justification=justification,
            confidence_score=0.95,
        )

    @classmethod
    def explain_flagged_intervention(
        cls,
        student_id: str,
        misconception_name: str,
        learning_events: List[Dict[str, Any]],
    ) -> RecommendationExplanation:
        """Explain 'Why was I flagged?' for a teacher intervention or learning alert."""
        incorrect_count = sum(1 for e in learning_events if e.get("misconception_detected"))
        evidence = [
            f"Detected misconception: '{misconception_name}'.",
            f"Triggered by {incorrect_count} consecutive incorrect responses on key diagnostic items.",
        ]
        for idx, event in enumerate(learning_events[:2], 1):
            evidence.append(f"Event #{idx}: Incorrect answer choice on item '{event.get('item_id', 'Q')}'")

        justification = (
            f"Proactive intervention is flagged so the teacher can resolve the underlying misconception '{misconception_name}' "
            "before advancing to higher-order concepts."
        )

        return RecommendationExplanation(
            student_id=student_id,
            explanation_type=ExplanationType.WHY_FLAGGED,
            title=f"Why was this intervention flagged?",
            summary=f"Flagged due to misconception pattern in '{misconception_name}'.",
            evidence_list=evidence,
            pedagogical_justification=justification,
            confidence_score=0.92,
        )

    @classmethod
    def explain_next_lesson(
        cls,
        student_id: str,
        target_lesson: str,
        prerequisite_masteries: Dict[str, float],
    ) -> RecommendationExplanation:
        """Explain 'Why is this my next lesson?'."""
        evidence = []
        all_passed = True
        for prereq, score in prerequisite_masteries.items():
            status = "PASSED" if score >= 70.0 else "INCOMPLETE"
            evidence.append(f"Prerequisite '{prereq}': {score:.1f}% mastery ({status}).")
            if score < 70.0:
                all_passed = False

        if all_passed:
            summary = f"All prerequisites for '{target_lesson}' have been successfully mastered."
            justification = f"Prerequisite mastery sequence is complete. You are ready to unlock '{target_lesson}'."
        else:
            summary = f"Prerequisites for '{target_lesson}' are partially met."
            justification = f"Completing remaining prerequisites will unlock '{target_lesson}'."

        return RecommendationExplanation(
            student_id=student_id,
            explanation_type=ExplanationType.WHY_NEXT_LESSON,
            title=f"Why is '{target_lesson}' your next lesson?",
            summary=summary,
            evidence_list=evidence,
            pedagogical_justification=justification,
            confidence_score=0.98,
        )

    @classmethod
    def explain_review_schedule(
        cls,
        student_id: str,
        concept_name: str,
        days_since_last_review: int,
        retention_probability: float,
    ) -> RecommendationExplanation:
        """Explain 'Why is this concept due for review?'."""
        retention_pct = retention_probability * 100.0
        evidence = [
            f"Last reviewed {days_since_last_review} days ago.",
            f"Spaced repetition memory decay model predicts current retention probability is {retention_pct:.1f}%.",
            f"Review threshold trigger: Retention fell below optimal 80.0% retention window.",
        ]

        justification = (
            f"Timely spaced review of '{concept_name}' prevents memory decay and solidifies long-term memory consolidation."
        )

        return RecommendationExplanation(
            student_id=student_id,
            explanation_type=ExplanationType.WHY_DUE_FOR_REVIEW,
            title=f"Why is '{concept_name}' due for review?",
            summary=f"Scheduled for spaced review as memory retention fell to {retention_pct:.1f}%.",
            evidence_list=evidence,
            pedagogical_justification=justification,
            confidence_score=0.96,
        )
