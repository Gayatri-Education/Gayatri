"""Phase 16 Test Suite: Teacher Workflow UI & Class Management.

Master Plan Section 12.16 Verification:
1. Teacher list courses and classes scoped strictly to organization.
2. Teacher create class group with default cohort.
3. Teacher view class roster with honest empty states and real SLR mastery.
4. Teacher unauthorized student selection denied (HTTP 403 Forbidden).
5. Teacher upload class note and verify class-scoped RAG retrieval.
6. Cross-class note isolation enforced (cross-class and cross-org denied).
7. Teacher upload remedial content and verify student-targeted RAG retrieval.
8. Cross-student remedial content isolation enforced.
9. Teacher compose scoped instructions hierarchy with policy validation.
10. Teacher create and list real assignments with class group filtering.
11. TeacherPortalController real service workflows and durability.
12. DesktopBridgeFacade teacher slots integration and error sanitization.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.bridge.facade import Bridge
from app.portals.teacher.controller import TeacherPortalController
from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    ClassGroup,
    Cohort,
    Course,
    CourseOffering,
    CourseStatus,
    CourseVisibility,
    Enrollment,
    Organization,
    StudentLearningRecord,
    MasteryState,
    User,
    UserRole,
)
from central_platform.slr.service import SLRService


@pytest.fixture
def managed_env(tmp_path, monkeypatch):
    """Provide isolated platform database and test client."""
    db_file = tmp_path / "phase16_teacher.db"
    monkeypatch.setenv("GAYATRI_DB_PATH", str(db_file))

    # Reset module singletons
    import central_platform.auth.dependencies as auth_deps
    auth_deps._DB_INSTANCE = PlatformDatabase(db_path=str(db_file))

    import central_platform.api.routes.teachers as teacher_route
    teacher_route._slr_service = SLRService(db=auth_deps._DB_INSTANCE)

    db = auth_deps._DB_INSTANCE

    # Seed baseline organizations
    db.create_organization(Organization(id="org-alpha", name="Alpha Academy", slug="alpha"))
    db.create_organization(Organization(id="org-beta", name="Beta Institute", slug="beta"))

    # Seed teachers
    tchr_alpha = User(
        id="tchr-alpha-01",
        email="teacher@alpha.local",
        full_name="Alpha Teacher",
        role=UserRole.TEACHER,
        organization_id="org-alpha",
    )
    tchr_beta = User(
        id="tchr-beta-01",
        email="teacher@beta.local",
        full_name="Beta Teacher",
        role=UserRole.TEACHER,
        organization_id="org-beta",
    )
    db.create_user(tchr_alpha)
    db.create_user(tchr_beta)

    # Seed students
    std_alpha_1 = User(
        id="std-alpha-01",
        email="alice@alpha.local",
        full_name="Alice Alpha",
        role=UserRole.STUDENT,
        organization_id="org-alpha",
    )
    std_alpha_2 = User(
        id="std-alpha-02",
        email="bob@alpha.local",
        full_name="Bob Alpha",
        role=UserRole.STUDENT,
        organization_id="org-alpha",
    )
    std_beta_1 = User(
        id="std-beta-01",
        email="charlie@beta.local",
        full_name="Charlie Beta",
        role=UserRole.STUDENT,
        organization_id="org-beta",
    )
    db.create_user(std_alpha_1)
    db.create_user(std_alpha_2)
    db.create_user(std_beta_1)

    # Seed courses
    now_iso = datetime.now(timezone.utc).isoformat()
    crs_alpha_math = Course(
        id="crs-alpha-math",
        organization_id="org-alpha",
        title="Calculus I",
        code="MATH-101",
        visibility=CourseVisibility.PRIVATE,
        created_at=now_iso,
    )
    crs_beta_chem = Course(
        id="crs-beta-chem",
        organization_id="org-beta",
        title="Organic Chemistry",
        code="CHEM-201",
        visibility=CourseVisibility.PRIVATE,
        created_at=now_iso,
    )
    crs_public_phy = Course(
        id="crs-public-phy",
        organization_id="org-alpha",
        title="General Physics",
        code="PHYS-101",
        visibility=CourseVisibility.PUBLIC,
        created_at=now_iso,
    )
    db.create_course(crs_alpha_math)
    db.create_course(crs_beta_chem)
    db.create_course(crs_public_phy)

    # Tokens
    token_tchr_alpha = create_access_token(user_id=tchr_alpha.id, role="TEACHER", organization_id="org-alpha")
    token_tchr_beta = create_access_token(user_id=tchr_beta.id, role="TEACHER", organization_id="org-beta")
    token_std_alpha_1 = create_access_token(user_id=std_alpha_1.id, role="STUDENT", organization_id="org-alpha")
    token_std_beta_1 = create_access_token(user_id=std_beta_1.id, role="STUDENT", organization_id="org-beta")

    client = TestClient(app)

    return {
        "db": db,
        "client": client,
        "headers_tchr_alpha": {"Authorization": f"Bearer {token_tchr_alpha}"},
        "headers_tchr_beta": {"Authorization": f"Bearer {token_tchr_beta}"},
        "headers_std_alpha_1": {"Authorization": f"Bearer {token_std_alpha_1}"},
        "headers_std_beta_1": {"Authorization": f"Bearer {token_std_beta_1}"},
        "users": {
            "tchr_alpha": tchr_alpha,
            "tchr_beta": tchr_beta,
            "std_alpha_1": std_alpha_1,
            "std_alpha_2": std_alpha_2,
            "std_beta_1": std_beta_1,
        },
        "courses": {
            "crs_alpha_math": crs_alpha_math,
            "crs_beta_chem": crs_beta_chem,
            "crs_public_phy": crs_public_phy,
        },
    }


def test_teacher_list_courses_and_classes_scoped_to_org(managed_env):
    """1. Verify teacher retrieves only courses and classes scoped to their organization."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    headers_beta = managed_env["headers_tchr_beta"]

    # Teacher Alpha queries courses
    res_courses = client.get("/api/v1/teachers/courses", headers=headers_alpha)
    assert res_courses.status_code == 200
    courses_alpha = res_courses.json()["data"]
    course_ids_alpha = [c["id"] for c in courses_alpha]
    assert "crs-alpha-math" in course_ids_alpha
    assert "crs-public-phy" in course_ids_alpha
    assert "crs-beta-chem" not in course_ids_alpha

    # Create a class in Alpha and a class in Beta
    db: PlatformDatabase = managed_env["db"]
    now_iso = datetime.now(timezone.utc).isoformat()
    cg_alpha = ClassGroup(
        id="cls-alpha-period-1",
        organization_id="org-alpha",
        course_id="crs-alpha-math",
        name="Calculus Period 1",
        section="1",
        created_at=now_iso,
    )
    cg_beta = ClassGroup(
        id="cls-beta-period-1",
        organization_id="org-beta",
        course_id="crs-beta-chem",
        name="Chemistry Period 1",
        section="1",
        created_at=now_iso,
    )
    db.create_class_group(cg_alpha)
    db.create_class_group(cg_beta)

    # Teacher Alpha gets classes
    res_cls_alpha = client.get("/api/v1/teachers/classes", headers=headers_alpha)
    assert res_cls_alpha.status_code == 200
    cls_data_alpha = res_cls_alpha.json()["data"]
    cls_ids_alpha = [cg["id"] for cg in cls_data_alpha]
    assert "cls-alpha-period-1" in cls_ids_alpha
    assert "cls-beta-period-1" not in cls_ids_alpha

    # Teacher Beta gets classes
    res_cls_beta = client.get("/api/v1/teachers/classes", headers=headers_beta)
    assert res_cls_beta.status_code == 200
    cls_data_beta = res_cls_beta.json()["data"]
    cls_ids_beta = [cg["id"] for cg in cls_data_beta]
    assert "cls-beta-period-1" in cls_ids_beta
    assert "cls-alpha-period-1" not in cls_ids_beta


def test_teacher_create_class_group(managed_env):
    """2. Verify teacher can create class group with default cohort in their org, denied for other org course."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    db: PlatformDatabase = managed_env["db"]

    payload = {
        "course_id": "crs-alpha-math",
        "name": "Calculus Advanced Section C",
        "section": "C",
    }
    res = client.post("/api/v1/teachers/classes", json=payload, headers=headers_alpha)
    assert res.status_code == 201
    created_cg = res.json()["data"]
    assert created_cg["name"] == "Calculus Advanced Section C"
    assert created_cg["organization_id"] == "org-alpha"
    assert created_cg["course_id"] == "crs-alpha-math"

    # Confirm in DB
    cg_in_db = db.get_class_group(created_cg["id"])
    assert cg_in_db is not None
    assert cg_in_db.section == "C"

    # Confirm default cohort created
    cohorts = db.get_cohorts_for_class_group(created_cg["id"])
    assert len(cohorts) == 1
    assert cohorts[0].name == "Calculus Advanced Section C Cohort"

    # Unauthorized course creation attempt (private course in Beta)
    payload_bad = {
        "course_id": "crs-beta-chem",
        "name": "Forbidden Chem",
        "section": "X",
    }
    res_bad = client.post("/api/v1/teachers/classes", json=payload_bad, headers=headers_alpha)
    assert res_bad.status_code == 403


def test_teacher_get_class_roster_empty_and_populated(managed_env):
    """3. Verify honest empty state on new class and populated roster with SLR mastery."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    db: PlatformDatabase = managed_env["db"]

    # 1. Create fresh class
    cg_res = client.post(
        "/api/v1/teachers/classes",
        json={"course_id": "crs-alpha-math", "name": "Period 4", "section": "4"},
        headers=headers_alpha,
    )
    assert cg_res.status_code == 201
    class_id = cg_res.json()["data"]["id"]

    # Honest empty state: no students
    roster_res = client.get(f"/api/v1/teachers/classes/{class_id}/students", headers=headers_alpha)
    assert roster_res.status_code == 200
    assert roster_res.json()["data"] == []

    # 2. Enroll student in cohort & course
    cohorts = db.get_cohorts_for_class_group(class_id)
    cohort_id = cohorts[0].id
    enrollment = Enrollment(
        id="enr-001",
        student_id="std-alpha-01",
        course_id="crs-alpha-math",
        cohort_id=cohort_id,
        is_active=True,
    )
    db.create_enrollment(enrollment)

    # Seed SLR record with mastery
    slr = StudentLearningRecord(
        id="slr-alpha-01",
        student_id="std-alpha-01",
        course_id="crs-alpha-math",
    )
    db.create_slr(slr)
    db.upsert_mastery_state(
        MasteryState(
            id="ms-001",
            slr_id=slr.id,
            concept_id="limits",
            score=0.85,
            confidence=0.9,
        )
    )

    # Fetch roster again
    roster_res_2 = client.get(f"/api/v1/teachers/classes/{class_id}/students", headers=headers_alpha)
    assert roster_res_2.status_code == 200
    roster = roster_res_2.json()["data"]
    assert len(roster) == 1
    assert roster[0]["student_id"] == "std-alpha-01"
    assert roster[0]["full_name"] == "Alice Alpha"
    assert roster[0]["mastery"] == 0.85
    assert roster[0]["needs_attention"] is False


def test_teacher_select_unauthorized_student_denied_403(managed_env):
    """4. Verify teacher cannot select students outside organization or unenrolled students."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]

    # Cross-tenant remedial content target
    payload_remedial_cross = {
        "course_id": "crs-alpha-math",
        "target_student_ids": ["std-beta-01"],
        "title": "Remedial Help",
        "content": "Work through limits.",
    }
    res_rem = client.post("/api/v1/teachers/remedial-content", json=payload_remedial_cross, headers=headers_alpha)
    assert res_rem.status_code == 403
    assert "not in your organization" in res_rem.json()["detail"]

    # Same-org but unenrolled student
    payload_remedial_unenrolled = {
        "course_id": "crs-alpha-math",
        "target_student_ids": ["std-alpha-02"],
        "title": "Remedial Help",
        "content": "Work through limits.",
    }
    res_rem2 = client.post("/api/v1/teachers/remedial-content", json=payload_remedial_unenrolled, headers=headers_alpha)
    assert res_rem2.status_code == 403
    assert "not enrolled in course" in res_rem2.json()["detail"]

    # Cross-tenant student instruction
    payload_instruction = {
        "instruction": "Focus on calculus derivations before applying formulas.",
        "course_id": "crs-alpha-math",
        "student_id": "std-beta-01",
        "priority": 5,
    }
    res_inst = client.post("/api/v1/teachers/instructions", json=payload_instruction, headers=headers_alpha)
    assert res_inst.status_code == 403
    assert "belongs to another organization" in res_inst.json()["detail"]


def test_teacher_upload_class_note_and_verify_rag_scoping(managed_env):
    """5. Verify uploading class notes scopes visibility strictly to the specified class."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    db: PlatformDatabase = managed_env["db"]

    # Create class
    cg_res = client.post(
        "/api/v1/teachers/classes",
        json={"course_id": "crs-alpha-math", "name": "Calculus Note Class", "section": "N1"},
        headers=headers_alpha,
    )
    class_id = cg_res.json()["data"]["id"]

    # Upload class note
    note_payload = {
        "title": "Limits and Continuity Lecture Notes",
        "content": "A function is continuous at c if the limit as x approaches c equals f(c).",
    }
    res_note = client.post(f"/api/v1/teachers/classes/{class_id}/notes", json=note_payload, headers=headers_alpha)
    assert res_note.status_code == 201
    data = res_note.json()["data"]
    assert data["class_id"] == class_id
    assert data["status"] == "PUBLISHED"
    assert data["chunks_created"] >= 1

    # Verify RAG chunk retrieval for this class
    chunks = db.get_rag_chunks_by_course(course_id="crs-alpha-math", class_id=class_id)
    assert len(chunks) >= 1
    assert any("continuous at c" in (ch.clean_text or ch.text) for ch in chunks)


def test_cross_class_note_isolation_denied(managed_env):
    """6. Verify notes from class A are isolated from class B and cross-org note uploads denied."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    headers_beta = managed_env["headers_tchr_beta"]
    db: PlatformDatabase = managed_env["db"]

    # Create Class A in Alpha
    cg_res = client.post(
        "/api/v1/teachers/classes",
        json={"course_id": "crs-alpha-math", "name": "Class A Notes", "section": "A"},
        headers=headers_alpha,
    )
    class_a_id = cg_res.json()["data"]["id"]

    # Upload note to Class A
    client.post(
        f"/api/v1/teachers/classes/{class_a_id}/notes",
        json={"title": "Class A Proprietary Note", "content": "Special theorem for Section A only."},
        headers=headers_alpha,
    )

    # Query RAG chunks for another class ID: should NOT retrieve Class A's note
    chunks_other = db.get_rag_chunks_by_course(course_id="crs-alpha-math", class_id="cls-unrelated-class")
    assert not any("Special theorem for Section A only." in (ch.clean_text or ch.text) for ch in chunks_other)

    # Query without class_id: class-scoped note must NOT be visible
    chunks_general = db.get_rag_chunks_by_course(course_id="crs-alpha-math")
    assert not any("Special theorem for Section A only." in (ch.clean_text or ch.text) for ch in chunks_general)

    # Teacher Beta tries to upload note to Class A (in Org Alpha) -> 403 Forbidden
    res_forbidden = client.post(
        f"/api/v1/teachers/classes/{class_a_id}/notes",
        json={"title": "Hacked Note", "content": "Cross-org note."},
        headers=headers_beta,
    )
    assert res_forbidden.status_code == 403
    assert "belongs to another organization" in res_forbidden.json()["detail"]


def test_teacher_upload_remedial_content_and_verify_rag_scoping(managed_env):
    """7. Verify remedial content upload scopes strictly to target student IDs."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    db: PlatformDatabase = managed_env["db"]

    # Enroll std-alpha-01
    db.create_enrollment(
        Enrollment(
            id="enr-target-01",
            student_id="std-alpha-01",
            course_id="crs-alpha-math",
            is_active=True,
        )
    )

    # Upload remedial content targeting std-alpha-01
    payload = {
        "course_id": "crs-alpha-math",
        "target_student_ids": ["std-alpha-01"],
        "title": "Remedial Guide: L'Hopital's Rule",
        "content": "When evaluating indeterminate forms 0/0, take derivatives of numerator and denominator.",
    }
    res = client.post("/api/v1/teachers/remedial-content", json=payload, headers=headers_alpha)
    assert res.status_code == 201
    data = res.json()["data"]
    assert "std-alpha-01" in data["target_student_ids"]
    assert data["chunks_created"] >= 1

    # Verify RAG chunk retrieved for std-alpha-01
    chunks = db.get_rag_chunks_by_course(course_id="crs-alpha-math", student_id="std-alpha-01")
    assert any("L'Hopital's Rule" in (ch.clean_text or ch.text) or "indeterminate forms" in (ch.clean_text or ch.text) for ch in chunks)


def test_cross_student_remedial_content_isolation_denied(managed_env):
    """8. Verify remedial content targeted to student 1 is isolated from student 2."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    headers_beta = managed_env["headers_tchr_beta"]
    db: PlatformDatabase = managed_env["db"]

    # Enroll both std-alpha-01 and std-alpha-02
    db.create_enrollment(
        Enrollment(
            id="enr-std1",
            student_id="std-alpha-01",
            course_id="crs-alpha-math",
            is_active=True,
        )
    )
    db.create_enrollment(
        Enrollment(
            id="enr-std2",
            student_id="std-alpha-02",
            course_id="crs-alpha-math",
            is_active=True,
        )
    )

    # Upload remedial targeting std-alpha-01 only
    client.post(
        "/api/v1/teachers/remedial-content",
        json={
            "course_id": "crs-alpha-math",
            "target_student_ids": ["std-alpha-01"],
            "title": "Private Remedial Tip",
            "content": "Secret mnemonic for Alice only.",
        },
        headers=headers_alpha,
    )

    # Query RAG chunks for std-alpha-02: must NOT contain the secret mnemonic
    chunks_std2 = db.get_rag_chunks_by_course(course_id="crs-alpha-math", student_id="std-alpha-02")
    assert not any("Secret mnemonic for Alice only." in (ch.clean_text or ch.text) for ch in chunks_std2)

    # Teacher Beta cannot upload remedial to crs-alpha-math
    res_beta = client.post(
        "/api/v1/teachers/remedial-content",
        json={
            "course_id": "crs-alpha-math",
            "target_student_ids": ["std-beta-01"],
            "title": "Unauthorized Remedial",
            "content": "Some text",
        },
        headers=headers_beta,
    )
    assert res_beta.status_code == 403


def test_teacher_compose_scoped_instructions_hierarchy(managed_env):
    """9. Verify hierarchical instructions composition (COURSE, CLASS, STUDENT) and policy checks."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    headers_std = managed_env["headers_std_alpha_1"]
    db: PlatformDatabase = managed_env["db"]

    # Create class
    cg_res = client.post(
        "/api/v1/teachers/classes",
        json={"course_id": "crs-alpha-math", "name": "Calculus Honors", "section": "H"},
        headers=headers_alpha,
    )
    class_id = cg_res.json()["data"]["id"]

    # 1. COURSE scope
    res_c = client.post(
        "/api/v1/teachers/instructions",
        json={
            "course_id": "crs-alpha-math",
            "instruction": "Always emphasize fundamental definitions first.",
            "scope_type": "COURSE",
            "priority": 3,
        },
        headers=headers_alpha,
    )
    assert res_c.status_code == 201
    assert res_c.json()["data"]["scope_type"] == "COURSE"

    # 2. CLASS scope
    res_cls = client.post(
        "/api/v1/teachers/instructions",
        json={
            "course_id": "crs-alpha-math",
            "class_id": class_id,
            "instruction": "Review epsilon-delta proofs in honors section.",
            "scope_type": "CLASS",
            "priority": 4,
        },
        headers=headers_alpha,
    )
    assert res_cls.status_code == 201
    assert res_cls.json()["data"]["class_id"] == class_id

    # 3. STUDENT scope
    res_stu = client.post(
        "/api/v1/teachers/instructions",
        json={
            "course_id": "crs-alpha-math",
            "student_id": "std-alpha-01",
            "instruction": "Provide additional geometry diagrams for limits.",
            "scope_type": "STUDENT",
            "priority": 5,
        },
        headers=headers_alpha,
    )
    assert res_stu.status_code == 201
    assert res_stu.json()["data"]["student_id"] == "std-alpha-01"

    # 4. Invariant violation: give direct answer to test
    res_viol = client.post(
        "/api/v1/teachers/instructions",
        json={
            "course_id": "crs-alpha-math",
            "instruction": "Just give the direct answers immediately.",
            "scope_type": "COURSE",
            "priority": 5,
        },
        headers=headers_alpha,
    )
    assert res_viol.status_code == 422
    assert "Policy violation" in res_viol.json()["detail"]

    # 5. Student cannot create instruction
    res_std = client.post(
        "/api/v1/teachers/instructions",
        json={
            "course_id": "crs-alpha-math",
            "instruction": "Make test questions easier.",
        },
        headers=headers_std,
    )
    assert res_std.status_code == 403


def test_teacher_create_and_list_real_assignments(managed_env):
    """10. Verify real assignment creation, class scoping, and honest empty list queries."""
    client = managed_env["client"]
    headers_alpha = managed_env["headers_tchr_alpha"]
    headers_beta = managed_env["headers_tchr_beta"]

    # Create class
    cg_res = client.post(
        "/api/v1/teachers/classes",
        json={"course_id": "crs-alpha-math", "name": "Calculus PS1", "section": "A1"},
        headers=headers_alpha,
    )
    class_id = cg_res.json()["data"]["id"]

    # Create real assignment
    asg_payload = {
        "course_id": "crs-alpha-math",
        "title": "Problem Set 1: Derivatives",
        "class_group_id": class_id,
        "due_date": "2026-10-15",
        "instructions": "Complete problems 1 through 10 in Section 2.1.",
    }
    res_asg = client.post("/api/v1/teachers/assignments", json=asg_payload, headers=headers_alpha)
    assert res_asg.status_code == 201
    asg_data = res_asg.json()["data"]
    assert asg_data["title"] == "Problem Set 1: Derivatives"
    assert asg_data["class_group_id"] == class_id

    # List assignments for this class group: must return the created assignment
    res_list = client.get(
        f"/api/v1/teachers/assignments?course_id=crs-alpha-math&class_group_id={class_id}",
        headers=headers_alpha,
    )
    assert res_list.status_code == 200
    items = res_list.json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "Problem Set 1: Derivatives"

    # List assignments for an empty class group: must return empty list []
    res_empty = client.get(
        "/api/v1/teachers/assignments?course_id=crs-alpha-math&class_group_id=cls-nonexistent",
        headers=headers_alpha,
    )
    assert res_empty.status_code == 200
    assert res_empty.json()["data"] == []

    # Teacher Beta cannot create assignment in Alpha's class
    res_bad = client.post(
        "/api/v1/teachers/assignments",
        json={
            "course_id": "crs-alpha-math",
            "title": "Beta Assignment",
            "class_group_id": class_id,
        },
        headers=headers_beta,
    )
    assert res_bad.status_code == 403


def test_teacher_portal_controller_real_workflows(managed_env):
    """11. Verify TeacherPortalController workflows, data isolation, and durability."""
    db: PlatformDatabase = managed_env["db"]
    ctrl = TeacherPortalController(db=db)

    # 1. Courses
    courses = ctrl.get_courses(teacher_id="tchr-alpha-01")
    c_ids = [c["id"] for c in courses]
    assert "crs-alpha-math" in c_ids
    assert "crs-beta-chem" not in c_ids

    # 2. Create class
    cg = ctrl.create_class(
        course_id="crs-alpha-math",
        name="Controller Class",
        section="K",
        teacher_id="tchr-alpha-01",
    )
    assert cg["name"] == "Controller Class"
    class_id = cg["id"]

    # 3. Class note
    note = ctrl.upload_class_note(
        class_id=class_id,
        title="Controller Note",
        content="Controller note content.",
        teacher_id="tchr-alpha-01",
    )
    assert note["status"] == "PUBLISHED"
    assert note["chunks_created"] >= 1

    # 4. Enroll student and verify get_class_students
    cohorts = db.get_cohorts_for_class_group(class_id)
    db.create_enrollment(
        Enrollment(
            id="enr-ctrl-1",
            student_id="std-alpha-01",
            course_id="crs-alpha-math",
            cohort_id=cohorts[0].id,
            is_active=True,
        )
    )
    roster = ctrl.get_class_students(class_id)
    assert len(roster) == 1
    assert roster[0]["student_id"] == "std-alpha-01"

    # 5. Cross-org violation via controller raises PermissionError
    with pytest.raises(PermissionError):
        ctrl.upload_class_note(
            class_id=class_id,
            title="Intruder Note",
            content="Cross-org attempt",
            teacher_id="tchr-beta-01",
        )


def test_desktop_bridge_teacher_slots_durability(managed_env, monkeypatch):
    """12. Verify DesktopBridgeFacade slots for teacher workflows return valid JSON and error handling."""
    db: PlatformDatabase = managed_env["db"]
    ctrl = TeacherPortalController(db=db)

    # Pre-create class
    cg = ctrl.create_class(
        course_id="crs-alpha-math",
        name="Bridge Class",
        section="B1",
        teacher_id="tchr-alpha-01",
    )
    class_id = cg["id"]

    facade = Bridge()
    # Direct DB reference in controller
    monkeypatch.setattr(
        "app.portals.teacher.controller.PlatformDatabase",
        lambda *args, **kwargs: db,
    )

    # 1. get_teacher_classes
    res_classes_raw = facade.get_teacher_classes(course_id="crs-alpha-math", teacher_id="tchr-alpha-01")
    res_classes = json.loads(res_classes_raw)
    assert res_classes["ok"] is True
    assert any(c["id"] == class_id for c in res_classes["classes"])

    # 2. get_class_students
    res_stu_raw = facade.get_class_students(class_id=class_id)
    res_stu = json.loads(res_stu_raw)
    assert res_stu["ok"] is True
    assert isinstance(res_stu["students"], list)

    # 3. upload_class_note
    res_note_raw = facade.upload_class_note(
        class_id=class_id,
        title="Bridge Class Note",
        content="Testing bridge slot note upload.",
        teacher_id="tchr-alpha-01",
    )
    res_note = json.loads(res_note_raw)
    assert res_note["ok"] is True
    assert res_note["data"]["status"] == "PUBLISHED"

    # 4. create_assignment
    res_asg_raw = facade.create_assignment(
        course_id="crs-alpha-math",
        title="Bridge Assignment",
        class_group_id=class_id,
        due_date="2026-11-01",
        instructions="Complete via bridge.",
        teacher_id="tchr-alpha-01",
    )
    res_asg = json.loads(res_asg_raw)
    assert res_asg["ok"] is True
    assert res_asg["assignment"]["title"] == "Bridge Assignment"

    # 5. Invalid input error handling
    res_err_raw = facade.upload_class_note(
        class_id="cls-non-existent-1234",
        title="Fail",
        content="Fail",
        teacher_id="tchr-alpha-01",
    )
    res_err = json.loads(res_err_raw)
    assert res_err["ok"] is False
    assert "error" in res_err
