"""Phase 36 — Decision Explainability Subsystem Unit & Integration Tests.

Verifies:
1. ExplanationType enum values and RecommendationExplanation serialization.
2. "Why am I seeing this?" content recommendation explanations.
3. "Why was I flagged?" intervention explanations with misconception evidence.
4. "Why is this my next lesson?" curriculum prerequisite sequence explanations.
5. "Why is this concept due for review?" spaced repetition decay explanations.
"""

import pytest

from central_platform.explainability.engine import (
    ExplainabilityEngine,
    ExplanationType,
    RecommendationExplanation,
)


def test_explanation_type_enum_and_dataclass():
    expl = RecommendationExplanation(
        student_id="std_101",
        explanation_type=ExplanationType.WHY_SEEING_THIS,
        title="Test Title",
        summary="Test Summary",
    )
    assert expl.explanation_type == ExplanationType.WHY_SEEING_THIS
    d = expl.to_dict()
    assert d["explanation_type"] == "why_seeing_this"
    assert d["student_id"] == "std_101"


def test_explain_content_recommendation():
    expl = ExplainabilityEngine.explain_content_recommendation(
        student_id="std_101",
        concept_name="Organic Chemistry",
        learner_state={"mastery_score": 62.5, "recent_mistakes_count": 2},
    )
    assert isinstance(expl, RecommendationExplanation)
    assert expl.explanation_type == ExplanationType.WHY_SEEING_THIS
    assert "Organic Chemistry" in expl.title
    assert "62.5%" in expl.summary
    assert len(expl.evidence_list) >= 2
    assert "62.5%" in expl.evidence_list[0]
    assert expl.pedagogical_justification != ""


def test_explain_flagged_intervention():
    events = [
        {"item_id": "Q101", "misconception_detected": True},
        {"item_id": "Q102", "misconception_detected": True},
    ]
    expl = ExplainabilityEngine.explain_flagged_intervention(
        student_id="std_102",
        misconception_name="Sign Flips in Equations",
        learning_events=events,
    )
    assert expl.explanation_type == ExplanationType.WHY_FLAGGED
    assert "Sign Flips in Equations" in expl.summary
    assert len(expl.evidence_list) >= 2
    assert "2 consecutive" in expl.evidence_list[1]


def test_explain_next_lesson():
    prereqs = {"Algebra Fundamentals": 85.0, "Linear Equations": 90.0}
    expl = ExplainabilityEngine.explain_next_lesson(
        student_id="std_103",
        target_lesson="Quadratic Equations",
        prerequisite_masteries=prereqs,
    )
    assert expl.explanation_type == ExplanationType.WHY_NEXT_LESSON
    assert "Quadratic Equations" in expl.title
    assert "successfully mastered" in expl.summary
    assert len(expl.evidence_list) == 2


def test_explain_review_schedule():
    expl = ExplainabilityEngine.explain_review_schedule(
        student_id="std_104",
        concept_name="Photosynthesis",
        days_since_last_review=14,
        retention_probability=0.72,
    )
    assert expl.explanation_type == ExplanationType.WHY_DUE_FOR_REVIEW
    assert "Photosynthesis" in expl.title
    assert "72.0%" in expl.summary
    assert len(expl.evidence_list) == 3
    assert "14 days ago" in expl.evidence_list[0]
