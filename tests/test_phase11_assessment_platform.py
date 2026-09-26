"""Unit test suite for Unified Assessment Platform (Phase 11)."""

import pytest
from central_platform.assessment.builder import (
    AssessmentBuilder,
    AssessmentSubmission,
    QuestionItem,
)


def test_assessment_creation_and_ai_grading():
    builder = AssessmentBuilder()

    q1 = QuestionItem("q1", "fractions", "What is 1/2 + 1/2?", "1")
    q2 = QuestionItem("q2", "fractions", "What is 3/4 - 1/4?", "1/2")
    builder.add_question(q1)
    builder.add_question(q2)

    builder.create_assessment("quiz_101", ["q1", "q2"])

    sub = AssessmentSubmission(
        submission_id="sub_1",
        assessment_id="quiz_101",
        student_id="student_1",
        answers={"q1": "1", "q2": "1/2"},  # Both correct
    )

    graded_sub = builder.submit_assessment(sub)
    assert graded_sub.is_graded is True
    assert graded_sub.ai_score == 1.0
    assert graded_sub.teacher_approved is False

    # Approve grading
    assert builder.approve_grading("sub_1") is True
    assert graded_sub.teacher_approved is True
