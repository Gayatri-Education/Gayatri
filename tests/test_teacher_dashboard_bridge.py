"""Unit test suite verifying Teacher Dashboard bridge slots."""

import json
import pytest
from app.bridge.facade import Bridge


@pytest.fixture
def bridge():
    from app.bridge.facade import (
        Bridge,
        get_teacher_instruction_engine,
        get_teacher_intervention_engine,
        get_teacher_portal_service,
    )
    from central_platform.teacher.instruction import TeacherInstruction
    from central_platform.teacher.intervention import AlertSeverity, TeacherAlert

    portal = get_teacher_portal_service()
    portal.register_student_snapshot(
        student_id="test_student_1",
        name="Test Student",
        course_id="crs-chem-101",
        mastery=0.85,
        chapter_mastery={"Thermodynamics": 0.88, "Chemical Bonding": 0.84},
    )

    inst_engine = get_teacher_instruction_engine()
    inst_engine.add_instruction(
        TeacherInstruction(
            instruction_id="inst-seed-01",
            teacher_id="tchr-101",
            student_id="all",
            course_id="crs-chem-101",
            instruction_text="Emphasize IUPAC sign conventions: work done by system is negative (-w).",
            priority=2,
        )
    )

    alert_engine = get_teacher_intervention_engine()
    alert_engine.raise_alert(
        TeacherAlert(
            alert_id="alt-b01",
            student_id="test_student_1",
            course_id="crs-chem-101",
            alert_type="repeated_failure",
            severity=AlertSeverity.CRITICAL,
            message="Test Student encountered repeated sign convention error.",
        )
    )

    return Bridge()


def test_get_teacher_dashboard_bridge_slot(bridge):
    raw_res = bridge.get_teacher_dashboard("crs-chem-101")
    res = json.loads(raw_res)

    assert res["ok"] is True
    assert res["course_id"] == "crs-chem-101"
    assert res["total_students"] >= 1
    assert res["class_health_status"] in ("Excellent", "Good")
    assert "chapter_averages" in res
    assert "alerts" in res
    assert "instructions" in res


def test_add_teacher_instruction_bridge_slot(bridge):
    raw_res = bridge.add_teacher_instruction("tchr-1", "stu-1", "Focus on Hess Law formula derivation")
    res = json.loads(raw_res)

    assert res["ok"] is True
    assert res["instruction_id"].startswith("inst-")


def test_teacher_instruction_persistence():
    from app.bridge.facade import get_teacher_instruction_engine
    engine = get_teacher_instruction_engine()
    instructions = engine.get_instructions_for_student("stu-1", "crs-chem-101")
    assert any("Hess Law" in i.instruction_text for i in instructions)


def test_resolve_teacher_alert_bridge_slot(bridge):
    raw_res = bridge.resolve_teacher_alert("alt-b01")
    res = json.loads(raw_res)
    assert res["ok"] is True


def test_toggle_teacher_instruction_bridge_slot(bridge):
    raw_res = bridge.toggle_teacher_instruction("inst-seed-01")
    res = json.loads(raw_res)
    assert res["ok"] is True


def test_sync_with_central_server_offline_handling(bridge):
    # Tests that when an invalid/offline server port is supplied, it handles gracefully without crashing
    raw_res = bridge.sync_with_central_server("http://127.0.0.1:59999")
    res = json.loads(raw_res)
    assert res["ok"] is False
    assert "error" in res
