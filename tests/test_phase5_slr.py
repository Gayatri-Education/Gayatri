"""Unit test suite for Central Learning Record (SLR) (Phase 5)."""

import pytest
from central_platform.slr.record import StudentLearningRecord


def test_slr_event_aggregation_and_timeline():
    slr = StudentLearningRecord("student_100")

    slr.add_event("evt_1", "assessment", "Completed Diagnostic Quiz", "2026-09-26T10:00:00")
    slr.add_event("evt_2", "mastery_change", "Fractions mastery updated to 0.85", "2026-09-26T10:15:00")
    slr.add_event("evt_3", "teacher_intervention", "Teacher assigned remediation exercise", "2026-09-26T10:30:00")

    timeline = slr.get_timeline(reverse=False)
    assert len(timeline) == 3
    assert timeline[0].item_id == "evt_1"
    assert timeline[2].item_id == "evt_3"

    rev_timeline = slr.get_timeline(reverse=True)
    assert rev_timeline[0].item_id == "evt_3"


def test_slr_mastery_snapshot():
    slr = StudentLearningRecord("student_200")
    slr.update_concept_mastery("fractions_basic", 0.90)
    slr.update_concept_mastery("fractions_addition", 0.65)

    snapshot = slr.get_mastery_snapshot()
    assert snapshot["fractions_basic"] == 0.90
    assert snapshot["fractions_addition"] == 0.65
