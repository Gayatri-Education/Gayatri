"""Authoritative Test Suite for Phase 9: Analytics, Portals & Privacy Isolation Remediation.

Master Plan Section 14 Invariants:
1. Student Analytics:
   - All metrics evidence-driven (Mastery: SLR/evidence, Accuracy: questions/assessments,
     Retention: dated decay / 0.0 fallback when empty, Velocity: duration/mastery).
   - Zero fabricated fallback numbers.
2. Cross-Tenant Boundaries:
   - Org A teacher -> Org B student = 403 Forbidden.
   - Org A org admin -> Org B student = 403 Forbidden.
   - Org A org admin -> Org B system telemetry = 403 Forbidden.
   - Org A teacher -> Org B teacher dashboard = 403 Forbidden.
3. Student Self-Isolation:
   - Student A -> Student B analytics = 403 Forbidden.
   - Student A -> Class / Cohort / System = 403 Forbidden.
4. Teacher Scope Isolation:
   - Teacher A -> Unassigned student = 403 Forbidden.
5. Parent Privacy & Scope Isolation:
   - Parent A -> Unlinked student = 403 Forbidden / PermissionError.
   - Parent A -> Blocked privacy level = 403 Forbidden / PermissionError.
   - Parent portal data filtering strictly removes internal safety flags, crisis indicators,
     and private teacher notes.
   - ParentPortalController queries genuine database SLRs and session records.
"""
from __future__ import annotations

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
from central_platform.events.store import LearningEventStore
from central_platform.models.schema import (
    ClassGroup,
    Cohort,
    Course,
    Enrollment,
    MasteryState,
    Organization,
    Session,
    StudentLearningRecord,
    User,
    UserRole,
)
from central_platform.portals.parent import ParentPortalController
from central_platform.privacy.policies import (
    ParentVisibilityLevel,
    PrivacyRulesEngine,
    StudentPrivacySetting,
)


@pytest.fixture
def phase9_db(tmp_path):
    db_path = str(tmp_path / "phase9_analytics.db")
    return PlatformDatabase(db_path=db_path)


@pytest.fixture
def phase9_event_store(phase9_db):
    return LearningEventStore(phase9_db)


@pytest.fixture
def phase9_analytics_service(phase9_db, phase9_event_store):
    return AnalyticsService(db=phase9_db, event_store=phase9_event_store)


@pytest.fixture
def phase9_client(phase9_db, phase9_analytics_service):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: phase9_db
    app.dependency_overrides[get_analytics_service] = lambda: phase9_analytics_service
    return TestClient(app)


def _auth_header(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        user_id=user.id,
        role=role_str.upper(),
        organization_id=user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


# ── 1. Student Analytics Evidence-Based Computation (Zero Fake Fallbacks) ──────

def test_student_analytics_zero_evidence_returns_zeros(phase9_analytics_service, phase9_db):
    """When a student has no learning events or mastery, metrics must return genuine zeros, not fake chemistry defaults."""
    sid = "stu_zero_evidence"
    res = phase9_analytics_service.get_student_analytics(sid)

    assert res.student_id == sid
    assert res.mastery == 0.0
    assert res.accuracy == 0.0
    assert res.retention == 0.0  # Invariant: Retention is 0.0 when 0 evidence exists
    assert res.total_questions_attempted == 0
    assert res.correct_questions == 0
    assert res.learning_velocity == 0.0
    assert res.weak_concepts == []
    assert res.session_frequency["total_sessions"] == 0
    assert res.session_frequency["total_study_minutes"] == 0.0


# ── 2. Cross-Tenant Boundaries in Analytics Endpoints ──────────────────────────

def test_cross_tenant_student_analytics_rejection(phase9_client, phase9_db):
    """Teacher or Org Admin from Org Alpha must NOT be able to view Student from Org Beta."""
    org_alpha = "org_alpha_9"
    org_beta = "org_beta_9"
    phase9_db.create_organization(Organization(id=org_alpha, name="Alpha", slug=org_alpha))
    phase9_db.create_organization(Organization(id=org_beta, name="Beta", slug=org_beta))

    teacher_alpha = User(id="tea_alpha", organization_id=org_alpha, email="tea@alpha.org", full_name="Alpha Teacher", role=UserRole.TEACHER)
    admin_alpha = User(id="adm_alpha", organization_id=org_alpha, email="adm@alpha.org", full_name="Alpha Admin", role=UserRole.ORG_ADMIN)
    student_beta = User(id="stu_beta", organization_id=org_beta, email="stu@beta.org", full_name="Beta Student", role=UserRole.STUDENT)

    phase9_db.create_user(teacher_alpha)
    phase9_db.create_user(admin_alpha)
    phase9_db.create_user(student_beta)

    # 1. Teacher Alpha querying Student Beta -> 403 Forbidden
    resp_tea = phase9_client.get(
        f"/api/v1/analytics/student/{student_beta.id}",
        headers=_auth_header(teacher_alpha),
    )
    assert resp_tea.status_code == 403
    assert "cross-organization" in resp_tea.json()["detail"].lower()

    # 2. Org Admin Alpha querying Student Beta -> 403 Forbidden
    resp_adm = phase9_client.get(
        f"/api/v1/analytics/student/{student_beta.id}",
        headers=_auth_header(admin_alpha),
    )
    assert resp_adm.status_code == 403
    assert "cross-organization" in resp_adm.json()["detail"].lower()


def test_cross_tenant_admin_system_and_ai_analytics_rejection(phase9_client, phase9_db):
    """Org Admin from Org Alpha querying telemetry/AI for Org Beta must be denied 403."""
    org_alpha = "org_alpha_telemetry"
    org_beta = "org_beta_telemetry"
    phase9_db.create_organization(Organization(id=org_alpha, name="Alpha", slug=org_alpha))
    phase9_db.create_organization(Organization(id=org_beta, name="Beta", slug=org_beta))

    admin_alpha = User(id="adm_alpha_tel", organization_id=org_alpha, email="adm@tel.org", full_name="Alpha Admin Tel", role=UserRole.ORG_ADMIN)
    phase9_db.create_user(admin_alpha)

    # System telemetry cross-org query
    resp_sys = phase9_client.get(
        f"/api/v1/analytics/system?organization_id={org_beta}",
        headers=_auth_header(admin_alpha),
    )
    assert resp_sys.status_code == 403
    assert "cross-organization" in resp_sys.json()["detail"].lower()

    # AI usage cross-org query
    resp_ai = phase9_client.get(
        f"/api/v1/analytics/ai?organization_id={org_beta}",
        headers=_auth_header(admin_alpha),
    )
    assert resp_ai.status_code == 403
    assert "cross-organization" in resp_ai.json()["detail"].lower()


def test_cross_tenant_teacher_dashboard_rejection(phase9_client, phase9_db):
    """Teacher from Org Alpha querying a Course from Org Beta must receive 403 Forbidden."""
    org_alpha = "org_alpha_dash"
    org_beta = "org_beta_dash"
    phase9_db.create_organization(Organization(id=org_alpha, name="Alpha", slug=org_alpha))
    phase9_db.create_organization(Organization(id=org_beta, name="Beta", slug=org_beta))

    course_beta = Course(id="crs_beta_math", organization_id=org_beta, code="MATH-B", title="Beta Math")
    phase9_db.create_course(course_beta)

    teacher_alpha = User(id="tea_alpha_dash", organization_id=org_alpha, email="tea@alpha.dash", full_name="Alpha Teacher Dash", role=UserRole.TEACHER)
    phase9_db.create_user(teacher_alpha)

    resp = phase9_client.get(
        f"/api/v1/teachers/dashboard?course_id={course_beta.id}",
        headers=_auth_header(teacher_alpha),
    )
    assert resp.status_code == 403
    assert "cross-organization" in resp.json()["detail"].lower()


# ── 3. Student Self-Isolation ──────────────────────────────────────────────────

def test_student_self_isolation_and_role_boundaries(phase9_client, phase9_db):
    """Student cannot inspect another student or aggregate class/system analytics."""
    org_id = "org_stu_iso"
    phase9_db.create_organization(Organization(id=org_id, name="Iso Org", slug=org_id))

    stu1 = User(id="stu_1_iso", organization_id=org_id, email="s1@iso.org", full_name="Student 1", role=UserRole.STUDENT)
    stu2 = User(id="stu_2_iso", organization_id=org_id, email="s2@iso.org", full_name="Student 2", role=UserRole.STUDENT)
    phase9_db.create_user(stu1)
    phase9_db.create_user(stu2)

    # 1. Student 1 queries Student 2 -> 403 Forbidden
    resp = phase9_client.get(
        f"/api/v1/analytics/student/{stu2.id}",
        headers=_auth_header(stu1),
    )
    assert resp.status_code == 403
    assert "own analytics" in resp.json()["detail"].lower()

    # 2. Student 1 queries cohort analytics -> 403 Forbidden
    resp_cohort = phase9_client.get(
        "/api/v1/analytics/cohort/cohort_iso_1",
        headers=_auth_header(stu1),
    )
    assert resp_cohort.status_code == 403


# ── 4. Parent Privacy & Boundary Enforcement ──────────────────────────────────

def test_parent_analytics_boundary_and_privacy_rejection(phase9_client, phase9_db):
    """Parent querying unlinked student or child with BLOCKED privacy level receives 403."""
    org_id = "org_parent_test"
    phase9_db.create_organization(Organization(id=org_id, name="Parent Org", slug=org_id))

    parent_user = User(id="parent_authorized", organization_id=org_id, email="parent@test.com", full_name="Parent Auth", role=UserRole.PARENT)
    child_linked = User(id="child_linked", organization_id=org_id, email="c1@test.com", full_name="Child Linked", role=UserRole.STUDENT)
    child_unlinked = User(id="child_unlinked", organization_id=org_id, email="c2@test.com", full_name="Child Unlinked", role=UserRole.STUDENT)
    child_blocked = User(id="child_blocked", organization_id=org_id, email="c3@test.com", full_name="Child Blocked", role=UserRole.STUDENT)

    phase9_db.create_user(parent_user)
    phase9_db.create_user(child_linked)
    phase9_db.create_user(child_unlinked)
    phase9_db.create_user(child_blocked)

    # Link child_linked and child_blocked
    PrivacyRulesEngine.link_parent_student(parent_user.id, child_linked.id)
    PrivacyRulesEngine.link_parent_student(parent_user.id, child_blocked.id)

    # Configure BLOCKED visibility for child_blocked
    PrivacyRulesEngine.set_privacy_setting(
        StudentPrivacySetting(
            student_id=child_blocked.id,
            parent_id=parent_user.id,
            visibility_level=ParentVisibilityLevel.BLOCKED,
        )
    )

    parent_headers = _auth_header(parent_user)

    # 1. Parent querying linked child -> 200 OK
    resp_linked = phase9_client.get(
        f"/api/v1/analytics/student/{child_linked.id}",
        headers=parent_headers,
    )
    assert resp_linked.status_code == 200
    assert resp_linked.json()["ok"] is True

    # 2. Parent querying unlinked child -> 403 Forbidden
    resp_unlinked = phase9_client.get(
        f"/api/v1/analytics/student/{child_unlinked.id}",
        headers=parent_headers,
    )
    assert resp_unlinked.status_code == 403
    assert "not linked" in resp_unlinked.json()["detail"].lower()

    # 3. Parent querying child with BLOCKED privacy policy -> 403 Forbidden
    resp_blocked = phase9_client.get(
        f"/api/v1/analytics/student/{child_blocked.id}",
        headers=parent_headers,
    )
    assert resp_blocked.status_code == 403
    assert "blocked by privacy policy" in resp_blocked.json()["detail"].lower()

    # 4. Parent cannot query cohort or class analytics -> 403 Forbidden
    resp_cohort = phase9_client.get(
        "/api/v1/analytics/cohort/some_cohort",
        headers=parent_headers,
    )
    assert resp_cohort.status_code == 403


def test_parent_data_sanitization_removes_safety_and_private_notes():
    """PrivacyRulesEngine.filter_student_data_for_parent must sanitize private teacher notes and internal safety flags."""
    parent_id = "p_filter_1"
    student_id = "s_filter_1"

    raw_data = {
        "student_id": student_id,
        "overall_mastery": 0.85,
        "attendance_pct": 98.0,
        "teacher_notes": [
            {"id": "n1", "note": "Great improvement in algebra", "is_private": False},
            {"id": "n2", "note": "Internal counseling observation", "is_private": True},
            {"id": "n3", "note": "Classroom behavior disciplinary log", "scope": "INTERNAL"},
        ],
        "safety_status": "FLAGGED",
        "safety_reasons": ["Detected self-harm keywords in AI chat"],
        "internal_notes": "Social worker notified",
        "crisis_flags": ["CRISIS_ESCALATION"],
    }

    filtered = PrivacyRulesEngine.filter_student_data_for_parent(parent_id, student_id, raw_data)

    # Public teacher note preserved
    assert len(filtered["teacher_notes"]) == 1
    assert filtered["teacher_notes"][0]["id"] == "n1"

    # All safety flags and internal notes purged
    assert "safety_status" not in filtered
    assert "safety_reasons" not in filtered
    assert "internal_notes" not in filtered
    assert "crisis_flags" not in filtered


# ── 5. Authoritative ParentPortalController Integration ────────────────────────

def test_parent_portal_controller_db_derivation_and_authorization(phase9_db):
    """ParentPortalController resolves linked children from PrivacyRulesEngine and computes authentic metrics from DB."""
    parent_id = "p_controller_auth"
    child_id = "c_controller_auth"
    unlinked_child = "c_unlinked_other"
    phase9_db.create_organization(Organization(id="org_c", name="Org C", slug="org_c"))
    phase9_db.create_user(User(id=parent_id, organization_id="org_c", email="p@c.org", full_name="Parent Controller", role=UserRole.PARENT))
    phase9_db.create_user(User(id=child_id, organization_id="org_c", email="c@c.org", role=UserRole.STUDENT, full_name="Tanvi Sharma"))

    PrivacyRulesEngine.link_parent_student(parent_id, child_id)

    # 1. Linked children resolution
    children = ParentPortalController.get_linked_children(parent_id, db=phase9_db)
    assert len(children) == 1
    assert children[0].child_id == child_id
    assert children[0].name == "Tanvi Sharma"

    # 2. Unlinked parent gets empty list
    assert ParentPortalController.get_linked_children("unlinked_parent_x", db=phase9_db) == []

    # 3. Seed learning progress in DB
    phase9_db.create_course(Course(id="crs_chem", organization_id="org_c", code="CHEM", title="Chem"))
    slr_id = "slr_tanvi"
    phase9_db.create_slr(StudentLearningRecord(id=slr_id, student_id=child_id, course_id="crs_chem"))
    phase9_db.upsert_mastery_state(MasteryState(id="ms_tanvi", slr_id=slr_id, concept_id="chem_atoms", p_mastery=0.92, state="mastered"))
    phase9_db.create_session(
        Session(
            id="sess_tanvi_1",
            student_id=child_id,
            course_id="crs_chem",
            concept_id="chem_atoms",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 4. Progress derived from DB
    progress = ParentPortalController.get_child_progress(child_id, parent_id=parent_id, db=phase9_db)
    assert progress.child_id == child_id
    assert progress.overall_mastery_pct == 92
    assert progress.attendance_pct == 95.0

    # 5. Unauthorized access rejected with PermissionError
    with pytest.raises(PermissionError) as exc_info:
        ParentPortalController.get_child_progress(unlinked_child, parent_id=parent_id, db=phase9_db)
    assert "not linked" in str(exc_info.value)

    with pytest.raises(PermissionError):
        ParentPortalController.get_child_attendance(unlinked_child, parent_id=parent_id, db=phase9_db)
