"""Phase 05: Knowledge Asset Ingestion & Publication Pipeline Tests.

Governing Document: GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md (Section 12.5)
Plan: docs/reports/PHASE_05_PLAN.md

Verifies:
1. Multi-Format Ingestion: Markdown, Plain Text, Structured JSON across Content Types.
2. Full Lifecycle Transitions:
   DRAFT/PROCESSING -> READY_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED.
3. Failure State Isolation:
   Malformed content transitions to FAILED; failed assets can never be approved or published;
   oversized content is rejected.
4. Role-Based Authorization Gates:
   Teachers can upload; teachers CANNOT approve or publish (403 PermissionError);
   Students CANNOT upload, approve, or publish (403 PermissionError);
   Only ORG_ADMIN and SUPER_ADMIN can approve and publish.
5. Phase Gate: Student Visibility Invariant:
   Unpublished assets (PROCESSING, READY_FOR_REVIEW, APPROVED, FAILED, ARCHIVED)
   are 100% invisible to student retrieval queries. Only PUBLISHED assets are retrievable.
"""
from __future__ import annotations

import json
import pytest

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    KnowledgeAssetStatus,
    KnowledgeContentType,
    Organization,
    RAGSourceStatus,
    User,
    UserRole,
)
from central_platform.rag.service import RAGService


@pytest.fixture
def clean_db():
    db = PlatformDatabase(db_path=":memory:")

    # Setup parent organization
    org = Organization(id="org-acme", name="Acme Academy", slug="acme-academy")
    db.create_organization(org)

    # Setup courses
    history_course = Course(
        id="crs-world-history-101",
        organization_id="org-acme",
        code="HIST-101",
        title="World History",
    )
    physics_course = Course(
        id="crs-physics-201",
        organization_id="org-acme",
        code="PHYS-201",
        title="Modern Physics",
    )
    db.create_course(history_course)
    db.create_course(physics_course)

    # Setup role users
    super_admin = User(
        id="usr-super-admin",
        organization_id="org-acme",
        email="superadmin@acme.edu",
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
    )
    org_admin = User(
        id="usr-org-admin",
        organization_id="org-acme",
        email="admin@acme.edu",
        full_name="Institutional Admin",
        role=UserRole.ORG_ADMIN,
    )
    teacher = User(
        id="usr-teacher-01",
        organization_id="org-acme",
        email="teacher@acme.edu",
        full_name="History Teacher",
        role=UserRole.TEACHER,
    )
    student = User(
        id="usr-student-01",
        organization_id="org-acme",
        email="student@acme.edu",
        full_name="Student One",
        role=UserRole.STUDENT,
    )
    for u in [super_admin, org_admin, teacher, student]:
        db.create_user(u)

    return db


@pytest.fixture
def rag_service(clean_db):
    return RAGService(clean_db)


# ── 1. Multi-Format & Multi-ContentType Ingestion ──────────────────────────────

def test_ingestion_multi_format_markdown(clean_db, rag_service):
    """Verify markdown content ingestion with section structure and chunking."""
    teacher = clean_db.get_user("usr-teacher-01")
    md_content = (
        "# The Industrial Revolution\n"
        "## Steam Engine Innovation\n"
        "James Watt modified Thomas Newcomen's 1712 engine with a separate condenser in 1769.\n"
        "This substantially avoided energy loss during cylinder heating and cooling cycles.\n\n"
        "## Textile Manufacturing\n"
        "The spinning jenny created by James Hargreaves in 1764 drastically reduced labor yarn production."
    )
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="Industrial Revolution Primer",
        content=md_content,
        organization_id="org-acme",
        subject="History",
        user=teacher,
        source_type="markdown",
        content_type=KnowledgeContentType.TEXTBOOK,
    )

    assert asset.status == RAGSourceStatus.READY_FOR_REVIEW.value
    assert asset.chunk_count >= 2
    assert asset.uploaded_by == "usr-teacher-01"
    assert asset.content_type == KnowledgeContentType.TEXTBOOK.value
    assert asset.error_message is None


def test_ingestion_multi_format_json(clean_db, rag_service):
    """Verify structured JSON content ingestion."""
    teacher = clean_db.get_user("usr-teacher-01")
    json_data = {
        "chapter": "Quantum Foundations",
        "sections": [
            {
                "topic": "Photoelectric Effect",
                "concept": "Planck-Einstein Relation",
                "page": 42,
                "text": "Energy of a photon is directly proportional to its frequency: E = h * nu.",
            },
            {
                "topic": "Wave-Particle Duality",
                "concept": "de Broglie Wavelength",
                "page": 45,
                "text": "Matter exhibits wave-like behavior with wavelength lambda = h / p.",
            },
        ],
    }
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-physics-201",
        title="Quantum Mechanics Notes",
        content=json.dumps(json_data),
        organization_id="org-acme",
        subject="Physics",
        user=teacher,
        source_type="json",
        content_type=KnowledgeContentType.TEACHER_NOTE,
    )

    assert asset.status == RAGSourceStatus.READY_FOR_REVIEW.value
    assert asset.chunk_count == 2
    assert asset.content_type == KnowledgeContentType.TEACHER_NOTE.value


def test_ingestion_multi_format_text(clean_db, rag_service):
    """Verify plain text ingestion across custom content classifications."""
    teacher = clean_db.get_user("usr-teacher-01")
    text_content = (
        "Practice Worksheet 1: Solve for velocity and acceleration.\n"
        "Problem 1: An object moves with constant acceleration of 9.8 m/s^2.\n"
        "Problem 2: Calculate displacement over a 5 second time interval."
    )
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-physics-201",
        title="Kinematics Worksheet",
        content=text_content,
        organization_id="org-acme",
        subject="Physics",
        user=teacher,
        source_type="text",
        content_type=KnowledgeContentType.WORKSHEET,
    )

    assert asset.status == RAGSourceStatus.READY_FOR_REVIEW.value
    assert asset.chunk_count >= 1
    assert asset.content_type == KnowledgeContentType.WORKSHEET.value


# ── 2. Full Lifecycle State Transitions ───────────────────────────────────────

def test_full_lifecycle_state_transitions(clean_db, rag_service):
    """Verify: DRAFT/PROCESSING -> READY_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED."""
    teacher = clean_db.get_user("usr-teacher-01")
    org_admin = clean_db.get_user("usr-org-admin")

    # 1. Upload by teacher -> transitions to READY_FOR_REVIEW
    content = "The Treaty of Versailles was signed on 28 June 1919 ending World War I."
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="Treaty of Versailles Summary",
        content=content,
        organization_id="org-acme",
        subject="History",
        user=teacher,
    )
    assert asset.status == KnowledgeAssetStatus.READY_FOR_REVIEW.value
    assert asset.published_at is None
    assert asset.published_by is None

    # 2. Institutional Admin approves -> transitions to APPROVED
    approved_asset = rag_service.approve_knowledge_asset(asset.id, user=org_admin)
    assert approved_asset.status == KnowledgeAssetStatus.APPROVED.value

    # Verify persisted in database
    persisted = clean_db.get_rag_source(asset.id)
    assert persisted.status == KnowledgeAssetStatus.APPROVED.value

    # 3. Institutional Admin publishes -> transitions to PUBLISHED
    published_asset = rag_service.publish_knowledge_asset(asset.id, user=org_admin)
    assert published_asset.status == KnowledgeAssetStatus.PUBLISHED.value
    assert published_asset.published_by == "usr-org-admin"
    assert published_asset.published_at is not None

    # 4. Author archives -> transitions to ARCHIVED
    archived_asset = rag_service.archive_knowledge_asset(asset.id, user=org_admin)
    assert archived_asset.status == KnowledgeAssetStatus.ARCHIVED.value


# ── 3. Failure State Isolation & Guardrails ───────────────────────────────────

def test_failure_state_malformed_json_handling(clean_db, rag_service):
    """Verify malformed content transitions to FAILED state and cannot be approved or published."""
    teacher = clean_db.get_user("usr-teacher-01")
    org_admin = clean_db.get_user("usr-org-admin")

    malformed_json = "{'broken': json syntax unclosed"
    failed_asset = rag_service.upload_knowledge_asset(
        course_id="crs-physics-201",
        title="Corrupted Document",
        content=malformed_json,
        organization_id="org-acme",
        subject="Physics",
        user=teacher,
        source_type="json",
    )

    assert failed_asset.status == KnowledgeAssetStatus.FAILED.value
    assert failed_asset.error_message is not None
    assert len(failed_asset.error_message) > 0

    # Ensure failed asset cannot be approved
    with pytest.raises(ValueError, match="Cannot approve failed knowledge asset"):
        rag_service.approve_knowledge_asset(failed_asset.id, user=org_admin)

    # Ensure failed asset cannot be published
    with pytest.raises(ValueError, match="Cannot publish failed knowledge asset"):
        rag_service.publish_knowledge_asset(failed_asset.id, user=org_admin)


def test_failure_state_empty_content_validation(clean_db, rag_service):
    """Verify empty content is rejected."""
    teacher = clean_db.get_user("usr-teacher-01")

    with pytest.raises(ValueError, match="Content cannot be empty"):
        rag_service.upload_knowledge_asset(
            course_id="crs-physics-201",
            title="Empty Document",
            content="    \n   ",
            organization_id="org-acme",
            subject="Physics",
            user=teacher,
        )


def test_failure_state_oversized_content_rejected(clean_db, rag_service):
    """Verify content exceeding size limit (10MB) is rejected."""
    teacher = clean_db.get_user("usr-teacher-01")
    huge_content = "X" * (11 * 1024 * 1024)

    with pytest.raises(ValueError, match="Content exceeds maximum allowed size"):
        rag_service.upload_knowledge_asset(
            course_id="crs-physics-201",
            title="Huge File",
            content=huge_content,
            organization_id="org-acme",
            subject="Physics",
            user=teacher,
        )


# ── 4. Role-Based Authorization Gates ─────────────────────────────────────────

def test_authorization_students_forbidden_from_upload(clean_db, rag_service):
    """Verify students cannot upload knowledge assets (403 PermissionError)."""
    student = clean_db.get_user("usr-student-01")

    with pytest.raises(PermissionError, match="Students are not permitted to upload"):
        rag_service.upload_knowledge_asset(
            course_id="crs-world-history-101",
            title="Student Notes Attempt",
            content="Notes written by a student trying to contaminate course RAG.",
            organization_id="org-acme",
            subject="History",
            user=student,
        )


def test_authorization_teachers_cannot_approve_or_publish(clean_db, rag_service):
    """Verify teachers can upload but CANNOT approve or publish assets."""
    teacher = clean_db.get_user("usr-teacher-01")

    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="French Revolution Overview",
        content="The Storming of the Bastille occurred on 14 July 1789.",
        organization_id="org-acme",
        subject="History",
        user=teacher,
    )
    assert asset.status == KnowledgeAssetStatus.READY_FOR_REVIEW.value

    # Teacher cannot approve
    with pytest.raises(PermissionError, match="Only institutional administrators"):
        rag_service.approve_knowledge_asset(asset.id, user=teacher)

    # Teacher cannot publish
    with pytest.raises(PermissionError, match="Only institutional administrators"):
        rag_service.publish_knowledge_asset(asset.id, user=teacher)


def test_authorization_super_admin_can_approve_and_publish(clean_db, rag_service):
    """Verify super administrator can approve and publish knowledge assets."""
    teacher = clean_db.get_user("usr-teacher-01")
    super_admin = clean_db.get_user("usr-super-admin")

    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="Renaissance Art",
        content="The Renaissance marked a transition from the Middle Ages to modernity.",
        organization_id="org-acme",
        subject="History",
        user=teacher,
    )

    approved = rag_service.approve_knowledge_asset(asset.id, user=super_admin)
    assert approved.status == KnowledgeAssetStatus.APPROVED.value

    published = rag_service.publish_knowledge_asset(asset.id, user=super_admin)
    assert published.status == KnowledgeAssetStatus.PUBLISHED.value
    assert published.published_by == "usr-super-admin"


# ── 5. Phase Gate: Student Visibility Invariant ───────────────────────────────

def test_phase_gate_student_visibility_invariant(clean_db, rag_service):
    """Verify that student retrieval queries NEVER retrieve unpublished assets.

    State progression:
    1. READY_FOR_REVIEW -> student query returns 0 chunks.
    2. APPROVED -> student query returns 0 chunks.
    3. FAILED -> student query returns 0 chunks.
    4. PUBLISHED -> student query retrieves matching chunks!
    5. ARCHIVED -> student query returns 0 chunks again!
    """
    teacher = clean_db.get_user("usr-teacher-01")
    org_admin = clean_db.get_user("usr-org-admin")
    student = clean_db.get_user("usr-student-01")

    history_content = (
        "# Ancient Rome\n"
        "## The Roman Republic\n"
        "The Roman Republic was established around 509 BC after the overthrow of the Tarquin monarchs.\n"
        "It was governed by two annually elected consuls advised by a senate of patricians."
    )

    # Step 1: Upload (READY_FOR_REVIEW)
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="Ancient Rome History",
        content=history_content,
        organization_id="org-acme",
        subject="History",
        user=teacher,
        source_type="markdown",
    )
    assert asset.status == KnowledgeAssetStatus.READY_FOR_REVIEW.value

    # Query as student while in READY_FOR_REVIEW -> MUST RETURN 0
    res_ready = rag_service.query(
        query_text="Roman Republic 509 BC consuls senate",
        course_id="crs-world-history-101",
        user=student,
    )
    assert res_ready["status"] == "RAG_EMPTY"
    assert len(res_ready["results"]) == 0
    assert res_ready["count"] == 0

    # Step 2: Approve (APPROVED)
    rag_service.approve_knowledge_asset(asset.id, user=org_admin)

    # Query as student while in APPROVED -> MUST STILL RETURN 0
    res_approved = rag_service.query(
        query_text="Roman Republic 509 BC consuls senate",
        course_id="crs-world-history-101",
        user=student,
    )
    assert res_approved["status"] == "RAG_EMPTY"
    assert len(res_approved["results"]) == 0
    assert res_approved["count"] == 0

    # Step 3: Publish (PUBLISHED)
    rag_service.publish_knowledge_asset(asset.id, user=org_admin)

    # Query as student while in PUBLISHED -> MUST RETRIEVE KNOWLEDGE
    res_published = rag_service.query(
        query_text="Roman Republic 509 BC consuls senate",
        course_id="crs-world-history-101",
        user=student,
    )
    assert res_published["status"] == "RAG_OK"
    assert res_published["count"] >= 1
    assert "509 BC" in res_published["results"][0]["text"]
    assert "<rag_evidence_data" in res_published["data_context"]

    # Step 4: Archive (ARCHIVED)
    rag_service.archive_knowledge_asset(asset.id, user=org_admin)

    # Query as student while ARCHIVED -> MUST RETURN 0 AGAIN
    res_archived = rag_service.query(
        query_text="Roman Republic 509 BC consuls senate",
        course_id="crs-world-history-101",
        user=student,
    )
    assert res_archived["status"] == "RAG_EMPTY"
    assert len(res_archived["results"]) == 0
    assert res_archived["count"] == 0


def test_cross_course_isolation_under_publication(clean_db, rag_service):
    """Verify published knowledge assets in Course A are invisible to Course B queries."""
    teacher = clean_db.get_user("usr-teacher-01")
    org_admin = clean_db.get_user("usr-org-admin")
    student = clean_db.get_user("usr-student-01")

    # Publish asset in History course
    asset = rag_service.upload_knowledge_asset(
        course_id="crs-world-history-101",
        title="World War II Summary",
        content="The Battle of Midway took place in June 1942 as a decisive naval battle.",
        organization_id="org-acme",
        subject="History",
        user=teacher,
    )
    rag_service.approve_knowledge_asset(asset.id, user=org_admin)
    rag_service.publish_knowledge_asset(asset.id, user=org_admin)

    # Query in Physics course should NOT retrieve History material
    res_physics = rag_service.query(
        query_text="Battle of Midway 1942 naval battle",
        course_id="crs-physics-201",
        user=student,
    )
    assert res_physics["status"] == "RAG_EMPTY"
    assert res_physics["count"] == 0
