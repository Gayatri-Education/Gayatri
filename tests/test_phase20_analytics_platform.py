"""Authoritative Test Suite for Phase 20: Multi-Tier Analytics & Telemetry Platform.

Master Plan Section 29:
1. Student Analytics:
   - mastery, accuracy, retention, session frequency, learning velocity, weak concepts, review compliance.
2. Teacher Class Analytics:
   - class mastery, student activity, difficult concepts, misconceptions, intervention rates, assessment outcomes.
3. Admin System & AI Observability Telemetry:
   - active users (DAU/WAU/MAU by role), course usage, AI usage (tokens, requests by provider/model), cost, latency percentiles, system health.
4. REST API & Multi-Tier RBAC Enforcement:
   - /student/{id}, /cohort/{id}, /class, /system, /ai endpoints with strict access boundaries.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from central_platform.analytics.service import AnalyticsService
from central_platform.api.app import create_app
from central_platform.api.routes.analytics import get_analytics_service
from central_platform.auth.dependencies import get_current_user, get_db
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore, LearningEventType
from central_platform.models.schema import (
    AIExecutionLog,
    Assessment,
    AssessmentAttempt,
    Cohort,
    Course,
    Enrollment,
    InterventionRecord,
    LearningEvent,
    MasteryState,
    Misconception,
    Organization,
    Session,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    User,
    UserRole,
)


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "analytics_test.db")
    return PlatformDatabase(db_path=db_path)


@pytest.fixture
def event_store(test_db):
    return LearningEventStore(test_db)


@pytest.fixture
def analytics_service(test_db, event_store):
    return AnalyticsService(db=test_db, event_store=event_store)


@pytest.fixture
def api_client(test_db, analytics_service):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service
    return TestClient(app)


def _auth_header(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        user_id=user.id,
        role=role_str.upper(),
        organization_id=user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


# ── 1. Student Analytics Unit Tests ──────────────────────────────────────────

def test_student_analytics_accurate_computation(analytics_service, test_db, event_store):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    student_id = f"stu_{uuid.uuid4().hex[:6]}"
    course_id = f"crs_{uuid.uuid4().hex[:6]}"

    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))
    test_db.create_user(User(id=student_id, organization_id=org_id, email=f"{student_id}@test.com", role=UserRole.STUDENT, full_name="Student One"))
    test_db.create_course(Course(id=course_id, organization_id=org_id, title="Chemistry 101", code="CHEM101"))

    # Create SLR & Mastery states
    slr_id = f"slr_{uuid.uuid4().hex[:6]}"
    test_db.create_slr(StudentLearningRecord(id=slr_id, student_id=student_id, course_id=course_id))
    test_db.upsert_mastery_state(MasteryState(id="ms_1", slr_id=slr_id, concept_id="chem_thermo_first_law", p_mastery=0.90, state="mastered"))
    test_db.upsert_mastery_state(MasteryState(id="ms_2", slr_id=slr_id, concept_id="chem_thermo_enthalpy", p_mastery=0.45, state="struggling"))
    test_db.upsert_mastery_state(MasteryState(id="ms_3", slr_id=slr_id, concept_id="chem_thermo_entropy", p_mastery=0.75, state="practicing"))

    # Record sessions first
    now = datetime.now(timezone.utc)
    s1_id = f"sess_{uuid.uuid4().hex[:6]}"
    test_db.create_session(
        Session(
            id=s1_id,
            student_id=student_id,
            course_id=course_id,
            concept_id="chem_thermo_first_law",
            started_at=(now - timedelta(days=1, minutes=30)).isoformat(),
            ended_at=(now - timedelta(days=1)).isoformat(),
        )
    )
    s2_id = f"sess_{uuid.uuid4().hex[:6]}"
    test_db.create_session(
        Session(
            id=s2_id,
            student_id=student_id,
            course_id=course_id,
            concept_id="chem_thermo_enthalpy",
            started_at=(now - timedelta(minutes=45)).isoformat(),
            ended_at=now.isoformat(),
        )
    )

    # Emit question attempt events (3 correct, 1 incorrect -> 75% accuracy)
    for i in range(3):
        test_db.record_learning_event(
            LearningEvent(
                id=f"ev_{i}_{uuid.uuid4().hex[:6]}",
                session_id=s1_id,
                student_id=student_id,
                course_id=course_id,
                event_type=getattr(LearningEventType.QUESTION_ATTEMPTED, "value", "question_attempted"),
                payload={"question_id": f"q_{i}", "is_correct": True, "score": 1.0},
            )
        )
    test_db.record_learning_event(
        LearningEvent(
            id=f"ev_fail_{uuid.uuid4().hex[:6]}",
            session_id=s1_id,
            student_id=student_id,
            course_id=course_id,
            event_type=getattr(LearningEventType.QUESTION_ATTEMPTED, "value", "question_attempted"),
            payload={"question_id": "q_fail", "is_correct": False, "score": 0.0},
        )
    )

    # Record active misconception
    test_db.create_misconception(
        Misconception(
            id="misc_def_sign",
            code="SIGN_CONVENTION_ERROR",
            category="chemistry",
            name="Sign convention error",
            description="Confuses enthalpy sign conventions",
        )
    )
    test_db.record_student_misconception(
        StudentMisconceptionRecord(
            id=f"misc_{uuid.uuid4().hex[:6]}",
            student_id=student_id,
            concept_id="chem_thermo_enthalpy",
            misconception_code="SIGN_CONVENTION_ERROR",
            description="Confuses enthalpy sign conventions",
        )
    )

    # Derive analytics
    res = analytics_service.get_student_analytics(student_id=student_id, course_id=course_id)

    assert res.student_id == student_id
    assert res.course_id == course_id
    # Mean mastery: (0.90 + 0.45 + 0.75) / 3 = 0.70
    assert abs(res.mastery - 0.70) < 1e-3
    assert res.mastery_distribution["mastered"] == 1
    assert res.mastery_distribution["progressing"] == 1
    assert res.mastery_distribution["struggling"] == 1

    # Accuracy: 3 correct / 4 total = 0.75
    assert res.total_questions_attempted == 4
    assert res.correct_questions == 3
    assert res.accuracy == 0.75

    # Retention: positive number <= 1.0
    assert 0.0 <= res.retention <= 1.0

    # Sessions & Streak
    assert res.session_frequency["total_sessions"] == 2
    assert res.session_frequency["total_study_minutes"] >= 70.0
    assert res.session_frequency["current_streak_days"] >= 1

    # Learning Velocity
    assert res.learning_velocity > 0.0

    # Weak concepts
    weak_ids = [w["concept_id"] for w in res.weak_concepts]
    assert "chem_thermo_enthalpy" in weak_ids


# ── 2. Teacher Class Analytics Unit Tests ─────────────────────────────────────

def test_teacher_class_analytics_aggregation(analytics_service, test_db, event_store):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    course_id = f"crs_{uuid.uuid4().hex[:6]}"
    cg_id = f"cg_{uuid.uuid4().hex[:6]}"
    cohort_id = f"coh_{uuid.uuid4().hex[:6]}"

    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))
    test_db.create_course(Course(id=course_id, organization_id=org_id, title="Physics 101", code="PHYS101"))
    from central_platform.models.schema import ClassGroup
    test_db.create_class_group(ClassGroup(id=cg_id, organization_id=org_id, course_id=course_id, name="Class A"))
    test_db.create_cohort(Cohort(id=cohort_id, class_group_id=cg_id, name="Cohort A"))

    # Create assessment
    test_db.create_assessment(
        Assessment(
            id="asmt_phys_midterm",
            course_id=course_id,
            title="Physics Midterm",
            assessment_type="summative",
        )
    )

    # Create base misconception
    test_db.create_misconception(
        Misconception(
            id="misc_def_force",
            code="FORCE_REQUIRES_MOTION",
            category="physics",
            name="Force requires motion",
            description="Aristotelian misconception on velocity and force",
        )
    )

    # Create 3 students in this cohort
    for idx, (p1, p2) in enumerate([(0.95, 0.85), (0.60, 0.50), (0.30, 0.40)]):
        sid = f"stu_class_{idx}_{uuid.uuid4().hex[:4]}"
        test_db.create_user(User(id=sid, organization_id=org_id, email=f"{sid}@test.com", role=UserRole.STUDENT, full_name=f"Student {idx}"))
        test_db.create_enrollment(Enrollment(id=f"enr_{sid}", student_id=sid, course_id=course_id, cohort_id=cohort_id))
        slr_id = f"slr_{sid}"
        test_db.create_slr(StudentLearningRecord(id=slr_id, student_id=sid, course_id=course_id))
        test_db.upsert_mastery_state(MasteryState(id=f"ms1_{sid}", slr_id=slr_id, concept_id="phys_mechanics_kinematics", p_mastery=p1, state="mastered" if p1 >= 0.80 else "struggling"))
        test_db.upsert_mastery_state(MasteryState(id=f"ms2_{sid}", slr_id=slr_id, concept_id="phys_mechanics_dynamics", p_mastery=p2, state="mastered" if p2 >= 0.80 else "struggling"))

        # Record misconception on dynamics for struggling students
        if p2 < 0.60:
            test_db.record_student_misconception(
                StudentMisconceptionRecord(
                    id=f"misc_{sid}",
                    student_id=sid,
                    concept_id="phys_mechanics_dynamics",
                    misconception_code="FORCE_REQUIRES_MOTION",
                    description="Aristotelian misconception on velocity and force",
                )
            )

        # Record assessment attempt
        test_db.record_assessment_attempt(
            AssessmentAttempt(
                id=f"att_{sid}",
                assessment_id="asmt_phys_midterm",
                student_id=sid,
                score=0.85 if idx == 0 else (0.65 if idx == 1 else 0.45),
                passed=idx == 0,
                answers={"q1": {"is_correct": idx != 2}},
            )
        )


    # Record teacher intervention
    test_db.create_intervention(
        InterventionRecord(
            id="int_1",
            student_id=sid,
            course_id=course_id,
            assigned_teacher="tea_1",
            message="Review Newton's second law",
        )
    )
    test_db.resolve_intervention("int_1")

    class_analytics = analytics_service.get_class_analytics(cohort_id=cohort_id)

    assert class_analytics.student_count == 3
    assert 0.0 < class_analytics.class_mastery < 1.0
    assert class_analytics.mastery_tiers["Mastered"] == 1
    assert class_analytics.mastery_tiers["Progressing"] == 1
    assert class_analytics.mastery_tiers["Critical"] == 1

    # Misconceptions aggregated
    assert len(class_analytics.misconceptions) >= 1
    top_misc = class_analytics.misconceptions[0]
    assert top_misc["code"] == "FORCE_REQUIRES_MOTION"
    assert top_misc["affected_students"] == 2

    # Intervention resolution
    assert class_analytics.intervention_rates["raised"] >= 1
    assert class_analytics.intervention_rates["resolved"] >= 1
    assert class_analytics.intervention_rates["resolution_rate"] == 100.0

    # Assessment outcomes
    assert class_analytics.assessment_outcomes["total_attempts"] == 3
    assert class_analytics.assessment_outcomes["pass_rate"] > 0.0


# ── 3. Admin System & AI Observability Unit Tests ─────────────────────────────

def test_admin_system_and_ai_telemetry(analytics_service, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="System Org", slug=org_id))

    # Create users
    test_db.create_user(User(id=f"u_admin_{uuid.uuid4().hex[:4]}", organization_id=org_id, email="admin@test.com", role=UserRole.SUPER_ADMIN, full_name="Super Admin"))
    test_db.create_user(User(id=f"u_tea_{uuid.uuid4().hex[:4]}", organization_id=org_id, email="teacher@test.com", role=UserRole.TEACHER, full_name="Teacher"))
    test_db.create_user(User(id=f"u_stu_{uuid.uuid4().hex[:4]}", organization_id=org_id, email="student@test.com", role=UserRole.STUDENT, full_name="Student"))

    # Record AI execution logs
    test_db.record_ai_execution_log(
        AIExecutionLog(
            id=f"ai_log_{uuid.uuid4().hex[:6]}",
            provider="gemini",
            model="gemini-2.5-pro",
            prompt_tokens=500,
            completion_tokens=150,
            total_tokens=650,
            cost_usd=0.0035,
            latency_ms=120.5,
        )
    )
    test_db.record_ai_execution_log(
        AIExecutionLog(
            id=f"ai_log_{uuid.uuid4().hex[:6]}",
            provider="openai",
            model="gpt-4o",
            prompt_tokens=400,
            completion_tokens=100,
            total_tokens=500,
            cost_usd=0.0050,
            latency_ms=95.0,
        )
    )

    sys_analytics = analytics_service.get_system_analytics(organization_id=org_id)

    assert sys_analytics.active_users["roles"]["super_admin"] >= 1
    assert sys_analytics.active_users["roles"]["teacher"] >= 1
    assert sys_analytics.active_users["roles"]["student"] >= 1

    # AI usage metrics
    assert sys_analytics.ai_usage["total_requests"] == 2
    assert sys_analytics.ai_usage["total_tokens"] == 1150
    assert "gemini" in sys_analytics.ai_usage["by_provider"]
    assert "openai" in sys_analytics.ai_usage["by_provider"]
    assert sys_analytics.cost["total_cost_usd"] > 0.008

    # Performance percentiles
    assert sys_analytics.performance["p50_ms"] > 0
    assert sys_analytics.performance["p99_ms"] >= sys_analytics.performance["p50_ms"]
    assert sys_analytics.system_health["status"] == "HEALTHY"


# ── 4. REST API & RBAC Integration Tests ──────────────────────────────────────

def test_analytics_rest_endpoints_and_rbac(api_client, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="API Test Org", slug=org_id))

    student_user = User(
        id=f"stu_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="student.api@test.com",
        role=UserRole.STUDENT,
        full_name="Student API",
    )
    test_db.create_user(student_user)

    teacher_user = User(
        id=f"tea_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="teacher.api@test.com",
        role=UserRole.TEACHER,
        full_name="Teacher API",
    )
    test_db.create_user(teacher_user)

    admin_user = User(
        id=f"adm_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="admin.api@test.com",
        role=UserRole.SUPER_ADMIN,
        full_name="Admin API",
    )
    test_db.create_user(admin_user)

    stu_headers = _auth_header(student_user)
    tea_headers = _auth_header(teacher_user)
    adm_headers = _auth_header(admin_user)

    # 1. Student accessing own analytics -> 200 OK
    res = api_client.get(f"/api/v1/analytics/student/{student_user.id}", headers=stu_headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert res.json()["data"]["student_id"] == student_user.id

    # 2. Student accessing another student's analytics -> 403 Forbidden
    res_forbidden = api_client.get("/api/v1/analytics/student/other_student_id", headers=stu_headers)
    assert res_forbidden.status_code == 403

    # 3. Student attempting to access class or system analytics -> 403 Forbidden
    res_class_forb = api_client.get("/api/v1/analytics/class", headers=stu_headers)
    assert res_class_forb.status_code == 403

    res_sys_forb = api_client.get("/api/v1/analytics/system", headers=stu_headers)
    assert res_sys_forb.status_code == 403

    # 4. Teacher accessing class analytics -> 200 OK
    res_tea_class = api_client.get("/api/v1/analytics/class", headers=tea_headers)
    assert res_tea_class.status_code == 200
    assert res_tea_class.json()["ok"] is True

    # 5. Admin accessing system analytics -> 200 OK
    res_adm_sys = api_client.get("/api/v1/analytics/system", headers=adm_headers)
    assert res_adm_sys.status_code == 200
    assert res_adm_sys.json()["ok"] is True
    assert "active_users" in res_adm_sys.json()["data"]

    # 6. Admin accessing AI observability -> 200 OK
    res_adm_ai = api_client.get("/api/v1/analytics/ai", headers=adm_headers)
    assert res_adm_ai.status_code == 200
    assert res_adm_ai.json()["ok"] is True
    assert "ai_usage" in res_adm_ai.json()["data"]
