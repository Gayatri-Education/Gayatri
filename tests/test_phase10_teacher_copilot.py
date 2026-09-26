"""Unit test suite for Teacher AI Copilot (Phase 10)."""

import pytest
from central_platform.slr.record import StudentLearningRecord
from central_platform.teacher.copilot import TeacherCopilot


def test_copilot_summarizes_student_sessions_with_citations():
    copilot = TeacherCopilot()
    record = StudentLearningRecord("student_101")
    record.add_event("evt_1", "assessment", "Scored 85% on Algebra Quiz")
    record.add_event("evt_2", "mistake", "Confused sign in equation solving")
    copilot.register_learning_record(record)

    response = copilot.summarize_student_sessions("student_101")
    assert "student_101" in response.answer
    assert len(response.citations) == 2
    assert response.citations[0].evidence_id == "evt_1"


def test_copilot_identifies_learning_gaps():
    copilot = TeacherCopilot()
    record = StudentLearningRecord("student_202")
    record.update_concept_mastery("linear_equations", 0.90)
    record.update_concept_mastery("quadratic_equations", 0.45)  # Gap
    copilot.register_learning_record(record)

    response = copilot.identify_learning_gaps("student_202")
    assert "quadratic_equations" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].evidence_id == "mastery_quadratic_equations"
