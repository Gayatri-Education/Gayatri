"""Comprehensive Verification Test Suite for Phase 14: Admin Web Portal.

Master Plan Section 23 Requirements:
1. 16 Core Admin Pages & Resource APIs:
   /dashboard, /organizations, /users, /teachers, /students,
   /courses, /curricula, /classes, /cohorts, /enrollments,
   /providers, /models, /ai-policies, /audit, /analytics, /system-health.
2. Multi-tenant administrative controls:
   create/update users, roles, organizations, courses, curricula,
   versions, classes, enrollments, AI providers, AI models,
   feature flags, emergency kill switch.
3. Multi-tenant RBAC gatekeeping:
   - Super Admin has global authority.
   - Org Admin is strictly confined to own organization (403 on cross-tenant).
   - Students and Teachers are blocked with 403 Forbidden.
4. Audit provenance: mutations recorded in audit log.
5. Frontend integrity: all 16 navigation views in app/ui/admin_portal.html.
"""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.models.schema import UserRole


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def super_admin_token():
    return create_access_token(user_id="super-admin-01", role="SUPER_ADMIN")


@pytest.fixture
def org_admin_token():
    return create_access_token(
        user_id="org-admin-01",
        role="ORG_ADMIN",
        organization_id="org-delhi",
    )


@pytest.fixture
def teacher_token():
    return create_access_token(user_id="teacher-01", role="TEACHER")


@pytest.fixture
def student_token():
    return create_access_token(user_id="student-01", role="STUDENT")


# ── 1. Dashboard & System Health ──────────────────────────────────────────

def test_admin_dashboard_metrics(client, super_admin_token):
    res = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "organizations_count" in data
    assert "total_users" in data
    assert "courses_count" in data
    assert "active_models_count" in data
    assert data["system_status"] == "HEALTHY"


def test_admin_system_health_and_kill_switch(client, super_admin_token, teacher_token):
    # Get system health
    res = client.get(
        "/api/v1/admin/system-health",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["api_server"] == "ONLINE"
    assert data["database"] == "ONLINE"

    # Super Admin toggles kill switch
    res_kill = client.post(
        "/api/v1/admin/kill-switch?active=true&reason=EmergencySafetyHalt",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_kill.status_code == 200
    assert res_kill.json()["data"]["kill_switch_active"] is True

    # Revert kill switch
    client.post(
        "/api/v1/admin/kill-switch?active=false&reason=TestNominal",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )

    # Teacher cannot toggle kill switch (403)
    res_forbidden = client.post(
        "/api/v1/admin/kill-switch?active=true&reason=Unauthorized",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_forbidden.status_code == 403


# ── 2. Organizations Management ───────────────────────────────────────────

def test_organizations_crud_and_tenant_scoping(client, super_admin_token, org_admin_token):
    # Super Admin creates organization
    org_payload = {"name": "Punjab Technology Institute", "slug": "pti", "tier": "ENTERPRISE", "student_quota": 600}
    res_create = client.post(
        "/api/v1/admin/organizations",
        json=org_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_create.status_code == 201
    created_org = res_create.json()["data"]
    assert created_org["name"] == "Punjab Technology Institute"
    assert created_org["slug"] == "pti"

    # Org Admin forbidden from creating organizations (Super Admin only)
    res_org_forbidden = client.post(
        "/api/v1/admin/organizations",
        json={"name": "Illegal Org", "slug": "ill"},
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert res_org_forbidden.status_code == 403


# ── 3. User Provisioning & Roles ──────────────────────────────────────────

def test_user_provisioning_and_scoping(client, super_admin_token, org_admin_token):
    # Super Admin creates a Teacher
    t_payload = {
        "email": "dr_sharma@gayatri.edu",
        "full_name": "Dr. Sharma",
        "role": "TEACHER",
        "organization_id": "org-delhi",
    }
    res_t = client.post(
        "/api/v1/admin/users",
        json=t_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_t.status_code == 201
    teacher = res_t.json()["data"]
    assert teacher["role"].upper() == "TEACHER"

    # Super Admin creates a Student
    s_payload = {
        "email": "aarav_patel@gayatri.edu",
        "full_name": "Aarav Patel",
        "role": "STUDENT",
        "organization_id": "org-delhi",
    }
    res_s = client.post(
        "/api/v1/admin/users",
        json=s_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_s.status_code == 201
    student = res_s.json()["data"]
    assert student["role"].upper() == "STUDENT"

    # Org Admin creates student in own tenant
    res_org_s = client.post(
        "/api/v1/admin/users",
        json={"email": "student_delhi@gayatri.edu", "full_name": "Delhi Student", "role": "STUDENT"},
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert res_org_s.status_code == 201

    # Org Admin blocked from creating Super Admin (403)
    res_esc = client.post(
        "/api/v1/admin/users",
        json={"email": "hacker@gayatri.edu", "full_name": "Hacker", "role": "SUPER_ADMIN"},
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert res_esc.status_code == 403

    # Org Admin blocked from creating user in another tenant (403)
    res_cross = client.post(
        "/api/v1/admin/users",
        json={"email": "cross@gayatri.edu", "full_name": "Cross", "role": "STUDENT", "organization_id": "org-mumbai"},
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert res_cross.status_code == 403


def test_user_update_and_soft_delete(client, super_admin_token):
    # Create user
    res = client.post(
        "/api/v1/admin/users",
        json={"email": "temp_user@gayatri.edu", "full_name": "Temp User", "role": "STUDENT"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    uid = res.json()["data"]["id"]

    # Patch user status
    res_patch = client.patch(
        f"/api/v1/admin/users/{uid}",
        json={"full_name": "Updated Name", "is_active": False},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["full_name"] == "Updated Name"

    # Delete user
    res_del = client.delete(
        f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_del.status_code == 200
    assert res_del.json()["data"]["deleted"] is True


def test_teacher_and_student_roster_endpoints(client, super_admin_token):
    res_t = client.get("/api/v1/admin/teachers", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_t.status_code == 200
    assert isinstance(res_t.json()["data"], list)

    res_s = client.get("/api/v1/admin/students", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_s.status_code == 200
    assert isinstance(res_s.json()["data"], list)


# ── 4. Courses, Curricula, Classes, Cohorts ───────────────────────────────

def test_academics_curriculum_classes_cohorts(client, super_admin_token):
    # 1. Create Course
    res_c = client.post(
        "/api/v1/admin/courses",
        json={"code": "CRS-BIO-101", "title": "Class 11 Biology", "description": "Cellular and Molecular Biology"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_c.status_code == 201
    course_id = res_c.json()["data"]["id"]

    # 2. Create Curriculum
    res_cur = client.post(
        "/api/v1/admin/curricula",
        json={"course_id": course_id, "title": "CBSE Biology Curriculum 2026", "version": "v1.2"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_cur.status_code == 201
    assert res_cur.json()["data"]["version"] == "v1.2"

    # 3. Create Class Group
    res_cg = client.post(
        "/api/v1/admin/classes",
        json={"name": "Grade 11 Section A", "section": "A", "course_id": course_id},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_cg.status_code == 201
    class_id = res_cg.json()["data"]["id"]

    # 4. Create Cohort
    res_ch = client.post(
        "/api/v1/admin/cohorts",
        json={"name": "Bio-2026-Batch-A", "academic_year": "2026-2027", "class_group_id": class_id},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_ch.status_code == 201
    assert res_ch.json()["data"]["name"] == "Bio-2026-Batch-A"


# ── 5. Enrollments Management ─────────────────────────────────────────────

def test_enrollments_lifecycle(client, super_admin_token):
    # 1. Prerequisite: Create student user
    res_s = client.post(
        "/api/v1/admin/users",
        json={"email": "enroll_test_student@gayatri.edu", "full_name": "Enroll Student", "role": "STUDENT"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_s.status_code == 201
    student_id = res_s.json()["data"]["id"]

    # 2. Prerequisite: Create course
    res_c = client.post(
        "/api/v1/admin/courses",
        json={"code": "CRS-ENR-101", "title": "Enrollment Course"},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_c.status_code == 201
    course_id = res_c.json()["data"]["id"]

    # 3. Prerequisite: Create class and cohort
    res_cg = client.post(
        "/api/v1/admin/classes",
        json={"name": "Class Enr", "section": "A", "course_id": course_id},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_cg.status_code == 201
    class_id = res_cg.json()["data"]["id"]

    res_ch = client.post(
        "/api/v1/admin/cohorts",
        json={"name": "Cohort-Enr-A", "academic_year": "2026-2027", "class_group_id": class_id},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_ch.status_code == 201
    cohort_id = res_ch.json()["data"]["id"]

    # 4. Enroll student
    payload = {"student_id": student_id, "course_id": course_id, "cohort_id": cohort_id}
    res = client.post(
        "/api/v1/admin/enrollments",
        json=payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res.status_code == 201
    enr_id = res.json()["data"]["id"]
    assert res.json()["data"]["student_id"] == student_id

    # List enrollments
    res_list = client.get("/api/v1/admin/enrollments", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_list.status_code == 200
    assert any(e["id"] == enr_id for e in res_list.json()["data"])

    # Revoke enrollment
    res_del = client.delete(
        f"/api/v1/admin/enrollments/{enr_id}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_del.status_code == 200
    assert res_del.json()["data"]["revoked"] is True


# ── 6. AI Providers & Models ──────────────────────────────────────────────

def test_ai_providers_and_models(client, super_admin_token):
    # List default providers
    res_p = client.get("/api/v1/admin/providers", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_p.status_code == 200
    assert len(res_p.json()["data"]) >= 2

    # Register new provider
    prov_payload = {"name": "Mistral AI API", "provider_type": "mistral", "base_url": "https://api.mistral.ai"}
    res_prov_create = client.post(
        "/api/v1/admin/providers",
        json=prov_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_prov_create.status_code == 201
    prov_id = res_prov_create.json()["data"]["id"]

    # Register new model
    model_payload = {"provider_id": prov_id, "model_name": "mistral-large-latest", "context_window": 32768, "is_default": False}
    res_model_create = client.post(
        "/api/v1/admin/models",
        json=model_payload,
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_model_create.status_code == 201
    assert res_model_create.json()["data"]["context_window"] == 32768


# ── 7. AI Policies & Feature Flags ────────────────────────────────────────

def test_ai_policies_and_feature_flags(client, super_admin_token):
    # AI Policies
    res_pol = client.get("/api/v1/admin/ai-policies", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_pol.status_code == 200
    assert res_pol.json()["data"]["ai_policy_level"] in ("strict", "balanced", "permissive")

    res_pol_update = client.post(
        "/api/v1/admin/ai-policies",
        json={"ai_policy_level": "balanced", "anti_answer_leakage": True},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_pol_update.status_code == 200
    assert res_pol_update.json()["data"]["ai_policy_level"] == "balanced"

    # Feature flags
    res_flags = client.get("/api/v1/admin/feature-flags", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_flags.status_code == 200
    assert "enable_voice" in res_flags.json()["data"]["flags"]

    res_flags_update = client.post(
        "/api/v1/admin/feature-flags",
        json={"flags": {"enable_voice": False, "enable_chemistry_3d": True}},
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_flags_update.status_code == 200
    assert res_flags_update.json()["data"]["flags"]["enable_voice"] is False


# ── 8. Audit Trail & Analytics ────────────────────────────────────────────

def test_audit_trail_and_analytics(client, super_admin_token):
    # Audit log
    res_audit = client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_audit.status_code == 200
    events = res_audit.json()["data"]
    assert isinstance(events, list)
    assert len(events) >= 1

    # Analytics telemetry
    res_an = client.get("/api/v1/admin/analytics", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_an.status_code == 200
    assert "daily_active_sessions" in res_an.json()["data"]


# ── 9. RBAC Security Rejection for Teachers & Students ────────────────────

def test_admin_endpoints_strictly_reject_students_and_teachers(client, student_token, teacher_token):
    endpoints = [
        "/api/v1/admin/dashboard",
        "/api/v1/admin/organizations",
        "/api/v1/admin/users",
        "/api/v1/admin/courses",
        "/api/v1/admin/curricula",
        "/api/v1/admin/classes",
        "/api/v1/admin/cohorts",
        "/api/v1/admin/enrollments",
        "/api/v1/admin/providers",
        "/api/v1/admin/models",
        "/api/v1/admin/ai-policies",
        "/api/v1/admin/feature-flags",
        "/api/v1/admin/audit",
        "/api/v1/admin/analytics",
        "/api/v1/admin/system-health",
    ]

    for ep in endpoints:
        r_student = client.get(ep, headers={"Authorization": f"Bearer {student_token}"})
        assert r_student.status_code == 403, f"Student allowed to access {ep}"

        r_teacher = client.get(ep, headers={"Authorization": f"Bearer {teacher_token}"})
        assert r_teacher.status_code == 403, f"Teacher allowed to access {ep}"


# ── 10. Frontend Admin Portal HTML Integrity ──────────────────────────────

def test_admin_portal_html_contains_all_16_views():
    path = os.path.join("app", "ui", "admin_portal.html")
    assert os.path.exists(path), "admin_portal.html must exist"

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    expected_views = [
        "view-dashboard",
        "view-organizations",
        "view-users",
        "view-teachers",
        "view-students",
        "view-courses",
        "view-curricula",
        "view-classes",
        "view-cohorts",
        "view-enrollments",
        "view-providers",
        "view-models",
        "view-ai-policies",
        "view-audit",
        "view-analytics",
        "view-system",
    ]

    for view_id in expected_views:
        assert f'id="{view_id}"' in html, f"Missing view element {view_id} in admin_portal.html"

    # Verify Kill switch banner
    assert 'id="killSwitchBanner"' in html
    assert 'AdminApp.init()' in html
