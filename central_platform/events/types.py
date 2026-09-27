"""Canonical Learning Event Taxonomy (Phase 05).

Master Plan Section 14:
- 20 canonical learning event types
- Case-insensitive string normalization
- Group categorization helpers
"""

from __future__ import annotations

from enum import Enum
from typing import Set


class LearningEventType(str, Enum):
    # 1. Session Lifecycle
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"

    # 2. Interactive QA Turn
    QUESTION_ATTEMPTED = "question_attempted"
    ANSWER_SUBMITTED = "answer_submitted"
    ANSWER_CORRECTED = "answer_corrected"

    # 3. Socratic Scaffolding & Hints
    HINT_REQUESTED = "hint_requested"
    HINT_USED = "hint_used"

    # 4. Pedagogical Concept Trajectory
    CONCEPT_INTRODUCED = "concept_introduced"
    CONCEPT_REINFORCED = "concept_reinforced"
    CONCEPT_MASTERED = "concept_mastered"

    # 5. Misconception Lifecycle
    MISCONCEPTION_DETECTED = "misconception_detected"
    MISCONCEPTION_RECOVERED = "misconception_recovered"

    # 6. Spaced Review
    REVIEW_COMPLETED = "review_completed"

    # 7. Formal Assessments
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"

    # 8. Teacher Directives & Feedback
    TEACHER_INSTRUCTION_CREATED = "teacher_instruction_created"
    TEACHER_INTERVENTION_CREATED = "teacher_intervention_created"
    TEACHER_FEEDBACK_ADDED = "teacher_feedback_added"

    # 9. Assignments
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_COMPLETED = "assignment_completed"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            norm = value.strip().lower()
            for member in cls:
                if member.value == norm or member.name.lower() == norm:
                    return member
        return super()._missing_(value)


# Group sets for fast category queries
SESSION_EVENTS: Set[LearningEventType] = {
    LearningEventType.SESSION_STARTED,
    LearningEventType.SESSION_COMPLETED,
}

QA_EVENTS: Set[LearningEventType] = {
    LearningEventType.QUESTION_ATTEMPTED,
    LearningEventType.ANSWER_SUBMITTED,
    LearningEventType.ANSWER_CORRECTED,
}

HINT_EVENTS: Set[LearningEventType] = {
    LearningEventType.HINT_REQUESTED,
    LearningEventType.HINT_USED,
}

MASTERY_EVENTS: Set[LearningEventType] = {
    LearningEventType.CONCEPT_INTRODUCED,
    LearningEventType.CONCEPT_REINFORCED,
    LearningEventType.CONCEPT_MASTERED,
}

MISCONCEPTION_EVENTS: Set[LearningEventType] = {
    LearningEventType.MISCONCEPTION_DETECTED,
    LearningEventType.MISCONCEPTION_RECOVERED,
}

TEACHER_EVENTS: Set[LearningEventType] = {
    LearningEventType.TEACHER_INSTRUCTION_CREATED,
    LearningEventType.TEACHER_INTERVENTION_CREATED,
    LearningEventType.TEACHER_FEEDBACK_ADDED,
}

ASSESSMENT_EVENTS: Set[LearningEventType] = {
    LearningEventType.ASSESSMENT_STARTED,
    LearningEventType.ASSESSMENT_COMPLETED,
}
