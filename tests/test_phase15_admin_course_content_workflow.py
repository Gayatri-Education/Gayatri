"""Phase 15 Test Suite: Admin Course & Content Workflow UI.

Master Plan Section 12.15 Verification:
1. Admin create private course with tenant isolation.
2. Admin create public course discoverable globally.
3. Admin select public course for organization (offering creation).
4. Cross-tenant private course selection forbidden (403).
5. Teacher draft version creation.
6. Content upload and RAG knowledge ingestion to course version.
7. Teacher submit version for administrative review.
8. Admin review queue scoping (tenant isolation & super admin global).
9. Admin approve and publish course version.
10. Student & Teacher forbidden actions rejected with 403.
11. Admin archive course and version.
12. UI controller state fidelity, audit trail durability, and zero demo rosters.
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.portals.admin.controller import AdminPortalController
from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    CourseStatus,
    CourseVisibility,
    Organization,
    User,
    UserRole,
)


@pytest.fixture
def managed_env(tmp_path, monkeypatch):
    """Provide isolated platform database and test client."""
    db_file = tmp_path / "phase15_admin.db"
    monkeypatch.setenv("GAYATRI_DB_PATH", str(db_file))

    # Reset any module singletons that reference db
    import central_platform.auth.dependencies as auth_deps
    auth_deps._DB_INSTANCE = PlatformDatabase(db_path=str(db_file))

    import central_platform.api.routes.admin as admin_route
    admin_route._admin_service = None

    db = auth_deps._DB_INSTANCE

    # Seed baseline organizations
    db.create_organization(Organization(id="org-alpha", name="Alpha Academy", slug="alpha"))
    db.create_organization(Organization(id="org-beta", name="Beta Institute", slug="beta"))

    # Seed users
    super_admin = User(
        id="usr-super-01",
        email="super@platform.local",
        full_name="Super Administrator",
        role=UserRole.SUPER_ADMIN,
    )
    admin_alpha = User(
        id="usr-admin-alpha",
        email="admin@alpha.edu",
        full_name="Alpha Admin",
        role=UserRole.ORG_ADMIN,
        organization_id="org-alpha",
    )
    admin_beta = User(
        id="usr-admin-beta",
        email="admin@beta.edu",
        full_name="Beta Admin",
        role=UserRole.ORG_ADMIN,
        organization_id="org-beta",
    )
    teacher_alpha = User(
        id="usr-teacher-alpha",
        email="teacher@alpha.edu",
        full_name="Alpha Teacher",
        role=UserRole.TEACHER,
        organization_id="org-alpha",
    )
    teacher_beta = User(
        id="usr-teacher-beta",
        email="teacher@beta.edu",
        full_name="Beta Teacher",
        role=UserRole.TEACHER,
        organization_id="org-beta",
    )
    student_alpha = User(
        id="usr-student-alpha",
        email="student@alpha.edu",
        full_name="Alpha Student",
        role=UserRole.STUDENT,
        organization_id="org-alpha",
    )

    for u in [super_admin, admin_alpha, admin_beta, teacher_alpha, teacher_beta, student_alpha]:
        db.create_user(u)

    client = TestClient(app)

    tokens = {
        "super_admin": create_access_token(user_id=super_admin.id, role="SUPER_ADMIN"),
        "admin_alpha": create_access_token(user_id=admin_alpha.id, role="ORG_ADMIN", organization_id="org-alpha"),
        "admin_beta": create_access_token(user_id=admin_beta.id, role="ORG_ADMIN", organization_id="org-beta"),
        "teacher_alpha": create_access_token(user_id=teacher_alpha.id, role="TEACHER", organization_id="org-alpha"),
        "teacher_beta": create_access_token(user_id=teacher_beta.id, role="TEACHER", organization_id="org-beta"),
        "student_alpha": create_access_token(user_id=student_alpha.id, role="STUDENT", organization_id="org-alpha"),
    }

    return {
        "db": db,
        "client": client,
        "tokens": tokens,
    }


# ── Test 1: Admin create private course with tenant isolation ─────────────────
def test_admin_create_private_course_tenant_isolation(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_beta = managed_env["tokens"]["admin_beta"]

    # Alpha Admin creates private course
    res = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={
            "code": "ALPHA-PHYS",
            "title": "Alpha Physics 101",
            "description": "Proprietary internal physics curriculum",
            "visibility": "PRIVATE",
            "organization_id": "org-alpha",
        },
    )
    assert res.status_code == 201
    course_data = res.json()["data"]
    assert course_data["code"] == "ALPHA-PHYS"
    assert course_data["visibility"] == "PRIVATE"
    assert course_data["organization_id"] == "org-alpha"

    # Beta Admin queries private courses
    res_beta = client.get(
        "/api/v1/courses?visibility=PRIVATE",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert res_beta.status_code == 200
    beta_courses = res_beta.json()["data"]
    course_codes = [c["code"] for c in beta_courses]
    assert "ALPHA-PHYS" not in course_codes


# ── Test 2: Admin create public course discoverable globally ──────────────────
def test_admin_create_public_course(managed_env):
    client = managed_env["client"]
    token_super = managed_env["tokens"]["super_admin"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_beta = managed_env["tokens"]["admin_beta"]

    res = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_super}"},
        json={
            "code": "MATH-OPEN",
            "title": "Open Math Fundamentals",
            "description": "Public curriculum available to all institutions",
            "visibility": "PUBLIC",
            "organization_id": "org-alpha",
        },
    )
    assert res.status_code == 201
    assert res.json()["data"]["visibility"] == "PUBLIC"

    # Both Alpha and Beta find it in public catalog
    for tok in [token_alpha, token_beta]:
        res_pub = client.get(
            "/api/v1/courses?visibility=PUBLIC",
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert res_pub.status_code == 200
        codes = [c["code"] for c in res_pub.json()["data"]]
        assert "MATH-OPEN" in codes


# ── Test 3: Admin select public course for organization ───────────────────────
def test_admin_select_public_course_for_organization(managed_env):
    client = managed_env["client"]
    token_super = managed_env["tokens"]["super_admin"]
    token_beta = managed_env["tokens"]["admin_beta"]

    # Create public course
    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_super}"},
        json={
            "code": "BIO-PUBLIC",
            "title": "Public Biology",
            "visibility": "PUBLIC",
            "organization_id": "org-alpha",
        },
    )
    course_id = res_c.json()["data"]["course_id"]

    # Beta Admin selects public course for Beta Institute
    res_sel = client.post(
        f"/api/v1/courses/{course_id}/select",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={"organization_id": "org-beta"},
    )
    assert res_sel.status_code == 200
    offering = res_sel.json()["data"]
    assert offering["course_id"] == course_id
    assert offering["organization_id"] == "org-beta"
    assert offering["is_active"] is True


# ── Test 4: Cross-tenant private course selection forbidden ───────────────────
def test_admin_select_private_course_cross_tenant_forbidden(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_beta = managed_env["tokens"]["admin_beta"]

    # Alpha creates private course
    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={
            "code": "SECRET-CHEM",
            "title": "Proprietary Chemistry",
            "visibility": "PRIVATE",
            "organization_id": "org-alpha",
        },
    )
    course_id = res_c.json()["data"]["course_id"]

    # Beta attempts to select Alpha's private course -> 403 Forbidden
    res_sel = client.post(
        f"/api/v1/courses/{course_id}/select",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={"organization_id": "org-beta"},
    )
    assert res_sel.status_code == 403
    assert "restricted" in res_sel.json()["detail"].lower()


# ── Test 5: Teacher draft version creation ────────────────────────────────────
def test_teacher_create_draft_version(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_teacher = managed_env["tokens"]["teacher_alpha"]

    # Course created
    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={
            "code": "HIST-101",
            "title": "World History",
            "visibility": "PRIVATE",
            "organization_id": "org-alpha",
        },
    )
    course_id = res_c.json()["data"]["course_id"]

    # Teacher drafts version 2.0
    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={"version_tag": "2.0"},
    )
    assert res_ver.status_code == 201
    ver_data = res_ver.json()["data"]
    assert ver_data["version_tag"] == "2.0"
    assert ver_data["status"] == "DRAFT"


# ── Test 6: Content upload and RAG knowledge ingestion to course version ──────
def test_content_upload_and_rag_ingest_to_course_version(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_teacher = managed_env["tokens"]["teacher_alpha"]

    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "GEO-201", "title": "Geography", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]

    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={"version_tag": "1.1"},
    )
    version_id = res_ver.json()["data"]["id"]

    # Register knowledge source for version 1.1
    res_src = client.post(
        "/api/v1/rag/sources",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={
            "course_id": course_id,
            "course_version_id": version_id,
            "subject": "Geography",
            "title": "Geological Formations",
            "source_type": "text",
            "content_type": "textbook",
            "visibility_scope": "course",
        },
    )
    assert res_src.status_code in (200, 201)
    source_id = res_src.json()["data"]["id"]

    # Ingest text content into source
    content_text = """# Plate Tectonics
The lithosphere is divided into tectonic plates that move relative to one another.
Continental drift explains fossil distribution across separated continents.
    """
    res_ing = client.post(
        f"/api/v1/rag/sources/{source_id}/ingest",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={"content": content_text, "file_name": "plate_tectonics.md"},
    )
    assert res_ing.status_code == 200
    ing_data = res_ing.json()["data"]
    assert ing_data["status"] in ("ingested", "READY")
    assert ing_data["chunks_created"] > 0


# ── Test 7: Teacher submit version for administrative review ─────────────────
def test_teacher_submit_version_for_review(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_teacher = managed_env["tokens"]["teacher_alpha"]

    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "LIT-301", "title": "Literature", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]

    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={"version_tag": "3.0"},
    )
    version_id = res_ver.json()["data"]["id"]

    # Submit for review
    res_sub = client.post(
        f"/api/v1/courses/{course_id}/versions/{version_id}/submit",
        headers={"Authorization": f"Bearer {token_teacher}"},
    )
    assert res_sub.status_code == 200
    assert res_sub.json()["data"]["status"] == "READY_FOR_REVIEW"

    # Submitting again when already READY_FOR_REVIEW -> 400
    res_sub2 = client.post(
        f"/api/v1/courses/{course_id}/versions/{version_id}/submit",
        headers={"Authorization": f"Bearer {token_teacher}"},
    )
    assert res_sub2.status_code == 400


# ── Test 8: Admin review queue scoping (tenant isolation & super admin global) ─
def test_admin_review_queue_scoping(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_beta = managed_env["tokens"]["admin_beta"]
    token_super = managed_env["tokens"]["super_admin"]
    token_teacher_alpha = managed_env["tokens"]["teacher_alpha"]

    # Create Alpha course & submit version
    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "QUEUE-101", "title": "Queue Test Course", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]
    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher_alpha}"},
        json={"version_tag": "1.5"},
    )
    ver_id = res_ver.json()["data"]["id"]
    client.post(f"/api/v1/courses/{course_id}/versions/{ver_id}/submit", headers={"Authorization": f"Bearer {token_teacher_alpha}"})

    # Alpha Admin sees the pending version in review queue
    res_q_alpha = client.get("/api/v1/courses/review-queue", headers={"Authorization": f"Bearer {token_alpha}"})
    assert res_q_alpha.status_code == 200
    q_alpha = res_q_alpha.json()["data"]
    version_ids_alpha = [item["version_id"] for item in q_alpha]
    assert ver_id in version_ids_alpha

    # Beta Admin does NOT see Alpha's pending version
    res_q_beta = client.get("/api/v1/courses/review-queue", headers={"Authorization": f"Bearer {token_beta}"})
    assert res_q_beta.status_code == 200
    q_beta = res_q_beta.json()["data"]
    version_ids_beta = [item["version_id"] for item in q_beta]
    assert ver_id not in version_ids_beta

    # Super Admin sees Alpha's pending version
    res_q_super = client.get("/api/v1/courses/review-queue", headers={"Authorization": f"Bearer {token_super}"})
    assert res_q_super.status_code == 200
    version_ids_super = [item["version_id"] for item in res_q_super.json()["data"]]
    assert ver_id in version_ids_super


# ── Test 9: Admin approve and publish course version ───────────────────────────
def test_admin_approve_and_publish_version(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_teacher_alpha = managed_env["tokens"]["teacher_alpha"]

    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "PUB-202", "title": "Publishing Test Course", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]
    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher_alpha}"},
        json={"version_tag": "2.1"},
    )
    ver_id = res_ver.json()["data"]["id"]
    client.post(f"/api/v1/courses/{course_id}/versions/{ver_id}/submit", headers={"Authorization": f"Bearer {token_teacher_alpha}"})

    # Alpha Admin approves and publishes version
    res_pub = client.post(
        f"/api/v1/courses/{course_id}/versions/{ver_id}/publish",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "PUBLISHED"

    # Verify published status persists
    res_list = client.get(f"/api/v1/courses/{course_id}/versions", headers={"Authorization": f"Bearer {token_alpha}"})
    assert res_list.status_code == 200
    v_published = next(v for v in res_list.json()["data"] if v["id"] == ver_id)
    assert v_published["status"] == "PUBLISHED"


# ── Test 10: Student & Teacher forbidden actions rejected with 403 ────────────
def test_student_and_teacher_forbidden_actions(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]
    token_student = managed_env["tokens"]["student_alpha"]
    token_teacher = managed_env["tokens"]["teacher_alpha"]

    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "RBAC-303", "title": "RBAC Course", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]
    res_ver = client.post(
        f"/api/v1/courses/{course_id}/versions",
        headers={"Authorization": f"Bearer {token_teacher}"},
        json={"version_tag": "1.0-rbac"},
    )
    ver_id = res_ver.json()["data"]["id"]
    client.post(f"/api/v1/courses/{course_id}/versions/{ver_id}/submit", headers={"Authorization": f"Bearer {token_teacher}"})

    # Student cannot approve and publish
    res_s_pub = client.post(
        f"/api/v1/courses/{course_id}/versions/{ver_id}/publish",
        headers={"Authorization": f"Bearer {token_student}"},
    )
    assert res_s_pub.status_code == 403

    # Teacher cannot approve and publish (must be Org Admin or Super Admin)
    res_t_pub = client.post(
        f"/api/v1/courses/{course_id}/versions/{ver_id}/publish",
        headers={"Authorization": f"Bearer {token_teacher}"},
    )
    assert res_t_pub.status_code == 403

    # Student cannot archive course
    res_s_arch = client.post(
        f"/api/v1/courses/{course_id}/archive",
        headers={"Authorization": f"Bearer {token_student}"},
    )
    assert res_s_arch.status_code == 403

    # Student cannot view review queue
    res_s_q = client.get(
        "/api/v1/courses/review-queue",
        headers={"Authorization": f"Bearer {token_student}"},
    )
    assert res_s_q.status_code == 403


# ── Test 11: Admin archive course and version ─────────────────────────────────
def test_admin_archive_course_and_version(managed_env):
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]

    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "ARCH-404", "title": "Archival Course", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]

    # Initial draft version created on course creation
    res_versions = client.get(f"/api/v1/courses/{course_id}/versions", headers={"Authorization": f"Bearer {token_alpha}"})
    v1_id = res_versions.json()["data"][0]["id"]

    # Archive version
    res_arch_v = client.post(
        f"/api/v1/courses/{course_id}/versions/{v1_id}/archive",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res_arch_v.status_code == 200
    assert res_arch_v.json()["data"]["status"] == "ARCHIVED"

    # Archive entire course
    res_arch_c = client.post(
        f"/api/v1/courses/{course_id}/archive",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res_arch_c.status_code == 200
    assert res_arch_c.json()["data"]["status"] == "ARCHIVED"

    # Soft-deleted course no longer appears in default list
    res_list = client.get(
        "/api/v1/courses?visibility=PRIVATE",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res_list.status_code == 200
    active_codes = [c["code"] for c in res_list.json()["data"]]
    assert "ARCH-404" not in active_codes


# ── Test 12: UI controller state fidelity, audit trail, zero demo rosters ──────
def test_ui_controller_and_audit_trail_durability(managed_env):
    db = managed_env["db"]
    client = managed_env["client"]
    token_alpha = managed_env["tokens"]["admin_alpha"]

    # Execute workflow to populate audit trail
    res_c = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"code": "AUDIT-505", "title": "Audited Course", "visibility": "PRIVATE", "organization_id": "org-alpha"},
    )
    course_id = res_c.json()["data"]["course_id"]
    client.post(f"/api/v1/courses/{course_id}/archive", headers={"Authorization": f"Bearer {token_alpha}"})

    # Instantiate AdminPortalController backed by real DB
    controller = AdminPortalController(db=db)
    ctx = controller.get_dashboard_context(user_id="usr-admin-alpha", organization_id="org-alpha")

    # Assert honest state & metrics
    assert ctx["portal"] == "admin"
    assert ctx["organization_id"] == "org-alpha"
    assert ctx["stats"]["active_organizations"] >= 2
    assert "review_queue" in ctx["supported_tabs"]

    # Verify zero fake demo roster entries in bridge/portal
    with db._get_connection() as conn:
        demo_students = conn.execute(
            "SELECT COUNT(*) FROM users WHERE full_name IN ('Rahul Kumar', 'Priya Sharma', 'Amit Patel');"
        ).fetchone()[0]
        assert demo_students == 0, "Fake demo roster detected in database!"

    # Verify audit trail contains real lifecycle records
    audit_logs = controller.get_audit_trail(organization_id="org-alpha")
    actions = [a["action"] for a in audit_logs]
    assert "CREATE_COURSE" in actions
    assert "ARCHIVE_COURSE" in actions
