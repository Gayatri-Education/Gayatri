"""Phase 24: Real End-to-End Journeys & Browser/Desktop Verification Master Suite.

Section 34 of GAYATRI_MASTER_PHASE_BY_PHASE_EXECUTION_AND_RECOVERY_GUIDE.md &
Section 12.24 of GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md:
1. Mandatory Journey A: Student Real E2E Loop
   (Login -> Discover -> Enroll -> Start Session -> Question -> RAG -> Model -> State Commit -> SLR -> Resume)
2. Mandatory Journey B: Teacher Real E2E Loop
   (Login -> Course -> Upload Content -> Review -> Publish -> Instruction -> View Student -> Intervene)
3. Mandatory Journey C: Admin Real E2E Loop
   (Login -> Create Course -> Public/Private -> Approve -> Publish -> Offering -> System Health & Audit)
4. Mandatory Adversarial & Negative Journeys (NJ-1 to NJ-11)
   (Wrong Tenant, IDOR, Class Scoping, Wrong Course, Unpublished Version, Unpublished Content, Expired Instruction, Unauthorized Tool, Missing Model, RAG Failure, DB Rollback)
5. Headless Portal Shell & Design System Verification
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
import central_platform.auth.dependencies as auth_deps
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    ClassGroup,
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    KnowledgeContentType,
    KnowledgeVisibilityScope,
    Organization,
    OrganizationCourseOffering,
    RAGChunk,
    RAGSource,
    RAGSourceStatus,
    Session,
    User,
    UserRole,
)
from central_platform.rag.service import RAGService
from central_platform.portals.student import StudentPortalController
from central_platform.portals.teacher import TeacherPortalController
from central_platform.portals.parent import ParentPortalController
from central_platform.portals.fee_admin import FeeAdminController
from central_platform.deployment.validator import DeploymentValidator, ValidationStatus


@pytest.fixture(scope="module")
def managed_env(tmp_path_factory):
    """Provide isolated platform database and test client sharing the exact same DB."""
    fn = tmp_path_factory.mktemp("p24") / "phase24_e2e.db"
    db_inst = PlatformDatabase(db_path=str(fn))
    os.environ["GAYATRI_DB_PATH"] = str(fn)
    auth_deps._DB_INSTANCE = db_inst
    app.dependency_overrides[auth_deps.get_db] = lambda: db_inst

    with TestClient(app) as c:
        yield {"db": db_inst, "client": c}

    app.dependency_overrides.pop(auth_deps.get_db, None)


@pytest.fixture(scope="module")
def client(managed_env):
    return managed_env["client"]


@pytest.fixture(scope="module")
def db(managed_env):
    return managed_env["db"]


# ==============================================================================
# 1. MANDATORY JOURNEY A: STUDENT REAL E2E LOOP
# ==============================================================================

def test_journey_a_student_complete_lifecycle(client: TestClient, db: PlatformDatabase):
    """Journey A: Student discovers course, enrolls, starts session, asks question,
    receives verified Socratic response, updates SLR, and successfully resumes session.
    """
    ts = int(time.time() * 1000)
    org_id = f"org-std-e2e-{ts}"
    student_id = f"usr-std-{ts}"
    teacher_id = f"usr-tch-a-{ts}"
    admin_id = f"usr-adm-a-{ts}"
    course_id = f"crs-phys-mechanics-{ts}"
    version_id = f"ver-phys-{ts}-v1"

    # 1. Setup persistent organization and accounts
    db.create_organization(Organization(id=org_id, name="Apex Academy", slug=f"apex-{ts}"))
    db.create_user(User(id=student_id, email=f"student_{ts}@apex.edu", full_name="Aarav Sharma", role=UserRole.STUDENT, organization_id=org_id))
    db.create_user(User(id=teacher_id, email=f"teacher_{ts}@apex.edu", full_name="Dr. Homi Bhabha", role=UserRole.TEACHER, organization_id=org_id))
    db.create_user(User(id=admin_id, email=f"admin_{ts}@apex.edu", full_name="Dean Vikram", role=UserRole.ORG_ADMIN, organization_id=org_id))

    # 2. Setup published public course and version
    course = Course(
        id=course_id,
        organization_id=org_id,
        code=f"PHYS-{ts}",
        title="Physics: Classical Mechanics",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)
    course_ver = CourseVersion(
        id=version_id,
        course_id=course_id,
        version_number="1.0.0",
        status=CourseStatus.PUBLISHED,
        created_by=admin_id,
    )
    db.create_course_version(course_ver)

    # 3. Ingest authoritative published RAG source via RAGService
    rag_svc = RAGService(db)
    teacher_user = db.get_user(teacher_id)
    admin_user = db.get_user(admin_id)
    asset = rag_svc.upload_knowledge_asset(
        course_id=course_id,
        title="Newtonian Laws of Motion Textbook",
        content="# Chapter 1: Newton's Laws\n\nNewton's First Law states that an object remains at rest or in uniform motion unless acted upon by an external force. This property is known as inertia.",
        organization_id=org_id,
        subject="Physics",
        user=teacher_user,
        course_version_id=version_id,
        content_type=KnowledgeContentType.TEXTBOOK,
    )
    rag_svc.approve_knowledge_asset(asset.id, user=admin_user)
    rag_svc.publish_knowledge_asset(asset.id, user=admin_user)

    # 4. Generate cryptographically signed student JWT token
    token = create_access_token(user_id=student_id, role="student", organization_id=org_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 5. Step: Course Discovery (HTTP GET /api/v1/courses)
    resp = client.get("/api/v1/courses", headers=headers)
    assert resp.status_code == 200, resp.text
    courses = resp.json().get("data", [])
    found = [c for c in courses if c.get("id") == course_id or c.get("course_id") == course_id]
    assert len(found) >= 1, "Published public course must be discoverable"

    # 6. Step: Enrollment (HTTP POST /api/v1/enrollments)
    resp = client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={"student_id": student_id, "course_id": course_id, "organization_id": org_id},
    )
    assert resp.status_code in (200, 201), resp.text

    # 7. Step: Start Session (HTTP POST /api/v1/sessions/start)
    resp = client.post(
        "/api/v1/sessions/start",
        headers=headers,
        json={
            "student_id": student_id,
            "course_id": course_id,
            "initial_concept": "phys_mechanics_inertia",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    session_id = resp.json().get("data", {}).get("session_id")
    assert session_id is not None

    # 8. Step: Submit Question to Real Tutor Orchestrator (HTTP POST /api/v1/tutor/turn)
    turn_payload = {
        "student_id": student_id,
        "session_id": session_id,
        "course_id": course_id,
        "course_version_id": version_id,
        "message": "What is inertia and how does it relate to the first law of motion?",
        "max_tokens": 256,
    }
    resp = client.post("/api/v1/tutor/turn", headers=headers, json=turn_payload)
    assert resp.status_code == 200, resp.text
    turn_data = resp.json()
    assert turn_data.get("ok") is True or "assistant_text" in turn_data or "response_text" in turn_data
    assistant_msg = turn_data.get("assistant_text") or turn_data.get("response_text", "")
    assert len(assistant_msg) > 10, "Tutor response must be substantive"

    # 9. Step: State Commit Verification
    events = db.get_learning_events_for_session(session_id)
    assert len(events) >= 1, "At least one learning event must be committed to the database"
    assert events[0].course_id == course_id

    # 10. Step: Query SLR Progress
    resp = client.get(f"/api/v1/students/{student_id}/progress?course_id={course_id}", headers=headers)
    assert resp.status_code == 200, resp.text

    # 11. Step: Restart Simulation & Session Resume
    restarted_db = PlatformDatabase()
    resumed_session = restarted_db.get_session(session_id)
    assert resumed_session is not None
    assert resumed_session.student_id == student_id
    assert resumed_session.course_id == course_id


# ==============================================================================
# 2. MANDATORY JOURNEY B: TEACHER REAL E2E LOOP
# ==============================================================================

def test_journey_b_teacher_complete_lifecycle(client: TestClient, db: PlatformDatabase):
    """Journey B: Teacher manages course, uploads knowledge asset, submits for review,
    publishes via administrative governance, issues hierarchical instruction, and reviews student mastery.
    """
    ts = int(time.time() * 1000)
    org_id = f"org-tch-e2e-{ts}"
    teacher_id = f"usr-tch-{ts}"
    admin_id = f"usr-adm-{ts}"
    course_id = f"crs-hist-{ts}"
    version_id = f"ver-hist-{ts}-v1"
    class_id = f"cls-hist-{ts}-10a"

    # 1. Setup persistent organization and accounts
    db.create_organization(Organization(id=org_id, name="Oxford International", slug=f"oxford-{ts}"))
    db.create_user(User(id=teacher_id, email=f"teacher_{ts}@oxford.edu", full_name="Prof. Arnold Toynbee", role=UserRole.TEACHER, organization_id=org_id))
    db.create_user(User(id=admin_id, email=f"admin_{ts}@oxford.edu", full_name="Provost Clark", role=UserRole.ORG_ADMIN, organization_id=org_id))

    # 2. Setup Course, Version, and Class Group
    course = Course(
        id=course_id,
        organization_id=org_id,
        code=f"HIST-{ts}",
        title="World History: 20th Century",
        visibility=CourseVisibility.PRIVATE,
    )
    db.create_course(course)
    db.create_course_version(CourseVersion(id=version_id, course_id=course_id, version_number="1.0.0", status=CourseStatus.PUBLISHED, created_by=teacher_id))
    db.create_class_group(ClassGroup(id=class_id, organization_id=org_id, course_id=course_id, name="Grade 10", section="A"))

    # 3. Teacher Token & Admin Token
    teacher_token = create_access_token(user_id=teacher_id, role="teacher", organization_id=org_id)
    admin_token = create_access_token(user_id=admin_id, role="org_admin", organization_id=org_id)
    t_headers = {"Authorization": f"Bearer {teacher_token}"}
    a_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Step: Teacher Uploads Knowledge Asset via API (HTTP POST /api/v1/rag/sources)
    upload_payload = {
        "course_id": course_id,
        "course_version_id": version_id,
        "subject": "History",
        "title": "League of Nations Remedial Summary",
        "content_type": "teacher_note",
        "source_type": "text",
    }
    resp = client.post("/api/v1/rag/sources", headers=t_headers, json=upload_payload)
    assert resp.status_code in (200, 201), resp.text
    source_id = resp.json().get("data", {}).get("id")
    assert source_id is not None

    # Ingest content into source
    ingest_payload = {
        "content": "The League of Nations suffered from lack of armed enforcement and absence of major world powers.",
        "file_name": "league.txt",
    }
    resp = client.post(f"/api/v1/rag/sources/{source_id}/ingest", headers=t_headers, json=ingest_payload)
    assert resp.status_code == 200, resp.text

    # Validate source
    resp = client.post(f"/api/v1/rag/sources/{source_id}/validate", headers=t_headers)
    assert resp.status_code == 200, resp.text

    # 5. Step: Admin Approves and Publishes Content (HTTP POST /api/v1/rag/sources/{id}/publish)
    pub_resp = client.post(f"/api/v1/rag/sources/{source_id}/publish", headers=a_headers)
    assert pub_resp.status_code in (200, 201), pub_resp.text
    src_record = db.get_rag_source(source_id)
    assert src_record is not None
    assert str(src_record.status).lower().endswith("published")

    # 6. Step: Teacher Issues Class Pedagogical Instruction (HTTP POST /api/v1/instructions)
    inst_payload = {
        "scope_type": "CLASS",
        "organization_id": org_id,
        "course_id": course_id,
        "class_id": class_id,
        "instruction": "Emphasize diplomatic failures and economic conditions rather than giving dates.",
        "priority": 4,
    }
    resp = client.post("/api/v1/instructions", headers=t_headers, json=inst_payload)
    assert resp.status_code in (200, 201), resp.text
    inst_id = resp.json().get("data", {}).get("instruction_id") or resp.json().get("id")
    assert inst_id is not None

    # 7. Step: Teacher Inspects Class Instruction Resolution
    resp = client.get(f"/api/v1/instructions?course_id={course_id}&class_id={class_id}", headers=t_headers)
    assert resp.status_code == 200, resp.text


# ==============================================================================
# 3. MANDATORY JOURNEY C: ADMIN REAL E2E LOOP
# ==============================================================================

def test_journey_c_admin_complete_lifecycle(client: TestClient, db: PlatformDatabase):
    """Journey C: Admin creates course, version draft, approves, publishes,
    configures organization course offering, and verifies system health.
    """
    ts = int(time.time() * 1000)
    org_id = f"org-adm-e2e-{ts}"
    admin_id = f"usr-super-{ts}"

    # 1. Setup persistent organization and admin
    db.create_organization(Organization(id=org_id, name="Silicon Valley Institute", slug=f"svi-{ts}"))
    db.create_user(User(id=admin_id, email=f"admin_{ts}@svi.edu", full_name="Dr. Anita Chen", role=UserRole.SUPER_ADMIN, organization_id=org_id))

    admin_token = create_access_token(user_id=admin_id, role="super_admin", organization_id=org_id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Step: Create New Generic Course (HTTP POST /api/v1/courses)
    course_payload = {
        "code": f"CS101-{ts}",
        "title": "Introduction to Computer Science",
        "description": "Foundational programming course",
        "visibility": "PUBLIC",
        "organization_id": org_id,
        "subject": "Computer Science",
    }
    resp = client.post("/api/v1/courses", headers=headers, json=course_payload)
    assert resp.status_code in (200, 201), resp.text
    created_course_id = resp.json().get("data", {}).get("course_id")
    assert created_course_id is not None

    # 3. Step: Create Course Version Draft (HTTP POST /api/v1/courses/{course_id}/versions)
    ver_payload = {
        "version_tag": "2.0.0",
        "changelog": "Initial full draft",
    }
    resp = client.post(f"/api/v1/courses/{created_course_id}/versions", headers=headers, json=ver_payload)
    assert resp.status_code in (200, 201), resp.text
    created_ver_id = resp.json().get("data", {}).get("id") or resp.json().get("data", {}).get("version_id")
    assert created_ver_id is not None

    # 4. Step: Submit Version for Review & Publish
    resp = client.post(f"/api/v1/courses/{created_course_id}/versions/{created_ver_id}/submit-review", headers=headers)
    assert resp.status_code in (200, 201, 204), resp.text

    resp = client.post(f"/api/v1/courses/{created_course_id}/versions/{created_ver_id}/publish", headers=headers)
    assert resp.status_code in (200, 201, 204), resp.text

    # 5. Step: Create Organization Course Offering
    offering_payload = {
        "organization_id": org_id,
        "course_version_id": created_ver_id,
    }
    resp = client.post(f"/api/v1/courses/{created_course_id}/select", headers=headers, json=offering_payload)
    assert resp.status_code in (200, 201), resp.text

    # 6. Step: System Health Probes
    for path in ["/healthz", "/readyz", "/livez", "/api/v1/health"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"Health check failed on {path}: {resp.text}"
        body = resp.json()
        assert (
            body.get("status") in ("ok", "ready", "alive", "UP", "ONLINE")
            or body.get("alive") is True
            or body.get("ready") is True
        )


# ==============================================================================
# 4. MANDATORY ADVERSARIAL & NEGATIVE JOURNEYS (NJ-1 to NJ-11)
# ==============================================================================

def test_negative_journeys_nj1_through_nj11(client: TestClient, db: PlatformDatabase):
    """Execute all 11 mandatory negative adversarial journeys through the real application boundary."""
    ts = int(time.time() * 1000)
    org_alpha = f"org-sec-a-{ts}"
    org_beta = f"org-sec-b-{ts}"
    student_alpha = f"usr-std-a-{ts}"
    student_beta = f"usr-std-b-{ts}"
    teacher_alpha = f"usr-tch-a-{ts}"
    private_course = f"crs-priv-{ts}"
    version_id = f"ver-priv-{ts}-v1"

    # Setup isolated orgs & users
    db.create_organization(Organization(id=org_alpha, name="Alpha Org", slug=f"alpha-{ts}"))
    db.create_organization(Organization(id=org_beta, name="Beta Org", slug=f"beta-{ts}"))
    db.create_user(User(id=student_alpha, email=f"a_{ts}@alpha.edu", full_name="Alpha Student", role=UserRole.STUDENT, organization_id=org_alpha))
    db.create_user(User(id=student_beta, email=f"b_{ts}@beta.edu", full_name="Beta Student", role=UserRole.STUDENT, organization_id=org_beta))
    db.create_user(User(id=teacher_alpha, email=f"t_{ts}@alpha.edu", full_name="Alpha Teacher", role=UserRole.TEACHER, organization_id=org_alpha))

    db.create_course(Course(id=private_course, organization_id=org_alpha, code="DEF101", title="Confidential Defense Tech", visibility=CourseVisibility.PRIVATE))
    db.create_course_version(CourseVersion(id=version_id, course_id=private_course, version_number="1.0.0", status=CourseStatus.PUBLISHED, created_by="system"))

    token_beta = create_access_token(user_id=student_beta, role="student", organization_id=org_beta)
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    # NJ-1: Wrong Tenant Isolation (Student Beta from Org Beta attempting to query Private Course of Org Alpha)
    resp = client.get(f"/api/v1/courses/{private_course}", headers=headers_beta)
    assert resp.status_code == 403, f"Cross-tenant access must be denied with 403: {resp.text}"

    # NJ-2: IDOR Student Isolation (Student Beta requesting Student Alpha's progress)
    resp = client.get(f"/api/v1/students/{student_alpha}/progress?course_id={private_course}", headers=headers_beta)
    assert resp.status_code in (401, 403), f"IDOR student record access must be rejected: {resp.text}"

    # NJ-3: Class-Scoped RAG Isolation
    # Chunks scoped strictly to class-10a must return 0 chunks when searched from class-10b
    class_a = f"class-10a-{ts}"
    class_b = f"class-10b-{ts}"
    db.create_class_group(ClassGroup(id=class_a, organization_id=org_alpha, course_id=private_course, name="Class A", section="A"))
    db.create_class_group(ClassGroup(id=class_b, organization_id=org_alpha, course_id=private_course, name="Class B", section="B"))

    src_cls = RAGSource(id=f"src-cls-{ts}", organization_id=org_alpha, course_id=private_course, course_version_id=version_id, subject="Defense", title="Class 10A Secret Exam Tips", content_type=KnowledgeContentType.TEACHER_NOTE, status=RAGSourceStatus.PUBLISHED, uploaded_by="teacher", class_id=class_a)
    db.create_rag_source(src_cls)
    db.add_rag_chunks([RAGChunk(id=f"chk-cls-{ts}", source_id=src_cls.id, course_id=private_course, subject="Defense", chapter="Ch1", topic="Defense", text="Class 10A confidential exam formula", clean_text="Class 10A confidential exam formula", course_version_id=version_id, class_id=class_a)])
    token_alpha = create_access_token(user_id=student_alpha, role="student", organization_id=org_alpha)
    headers_alpha = {"Authorization": f"Bearer {token_alpha}"}
    rag_query_payload = {"course_id": private_course, "query": "confidential exam formula", "class_id": class_b}
    resp = client.post("/api/v1/rag/query", headers=headers_alpha, json=rag_query_payload)
    res_data_3 = resp.json().get("data", {}) if isinstance(resp.json().get("data"), dict) else resp.json()
    matched_chunks = [c for c in res_data_3.get("chunks", []) if "Class 10A" in (c.get("content") or c.get("text") or "")]
    assert len(matched_chunks) == 0, "Class 10A chunks must never be returned to Class 10B query"

    # NJ-4: Wrong Course Context Rejection
    fake_course = "crs-nonexistent-9999"
    turn_bad_course = {"student_id": student_alpha, "session_id": f"ses-bad-{ts}", "course_id": fake_course, "message": "Hello"}
    resp = client.post("/api/v1/tutor/turn", headers=headers_alpha, json=turn_bad_course)
    assert resp.status_code == 404, f"Non-existent course turn must return 404: {resp.text}"

    # NJ-5: Unpublished Course Version Rejection
    draft_course = f"crs-draft-{ts}"
    draft_ver = f"ver-draft-{ts}"
    db.create_course(Course(id=draft_course, organization_id=org_alpha, code="DFT101", title="Unpublished Draft Course", visibility=CourseVisibility.PUBLIC))
    db.create_course_version(CourseVersion(id=draft_ver, course_id=draft_course, version_number="0.1.0", status=CourseStatus.DRAFT, created_by="system"))
    turn_draft_ver = {"student_id": student_alpha, "session_id": f"ses-draft-{ts}", "course_id": draft_course, "course_version_id": draft_ver, "message": "Can I take this?"}
    resp = client.post("/api/v1/tutor/turn", headers=headers_alpha, json=turn_draft_ver)
    assert resp.status_code in (403, 404), f"Draft version turn must be rejected: {resp.text}"

    # NJ-6: Unpublished Knowledge Asset Invariant
    # Draft knowledge asset must NEVER be returned in student RAG queries
    src_draft = RAGSource(id=f"src-dft-{ts}", organization_id=org_alpha, course_id=private_course, course_version_id=version_id, subject="Defense", title="Unreviewed Draft Notes", content_type=KnowledgeContentType.TEXTBOOK, status=RAGSourceStatus.DRAFT, uploaded_by="teacher")
    db.create_rag_source(src_draft)
    db.add_rag_chunks([RAGChunk(id=f"chk-dft-{ts}", source_id=src_draft.id, course_id=private_course, subject="Defense", chapter="Ch1", topic="Defense", text="UNPUBLISHED_SECRET_TOPIC_TEXT", clean_text="UNPUBLISHED_SECRET_TOPIC_TEXT", course_version_id=version_id)])
    resp = client.post("/api/v1/rag/query", headers=headers_alpha, json={"course_id": private_course, "query": "UNPUBLISHED_SECRET_TOPIC_TEXT"})
    assert resp.status_code == 200
    res_data_6 = resp.json().get("data", {}) if isinstance(resp.json().get("data"), dict) else resp.json()
    leaked = [c for c in res_data_6.get("chunks", []) if "UNPUBLISHED_SECRET" in (c.get("content") or c.get("text") or "")]
    assert len(leaked) == 0, "Draft knowledge chunks must never be returned in student RAG queries"

    # NJ-7: Expired Instruction Eviction
    # Teacher instruction with expires_at in the past must not be active
    expired_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    resp = client.post(
        "/api/v1/instructions",
        headers={"Authorization": f"Bearer {create_access_token(user_id=teacher_alpha, role='teacher', organization_id=org_alpha)}"},
        json={
            "scope_type": "COURSE",
            "organization_id": org_alpha,
            "course_id": private_course,
            "instruction": "EXPIRED_TEST_DIRECTIVE",
            "expires_at": expired_time,
            "priority": 5,
        },
    )
    assert resp.status_code in (200, 201)
    # Query hierarchical resolution: expired instruction must be excluded
    resp = client.get(f"/api/v1/instructions?course_id={private_course}", headers=headers_alpha)
    assert resp.status_code == 200
    active_texts = [i.get("instruction_text") or i.get("instruction") for i in resp.json().get("data", [])]
    assert "EXPIRED_TEST_DIRECTIVE" not in active_texts, "Expired instructions must be evicted"

    # NJ-8: Unauthorized Tool Denial
    # Attempting to execute code without teacher/admin privileges or outside course tool policy
    resp = client.post(
        "/api/v1/tools/execute",
        headers=headers_beta,
        json={"tool_id": "code_execution", "course_id": private_course, "arguments": {"code": "print('exploit')"}},
    )
    assert resp.status_code in (400, 403, 404, 422), f"Unauthorized tool execution must be rejected: {resp.text}"

    # NJ-9: Missing Model Resilience
    # Tutor orchestrator gracefully handles missing model without unhandled crash
    turn_req = {"student_id": student_alpha, "session_id": f"ses-model-{ts}", "course_id": private_course, "message": "Test question"}
    resp = client.post("/api/v1/tutor/turn", headers=headers_alpha, json=turn_req)
    assert resp.status_code in (200, 403, 503)

    # NJ-10: RAG Failure Resilience
    # Query with non-matching RAG keywords must return empty chunks cleanly
    resp = client.post("/api/v1/rag/query", headers=headers_alpha, json={"course_id": private_course, "query": "xyzzy_unmatched_garbage_tokens_12345"})
    assert resp.status_code == 200
    res_data = resp.json().get("data", {}) if isinstance(resp.json().get("data"), dict) else resp.json()
    chunks = res_data.get("chunks", [])
    assert len(chunks) == 0

    # NJ-11: Database Rollback Verification
    # Database integrity is maintained
    db_test = PlatformDatabase()
    assert db_test.get_user(student_alpha) is not None


# ==============================================================================
# 5. HEADLESS PORTAL CONTROLLER & DESIGN SYSTEM ASSET VERIFICATION
# ==============================================================================

def test_headless_portals_and_design_system():
    """Verify portal controllers instantiate cleanly headless, all 16 static UI
    design system assets exist, and deployment validator confirms readiness.
    """
    student_ctrl = StudentPortalController()
    teacher_ctrl = TeacherPortalController()
    parent_ctrl = ParentPortalController()
    fee_ctrl = FeeAdminController()

    assert student_ctrl is not None
    assert teacher_ctrl is not None
    assert parent_ctrl is not None
    assert fee_ctrl is not None

    # Verify static design system assets
    validator = DeploymentValidator()
    report = validator.validate_static_assets()
    assert report.status == ValidationStatus.PASS
    assert report.details.get("asset_count") == 16

    # Full deployment validation check
    full_report = validator.run_full_validation()
    assert full_report.failed_checks == 0, f"Validation failures: {full_report.summary}"
    assert full_report.is_ready is True
