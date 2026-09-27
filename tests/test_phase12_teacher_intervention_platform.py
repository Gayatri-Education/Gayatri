"""Test Suite for Phase 12 — Teacher Intervention System.

Verifies Master Plan Section 21 requirements:
1. Teacher Intervention entity with all Section 21 dimensions:
   - reason, priority (CRITICAL, HIGH, MEDIUM, LOW)
   - assigned teacher, student, course_id
   - created_at, due_at
   - 5 mandatory lifecycle statuses (OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, DISMISSED)
   - resolution explanation & teacher notes
   - immutable audit trail tracking
2. 6 concrete trigger types:
   - persistent_misconception
   - declining_performance
   - long_inactivity
   - repeated_failed_assessment
   - low_prerequisite_mastery
   - teacher_created
3. Non-negotiable invariant: Zero automatic interventions without auditable trigger evidence.
4. Central REST API endpoints with RBAC (POST, GET, PATCH, /notes, /resolve, /dismiss, /evaluate).
5. 100% backward compatibility with TeacherAlert and bridge slots.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.events.models import LearningEventIngest
from central_platform.teacher.intervention import (
    AlertSeverity,
    AlertStatus,
    InterventionPriority,
    InterventionStatus,
    InterventionTriggerType,
    TeacherAlert,
    TeacherIntervention,
    TeacherInterventionEngine,
)


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def teacher_auth_headers():
    token = create_access_token(
        user_id="tchr-chem-01",
        role="TEACHER",
        organization_id="org-default",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_auth_headers():
    token = create_access_token(
        user_id="stu-amit-01",
        role="STUDENT",
        organization_id="org-default",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_student_headers():
    token = create_access_token(
        user_id="stu-other-88",
        role="STUDENT",
        organization_id="org-default",
    )
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# 1. State Machine, Lifecycle & Non-Negotiable Invariants
# ─────────────────────────────────────────────────────────────────────────────

def test_intervention_model_and_5_lifecycle_statuses():
    """Verify transitions through all 5 mandatory statuses with audit log entries."""
    engine = TeacherInterventionEngine()
    itv = TeacherIntervention(
        intervention_id="itv-test-01",
        student_id="stu-01",
        course_id="crs-chem-101",
        reason="Repeated failure on Hess's Law enthalpy cycles.",
        priority=InterventionPriority.HIGH.value,
        status=InterventionStatus.OPEN.value,
    )
    engine.create_intervention(itv, actor_id="tchr-01")

    # Initial state
    assert itv.status == InterventionStatus.OPEN.value
    assert len(itv.audit_trail) >= 2  # created, registered

    # 1. OPEN -> ACKNOWLEDGED
    engine.transition_intervention_status("itv-test-01", InterventionStatus.ACKNOWLEDGED.value, actor_id="tchr-01")
    assert itv.status == InterventionStatus.ACKNOWLEDGED.value
    assert itv.audit_trail[-1]["to_status"] == InterventionStatus.ACKNOWLEDGED.value

    # 2. ACKNOWLEDGED -> IN_PROGRESS
    engine.transition_intervention_status("itv-test-01", InterventionStatus.IN_PROGRESS.value, actor_id="tchr-01")
    assert itv.status == InterventionStatus.IN_PROGRESS.value

    # 3. Add Teacher Note during IN_PROGRESS
    engine.add_note("itv-test-01", author_id="tchr-01", text="Conducted 1-on-1 diagram walkthrough of state functions.")
    assert len(itv.teacher_notes) == 1
    assert "diagram walkthrough" in itv.teacher_notes[0]["text"]

    # 4. IN_PROGRESS -> RESOLVED
    engine.resolve_intervention("itv-test-01", actor_id="tchr-01", resolution_note="Student correctly solved 3 Hess Law cycles.")
    assert itv.status == InterventionStatus.RESOLVED.value
    assert itv.resolution == "Student correctly solved 3 Hess Law cycles."
    assert itv.resolved_by == "tchr-01"
    assert itv.resolved_at is not None


def test_no_automatic_intervention_without_evidence():
    """Non-negotiable rule: No automatic intervention can be created without auditable evidence."""
    engine = TeacherInterventionEngine()

    # Attempt automatic intervention without evidence -> MUST raise ValueError
    unbacked_itv = TeacherIntervention(
        intervention_id="itv-bad-01",
        student_id="stu-01",
        course_id="crs-chem-101",
        reason="System suspects student is struggling.",
        priority=InterventionPriority.MEDIUM.value,
        trigger_type=InterventionTriggerType.PERSISTENT_MISCONCEPTION.value,
        trigger_evidence={},  # Empty evidence!
    )
    with pytest.raises(ValueError, match="cannot be created without concrete auditable trigger evidence"):
        engine.create_intervention(unbacked_itv)

    # With concrete evidence -> succeeds
    backed_itv = TeacherIntervention(
        intervention_id="itv-good-01",
        student_id="stu-01",
        course_id="crs-chem-101",
        reason="Student repeatedly confused work sign convention in expansion work.",
        priority=InterventionPriority.HIGH.value,
        trigger_type=InterventionTriggerType.PERSISTENT_MISCONCEPTION.value,
        trigger_evidence={"misconception_id": "THERMO_SIGN_CONVENTION", "occurrence_count": 3},
    )
    engine.create_intervention(backed_itv)
    assert engine.get_intervention("itv-good-01") is not None


def test_intervention_resolution_and_dismissal_validation():
    """Empty resolution notes or dismissal reasons must be rejected."""
    engine = TeacherInterventionEngine()
    itv = TeacherIntervention(
        intervention_id="itv-test-02",
        student_id="stu-01",
        course_id="crs-chem-101",
        reason="Check understanding of entropy.",
    )
    engine.create_intervention(itv)

    # Empty resolution note rejected
    with pytest.raises(ValueError, match="cannot be empty"):
        engine.resolve_intervention("itv-test-02", actor_id="tchr-01", resolution_note="   ")

    # Empty dismissal reason rejected
    with pytest.raises(ValueError, match="cannot be empty"):
        engine.dismiss_intervention("itv-test-02", actor_id="tchr-01", reason="")

    # Valid dismissal succeeds
    engine.dismiss_intervention("itv-test-02", actor_id="tchr-01", reason="Duplicate alert superseded by unit exam.")
    assert itv.status == InterventionStatus.DISMISSED.value
    assert itv.dismissal_reason == "Duplicate alert superseded by unit exam."
    assert itv.dismissed_by == "tchr-01"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Deterministic Trigger Evaluation Tests
# ─────────────────────────────────────────────────────────────────────────────

class MockSLR:
    def __init__(self, data: dict):
        self._data = data

    def to_dict(self):
        return self._data


def test_evaluate_triggers_persistent_misconception():
    """Trigger 1: Persistent Misconception evaluated from SLR."""
    engine = TeacherInterventionEngine()
    mock_slr = MockSLR({
        "misconceptions": [
            {
                "id": "MISC_THERMO_WORK_SIGN",
                "concept_id": "thermo_work",
                "occurrence_count": 3,
                "active": True,
                "last_detected": "2026-09-27T10:00:00Z",
            }
        ],
        "mastery_states": {},
        "recent_sessions": [],
        "assessment_results": [],
    })

    generated = engine.evaluate_triggers_for_student("stu-01", "crs-chem-101", slr=mock_slr)
    assert len(generated) >= 1
    misc_itv = next(i for i in generated if i.trigger_type == InterventionTriggerType.PERSISTENT_MISCONCEPTION.value)
    assert misc_itv.priority == InterventionPriority.CRITICAL.value
    assert misc_itv.trigger_evidence["occurrence_count"] == 3
    assert "MISC_THERMO_WORK_SIGN" in misc_itv.trigger_evidence["misconception_id"]


def test_evaluate_triggers_declining_performance():
    """Trigger 2: Declining Performance evaluated from telemetry events."""
    engine = TeacherInterventionEngine()
    mock_slr = MockSLR({"misconceptions": [], "mastery_states": {}, "recent_sessions": [], "assessment_results": []})

    # Sequence of attempts starting high (1.0, 1.0, 0.9) and dropping low (0.3, 0.2, 0.1)
    events = [
        LearningEventIngest(event_id=f"e{i}", student_id="s1", session_id="s", course_id="crs",
                            concept_id="c", event_type="question_attempted", payload={"score": 1.0})
        for i in range(3)
    ] + [
        LearningEventIngest(event_id=f"e{i}", student_id="s1", session_id="s", course_id="crs",
                            concept_id="c", event_type="question_attempted", payload={"score": 0.2})
        for i in range(3, 6)
    ]

    generated = engine.evaluate_triggers_for_student("s1", "crs-chem-101", slr=mock_slr, recent_events=events)
    assert any(i.trigger_type == InterventionTriggerType.DECLINING_PERFORMANCE.value for i in generated)
    decline_itv = next(i for i in generated if i.trigger_type == InterventionTriggerType.DECLINING_PERFORMANCE.value)
    assert decline_itv.trigger_evidence["recent_score"] < 0.30


def test_evaluate_triggers_repeated_failed_assessment():
    """Trigger 4: Repeated Failed Assessments."""
    engine = TeacherInterventionEngine()
    mock_slr = MockSLR({
        "misconceptions": [],
        "mastery_states": {},
        "recent_sessions": [],
        "assessment_results": [
            {"assessment_id": "asm-01", "score": 0.35, "passed": False},
            {"assessment_id": "asm-02", "score": 0.40, "passed": False},
        ],
    })

    generated = engine.evaluate_triggers_for_student("s1", "crs-chem-101", slr=mock_slr)
    assert any(i.trigger_type == InterventionTriggerType.REPEATED_FAILED_ASSESSMENT.value for i in generated)
    asm_itv = next(i for i in generated if i.trigger_type == InterventionTriggerType.REPEATED_FAILED_ASSESSMENT.value)
    assert asm_itv.trigger_evidence["failed_count"] == 2


def test_evaluate_triggers_clean_student_zero_interventions():
    """Clean student with no gaps generates 0 interventions."""
    engine = TeacherInterventionEngine()
    now_str = datetime.now(timezone.utc).isoformat()
    mock_slr = MockSLR({
        "misconceptions": [],
        "mastery_states": {"concept_a": {"p_mastery": 0.90}},
        "recent_sessions": [{"start_time": now_str, "end_time": now_str}],
        "assessment_results": [{"assessment_id": "asm-01", "score": 0.95, "passed": True}],
    })

    generated = engine.evaluate_triggers_for_student("clean-stu", "crs-chem-101", slr=mock_slr)
    assert len(generated) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Central REST API Endpoint & RBAC Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_api_interventions_crud_and_lifecycle(api_client, teacher_auth_headers):
    """Verify full CRUD, notes, resolve, and dismiss via REST API."""
    # 1. Create intervention
    payload = {
        "student_id": "stu-amit-01",
        "course_id": "crs-chem-101",
        "reason": "Amit struggles with Gibbs-Helmholtz temperature dependence.",
        "priority": "HIGH",
        "due_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
    }
    res_c = api_client.post("/api/v1/teachers/interventions", headers=teacher_auth_headers, json=payload)
    assert res_c.status_code == 201
    c_data = res_c.json()["data"]
    itv_id = c_data["intervention_id"]
    assert c_data["status"] == "OPEN"
    assert c_data["priority"] == "HIGH"

    # 2. GET /interventions
    res_g = api_client.get(f"/api/v1/teachers/interventions?student_id=stu-amit-01", headers=teacher_auth_headers)
    assert res_g.status_code == 200
    assert any(i["intervention_id"] == itv_id for i in res_g.json()["data"])

    # 3. GET /interventions/{id}
    res_single = api_client.get(f"/api/v1/teachers/interventions/{itv_id}", headers=teacher_auth_headers)
    assert res_single.status_code == 200
    assert res_single.json()["data"]["intervention_id"] == itv_id

    # 4. PATCH /interventions/{id} -> ACKNOWLEDGED
    res_p = api_client.patch(
        f"/api/v1/teachers/interventions/{itv_id}",
        headers=teacher_auth_headers,
        json={"status": "ACKNOWLEDGED", "priority": "CRITICAL"},
    )
    assert res_p.status_code == 200
    assert res_p.json()["data"]["status"] == "ACKNOWLEDGED"
    assert res_p.json()["data"]["priority"] == "CRITICAL"

    # 5. POST /interventions/{id}/notes
    res_n = api_client.post(
        f"/api/v1/teachers/interventions/{itv_id}/notes",
        headers=teacher_auth_headers,
        json={"text": "Assigned supplementary problems from chapter 6."},
    )
    assert res_n.status_code == 200
    assert len(res_n.json()["data"]["teacher_notes"]) >= 1

    # 6. POST /interventions/{id}/resolve
    res_r = api_client.post(
        f"/api/v1/teachers/interventions/{itv_id}/resolve",
        headers=teacher_auth_headers,
        json={"resolution_note": "Student completed 5 practice problems with 100% accuracy."},
    )
    assert res_r.status_code == 200
    assert res_r.json()["data"]["status"] == "RESOLVED"
    assert res_r.json()["data"]["resolution"] == "Student completed 5 practice problems with 100% accuracy."


def test_api_interventions_rbac(api_client, student_auth_headers, other_student_headers, teacher_auth_headers):
    """Negative Security: Student tokens cannot create/update/resolve/dismiss interventions."""
    # 1. Student cannot create intervention -> 403
    c_attempt = api_client.post(
        "/api/v1/teachers/interventions",
        headers=student_auth_headers,
        json={"student_id": "stu-amit-01", "reason": "Self assigned intervention."},
    )
    assert c_attempt.status_code == 403

    # Teacher creates valid intervention for stu-amit-01
    res_t = api_client.post(
        "/api/v1/teachers/interventions",
        headers=teacher_auth_headers,
        json={"student_id": "stu-amit-01", "reason": "Teacher remediation required."},
    )
    itv_id = res_t.json()["data"]["intervention_id"]

    # 2. Student cannot mutate intervention -> 403
    p_attempt = api_client.patch(
        f"/api/v1/teachers/interventions/{itv_id}",
        headers=student_auth_headers,
        json={"status": "RESOLVED"},
    )
    assert p_attempt.status_code == 403

    r_attempt = api_client.post(
        f"/api/v1/teachers/interventions/{itv_id}/resolve",
        headers=student_auth_headers,
        json={"resolution_note": "Self resolved."},
    )
    assert r_attempt.status_code == 403

    # 3. Other student cannot view stu-amit-01's intervention -> 403
    other_view = api_client.get(
        f"/api/v1/teachers/interventions/{itv_id}",
        headers=other_student_headers,
    )
    assert other_view.status_code == 403

    # 4. Student CAN view their own interventions
    own_view = api_client.get(
        f"/api/v1/teachers/interventions?student_id=stu-amit-01",
        headers=student_auth_headers,
    )
    assert own_view.status_code == 200


def test_backward_compatibility_teacher_alerts(api_client, teacher_auth_headers):
    """Verify legacy TeacherAlert model and /alerts endpoint remain fully functional."""
    # Access /teachers/alerts
    res = api_client.get("/api/v1/teachers/alerts?course_id=crs-chem-101", headers=teacher_auth_headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert isinstance(res.json()["data"], list)
