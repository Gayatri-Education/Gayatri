"""Gayatri AI Platform — Phase 06 Authoritative Student Learning Record (SLR) Tests.

Master Plan Section 15:
- Build the real SLR from central events.
- SLR must expose all 15 canonical dimensions:
  1.  identity
  2.  enrollment
  3.  course
  4.  curriculum
  5.  mastery
  6.  recent_sessions
  7.  learning_timeline
  8.  misconceptions
  9.  assessment_results
  10. hints
  11. teacher_feedback
  12. teacher_instructions
  13. interventions
  14. recommendations
  15. alerts
- Single source of truth across student and teacher portals.
- Strict multi-tenant RBAC boundaries (student self-access only; cross-student access 403).
- Backward compatibility with legacy StudentLearningRecord callers.
"""
from __future__ import annotations

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import (
    Assessment,
    AssessmentAttempt,
    AssessmentType,
    Course,
    InterventionRecord,
    LearningEvent,
    Misconception,
    Organization,
    Session,
    SessionStatus,
    TeacherInstructionRecord,
    User,
    UserRole,
)
from central_platform.slr.models import AuthoritativeSLR
from central_platform.slr.record import StudentLearningRecord, TimelineItem
from central_platform.slr.service import SLRService


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "phase06_test.db")
    return PlatformDatabase(db_file)


@pytest.fixture
def slr_service(temp_db):
    event_store = LearningEventStore(db=temp_db)
    return SLRService(db=temp_db, event_store=event_store)


@pytest.fixture
def api_client():
    return TestClient(app)


# ── 1. Canonical 15 Dimensions Verification ──────────────────────────────────

def test_authoritative_slr_all_15_dimensions(slr_service):
    """Test 1: Verify all 15 Section 15 dimensions are populated and typed."""
    student_id = "stu_canonical_15"
    slr = slr_service.get_authoritative_slr(student_id)

    assert isinstance(slr, AuthoritativeSLR)
    assert slr.authoritative is True
    assert slr.schema_version == "1.0.0"
    assert slr.student_id == student_id

    # 1. Identity
    assert slr.identity.student_id == student_id
    assert slr.identity.organization_id is not None

    # 2. Enrollment
    assert slr.enrollment.course_id is not None
    assert slr.enrollment.is_active is True

    # 3. Course
    assert slr.course.course_id is not None
    assert "CHEM" in slr.course.code or len(slr.course.code) > 0

    # 4. Curriculum
    assert slr.curriculum.curriculum_id is not None
    assert slr.curriculum.current_concept is not None

    # 5. Mastery
    assert 0.0 <= slr.mastery.overall_score <= 1.0
    assert isinstance(slr.mastery.concept_scores, dict)

    # 6. Recent sessions
    assert isinstance(slr.recent_sessions, list)

    # 7. Learning timeline
    assert isinstance(slr.learning_timeline, list)

    # 8. Misconceptions
    assert isinstance(slr.misconceptions, list)

    # 9. Assessment results
    assert isinstance(slr.assessment_results, list)

    # 10. Hints
    assert isinstance(slr.hints.total_hints_requested, int)
    assert isinstance(slr.hints.per_concept_breakdown, dict)

    # 11. Teacher feedback
    assert isinstance(slr.teacher_feedback, list)

    # 12. Teacher instructions
    assert isinstance(slr.teacher_instructions, list)

    # 13. Interventions
    assert isinstance(slr.interventions, list)

    # 14. Recommendations
    assert isinstance(slr.recommendations, list)

    # 15. Alerts
    assert isinstance(slr.alerts, list)


# ── 2. Database Persistence & Mastery State ─────────────────────────────────

def test_slr_database_persistence_and_retrieval(slr_service, temp_db):
    """Test 2: Verify updating concept mastery persists to database and updates SLR."""
    student_id = "stu_persistence_01"
    course_id = "crs-chem-101"

    slr_updated = slr_service.update_concept_mastery(
        student_id=student_id,
        concept_id="chem_thermo_entropy",
        score=0.92,
        course_id=course_id,
        confidence=0.88,
    )
    assert slr_updated.mastery.concept_scores["chem_thermo_entropy"] == 0.92
    assert slr_updated.mastery.concept_confidences["chem_thermo_entropy"] == 0.88

    # Query DB directly to verify persistence
    db_slr = temp_db.get_slr(student_id, course_id)
    assert db_slr is not None
    states = temp_db.get_mastery_states_for_slr(db_slr.id)
    entropy_state = next((s for s in states if s.concept_id == "chem_thermo_entropy"), None)
    assert entropy_state is not None
    assert entropy_state.score == 0.92


# ── 3. Event Projection & Dynamic Mastery ───────────────────────────────────

def test_slr_event_projection_pipeline(slr_service, temp_db):
    """Test 3: Verify learning events from event store project into SLR."""
    student_id = "stu_event_proj_01"
    course_id = "crs-chem-101"
    session_id = "sess_proj_101"
    slr_service._ensure_student_scaffolding(student_id, course_id)

    # Pre-seed session
    temp_db.create_session(
        Session(
            id=session_id,
            student_id=student_id,
            course_id=course_id,
            concept_id="chem_thermo_gibbs",
            status=SessionStatus.COMPLETED,
            started_at="2026-09-27T10:00:00Z",
            ended_at="2026-09-27T10:30:00Z",
        )
    )

    # Record events in event store
    ev1 = LearningEvent(
        id="ev_proj_01",
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        concept_id="chem_thermo_gibbs",
        event_type=LearningEventType.QUESTION_ATTEMPTED.value,
        payload={"difficulty": "medium"},
    )
    ev2 = LearningEvent(
        id="ev_proj_02",
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        concept_id="chem_thermo_gibbs",
        event_type=LearningEventType.HINT_REQUESTED.value,
        payload={"hint_level": 1},
    )
    ev3 = LearningEvent(
        id="ev_proj_03",
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        concept_id="chem_thermo_gibbs",
        event_type=LearningEventType.CONCEPT_MASTERED.value,
        score=0.95,
        payload={"mastery": 0.95},
    )
    temp_db.record_learning_event(ev1)
    temp_db.record_learning_event(ev2)
    temp_db.record_learning_event(ev3)

    # Project from events
    projected_slr = slr_service.project_from_events(student_id, course_id=course_id)

    # Verify projected timeline has 3 items
    assert len(projected_slr.learning_timeline) == 3
    # Verify hints counted
    assert projected_slr.hints.total_hints_requested == 1
    assert projected_slr.hints.per_concept_breakdown["chem_thermo_gibbs"] == 1
    # Verify session captured
    assert len(projected_slr.recent_sessions) >= 1
    assert projected_slr.recent_sessions[0].session_id == session_id


# ── 4. Misconceptions Aggregation ───────────────────────────────────────────

def test_slr_misconception_aggregation(slr_service, temp_db):
    """Test 4: Verify misconceptions are cataloged, enriched, and tracked in SLR."""
    student_id = "stu_misc_01"

    # Seed catalog misconception
    temp_db.create_misconception(
        Misconception(
            id="misc-thermo-01",
            code="MISC_HEAT_TEMP_CONFUSION",
            category="thermodynamics",
            name="Heat vs Temperature Confusion",
            description="Student confuses heat energy with temperature",
            remediation="Review kinetic definition of temperature and heat transfer equations",
        )
    )

    # Record misconception observation twice
    slr_service.record_student_misconception(student_id, "MISC_HEAT_TEMP_CONFUSION")
    slr_after = slr_service.record_student_misconception(student_id, "MISC_HEAT_TEMP_CONFUSION")

    assert len(slr_after.misconceptions) == 1
    m = slr_after.misconceptions[0]
    assert m.code == "MISC_HEAT_TEMP_CONFUSION"
    assert m.name == "Heat vs Temperature Confusion"
    assert m.frequency == 2
    assert m.status == "active"
    assert "kinetic definition" in m.remediation


# ── 5. Timeline Ordering ────────────────────────────────────────────────────

def test_slr_timeline_ordering(slr_service, temp_db):
    """Test 5: Verify forward and reverse chronological timeline retrieval."""
    student_id = "stu_timeline_01"
    course_id = "crs-chem-101"
    session_id = "sess_time_01"
    slr_service._ensure_student_scaffolding(student_id, course_id)

    temp_db.create_session(
        Session(
            id=session_id,
            student_id=student_id,
            course_id=course_id,
            concept_id="thermo",
            status=SessionStatus.ACTIVE,
        )
    )

    t1 = "2026-09-27T08:00:00Z"
    t2 = "2026-09-27T09:00:00Z"
    t3 = "2026-09-27T10:00:00Z"

    temp_db.record_learning_event(
        LearningEvent(id="ev_t1", session_id=session_id, student_id=student_id, course_id=course_id, event_type="session_started", created_at=t1)
    )
    temp_db.record_learning_event(
        LearningEvent(id="ev_t2", session_id=session_id, student_id=student_id, course_id=course_id, event_type="question_attempted", created_at=t2)
    )
    temp_db.record_learning_event(
        LearningEvent(id="ev_t3", session_id=session_id, student_id=student_id, course_id=course_id, event_type="session_completed", created_at=t3)
    )

    forward = slr_service.get_timeline(student_id, reverse=False)
    reverse = slr_service.get_timeline(student_id, reverse=True)

    assert forward[0].item_id == "ev_t1"
    assert forward[2].item_id == "ev_t3"
    assert reverse[0].item_id == "ev_t3"
    assert reverse[2].item_id == "ev_t1"


# ── 6. Teacher Instructions & Interventions Exposure ─────────────────────────

def test_slr_teacher_instructions_and_interventions(slr_service, temp_db):
    """Test 6: Verify teacher directives and alerts appear in student SLR."""
    student_id = "stu_teacher_exp_01"
    course_id = "crs-chem-101"
    slr_service._ensure_student_scaffolding(student_id, course_id)

    # Seed teacher user to satisfy foreign key constraint
    temp_db.create_user(
        User(
            id="teach-prof-sharma",
            email="sharma@gayatri.ai",
            full_name="Prof Sharma",
            role=UserRole.TEACHER,
            organization_id="org-default",
        )
    )

    # Seed teacher instruction
    temp_db.create_teacher_instruction(
        TeacherInstructionRecord(
            id="ti-slr-01",
            teacher_id="teach-prof-sharma",
            student_id=student_id,
            course_id=course_id,
            instruction_text="Focus on reversible vs irreversible expansion work",
            concept_scope="chem_thermo_work",
            priority=1,
            is_active=True,
        )
    )

    # Seed intervention
    temp_db.create_intervention(
        InterventionRecord(
            id="intv-slr-01",
            student_id=student_id,
            course_id=course_id,
            alert_type="learning_gap",
            message="Repeated sign errors in work done equation",
        )
    )

    slr = slr_service.get_authoritative_slr(student_id, course_id=course_id)
    assert len(slr.teacher_instructions) >= 1
    assert slr.teacher_instructions[0].instruction_id == "ti-slr-01"
    assert "reversible vs irreversible" in slr.teacher_instructions[0].instruction_text

    assert len(slr.interventions) >= 1
    assert slr.interventions[0].intervention_id == "intv-slr-01"
    assert "sign errors" in slr.interventions[0].message


# ── 7. Assessment Results Aggregation ────────────────────────────────────────

def test_slr_assessment_results(slr_service, temp_db):
    """Test 7: Verify completed assessment attempts appear in student SLR."""
    student_id = "stu_asmt_exp_01"
    course_id = "crs-chem-101"
    slr_service._ensure_student_scaffolding(student_id, course_id)

    # Create assessment
    asmt = Assessment(
        id="asmt-midterm-01",
        course_id=course_id,
        title="Midterm Examination - Thermodynamics",
        assessment_type=AssessmentType.SUMMATIVE,
        total_marks=50.0,
    )

    temp_db.create_assessment(asmt)

    # Record attempt
    attempt = AssessmentAttempt(
        id="att-slr-01",
        assessment_id=asmt.id,
        student_id=student_id,
        score=42.5,
        passed=True,
        started_at="2026-09-27T09:00:00Z",
        completed_at="2026-09-27T10:00:00Z",
    )
    temp_db.record_assessment_attempt(attempt)

    slr = slr_service.get_authoritative_slr(student_id, course_id=course_id)
    assert len(slr.assessment_results) == 1
    res = slr.assessment_results[0]
    assert res.assessment_id == "asmt-midterm-01"
    assert res.score == 42.5
    assert res.max_marks == 50.0
    assert res.percentage == 85.0
    assert res.passed is True


# ── 8. Dynamic Recommendations & Learning Alerts ────────────────────────────

def test_slr_dynamic_recommendations_and_alerts(slr_service):
    """Test 8: Verify low mastery (<0.6) and misconceptions generate recommendations and alerts."""
    student_id = "stu_recs_01"

    # Set weak concept mastery
    slr_service.update_concept_mastery(
        student_id=student_id,
        concept_id="chem_thermo_carnot_cycle",
        score=0.35,  # Critical gap (< 0.40)
    )

    # Set persistent misconception (3 occurrences)
    slr_service.record_student_misconception(student_id, "MISC_SIGN_CONVENTION")
    slr_service.record_student_misconception(student_id, "MISC_SIGN_CONVENTION")
    slr = slr_service.record_student_misconception(student_id, "MISC_SIGN_CONVENTION")

    # Check recommendations
    assert len(slr.recommendations) >= 2
    concept_rec = next((r for r in slr.recommendations if r.concept_id == "chem_thermo_carnot_cycle"), None)
    assert concept_rec is not None
    assert concept_rec.action_type == "review"

    # Check alerts
    assert len(slr.alerts) >= 2
    gap_alert = next((a for a in slr.alerts if a.alert_type == "learning_gap"), None)
    assert gap_alert is not None
    assert "carnot_cycle" in gap_alert.message

    misc_alert = next((a for a in slr.alerts if a.alert_type == "persistent_misconception"), None)
    assert misc_alert is not None
    assert misc_alert.severity == "critical"


# ── 9. RBAC Security: Student Cross-Access Blocked ───────────────────────────

def test_slr_rbac_security_student_isolation(api_client):
    """Test 9: Verify student Alice accessing Bob's SLR is rejected with 403 Forbidden."""
    # Alice (student)
    alice_token = create_access_token(
        user_id="stu_alice_99",
        role="student",
        organization_id="org-test",
    )
    # Bob (student)
    bob_token = create_access_token(
        user_id="stu_bob_99",
        role="student",
        organization_id="org-test",
    )

    # Alice accesses Alice's SLR: 200 OK
    r_alice = api_client.get(
        "/api/v1/students/stu_alice_99/slr",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r_alice.status_code == 200
    assert r_alice.json()["ok"] is True
    assert r_alice.json()["data"]["authoritative"] is True
    assert r_alice.json()["data"]["identity"]["student_id"] == "stu_alice_99"

    # Alice attempts to access Bob's SLR: MUST RETURN 403 FORBIDDEN
    r_bad = api_client.get(
        "/api/v1/students/stu_bob_99/slr",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r_bad.status_code == 403
    assert "Forbidden" in r_bad.json()["detail"] or "Forbidden" in r_bad.text

    # Alice attempts to call teacher's student SLR endpoint: MUST RETURN 403 FORBIDDEN
    r_teach_cross = api_client.get(
        "/api/v1/teachers/students/stu_bob_99/slr",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert r_teach_cross.status_code == 403


# ── 10. Single Source of Truth Across Portals ───────────────────────────────

def test_slr_single_source_of_truth_across_portals(api_client):
    """Test 10: Verify Teacher and Student endpoints return identical canonical SLR data."""
    admin_token = create_access_token(
        user_id="admin_slr",
        role="super_admin",
        organization_id="org-default",
    )
    student_id = "stu_unified_truth_01"

    # Push snapshot via student API
    r_snap = api_client.post(
        "/api/v1/students/snapshot",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "student_id": student_id,
            "student_name": "Devansh",
            "course_id": "crs-chem-101",
            "mastery": 0.88,
            "needs_attention": False,
            "misconceptions": ["MISC_WORK_SIGN"],
            "hint_count": 2,
            "retention_rate": 0.91,
        },
    )
    assert r_snap.status_code == 200

    # Read from Student SLR endpoint
    r_std_slr = api_client.get(
        f"/api/v1/students/{student_id}/slr",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_std_slr.status_code == 200
    std_slr = r_std_slr.json()["data"]

    # Read from Teacher SLR endpoint
    r_tch_slr = api_client.get(
        f"/api/v1/teachers/students/{student_id}/slr",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_tch_slr.status_code == 200
    tch_slr = r_tch_slr.json()["data"]

    # Invariant: Both student and teacher see identical authoritative state
    assert std_slr["authoritative"] is True
    assert tch_slr["authoritative"] is True
    assert std_slr["identity"]["student_id"] == tch_slr["identity"]["student_id"]
    assert std_slr["mastery"]["overall_score"] == tch_slr["mastery"]["overall_score"]
    assert len(std_slr["misconceptions"]) == len(tch_slr["misconceptions"])


# ── 11. Backward Compatibility with Existing Callers ────────────────────────

def test_backward_compatibility_existing_slr_record():
    """Test 11: Verify legacy StudentLearningRecord and TimelineItem work without regressions."""
    record = StudentLearningRecord("stu_compat_001")
    item = record.add_event("ev_c1", "assessment", "Scored 90% on quiz", "2026-09-27T10:00:00")

    assert isinstance(item, TimelineItem)
    assert item.item_id == "ev_c1"
    assert len(record.get_timeline()) == 1

    record.update_concept_mastery("thermo_law_1", 0.88)
    snapshot = record.get_mastery_snapshot()
    assert snapshot["thermo_law_1"] == 0.88
