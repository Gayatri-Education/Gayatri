"""Phase 18: Teacher Instruction + RAG Integration Test Suite.

Verifies Master Plan Section 12.18:
1. Merged context with course textbook + class note + student remedial note.
2. Provenance and audit tracking: exact source_ids, chunk_ids, instruction_ids recorded.
3. Directives vs evidence separation: directives in system prompt, evidence enveloped in XML in user prompt.
4. Precedence cascade: SESSION > STUDENT > CLASS > COURSE > ORGANIZATION.
5. Priority tie-breaking within the same scope.
6. Expired instruction exclusion.
7. Unauthorized RAG note exclusion (cross-class and foreign-student remedial notes blocked).
8. Graceful empty RAG handling (RAG_EMPTY with clean fallback).
9. Graceful empty instructions handling (zero directives).
10. Mixed scopes with multiple active directives and multi-level RAG.
11. Course version pinning: RAG chunks and instructions strictly respect pinned course version.
12. REST API /api/v1/tutor/turn end-to-end integration verifying provenance and applied instruction IDs in HTTP response.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from central_platform.ai.context_builder import ContextBuilder, AssembledContext
from central_platform.api.app import app
from central_platform.auth.dependencies import get_db
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    ClassGroup,
    Cohort,
    Concept,
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Curriculum,
    Enrollment,
    KnowledgeContentType,
    KnowledgeVisibilityScope,
    Module,
    Organization,
    RAGSourceStatus,
    Session,
    SessionStatus,
    Topic,
    User,
    UserRole,
)
from central_platform.rag.service import RAGService
from central_platform.teacher.instruction import (
    InstructionStatus,
    SafetyStatus,
    ScopeType,
    TeacherInstruction,
    TeacherInstructionEngine,
)
from central_platform.tutor.orchestrator import (
    GenericTutorOrchestrator,
    TutorTurnRequest,
    TutorTurnResult,
)


@pytest.fixture
def db(tmp_path):
    """Provide isolated SQLite database instance for Phase 18 tests."""
    db_file = str(tmp_path / "phase18_test.db")
    db = PlatformDatabase(db_file)

    # Seed baseline organization, teacher, and student
    org = Organization(id="org-acme", name="Acme Academy", slug="acme-academy")
    db.create_organization(org)

    teacher = User(
        id="teacher-01",
        organization_id="org-acme",
        email="teacher@acme.edu",
        full_name="Prof. Sharma",
        role=UserRole.TEACHER,
    )
    db.create_user(teacher)

    student1 = User(
        id="student-01",
        organization_id="org-acme",
        email="student01@acme.edu",
        full_name="Aarav Patel",
        role=UserRole.STUDENT,
    )
    db.create_user(student1)

    student2 = User(
        id="student-02",
        organization_id="org-acme",
        email="student02@acme.edu",
        full_name="Diya Iyer",
        role=UserRole.STUDENT,
    )
    db.create_user(student2)

    course = Course(
        id="crs-phys-101",
        organization_id="org-acme",
        title="AP Physics 1: Mechanics",
        code="PHYS101",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)

    v1 = CourseVersion(
        id="ver-1.0",
        course_id="crs-phys-101",
        version_number="1.0",
        status=CourseStatus.PUBLISHED,
    )
    db.create_course_version(v1)

    cur = Curriculum(id="cur-phys", course_id="crs-phys-101", title="AP Physics 1 Curriculum", version="1.0")
    db.create_curriculum(cur)

    mod = Module(id="mod-mechanics", curriculum_id="cur-phys", title="Mechanics", sequence_order=1)
    db.create_module(mod)

    top = Topic(id="top-kinematics", module_id="mod-mechanics", title="Kinematics", sequence_order=1)
    db.create_topic(top)

    cpt = Concept(
        id="cpt-kinematics",
        topic_id="top-kinematics",
        name="Kinematics",
        description="One-dimensional motion, displacement, velocity, and acceleration.",
        difficulty=0.5,
    )
    db.create_concept(cpt)
    cg = ClassGroup(id="cg-phys", organization_id="org-acme", course_id="crs-phys-101", name="Physics Class Group")
    db.create_class_group(cg)

    c_a = Cohort(id="cls-a", class_group_id="cg-phys", name="Cohort A", academic_year="2026")
    db.create_cohort(c_a)

    c_b = Cohort(id="cls-b", class_group_id="cg-phys", name="Cohort B", academic_year="2026")
    db.create_cohort(c_b)

    # Enroll student-01 into cohort cls-a
    enr1 = Enrollment(
        id="enr-01",
        student_id="student-01",
        course_id="crs-phys-101",
        cohort_id="cls-a",
        is_active=True,
    )
    db.create_enrollment(enr1)

    # Enroll student-02 into cohort cls-b
    enr2 = Enrollment(
        id="enr-02",
        student_id="student-02",
        course_id="crs-phys-101",
        cohort_id="cls-b",
        is_active=True,
    )
    db.create_enrollment(enr2)

    return db


def _publish_rag_source(
    rag_service: RAGService,
    course_id: str,
    title: str,
    text: str,
    subject: str = "Physics",
    authority: str = "NCERT",
    visibility_scope: str = "course",
    class_id: str | None = None,
    target_student_ids: list[str] | None = None,
    course_version_id: str | None = None,
    source_id: str | None = None,
):
    """Helper to register, ingest, validate, and publish a RAG source."""
    src = rag_service.register_source(
        organization_id="org-acme",
        course_id=course_id,
        subject=subject,
        title=title,
        source_type="markdown",
        authority=authority,
        visibility_scope=visibility_scope,
        class_id=class_id,
        target_student_ids=target_student_ids,
        course_version_id=course_version_id,
        source_id=source_id,
    )
    rag_service.ingest_document(src.id, text)
    rag_service.validate_source(src.id)
    return rag_service.publish_source(src.id)


# ── Test 1: Merged Context (Textbook + Class Note + Student Remedial) ────────

def test_merged_context_course_textbook_class_note_student_remedial(db):
    """Verify that Course textbook, Class notes, and Student remedial notes are correctly retrieved and merged."""
    rag_service = RAGService(db)

    # 1. Course Textbook (course-wide)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="NCERT Physics Textbook: Kinematics",
        text="# Kinematics\nDisplacement is the vector change in position. Velocity is rate of change of displacement.",
        visibility_scope="course",
        source_id="src-ncert-textbook",
    )

    # 2. Class Note (cls-a only)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Class A Problem Solving Handout",
        text="# Kinematics Strategies\nFor Class A, always sketch velocity-time graph before calculating displacement.",
        visibility_scope="class",
        class_id="cls-a",
        source_id="src-class-a-handout",
    )

    # 3. Student Remedial Note (student-01 only)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Aarav Remedial Kinematics Card",
        text="# Kinematics Reminders\nAarav: Acceleration is negative when slowing down in positive direction.",
        visibility_scope="student_targeted",
        target_student_ids=["student-01"],
        source_id="src-remedial-aarav",
    )

    # Query for student-01 in cls-a
    builder = ContextBuilder(db)
    ctx = builder.build_context(
        query="Explain velocity and acceleration in kinematics",
        student_id="student-01",
        course_id="crs-phys-101",
        concept_id="cpt-kinematics",
        class_id="cls-a",
        max_rag_chunks=5,
    )

    assert len(ctx.rag_context) >= 3
    retrieved_sources = {r["source_id"] for r in ctx.rag_context}
    assert "src-ncert-textbook" in retrieved_sources
    assert "src-class-a-handout" in retrieved_sources
    assert "src-remedial-aarav" in retrieved_sources

    assert "src-ncert-textbook" in ctx.contributed_source_ids
    assert "src-class-a-handout" in ctx.contributed_source_ids
    assert "src-remedial-aarav" in ctx.contributed_source_ids
    assert len(ctx.contributed_chunk_ids) >= 3
    assert len(ctx.provenance_records) >= 3


# ── Test 2: Provenance and Audit Tracking ────────────────────────────────────

def test_provenance_and_audit_tracking(db):
    """Verify that TutorTurnResult and AssembledContext record accurate provenance metadata."""
    rag_service = RAGService(db)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Newtonian Principles",
        text="# Newton Second Law\nThe acceleration of an object is directly proportional to net force: F = m*a.",
        source_id="src-newton-laws",
    )

    teacher_engine = TeacherInstructionEngine(db)
    inst = TeacherInstruction(
        instruction_id="inst-diag-01",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        instruction_text="Require students to state Newton second law formula.",
        priority=3,
        scope_type="COURSE",
    )
    teacher_engine.add_instruction(inst)

    orchestrator = GenericTutorOrchestrator(db=db)
    req = TutorTurnRequest(
        student_id="student-01",
        session_id="sess-turn-01",
        course_id="crs-phys-101",
        class_id="cls-a",
        concept_id="cpt-kinematics",
        message="What is the relation between force and acceleration in Newton's second law?",
    )

    res = orchestrator.execute_turn(req)
    assert res.status == "SUCCESS"
    assert "inst-diag-01" in res.applied_instruction_ids
    assert "src-newton-laws" in res.contributed_source_ids
    assert len(res.contributed_chunk_ids) >= 1
    assert len(res.provenance_records) >= 1

    prov = res.provenance_records[0]
    assert prov["source_id"] == "src-newton-laws"
    assert "chunk_id" in prov
    assert prov["authority"] == "NCERT"
    assert prov["provenance_type"] == "NCERT"
    assert prov["visibility_scope"] == "course"


# ── Test 3: Directives vs Evidence Separation Invariant ───────────────────────

def test_directives_vs_evidence_separation(db):
    """Verify directives are strictly framed in System Prompt, and RAG evidence is in User Prompt in XML tags."""
    teacher_engine = TeacherInstructionEngine(db)
    inst = TeacherInstruction(
        instruction_id="inst-socratic-01",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        instruction_text="Guide student to identify variables before writing formula.",
        priority=4,
        scope_type="COURSE",
    )
    teacher_engine.add_instruction(inst)

    rag_service = RAGService(db)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Kinematics Equations",
        text="# Kinematics Equations\nFormula for final velocity with acceleration and distance: v^2 = u^2 + 2*a*s.",
        source_id="src-kinematics-equations",
    )

    builder = ContextBuilder(db)
    ctx = builder.build_context(
        query="How do I find final velocity with acceleration and distance?",
        student_id="student-01",
        course_id="crs-phys-101",
        concept_id="cpt-kinematics",
    )

    sys_prompt = ContextBuilder.build_system_prompt(
        subject="Physics",
        formatted_directives=ctx.teacher_directives_block,
    )
    user_prompt = ContextBuilder.build_user_prompt(
        user_query=ctx.query,
        rag_context=ctx.rag_evidence_block,
    )

    # 1. System Prompt checks (Directives present, no RAG chunk text, strictly invariant framed)
    assert "[TEACHER PEDAGOGICAL DIRECTIVES - STRICT DATA FRAMING]:" in sys_prompt
    assert "Guide student to identify variables before writing formula." in sys_prompt
    assert "[SYSTEM INVARIANT NOTE]:" in sys_prompt
    assert "v^2 = u^2 + 2*a*s" not in sys_prompt

    # 2. User Prompt checks (Evidence wrapped in XML, no teacher directives)
    assert "<rag_evidence_data" in user_prompt
    assert "</rag_evidence_data>" in user_prompt
    assert "v^2 = u^2 + 2*a*s" in user_prompt
    assert "Guide student to identify variables before writing formula." not in user_prompt


# ── Test 4: Precedence Cascade (SESSION > STUDENT > CLASS > COURSE > ORG) ───

def test_precedence_cascade_session_student_class_course_org(db):
    """Verify deterministic hierarchy resolution: SESSION(5) > STUDENT(4) > CLASS(3) > COURSE(2) > ORGANIZATION(1)."""
    engine = TeacherInstructionEngine(db)

    i_org = TeacherInstruction(
        instruction_id="inst-org",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="*",
        scope_type=ScopeType.ORGANIZATION.value,
        instruction_text="Org Directive: Strictly adhere to state standard terminology.",
        priority=1,
    )
    i_crs = TeacherInstruction(
        instruction_id="inst-crs",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="crs-phys-101",
        scope_type=ScopeType.COURSE.value,
        instruction_text="Course Directive: Emphasize SI units in all responses.",
        priority=1,
    )
    i_cls = TeacherInstruction(
        instruction_id="inst-cls",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="crs-phys-101",
        class_id="cls-a",
        scope_type=ScopeType.CLASS.value,
        instruction_text="Class Directive: Use collaborative inquiry tone.",
        priority=1,
    )
    i_stu = TeacherInstruction(
        instruction_id="inst-stu",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="crs-phys-101",
        student_id="student-01",
        scope_type=ScopeType.STUDENT.value,
        instruction_text="Student Directive: Provide extra visual analogies.",
        priority=1,
    )
    i_ses = TeacherInstruction(
        instruction_id="inst-ses",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="crs-phys-101",
        session_id="sess-active-01",
        scope_type=ScopeType.SESSION.value,
        instruction_text="Session Directive: Focus only on question 5 review.",
        priority=1,
    )

    for i in [i_org, i_crs, i_cls, i_stu, i_ses]:
        engine.add_instruction(i)

    resolved = engine.resolve_hierarchical_instructions(
        course_id="crs-phys-101",
        organization_id="org-acme",
        class_id="cls-a",
        student_id="student-01",
        session_id="sess-active-01",
    )

    assert len(resolved) == 5
    expected_order = ["inst-ses", "inst-stu", "inst-cls", "inst-crs", "inst-org"]
    actual_order = [inst.instruction_id for inst in resolved]
    assert actual_order == expected_order


# ── Test 5: Priority Tie-Breaking Within Same Scope ──────────────────────────

def test_priority_tie_breaking_within_same_scope(db):
    """Verify that within the same scope, higher priority directives take precedence."""
    engine = TeacherInstructionEngine(db)

    i_low = TeacherInstruction(
        instruction_id="inst-low",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        class_id="cls-a",
        scope_type="CLASS",
        instruction_text="Optional: Discuss historical background.",
        priority=1,
    )
    i_urgent = TeacherInstruction(
        instruction_id="inst-urgent",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        class_id="cls-a",
        scope_type="CLASS",
        instruction_text="Urgent: Focus heavily on upcoming midterm problems.",
        priority=4,
    )
    i_high = TeacherInstruction(
        instruction_id="inst-high",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        class_id="cls-a",
        scope_type="CLASS",
        instruction_text="High: Review free body diagram vectors.",
        priority=3,
    )

    for i in [i_low, i_urgent, i_high]:
        engine.add_instruction(i)

    resolved = engine.resolve_hierarchical_instructions(
        course_id="crs-phys-101",
        class_id="cls-a",
    )

    assert len(resolved) == 3
    assert resolved[0].instruction_id == "inst-urgent"
    assert resolved[1].instruction_id == "inst-high"
    assert resolved[2].instruction_id == "inst-low"


# ── Test 6: Expired Instruction Exclusion ────────────────────────────────────

def test_expired_instruction_exclusion(db):
    """Verify that temporally expired teacher instructions are automatically filtered out."""
    engine = TeacherInstructionEngine(db)

    i_expired = TeacherInstruction(
        instruction_id="inst-expired",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        instruction_text="Old Directive: Temporary review from last semester.",
        priority=5,
        start_at="2020-01-01T00:00:00Z",
        expires_at="2020-06-01T00:00:00Z",
    )
    i_active = TeacherInstruction(
        instruction_id="inst-active",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        instruction_text="Current Directive: Emphasize scientific notation.",
        priority=2,
        start_at="2020-01-01T00:00:00Z",
        expires_at="2035-01-01T00:00:00Z",
    )

    engine.add_instruction(i_expired)
    engine.add_instruction(i_active)

    resolved = engine.resolve_hierarchical_instructions(course_id="crs-phys-101")
    resolved_ids = [i.instruction_id for i in resolved]

    assert "inst-active" in resolved_ids
    assert "inst-expired" not in resolved_ids


# ── Test 7: Unauthorized RAG Note Exclusion (Cross-Class & Foreign Student) ──

def test_unauthorized_rag_note_exclusion(db):
    """Verify that class notes and student remedial cards are strictly isolated from unauthorized learners."""
    rag_service = RAGService(db)

    # Course textbook (authorized)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Public Physics Text",
        text="# Free Fall\nObjects in free fall experience uniform acceleration g = 9.8 m/s^2.",
        visibility_scope="course",
        source_id="src-pub-text",
    )

    # Class B note (UNAUTHORIZED for student-01 in cls-a)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Class B Internal Quiz Leaks",
        text="# Free Fall Quiz\nClass B confidential: quiz question 3 uses initial height h=20m.",
        visibility_scope="class",
        class_id="cls-b",
        source_id="src-cls-b-leak",
    )

    # Student 02 remedial note (UNAUTHORIZED for student-01)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Diya Private Notes",
        text="# Free Fall\nDiya private note: remember to multiply by 0.5 for displacement.",
        visibility_scope="student_targeted",
        target_student_ids=["student-02"],
        source_id="src-student-02-private",
    )

    # Query as student-01 in cls-a
    builder = ContextBuilder(db)
    ctx = builder.build_context(
        query="What acceleration do objects experience in free fall?",
        student_id="student-01",
        course_id="crs-phys-101",
        concept_id="cpt-kinematics",
        class_id="cls-a",
    )

    retrieved_sources = {c["source_id"] for c in ctx.rag_context}
    assert "src-pub-text" in retrieved_sources
    assert "src-cls-b-leak" not in retrieved_sources
    assert "src-student-02-private" not in retrieved_sources

    assert "src-cls-b-leak" not in ctx.contributed_source_ids
    assert "src-student-02-private" not in ctx.contributed_source_ids


# ── Test 8: Graceful Empty RAG Handling ──────────────────────────────────────

def test_graceful_empty_rag_handling(db):
    """Verify that when RAG returns 0 chunks, turn executes cleanly with RAG_EMPTY status."""
    orchestrator = GenericTutorOrchestrator(db=db)
    req = TutorTurnRequest(
        student_id="student-01",
        session_id="sess-empty-rag",
        course_id="crs-phys-101",
        message="A topic completely unmentioned in the curriculum like XYZ123.",
    )

    res = orchestrator.execute_turn(req)
    assert res.status == "SUCCESS"
    assert res.rag_sources_used == []
    assert res.contributed_chunk_ids == []
    assert res.contributed_source_ids == []
    assert res.provenance_records == []
    assert res.validation_passed is True


# ── Test 9: Graceful Empty Instructions Handling ─────────────────────────────

def test_graceful_empty_instructions_handling(db):
    """Verify that when no teacher instructions exist, context assembly and system prompt build without error."""
    builder = ContextBuilder(db)
    ctx = builder.build_context(
        query="What is velocity?",
        student_id="student-01",
        course_id="crs-phys-101",
        concept_id="cpt-kinematics",
    )

    assert ctx.applied_instruction_ids == []
    assert ctx.teacher_instructions_context == []
    assert ctx.teacher_directives_block == ""

    sys_prompt = ContextBuilder.build_system_prompt(
        subject="Physics",
        formatted_directives=ctx.teacher_directives_block,
    )
    assert "[TEACHER PEDAGOGICAL DIRECTIVES" not in sys_prompt
    assert "You are Gayatri AI" in sys_prompt


# ── Test 10: Mixed Scopes with Multiple Directives and RAG ───────────────────

def test_mixed_scopes_multiple_directives_and_rag(db):
    """Verify combined multi-tier hierarchy and multi-scope RAG in a single tutoring turn."""
    engine = TeacherInstructionEngine(db)
    i1 = TeacherInstruction(
        instruction_id="inst-org-01",
        teacher_id="teacher-01",
        organization_id="org-acme",
        course_id="crs-phys-101",
        scope_type="ORGANIZATION",
        instruction_text="Org rule: Encourage active reflection.",
        priority=1,
    )
    i2 = TeacherInstruction(
        instruction_id="inst-course-01",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        scope_type="COURSE",
        instruction_text="Course rule: Use SI units.",
        priority=2,
    )
    engine.add_instruction(i1)
    engine.add_instruction(i2)

    rag_service = RAGService(db)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Physics Text",
        text="# Motion\nVelocity has magnitude and direction in meters per second.",
        source_id="src-phys-text",
    )

    orchestrator = GenericTutorOrchestrator(db=db)
    req = TutorTurnRequest(
        student_id="student-01",
        session_id="sess-mixed-turn",
        course_id="crs-phys-101",
        concept_id="cpt-kinematics",
        message="What are the units of velocity in meters per second?",
    )

    res = orchestrator.execute_turn(req)
    assert res.status == "SUCCESS"
    assert "inst-course-01" in res.applied_instruction_ids
    assert "inst-org-01" in res.applied_instruction_ids
    assert "src-phys-text" in res.contributed_source_ids
    assert len(res.provenance_records) >= 1


# ── Test 11: Course Version Pinning ──────────────────────────────────────────

def test_course_version_pinning(db):
    """Verify that RAG chunks and teacher instructions strictly respect pinned course versions."""
    # Create version 2.0
    v2 = CourseVersion(
        id="ver-2.0",
        course_id="crs-phys-101",
        version_number="2.0",
        status=CourseStatus.PUBLISHED,
    )
    db.create_course_version(v2)

    rag_service = RAGService(db)
    # RAG source pinned to ver-1.0
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Classical Physics Edition 1",
        text="# Version 1\nClassic edition definition of inertia and momentum.",
        course_version_id="ver-1.0",
        source_id="src-v1-text",
    )
    # RAG source pinned to ver-2.0
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Modern Physics Edition 2",
        text="# Version 2\nRevised modern edition definition of inertia and relativistic mass.",
        course_version_id="ver-2.0",
        source_id="src-v2-text",
    )

    # Teacher instruction pinned to ver-1.0
    engine = TeacherInstructionEngine(db)
    inst_v1 = TeacherInstruction(
        instruction_id="inst-v1-only",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        course_version_id="ver-1.0",
        instruction_text="Focus strictly on Newtonian non-relativistic mechanics.",
        priority=3,
        scope_type="COURSE",
    )
    inst_v2 = TeacherInstruction(
        instruction_id="inst-v2-only",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        course_version_id="ver-2.0",
        instruction_text="Introduce relativistic velocity transformations.",
        priority=3,
        scope_type="COURSE",
    )
    engine.add_instruction(inst_v1)
    engine.add_instruction(inst_v2)

    # 1. Query with pinned version ver-1.0
    orchestrator = GenericTutorOrchestrator(db=db)
    req_v1 = TutorTurnRequest(
        student_id="student-01",
        session_id="sess-v1-pin",
        course_id="crs-phys-101",
        course_version_id="ver-1.0",
        message="What is the definition of inertia and velocity?",
    )
    res_v1 = orchestrator.execute_turn(req_v1)

    assert "inst-v1-only" in res_v1.applied_instruction_ids
    assert "inst-v2-only" not in res_v1.applied_instruction_ids
    assert "src-v1-text" in res_v1.contributed_source_ids
    assert "src-v2-text" not in res_v1.contributed_source_ids

    # 2. Query with pinned version ver-2.0
    req_v2 = TutorTurnRequest(
        student_id="student-01",
        session_id="sess-v2-pin",
        course_id="crs-phys-101",
        course_version_id="ver-2.0",
        message="What is the definition of inertia and velocity?",
    )
    res_v2 = orchestrator.execute_turn(req_v2)

    assert "inst-v2-only" in res_v2.applied_instruction_ids
    assert "inst-v1-only" not in res_v2.applied_instruction_ids
    assert "src-v2-text" in res_v2.contributed_source_ids
    assert "src-v1-text" not in res_v2.contributed_source_ids


# ── Test 12: REST API Turn Provenance and Instructions ───────────────────────

def test_rest_api_turn_provenance_and_instructions(db):
    """Verify that /api/v1/tutor/turn returns applied_instruction_ids, contributed_source_ids, and provenance_records."""
    # Seed instruction and RAG source
    engine = TeacherInstructionEngine(db)
    inst = TeacherInstruction(
        instruction_id="inst-api-test",
        teacher_id="teacher-01",
        course_id="crs-phys-101",
        instruction_text="Ask student for units in final response.",
        priority=3,
        scope_type="COURSE",
    )
    engine.add_instruction(inst)

    rag_service = RAGService(db)
    _publish_rag_source(
        rag_service=rag_service,
        course_id="crs-phys-101",
        title="Physics Units Guide",
        text="# Units of Force\nThe SI unit of force is Newton (N), which equals kg*m/s^2.",
        source_id="src-units-guide",
    )

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    from central_platform.auth.tokens import create_access_token
    token = create_access_token(user_id="student-01", role="student")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "student_id": "student-01",
        "session_id": "sess-api-turn-01",
        "course_id": "crs-phys-101",
        "message": "What is the SI unit of force?",
    }

    resp = client.post("/api/v1/tutor/turn", headers=headers, json=payload)
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["status"] == "SUCCESS"
    assert "inst-api-test" in data["applied_instruction_ids"]
    assert "src-units-guide" in data["contributed_source_ids"]
    assert len(data["contributed_chunk_ids"]) >= 1
    assert len(data["provenance_records"]) >= 1
    assert data["provenance_records"][0]["source_id"] == "src-units-guide"
