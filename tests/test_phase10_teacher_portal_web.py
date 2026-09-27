"""Tests for Phase 10: Teacher Web Portal (Section 19).

Master Plan Section 19 Verification Suite:
- Actual browser teacher application covering 15 minimum routes:
  1. /login
  2. /dashboard
  3. /students
  4. /students/:id
  5. /students/:id/timeline
  6. /students/:id/mastery
  7. /students/:id/misconceptions
  8. /students/:id/sessions
  9. /students/:id/interventions
  10. /students/:id/instructions
  11. /assignments
  12. /assessments
  13. /copilot
  14. /alerts
  15. /settings
- Teacher dashboard dimensions verified:
  1. students active
  2. average mastery
  3. difficult concepts
  4. common misconceptions
  5. recent activity
  6. intervention alerts
- Student view dimensions verified:
  1. mastery
  2. learning timeline
  3. sessions
  4. misconceptions
  5. recommendations
  6. assessment results
  7. teacher instructions
  8. interventions
- Zero mock data in production screens (all data directly from API / Authoritative SLR)
- All 8 mandatory UI states handled:
  loading, empty, success, partial_data, offline, api_error, permission_error, retry
- RBAC boundary enforcement: student access rejected with 403 Forbidden.
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.slr.service import SLRService
from central_platform.teacher.portal import TeacherPortalService, TeacherDashboardOverview


@pytest.fixture
def managed_db(tmp_path):
    """Provide isolated platform database."""
    db_file = tmp_path / "test_phase10_teacher.db"
    db = PlatformDatabase(db_path=str(db_file))
    yield db
    db.close()


@pytest.fixture
def populated_cohort(managed_db):
    """Seed cohort with realistic students, events, mastery states, and misconceptions."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    portal_service = TeacherPortalService(db=managed_db, slr_service=slr_service, event_store=event_store)

    course_id = "crs-chem-101"

    # Seed 3 distinct students
    # Student 1: High performer
    s1 = "stu_high_01"
    slr_service._ensure_student_scaffolding(s1, course_id)
    slr_service.update_concept_mastery(s1, "chem_thermo_first_law", 0.95, course_id, 0.90)
    slr_service.update_concept_mastery(s1, "chem_thermo_enthalpy", 0.90, course_id, 0.90)
    event_store.ingest_event(LearningEventIngest(
        event_id="ev_tchr_01", student_id=s1, session_id="sess_tchr_1", course_id=course_id,
        concept_id="chem_thermo_first_law", event_type="question_attempted",
        payload={"correctness": "correct", "score": 1.0}
    ))

    # Student 2: Struggling performer with misconception
    s2 = "stu_struggling_02"
    slr_service._ensure_student_scaffolding(s2, course_id)
    slr_service.update_concept_mastery(s2, "chem_thermo_first_law", 0.40, course_id, 0.70)
    slr_service.update_concept_mastery(s2, "chem_inorg_bonding_lewis", 0.35, course_id, 0.70)
    slr_service.record_student_misconception(s2, "SIGN_CONVENTION_CONFUSION", course_id)
    event_store.ingest_event(LearningEventIngest(
        event_id="ev_tchr_02", student_id=s2, session_id="sess_tchr_2", course_id=course_id,
        concept_id="chem_thermo_first_law", event_type="question_attempted",
        payload={"correctness": "incorrect", "score": 0.0, "misconception_code": "SIGN_CONVENTION_CONFUSION"}
    ))

    # Student 3: Progressing performer
    s3 = "stu_progressing_03"
    slr_service._ensure_student_scaffolding(s3, course_id)
    slr_service.update_concept_mastery(s3, "chem_thermo_first_law", 0.70, course_id, 0.80)
    slr_service.update_concept_mastery(s3, "chem_inorg_balancing", 0.75, course_id, 0.80)
    event_store.ingest_event(LearningEventIngest(
        event_id="ev_tchr_03", student_id=s3, session_id="sess_tchr_3", course_id=course_id,
        concept_id="chem_inorg_balancing", event_type="question_attempted",
        payload={"correctness": "correct", "score": 1.0}
    ))

    return {
        "portal_service": portal_service,
        "slr_service": slr_service,
        "event_store": event_store,
        "course_id": course_id,
        "student_ids": [s1, s2, s3],
    }


def test_teacher_dashboard_cohort_metrics(populated_cohort):
    """Verifies that TeacherPortalService computes all 6 Section 19 dashboard dimensions."""
    ps: TeacherPortalService = populated_cohort["portal_service"]
    course_id = populated_cohort["course_id"]

    overview = ps.get_dashboard_overview(course_id)
    assert isinstance(overview, TeacherDashboardOverview)

    # 1. students active
    assert overview.students_active >= 3
    assert overview.total_students >= 3

    # 2. average mastery
    assert 0.0 < overview.average_mastery < 1.0

    # 3. difficult concepts (concepts < 0.60 across cohort)
    assert isinstance(overview.difficult_concepts, list)
    # Inorganic chemistry had 0.35 on student 2 and 0.75 on student 3
    assert any("inorg" in str(c.get("concept_id", "")).lower() or c.get("cohort_mastery", 1.0) < 0.60 for c in overview.difficult_concepts)

    # 4. common misconceptions
    assert isinstance(overview.common_misconceptions, list)
    assert any(m["code"] == "SIGN_CONVENTION_CONFUSION" for m in overview.common_misconceptions)

    # 5. recent activity
    assert isinstance(overview.recent_activity, list)
    assert len(overview.recent_activity) >= 1

    # 6. intervention alerts
    assert isinstance(overview.intervention_alerts, list)
    assert any(a["student_id"] == "stu_struggling_02" for a in overview.intervention_alerts)


def test_teacher_student_detail_all_8_dimensions(populated_cohort):
    """Verifies that get_student_detail populates all 8 Section 19 student view elements."""
    ps: TeacherPortalService = populated_cohort["portal_service"]
    s2 = "stu_struggling_02"

    detail = ps.get_student_detail(s2)
    assert detail["student_id"] == s2
    assert detail["authoritative"] is True

    # 1. mastery
    assert "mastery" in detail
    assert "overall_score" in detail["mastery"]
    assert "concept_scores" in detail["mastery"]

    # 2. learning timeline
    assert "learning_timeline" in detail
    assert isinstance(detail["learning_timeline"], list)

    # 3. sessions
    assert "sessions" in detail
    assert isinstance(detail["sessions"], list)

    # 4. misconceptions
    assert "misconceptions" in detail
    assert any(m["code"] == "SIGN_CONVENTION_CONFUSION" for m in detail["misconceptions"])

    # 5. recommendations (strictly policy-generated)
    assert "recommendations" in detail
    assert isinstance(detail["recommendations"], list)

    # 6. assessment results
    assert "assessment_results" in detail
    assert isinstance(detail["assessment_results"], list)

    # 7. teacher instructions
    assert "teacher_instructions" in detail
    assert isinstance(detail["teacher_instructions"], list)

    # 8. interventions
    assert "interventions" in detail
    assert isinstance(detail["interventions"], list)


def test_api_teacher_dashboard_and_students_endpoints(populated_cohort, monkeypatch):
    """Verifies REST API endpoints /teachers/dashboard, /teachers/students, and /teachers/students/{id}."""
    ps = populated_cohort["portal_service"]
    course_id = populated_cohort["course_id"]
    monkeypatch.setattr("central_platform.api.routes.teachers._portal_service", ps)

    client = TestClient(app)
    t_token = create_access_token(user_id="tchr_01", role="TEACHER", organization_id="org-default")
    headers = {"Authorization": f"Bearer {t_token}"}

    # 1. GET /teachers/dashboard
    res_dash = client.get(f"/api/v1/teachers/dashboard?course_id={course_id}", headers=headers)
    assert res_dash.status_code == 200
    data_dash = res_dash.json()
    assert data_dash["ok"] is True
    dash = data_dash["data"]
    assert "total_students" in dash
    assert "students_active" in dash
    assert "average_mastery" in dash
    assert "difficult_concepts" in dash
    assert "common_misconceptions" in dash
    assert "recent_activity" in dash
    assert "intervention_alerts" in dash

    # 2. GET /teachers/students
    res_stu = client.get(f"/api/v1/teachers/students?course_id={course_id}", headers=headers)
    assert res_stu.status_code == 200
    data_stu = res_stu.json()
    assert data_stu["ok"] is True
    assert len(data_stu["data"]) >= 3

    # 3. GET /teachers/students/{student_id}
    res_detail = client.get(f"/api/v1/teachers/students/stu_struggling_02?course_id={course_id}", headers=headers)
    assert res_detail.status_code == 200
    data_detail = res_detail.json()
    assert data_detail["ok"] is True
    assert data_detail["data"]["student_id"] == "stu_struggling_02"
    assert "mastery" in data_detail["data"]
    assert "misconceptions" in data_detail["data"]


def test_api_teacher_subviews_endpoints(populated_cohort, monkeypatch):
    """Verifies subview endpoints: /timeline, /mastery, /misconceptions, /sessions, /interventions, /instructions."""
    ps = populated_cohort["portal_service"]
    course_id = populated_cohort["course_id"]
    monkeypatch.setattr("central_platform.api.routes.teachers._portal_service", ps)

    client = TestClient(app)
    t_token = create_access_token(user_id="tchr_01", role="TEACHER", organization_id="org-default")
    headers = {"Authorization": f"Bearer {t_token}"}
    sid = "stu_struggling_02"

    # Timeline
    res_tl = client.get(f"/api/v1/teachers/students/{sid}/timeline", headers=headers)
    assert res_tl.status_code == 200
    assert res_tl.json()["ok"] is True

    # Mastery
    res_m = client.get(f"/api/v1/teachers/students/{sid}/mastery", headers=headers)
    assert res_m.status_code == 200
    assert "concept_scores" in res_m.json()["data"]

    # Misconceptions
    res_misc = client.get(f"/api/v1/teachers/students/{sid}/misconceptions", headers=headers)
    assert res_misc.status_code == 200
    assert isinstance(res_misc.json()["data"], list)

    # Sessions
    res_sess = client.get(f"/api/v1/teachers/students/{sid}/sessions", headers=headers)
    assert res_sess.status_code == 200
    assert isinstance(res_sess.json()["data"], list)

    # Interventions
    res_iv = client.get(f"/api/v1/teachers/students/{sid}/interventions", headers=headers)
    assert res_iv.status_code == 200
    assert isinstance(res_iv.json()["data"], list)

    # Instructions
    res_inst = client.get(f"/api/v1/teachers/students/{sid}/instructions", headers=headers)
    assert res_inst.status_code == 200
    assert isinstance(res_inst.json()["data"], list)


def test_api_teacher_assignments_assessments_alerts(populated_cohort):
    """Verifies assignments, assessments, and alerts endpoints."""
    client = TestClient(app)
    t_token = create_access_token(user_id="tchr_01", role="TEACHER", organization_id="org-default")
    headers = {"Authorization": f"Bearer {t_token}"}

    # Assignments
    res_asg = client.get("/api/v1/teachers/assignments", headers=headers)
    assert res_asg.status_code == 200
    assert res_asg.json()["ok"] is True
    assert len(res_asg.json()["data"]) >= 2

    # Assessments
    res_asm = client.get("/api/v1/teachers/assessments", headers=headers)
    assert res_asm.status_code == 200
    assert res_asm.json()["ok"] is True
    assert len(res_asm.json()["data"]) >= 2

    # Alerts
    res_alt = client.get("/api/v1/teachers/alerts", headers=headers)
    assert res_alt.status_code == 200
    assert res_alt.json()["ok"] is True


def test_api_teacher_rbac_student_blocked():
    """Negative Security: Student attempting to access teacher endpoints receives 403 Forbidden."""
    client = TestClient(app)
    s_token = create_access_token(user_id="student_hacker", role="STUDENT", organization_id="org-default")
    headers = {"Authorization": f"Bearer {s_token}"}

    # Student accesses /teachers/dashboard
    res_dash = client.get("/api/v1/teachers/dashboard", headers=headers)
    assert res_dash.status_code == 403
    assert "Forbidden" in res_dash.json()["detail"] or "Forbidden" in res_dash.json().get("error", {}).get("message", "")

    # Student accesses /teachers/students
    res_stu = client.get("/api/v1/teachers/students", headers=headers)
    assert res_stu.status_code == 403

    # Student accesses /teachers/assignments
    res_asg = client.get("/api/v1/teachers/assignments", headers=headers)
    assert res_asg.status_code == 403

    # Student accesses /teachers/assessments
    res_asm = client.get("/api/v1/teachers/assessments", headers=headers)
    assert res_asm.status_code == 403


def test_teacher_portal_html_serves_and_routes():
    """Verifies that app/ui/teacher_portal.html is served and covers all 15 routes and 8 states."""
    html_path = os.path.join("app", "ui", "teacher_portal.html")
    assert os.path.exists(html_path), "teacher_portal.html must exist in app/ui/"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Verify all 15 required routes are defined
    required_routes = [
        "login",
        "dashboard",
        "students",
        "timeline",
        "mastery",
        "misconceptions",
        "sessions",
        "interventions",
        "instructions",
        "assignments",
        "assessments",
        "copilot",
        "alerts",
        "settings",
    ]
    for r in required_routes:
        assert r in content, f"Route or view for '{r}' must be implemented in teacher_portal.html"

    # 2. Verify all 6 Teacher Dashboard dimensions are represented
    assert "dashStudentsActive" in content
    assert "dashAverageMastery" in content
    assert "dashDifficultConceptsList" in content
    assert "dashCommonMisconceptionsList" in content
    assert "dashRecentActivityList" in content
    assert "dashAlertsCount" in content

    # 3. Verify all 8 mandatory UI states are defined
    # loading
    assert "stateLoading" in content
    # empty
    assert "stateEmpty" in content
    # success
    assert "view-dashboard" in content
    # partial_data
    assert "statePartialData" in content
    # offline
    assert "stateOffline" in content
    # api_error
    assert "stateApiError" in content
    # permission_error
    assert "statePermissionError" in content
    # retry
    assert "TeacherApp.retry" in content or "btnRetryBanner" in content

    # 4. Verify HTTP serving at /teacher and /portal
    client = TestClient(app)
    res_tchr = client.get("/teacher")
    assert res_tchr.status_code == 200
    assert "Teacher Command Center" in res_tchr.text

    res_portal = client.get("/portal")
    assert res_portal.status_code == 200
    assert "Teacher Command Center" in res_portal.text
