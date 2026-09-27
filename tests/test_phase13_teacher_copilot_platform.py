"""Comprehensive Platform Verification Test Suite for Phase 13: Teacher Copilot.

Master Plan Section 22 Invariants:
1. Turn prototype into real retrieval-backed assistant for 6 core queries:
   - "Why is this student struggling?"
   - "What concepts are weak?"
   - "What changed recently?"
   - "Which students need intervention?"
   - "What should I assign?"
   - "Summarize this student's last week"
2. Every student-specific statement must be traceable to authorized data.
3. Output structure: answer, evidence, source records, confidence, recommended action.
4. Zero fabrication: never fabricate student performance (unknown students return confidence 0.0).
5. Authorization isolation: never expose unauthorized students (RBAC 403 Forbidden).
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import User, UserRole
from central_platform.slr.record import StudentLearningRecord
from central_platform.teacher.copilot import (
    CopilotEvidenceItem,
    CopilotResponse,
    CopilotSourceRecord,
    TeacherCopilot,
)


@pytest.fixture
def copilot_engine():
    copilot = TeacherCopilot()
    # Register struggling student
    s1 = StudentLearningRecord("student_struggling_01")
    s1.update_concept_mastery("thermodynamics_first_law", 0.42)
    s1.update_concept_mastery("chemical_equilibrium", 0.78)
    s1.add_event(
        "evt_01",
        "mistake",
        "Confused work sign convention W = -P*deltaV",
        metadata={"concept_id": "thermodynamics_first_law"},
    )
    s1.add_event(
        "evt_02",
        "assessment_failed",
        "Failed Quiz 2 on First Law of Thermodynamics (Score: 40%)",
        metadata={"concept_id": "thermodynamics_first_law"},
    )
    copilot.register_learning_record(s1)

    # Register proficient student
    s2 = StudentLearningRecord("student_proficient_02")
    s2.update_concept_mastery("thermodynamics_first_law", 0.92)
    s2.update_concept_mastery("chemical_equilibrium", 0.88)
    s2.add_event("evt_03", "session", "Completed module on Le Chatelier's Principle")
    copilot.register_learning_record(s2)

    return copilot


def test_copilot_why_student_struggling(copilot_engine):
    """Query 1: 'Why is this student struggling?' identifies root blockers with citations and evidence."""
    resp = copilot_engine.query(
        "Why is this student struggling?", student_id="student_struggling_01"
    )

    assert isinstance(resp, CopilotResponse)
    assert "student_struggling_01" in resp.answer
    assert "thermodynamics_first_law" in resp.answer or "0.42" in resp.answer
    assert resp.confidence >= 0.80
    assert len(resp.evidence) >= 1
    assert len(resp.source_records) >= 1
    assert resp.recommended_action != ""

    # Verify evidence traceability
    evidence_categories = [e.category for e in resp.evidence]
    assert "low_mastery" in evidence_categories or "mistake" in evidence_categories


def test_copilot_what_concepts_are_weak(copilot_engine):
    """Query 2: 'What concepts are weak?' extracts concepts below 0.60 threshold."""
    resp = copilot_engine.query(
        "What concepts are weak?", student_id="student_struggling_01"
    )

    assert "thermodynamics_first_law" in resp.answer
    assert "chemical_equilibrium" not in resp.answer  # Equilibrium is 0.78 (proficient)
    assert len(resp.evidence) == 1
    assert resp.evidence[0].concept_id == "thermodynamics_first_law"
    assert resp.evidence[0].metric_value == 0.42
    assert resp.confidence >= 0.90
    assert "thermodynamics_first_law" in resp.recommended_focus_concept


def test_copilot_what_changed_recently(copilot_engine):
    """Query 3: 'What changed recently?' evaluates event velocity over the time window."""
    resp = copilot_engine.query(
        "What changed recently?", student_id="student_struggling_01", time_window_days=7
    )

    assert "student_struggling_01" in resp.answer
    assert len(resp.evidence) >= 1
    assert resp.confidence >= 0.85
    assert len(resp.source_records) >= 1


def test_copilot_which_students_need_intervention(copilot_engine):
    """Query 4: 'Which students need intervention?' scans cohort and flags at-risk students."""
    resp = copilot_engine.query("Which students need intervention?")

    assert "student_struggling_01" in resp.answer
    assert resp.confidence >= 0.90
    assert len(resp.evidence) >= 1
    assert any("student_struggling_01" in e.description for e in resp.evidence)


def test_copilot_what_should_i_assign(copilot_engine):
    """Query 5: 'What should I assign?' recommends practice targeting weakest concept."""
    resp = copilot_engine.query(
        "What should I assign?", student_id="student_struggling_01"
    )

    assert "thermodynamics_first_law" in resp.answer
    assert resp.recommended_focus_concept == "thermodynamics_first_law"
    assert "practice" in resp.recommended_action.lower() or "assign" in resp.recommended_action.lower()
    assert resp.confidence >= 0.90


def test_copilot_summarize_student_last_week(copilot_engine):
    """Query 6: 'Summarize this student's last week' provides 7-day retrospective timeline."""
    resp = copilot_engine.query(
        "Summarize this student's last week", student_id="student_struggling_01"
    )

    assert "7-Day" in resp.answer or "week" in resp.answer.lower()
    assert "student_struggling_01" in resp.answer
    assert len(resp.evidence) >= 1
    assert resp.confidence >= 0.90


def test_zero_fabrication_on_unknown_student(copilot_engine):
    """Invariant: Copilot MUST NEVER fabricate performance for unknown or unrecorded students."""
    resp = copilot_engine.query(
        "Why is this student struggling?", student_id="non_existent_student_9999"
    )

    assert resp.confidence == 0.0
    assert len(resp.evidence) == 0
    assert len(resp.source_records) == 0
    assert "No learning evidence found" in resp.answer
    assert len(resp.citations) == 0


def test_traceability_of_source_records(copilot_engine):
    """Invariant: Every statement in response is backed by explicit source records."""
    resp = copilot_engine.query(
        "Why is this student struggling?", student_id="student_struggling_01"
    )

    assert len(resp.source_records) > 0
    for record in resp.source_records:
        assert record.record_id != ""
        assert record.record_type in ("mastery", "mistake", "assessment_failed", "event", "misconception")
        assert record.summary != ""


def test_rest_api_copilot_query_endpoint():
    """Verify POST /api/v1/teachers/copilot/query with teacher authorization."""
    client = TestClient(app)
    token = create_access_token(user_id="t_copilot_1", role="TEACHER")

    # Query cohort overview
    payload = {
        "query": "Summarize overall cohort progress and critical misconceptions.",
        "course_id": "crs-chem-101",
    }
    res = client.post(
        "/api/v1/teachers/copilot/query",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "answer" in data
    assert "confidence" in data
    assert "recommended_action" in data
    assert isinstance(data["evidence"], list)
    assert isinstance(data["source_records"], list)


def test_rest_api_copilot_student_forbidden_for_students():
    """Invariant: Students are strictly forbidden from accessing Teacher Copilot."""
    client = TestClient(app)
    token = create_access_token(user_id="student_forbidden_01", role="STUDENT")

    payload = {"query": "What concepts are weak?"}
    res = client.post(
        "/api/v1/teachers/copilot/query",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]


def test_rest_api_copilot_teacher_scoping_isolation(monkeypatch):
    """Invariant: Teachers cannot access students outside their assigned cohort."""
    client = TestClient(app)
    teacher_token = create_access_token(user_id="t_restricted_01", role="TEACHER")

    monkeypatch.setattr(
        PlatformDatabase,
        "get_assigned_student_ids_for_teacher",
        lambda self, tid: {"student_allowed_01"},
    )

    # Attempt to query unauthorized student
    payload = {
        "query": "Why is this student struggling?",
        "student_id": "student_unauthorized_99",
    }
    res = client.post(
        "/api/v1/teachers/copilot/query",
        json=payload,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res.status_code == 403
    assert "not assigned to this teacher" in res.json()["detail"]
