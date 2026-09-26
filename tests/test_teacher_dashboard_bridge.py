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
