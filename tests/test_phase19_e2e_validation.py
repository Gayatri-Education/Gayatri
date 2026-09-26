"""Unit and integration test suite for Phase 19: End-to-End System Validation."""

import pytest
from central_platform.e2e.validator import E2EValidator


@pytest.fixture
def e2e_validator(tmp_path):
    db_file = str(tmp_path / "e2e_test.db")
    return E2EValidator(db_file)


def test_e2e_student_lifecycle(e2e_validator):
    result = e2e_validator.run_student_lifecycle()
    assert result.scenario == "student_lifecycle"
    assert result.passed is True
    assert result.details["assessment_score"] == 1.0


def test_e2e_teacher_lifecycle(e2e_validator):
    result = e2e_validator.run_teacher_lifecycle()
    assert result.scenario == "teacher_lifecycle"
    assert result.passed is True
    assert result.details["citations_count"] >= 1
