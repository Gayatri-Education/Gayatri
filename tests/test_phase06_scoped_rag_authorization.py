"""Phase 06: Scoped RAG & Knowledge Authorization Test Suite.

Governing Document: GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md (Section 12.6)
Plan: docs/reports/PHASE_06_PLAN.md

Verifies:
1. Course Textbook Scope: Standard course material visible to enrolled students.
2. Multi-Tenant Org Isolation: Private courses are strictly denied to students of other
   organizations unless an active CourseOffering exists (RAG_DENIED with zero leaks).
3. Partner Org Offering: Active CourseOffering grants cross-org student access.
4. Class-Scoped Isolation: Class-specific notes (CLASS scope) visible only to students of that class.
5. Student-Targeted Remedial: Remedial materials visible only to targeted students.
6. Course Version Isolation: Pinned version queries retrieve only matching version chunks.
7. CourseLearningContext Binding: Scoped learning context parameter correctly unpacks and scopes retrieval.
8. No Fallback Under Scoped Search: Empty scoped searches return RAG_EMPTY without global fallback leaks.
9. Diagnostic Transparency: Non-sensitive status codes and reasons returned without chunk leakage.
10. REST API Endpoints: Scoped creation, filtering, chunk listing, and query retrieval over /api/v1/rag.
"""
from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.dependencies import get_db
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseLearningContext,
    CourseOffering,
    CourseVersion,
    CourseVisibility,
    KnowledgeContentType,
    KnowledgeVisibilityScope,
    Organization,
    RAGSourceStatus,
    User,
    UserRole,
)
from central_platform.rag.service import RAGService
from central_platform.auth.tokens import create_access_token


@pytest.fixture
def clean_db():
    db = PlatformDatabase(db_path=":memory:")

    # Organizations
    org_alpha = Organization(id="org-alpha", name="Alpha Institute", slug="alpha-inst")
    org_beta = Organization(id="org-beta", name="Beta College", slug="beta-coll")
    db.create_organization(org_alpha)
    db.create_organization(org_beta)

    # Public and Private Courses
    crs_public = Course(
        id="crs-pub-cs101",
        organization_id="org-alpha",
        code="CS-101",
        title="Public Computer Science",
        visibility=CourseVisibility.PUBLIC,
    )
    crs_private_alpha = Course(
        id="crs-priv-ai401",
        organization_id="org-alpha",
        code="AI-401",
        title="Proprietary AI Systems",
        visibility=CourseVisibility.PRIVATE,
    )
    db.create_course(crs_public)
    db.create_course(crs_private_alpha)

    # Course Versions
    ver_ai_10 = CourseVersion(
        id="ver-ai-10",
        course_id="crs-priv-ai401",
        version_number="1.0.0",
    )
    ver_ai_20 = CourseVersion(
        id="ver-ai-20",
        course_id="crs-priv-ai401",
        version_number="2.0.0",
    )
    db.create_course_version(ver_ai_10)
    db.create_course_version(ver_ai_20)

    # Users
    admin_alpha = User(
        id="usr-admin-alpha",
        organization_id="org-alpha",
        email="admin@alpha.edu",
        full_name="Admin Alpha",
        role=UserRole.ORG_ADMIN,
    )
    teacher_alpha = User(
        id="usr-teacher-alpha",
        organization_id="org-alpha",
        email="teacher@alpha.edu",
        full_name="Teacher Alpha",
        role=UserRole.TEACHER,
    )
    student_alpha_1 = User(
        id="usr-stud-alpha-1",
        organization_id="org-alpha",
        email="stud1@alpha.edu",
        full_name="Student Alpha 1",
        role=UserRole.STUDENT,
    )
    student_alpha_2 = User(
        id="usr-stud-alpha-2",
        organization_id="org-alpha",
        email="stud2@alpha.edu",
        full_name="Student Alpha 2",
        role=UserRole.STUDENT,
    )
    student_beta = User(
        id="usr-stud-beta",
        organization_id="org-beta",
        email="stud@beta.edu",
        full_name="Student Beta",
        role=UserRole.STUDENT,
    )
    for u in [admin_alpha, teacher_alpha, student_alpha_1, student_alpha_2, student_beta]:
        db.create_user(u)

    return db


@pytest.fixture
def rag_service(clean_db):
    return RAGService(clean_db)


# ── 1. Course Scope ─────────────────────────────────────────────────────────

def test_course_textbook_visible_to_enrolled_students(clean_db, rag_service):
    """Course-scoped textbook published in a course is accessible to enrolled students."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student = clean_db.get_user("usr-stud-alpha-1")

    content = (
        "# Artificial Intelligence Core\n\n"
        "## Search Algorithms\n"
        "Breadth-first search traverses a tree level by level using a FIFO queue.\n"
        "Depth-first search traverses down a single branch before backtracking using a LIFO stack."
    )
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="AI Search Handbook",
        content=content,
        organization_id="org-alpha",
        subject="Computer Science",
        user=teacher,
        content_type=KnowledgeContentType.TEXTBOOK,
        visibility_scope=KnowledgeVisibilityScope.COURSE,
        course_version_id="ver-ai-10",
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Student query
    res = rag_service.query(
        query_text="Breadth-first search queue",
        course_id="crs-priv-ai401",
        user=student,
    )
    assert res["status"] == "RAG_OK"
    assert res["count"] >= 1
    assert "FIFO queue" in res["results"][0]["text"]
    assert res["results"][0]["course_version_id"] == "ver-ai-10"
    assert res["results"][0]["visibility_scope"] == "course"


# ── 2. Multi-Tenant Org Isolation ───────────────────────────────────────────

def test_private_course_invisible_to_other_org(clean_db, rag_service):
    """Student of org-beta cannot access private course of org-alpha without an offering."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student_beta = clean_db.get_user("usr-stud-beta")
    student_alpha = clean_db.get_user("usr-stud-alpha-1")

    content = "Proprietary Alpha Algorithm secret formula: AlphaOmega-99."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="Proprietary Formula",
        content=content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Beta student query must be DENIED
    res_beta = rag_service.query(
        query_text="Proprietary Alpha Algorithm formula",
        course_id="crs-priv-ai401",
        user=student_beta,
    )
    assert res_beta["status"] == "RAG_DENIED"
    assert res_beta["count"] == 0
    assert res_beta["results"] == []
    assert "Access denied" in res_beta["reason"]
    assert "AlphaOmega-99" not in str(res_beta)

    # Alpha student query succeeds
    res_alpha = rag_service.query(
        query_text="Proprietary Alpha Algorithm formula",
        course_id="crs-priv-ai401",
        user=student_alpha,
    )
    assert res_alpha["status"] == "RAG_OK"
    assert res_alpha["count"] >= 1


# ── 3. Partner Org Offering ─────────────────────────────────────────────────

def test_active_offering_grants_access_to_partner_org(clean_db, rag_service):
    """Creating an active CourseOffering for org-beta grants its students authorized retrieval."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student_beta = clean_db.get_user("usr-stud-beta")

    content = "Shared AI Curriculum module on heuristic evaluation functions."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="Heuristic Evaluation",
        content=content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Create offering to partner org-beta
    offering = CourseOffering(
        id="offering-beta-ai",
        organization_id="org-beta",
        course_id="crs-priv-ai401",
        pinned_version_id="ver-ai-10",
    )
    clean_db.create_course_offering(offering)

    # Beta student now succeeds
    res = rag_service.query(
        query_text="heuristic evaluation functions",
        course_id="crs-priv-ai401",
        user=student_beta,
    )
    assert res["status"] == "RAG_OK"
    assert res["count"] >= 1
    assert "heuristic evaluation" in res["results"][0]["text"].lower()


# ── 4. Class-Scoped Isolation ───────────────────────────────────────────────

def test_class_notes_visible_only_to_class(clean_db, rag_service):
    """Class notes published with visibility_scope='CLASS' are retrievable only with matching class_id."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student = clean_db.get_user("usr-stud-alpha-1")

    content = "Morning Class Notes: Midterm exam on Monday covering Chapters 1 through 4."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="Morning Class Notes",
        content=content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
        content_type=KnowledgeContentType.TEACHER_NOTE,
        visibility_scope=KnowledgeVisibilityScope.CLASS,
        class_id="cls-morning-101",
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Query with matching class_id -> Retrieves notes
    res_morning = rag_service.query(
        query_text="Midterm exam Monday",
        course_id="crs-priv-ai401",
        user=student,
        class_id="cls-morning-101",
    )
    assert res_morning["status"] == "RAG_OK"
    assert res_morning["count"] >= 1
    assert "Midterm exam on Monday" in res_morning["results"][0]["text"]
    assert res_morning["results"][0]["class_id"] == "cls-morning-101"

    # Query with different class_id -> RAG_EMPTY
    res_evening = rag_service.query(
        query_text="Midterm exam Monday",
        course_id="crs-priv-ai401",
        user=student,
        class_id="cls-evening-202",
    )
    assert res_evening["status"] == "RAG_EMPTY"
    assert res_evening["count"] == 0

    # Query with no class_id -> RAG_EMPTY
    res_none = rag_service.query(
        query_text="Midterm exam Monday",
        course_id="crs-priv-ai401",
        user=student,
    )
    assert res_none["status"] == "RAG_EMPTY"
    assert res_none["count"] == 0


# ── 5. Student-Targeted Remedial Material ───────────────────────────────────

def test_student_targeted_remedial_material_visible_only_to_target(clean_db, rag_service):
    """Remedial material tagged for student 1 is invisible to student 2."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student_1 = clean_db.get_user("usr-stud-alpha-1")
    student_2 = clean_db.get_user("usr-stud-alpha-2")

    content = "Remedial Guide: Step-by-step calculus differentiation rules for struggling students."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="Targeted Calculus Remediation",
        content=content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
        content_type=KnowledgeContentType.REMEDIAL,
        visibility_scope=KnowledgeVisibilityScope.STUDENT_TARGETED,
        target_student_ids=["usr-stud-alpha-1"],
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Student 1 (Targeted) -> Retrieves remedial chunk
    res_s1 = rag_service.query(
        query_text="differentiation rules calculus",
        course_id="crs-priv-ai401",
        user=student_1,
    )
    assert res_s1["status"] == "RAG_OK"
    assert res_s1["count"] >= 1
    assert "differentiation rules" in res_s1["results"][0]["text"]

    # Student 2 (Not targeted) -> RAG_EMPTY
    res_s2 = rag_service.query(
        query_text="differentiation rules calculus",
        course_id="crs-priv-ai401",
        user=student_2,
    )
    assert res_s2["status"] == "RAG_EMPTY"
    assert res_s2["count"] == 0


# ── 6. Course Version Isolation ─────────────────────────────────────────────

def test_version_isolation(clean_db, rag_service):
    """Pinned version 1.0 never retrieves version 2.0 chunks and vice versa."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")
    student = clean_db.get_user("usr-stud-alpha-1")

    v1_content = "Syllabus 1.0: We focus on classical perceptrons and support vector machines."
    v2_content = "Syllabus 2.0: We focus on multi-head attention and transformer architectures."

    asset_v1 = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="AI Syllabus V1",
        content=v1_content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
        course_version_id="ver-ai-10",
    )
    asset_v2 = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="AI Syllabus V2",
        content=v2_content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
        course_version_id="ver-ai-20",
    )
    rag_service.approve_knowledge_asset(asset_v1.id, user=admin)
    rag_service.publish_knowledge_asset(asset_v1.id, user=admin)
    rag_service.approve_knowledge_asset(asset_v2.id, user=admin)
    rag_service.publish_knowledge_asset(asset_v2.id, user=admin)

    # Query pinned to Version 1.0
    res_v1 = rag_service.query(
        query_text="focus syllabus architectures perceptrons",
        course_id="crs-priv-ai401",
        course_version_id="ver-ai-10",
        user=student,
    )
    assert res_v1["status"] == "RAG_OK"
    assert all(r["course_version_id"] == "ver-ai-10" for r in res_v1["results"])
    assert any("perceptrons" in r["text"].lower() for r in res_v1["results"])
    assert not any("transformer" in r["text"].lower() for r in res_v1["results"])

    # Query pinned to Version 2.0
    res_v2 = rag_service.query(
        query_text="focus syllabus architectures perceptrons",
        course_id="crs-priv-ai401",
        course_version_id="ver-ai-20",
        user=student,
    )
    assert res_v2["status"] == "RAG_OK"
    assert all(r["course_version_id"] == "ver-ai-20" for r in res_v2["results"])
    assert any("transformer" in r["text"].lower() for r in res_v2["results"])
    assert not any("perceptrons" in r["text"].lower() for r in res_v2["results"])


# ── 7. CourseLearningContext Binding ────────────────────────────────────────

def test_course_learning_context_binding(clean_db, rag_service):
    """CourseLearningContext encapsulates student, course, version, and class parameters."""
    teacher = clean_db.get_user("usr-teacher-alpha")
    admin = clean_db.get_user("usr-admin-alpha")

    content = "Context Bound Note: Reinforcement learning Q-learning Bellman update equations."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-priv-ai401",
        title="RL Bellman Note",
        content=content,
        organization_id="org-alpha",
        subject="AI",
        user=teacher,
        course_version_id="ver-ai-10",
        visibility_scope=KnowledgeVisibilityScope.CLASS,
        class_id="cls-morning-101",
    )
    rag_service.approve_knowledge_asset(asset.id, user=admin)
    rag_service.publish_knowledge_asset(asset.id, user=admin)

    # Valid matching context
    ctx = CourseLearningContext(
        student_id="usr-stud-alpha-1",
        course_id="crs-priv-ai401",
        organization_id="org-alpha",
        course_version_id="ver-ai-10",
        class_id="cls-morning-101",
    )
    res = rag_service.query("Bellman update equations", context=ctx)
    assert res["status"] == "RAG_OK"
    assert res["count"] >= 1
    assert "Bellman update" in res["results"][0]["text"]

    # Context with mismatched class
    ctx_other_class = CourseLearningContext(
        student_id="usr-stud-alpha-1",
        course_id="crs-priv-ai401",
        organization_id="org-alpha",
        course_version_id="ver-ai-10",
        class_id="cls-other",
    )
    res_mismatch = rag_service.query("Bellman update equations", context=ctx_other_class)
    assert res_mismatch["status"] == "RAG_EMPTY"
    assert res_mismatch["count"] == 0


# ── 8. No Fallback Under Scoped Search ───────────────────────────────────────

def test_no_fallback_under_scoped_search(clean_db, rag_service):
    """When a course is specified and yields 0 matches, return RAG_EMPTY with zero legacy/global leakage."""
    student = clean_db.get_user("usr-stud-alpha-1")

    # Scoped query on a course with zero published assets
    res = rag_service.query(
        query_text="thermodynamics enthalpy first law internal energy",
        course_id="crs-pub-cs101",
        user=student,
    )
    assert res["status"] == "RAG_EMPTY"
    assert res["count"] == 0
    assert res["results"] == []
    assert res["data_context"] == ""


# ── 9. Diagnostics Exposed Without Leakage ──────────────────────────────────

def test_diagnostics_exposed_without_chunk_leak(clean_db, rag_service):
    """Denial and empty states supply clear status without revealing confidential data."""
    student_beta = clean_db.get_user("usr-stud-beta")
    res = rag_service.query(
        query_text="classified neural weights",
        course_id="crs-priv-ai401",
        user=student_beta,
    )
    assert res["status"] == "RAG_DENIED"
    assert "reason" in res
    assert "Access denied" in res["reason"]
    assert res["results"] == []
    assert res["count"] == 0
    assert not res.get("data_context")


# ── 10. REST API Endpoints Scoped RAG ────────────────────────────────────────

def test_scoped_rag_api_flow():
    """Verify REST API registration, filtering, chunk inspection, and query with scoping parameters."""
    client = TestClient(app)
    db = get_db()

    # Create org, users, and courses
    org = Organization(id="org-api-test", name="API Org", slug="api-org")
    db.create_organization(org)
    teacher = User(
        id="usr-api-teacher",
        email="teacher@api-org.edu",
        full_name="API Teacher",
        role=UserRole.TEACHER,
        organization_id="org-api-test",
    )
    admin = User(
        id="usr-api-admin",
        email="admin@api-org.edu",
        full_name="API Admin",
        role=UserRole.ORG_ADMIN,
        organization_id="org-api-test",
    )
    db.create_user(teacher)
    db.create_user(admin)

    course = Course(
        id="crs-api-scope",
        organization_id="org-api-test",
        code="SCOPE-101",
        title="API Scoped RAG",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)

    teacher_token = create_access_token(user_id=teacher.id, role="TEACHER", organization_id="org-api-test")
    admin_token = create_access_token(user_id=admin.id, role="ORG_ADMIN", organization_id="org-api-test")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Register Source with scoping fields (requires TEACHER auth)
    resp = client.post(
        "/api/v1/rag/sources",
        headers=teacher_headers,
        json={
            "course_id": "crs-api-scope",
            "subject": "Computer Science",
            "title": "API Scope Reference",
            "course_version_id": "ver-api-1",
            "visibility_scope": "class",
            "class_id": "class-api-a",
            "target_student_ids": ["stud-api-1"],
        },
    )
    assert resp.status_code == 201
    src_data = resp.json()["data"]
    source_id = src_data["id"]
    assert src_data["course_version_id"] == "ver-api-1"
    assert src_data["visibility_scope"] == "class"
    assert src_data["class_id"] == "class-api-a"

    # 2. Ingest (requires TEACHER auth)
    content = "Scoped chunk text: Algorithm complexity of QuickSort is O(N log N) on average."
    resp_ingest = client.post(
        f"/api/v1/rag/sources/{source_id}/ingest",
        headers=teacher_headers,
        json={"content": content, "file_name": "quicksort.txt"},
    )
    assert resp_ingest.status_code == 200

    # 3. Validate (requires TEACHER auth) and Publish (requires ADMIN auth)
    client.post(f"/api/v1/rag/sources/{source_id}/validate", headers=teacher_headers)
    resp_pub = client.post(f"/api/v1/rag/sources/{source_id}/publish", headers=admin_headers)
    assert resp_pub.status_code == 200

    # 4. List sources with filtering (no auth required — read-only)
    resp_list = client.get(
        "/api/v1/rag/sources",
        params={
            "course_id": "crs-api-scope",
            "course_version_id": "ver-api-1",
            "visibility_scope": "class",
            "class_id": "class-api-a",
        },
    )
    assert resp_list.status_code == 200
    assert len(resp_list.json()["data"]) >= 1

    # 5. List chunks (no auth required — read-only)
    resp_chunks = client.get(f"/api/v1/rag/sources/{source_id}/chunks")
    assert resp_chunks.status_code == 200
    chunk = resp_chunks.json()["data"][0]
    assert chunk["course_version_id"] == "ver-api-1"
    assert chunk["visibility_scope"] == "class"
    assert chunk["class_id"] == "class-api-a"

    # 6. Query with correct class_id (no auth required — read-only)
    resp_q_ok = client.post(
        "/api/v1/rag/query",
        json={
            "query": "QuickSort algorithm complexity",
            "course_id": "crs-api-scope",
            "course_version_id": "ver-api-1",
            "class_id": "class-api-a",
        },
    )
    assert resp_q_ok.status_code == 200
    assert resp_q_ok.json()["data"]["status"] == "RAG_OK"
    assert resp_q_ok.json()["data"]["count"] >= 1

    # 7. Query with wrong class_id -> RAG_EMPTY
    resp_q_empty = client.post(
        "/api/v1/rag/query",
        json={
            "query": "QuickSort algorithm complexity",
            "course_id": "crs-api-scope",
            "course_version_id": "ver-api-1",
            "class_id": "class-api-wrong",
        },
    )
    assert resp_q_empty.status_code == 200
    assert resp_q_empty.json()["data"]["status"] == "RAG_EMPTY"
    assert resp_q_empty.json()["data"]["count"] == 0
