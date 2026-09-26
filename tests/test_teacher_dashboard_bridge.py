"""Unit test suite verifying Teacher Dashboard bridge slots."""

import json
import pytest
from app.bridge.facade import Bridge


@pytest.fixture
def bridge():
    return Bridge()


def test_get_teacher_dashboard_bridge_slot(bridge):
    raw_res = bridge.get_teacher_dashboard("crs-chem-101")
    res = json.loads(raw_res)

    assert res["ok"] is True
    assert res["course_id"] == "crs-chem-101"
    assert res["total_students"] == 1
    assert res["class_health_status"] == "Excellent"


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


def test_sync_with_central_server_offline_handling(bridge):
    # Tests that when an invalid/offline server port is supplied, it handles gracefully without crashing
    raw_res = bridge.sync_with_central_server("http://127.0.0.1:59999")
    res = json.loads(raw_res)
    assert res["ok"] is False
    assert "error" in res

