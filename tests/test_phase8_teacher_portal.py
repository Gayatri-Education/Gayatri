"""Unit test suite for Teacher Portal MVP (Phase 8)."""

import pytest
from central_platform.teacher.portal import TeacherPortalService


def test_teacher_dashboard_overview_aggregation():
    portal = TeacherPortalService()

    portal.register_student_snapshot("s1", "Alice", "c_math", 0.90, needs_attention=False)
    portal.register_student_snapshot("s2", "Bob", "c_math", 0.40, needs_attention=True)
    portal.register_student_snapshot("s3", "Charlie", "c_math", 0.85, needs_attention=False)

    overview = portal.get_dashboard_overview("c_math")
    assert overview.total_students == 3
    assert overview.students_needing_attention == 1
    assert overview.average_mastery == round((0.90 + 0.40 + 0.85) / 3, 3)
    assert overview.class_health_status == "Good"

    attention_list = portal.get_students_needing_attention("c_math")
    assert len(attention_list) == 1
    assert attention_list[0]["id"] == "s2"


def test_teacher_dashboard_course_isolation():
    portal = TeacherPortalService()
    portal.register_student_snapshot("s1", "Alice", "c_math", 0.90)
    portal.register_student_snapshot("s10", "Dave", "c_phys", 0.30, needs_attention=True)

    math_overview = portal.get_dashboard_overview("c_math")
    assert math_overview.total_students == 1
    assert math_overview.students_needing_attention == 0

    phys_overview = portal.get_dashboard_overview("c_phys")
    assert phys_overview.total_students == 1
    assert phys_overview.students_needing_attention == 1
