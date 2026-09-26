"""Unit test suite for Adaptive Teacher Intervention (Phase 9)."""

import pytest
from central_platform.teacher.intervention import (
    AlertSeverity,
    AlertStatus,
    TeacherAlert,
    TeacherInterventionEngine,
)


def test_alert_raising_and_filtering():
    engine = TeacherInterventionEngine()

    alert1 = TeacherAlert(
        alert_id="alt_1",
        student_id="s1",
        course_id="c_math",
        alert_type="repeated_failure",
        severity=AlertSeverity.CRITICAL,
        message="Student failed quiz 3 times.",
        assigned_teacher_id="t_1",
    )
    alert2 = TeacherAlert(
        alert_id="alt_2",
        student_id="s2",
        course_id="c_phys",
        alert_type="mastery_regression",
        severity=AlertSeverity.WARNING,
        message="Physics mastery dropped.",
        assigned_teacher_id="t_2",
    )

    engine.raise_alert(alert1)
    engine.raise_alert(alert2)

    math_alerts = engine.get_alerts_for_teacher(teacher_id="t_1", course_id="c_math")
    assert len(math_alerts) == 1
    assert math_alerts[0].alert_id == "alt_1"
    assert math_alerts[0].status == AlertStatus.DETECTED


def test_alert_lifecycle_transitions():
    engine = TeacherInterventionEngine()
    alert = TeacherAlert(
        alert_id="alt_10",
        student_id="s1",
        course_id="c_math",
        alert_type="inactivity",
        severity=AlertSeverity.INFO,
        message="No activity for 5 days.",
    )
    engine.raise_alert(alert)

    assert engine.transition_alert_status("alt_10", AlertStatus.ACKNOWLEDGED) is True
    alerts = engine.get_alerts_for_teacher()
    assert alerts[0].status == AlertStatus.ACKNOWLEDGED

    assert engine.transition_alert_status("alt_10", AlertStatus.RESOLVED) is True
    assert alerts[0].status == AlertStatus.RESOLVED
