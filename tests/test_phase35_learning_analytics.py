"""Phase 35 — Learning Analytics Subsystem Unit & Integration Tests.

Verifies:
1. LearningHealthLevel classification logic (EXCELLENT, GOOD, NEEDS_ATTENTION, AT_RISK).
2. Student learning health computation from learning event evidence.
3. Class/cohort learning health aggregate calculation.
4. Section learning health aggregate calculation.
5. Institution wide learning health metrics.
6. Edge cases: empty event lists, zero student enrollments, extreme scores.
"""

import pytest

from central_platform.analytics.engine import (
    ClassHealthMetric,
    InstitutionHealthMetric,
    LearningAnalyticsEngine,
    LearningHealthLevel,
    SectionHealthMetric,
    StudentHealthMetric,
)


def test_classify_health_level():
    assert LearningAnalyticsEngine.classify_health_level(90.0, 0) == LearningHealthLevel.EXCELLENT
    assert LearningAnalyticsEngine.classify_health_level(78.0, 0) == LearningHealthLevel.GOOD
    assert LearningAnalyticsEngine.classify_health_level(62.0, 0) == LearningHealthLevel.NEEDS_ATTENTION
    assert LearningAnalyticsEngine.classify_health_level(45.0, 0) == LearningHealthLevel.AT_RISK
    # Misconceptions trigger AT_RISK even with high score
    assert LearningAnalyticsEngine.classify_health_level(90.0, 3) == LearningHealthLevel.AT_RISK


def test_student_learning_health_computation():
    events = [
        {"score": 90.0, "misconception_detected": False},
        {"score": 85.0, "misconception_detected": False},
        {"score": 95.0, "misconception_detected": False},
    ]
    student_metric = LearningAnalyticsEngine.compute_student_learning_health(
        student_id="std_101",
        student_name="Rahul",
        learning_events=events,
    )
    assert isinstance(student_metric, StudentHealthMetric)
    assert student_metric.mastery_score == 90.0
    assert student_metric.health_level == LearningHealthLevel.EXCELLENT
    assert len(student_metric.evidence_summary) >= 2

    d = student_metric.to_dict()
    assert d["health_level"] == "excellent"


def test_multi_level_analytics_hierarchy():
    # 1. Students
    s1 = LearningAnalyticsEngine.compute_student_learning_health("s1", "Aarav", [{"score": 90.0}])
    s2 = LearningAnalyticsEngine.compute_student_learning_health("s2", "Priya", [{"score": 80.0}])
    s3 = LearningAnalyticsEngine.compute_student_learning_health("s3", "Vikram", [{"score": 40.0}])  # At risk

    student_list = [s1, s2, s3]

    # 2. Class
    class_metric = LearningAnalyticsEngine.compute_class_learning_health("c101", "Physics 101", student_list)
    assert isinstance(class_metric, ClassHealthMetric)
    assert class_metric.enrolled_count == 3
    assert class_metric.at_risk_count == 1
    assert round(class_metric.average_mastery, 1) == 70.0

    # 3. Section
    section_metric = LearningAnalyticsEngine.compute_section_learning_health("sec_A", "Section A", student_list)
    assert isinstance(section_metric, SectionHealthMetric)
    assert section_metric.student_count == 3

    # 4. Institution
    inst_metric = LearningAnalyticsEngine.compute_institution_learning_health(
        org_id="org_01",
        org_name="Gayatri Vidyalaya",
        class_metrics=[class_metric],
    )
    assert isinstance(inst_metric, InstitutionHealthMetric)
    assert inst_metric.total_students == 3
    assert inst_metric.active_interventions_count == 1


def test_analytics_edge_cases_empty_inputs():
    empty_student = LearningAnalyticsEngine.compute_student_learning_health("s0", "New Student", [])
    assert empty_student.health_level == LearningHealthLevel.GOOD

    empty_class = LearningAnalyticsEngine.compute_class_learning_health("c0", "Empty Class", [])
    assert empty_class.enrolled_count == 0

    empty_inst = LearningAnalyticsEngine.compute_institution_learning_health("o0", "Empty Org", [])
    assert empty_inst.total_students == 0
