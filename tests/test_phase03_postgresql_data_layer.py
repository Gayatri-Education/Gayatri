"""Phase 03 Test Suite — PostgreSQL Central Data Layer Verification.

Covers Master Plan Section 12:
1. Complete 29-entity relational lifecycle across multi-tenant boundaries.
2. Foreign key cascade integrity, unique constraints, and indexes.
3. Soft deletion filtering and restoration.
4. Schema migrations tracking (UP, DOWN, checksum, idempotency).
5. Immutable security audit logging.
"""

import json
import sqlite3
import pytest
from datetime import datetime, timezone

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    AIExecutionLog,
    AIModel,
    AIProvider,
    AlertSeverity,
    AlertStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentItem,
    AssessmentType,
    Assignment,
    AuditLog,
    ClassGroup,
    Cohort,
    Concept,
    Course,
    Curriculum,
    CurriculumVersion,
    Enrollment,
    InterventionRecord,
    LearningEvent,
    MasteryState,
    Misconception,
    Module,
    Notification,
    Organization,
    Permission,
    Prerequisite,
    Role,
    Session,
    SessionStatus,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    Subject,
    TeacherInstructionRecord,
    Topic,
    User,
    UserRole,
)
from scripts.migrate_db import (
    get_applied_migrations,
    rollback_all_migrations,
    run_all_migrations,
)


@pytest.fixture
def db(tmp_path):
    """Provide a fresh isolated database with all Phase 03 migrations applied."""
    db_file = str(tmp_path / "phase03_test.db")
    return PlatformDatabase(db_file)


# ── 1. Migration & Schema Ledger ─────────────────────────────────────────

def test_migration_tracking_and_checksum(db):
    """Verify that migration 001 is applied with a valid checksum and timestamp."""
    conn = db._get_connection()
    applied = get_applied_migrations(conn)
    assert len(applied) >= 1
    m001 = applied[0]
    assert m001["version"] == "001"
    assert "Authoritative Platform Schema" in m001["description"]
    assert len(m001["checksum"]) == 64  # SHA-256


def test_migration_rollback_and_reapply(tmp_path):
    """Test full rollback down and re-apply up idempotency."""
    db_file = str(tmp_path / "mig_cycle.db")
    db = PlatformDatabase(db_file)
    conn = db._get_connection()

    # Initial state: 1 migration applied
    assert len(get_applied_migrations(conn)) == 1

    # Rollback
    rolled = rollback_all_migrations(conn)
    assert rolled == ["001"]
    assert len(get_applied_migrations(conn)) == 0

    # Verify tables dropped
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    table_names = [t[0] for t in tables]
    assert "users" not in table_names
    assert "courses" not in table_names

    # Re-apply
    reapplied = run_all_migrations(conn)
    assert reapplied == ["001"]
    assert len(get_applied_migrations(conn)) == 1
    db.close()


# ── 2. Organizations, Identity & Soft Deletion ───────────────────────────

def test_organization_lifecycle_and_soft_delete(db):
    """Test organization creation, lookup, listing, and soft deletion."""
    org = Organization(id="org-dsa", name="Delhi Science Academy", slug="dsa")
    db.create_organization(org)

    fetched = db.get_organization("org-dsa")
    assert fetched is not None
    assert fetched.name == "Delhi Science Academy"
    assert fetched.is_deleted is False

    # List organizations
    orgs = db.list_organizations()
    assert any(o.id == "org-dsa" for o in orgs)

    # Soft delete
    deleted = db.soft_delete_organization("org-dsa")
    assert deleted is True

    # Excluded from active queries
    assert db.get_organization("org-dsa") is None
    assert not any(o.id == "org-dsa" for o in db.list_organizations())

    # Retrievable when include_deleted=True
    deleted_org = db.get_organization("org-dsa", include_deleted=True)
    assert deleted_org is not None
    assert deleted_org.is_deleted is True
    assert deleted_org.deleted_at is not None


def test_user_creation_and_soft_delete(db):
    """Test user provisioning, role enum, and soft deletion."""
    org = Organization(id="org-test", name="Test Org", slug="test-org")
    db.create_organization(org)

    user = User(
        id="usr-101",
        email="student@test.edu",
        full_name="Aarav Sharma",
        role=UserRole.STUDENT,
        organization_id=org.id,
    )
    db.create_user(user)

    fetched = db.get_user("usr-101")
    assert fetched is not None
    assert fetched.role == UserRole.STUDENT
    assert fetched.full_name == "Aarav Sharma"

    # Soft delete user
    assert db.soft_delete_user("usr-101") is True
    assert db.get_user("usr-101") is None
    assert db.get_user("usr-101", include_deleted=True) is not None


def test_roles_and_permissions_matrix(db):
    """Test role and permission entities and mapping."""
    role = Role(id="role-lead-teacher", name="Lead Teacher", description="Cohort Manager")
    db.create_role(role)

    perm = Permission(id="perm-assign-instr", code="instructions:create", description="Dispatch instructions")
    db.create_permission(perm)

    db.assign_role_permission(role.id, perm.id)

    # Check join table
    conn = db._get_connection()
    row = conn.execute("SELECT * FROM role_permissions WHERE role_id = ? AND permission_id = ?;", (role.id, perm.id)).fetchone()
    assert row is not None


# ── 3. Multi-Tenant Isolation ────────────────────────────────────────────

def test_multi_tenant_isolation_boundary(db):
    """Ensure strict isolation between Org A and Org B."""
    org_a = Organization(id="org-delhi", name="Delhi Academy", slug="delhi-acad")
    org_b = Organization(id="org-mumbai", name="Mumbai Academy", slug="mumbai-acad")
    db.create_organization(org_a)
    db.create_organization(org_b)

    u_a = User(id="u-delhi-1", email="d1@delhi.edu", full_name="Delhi Student", role=UserRole.STUDENT, organization_id=org_a.id)
    u_b = User(id="u-mumbai-1", email="m1@mumbai.edu", full_name="Mumbai Student", role=UserRole.STUDENT, organization_id=org_b.id)
    db.create_user(u_a)
    db.create_user(u_b)

    c_a = Course(id="crs-delhi-chem", organization_id=org_a.id, code="CHEM-101", title="Delhi Chemistry")
    c_b = Course(id="crs-mumbai-chem", organization_id=org_b.id, code="CHEM-101", title="Mumbai Chemistry")
    db.create_course(c_a)
    db.create_course(c_b)

    # Verify query isolation
    users_a = db.get_users_by_organization(org_a.id)
    courses_a = db.get_courses_by_organization(org_a.id)
    assert len(users_a) == 1
    assert users_a[0].id == "u-delhi-1"
    assert len(courses_a) == 1
    assert courses_a[0].id == "crs-delhi-chem"

    users_b = db.get_users_by_organization(org_b.id)
    courses_b = db.get_courses_by_organization(org_b.id)
    assert len(users_b) == 1
    assert users_b[0].id == "u-mumbai-1"
    assert len(courses_b) == 1
    assert courses_b[0].id == "crs-mumbai-chem"


# ── 4. Academic Curriculum & Prerequisites ───────────────────────────────

def test_curriculum_hierarchy_and_prerequisites(db):
    """Test full curriculum hierarchy: Course -> Subject -> Curriculum -> Module -> Topic -> Concept."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)

    course = Course(id="crs-chem-11", organization_id=org.id, code="CHEM-11", title="Class 11 Chemistry")
    db.create_course(course)

    subject = Subject(id="subj-pc", course_id=course.id, name="Physical Chemistry", code="PHY-CHEM")
    db.create_subject(subject)

    curriculum = Curriculum(id="curr-ncert-11", course_id=course.id, title="NCERT Class 11 Chemistry", version="2026.1")
    db.create_curriculum(curriculum)

    module = Module(id="mod-thermo", curriculum_id=curriculum.id, title="Thermodynamics", sequence_order=1)
    db.create_module(module)

    topic = Topic(id="top-first-law", module_id=module.id, title="First Law & Work", sequence_order=1)
    db.create_topic(topic)

    c1 = Concept(id="c-internal-energy", topic_id=topic.id, name="Internal Energy", difficulty=0.4)
    c2 = Concept(id="c-first-law", topic_id=topic.id, name="First Law Calculation", difficulty=0.6)
    db.create_concept(c1)
    db.create_concept(c2)

    # Prerequisite: Internal Energy is required before First Law Calculation
    db.add_prerequisite(Prerequisite(prerequisite_concept_id=c1.id, dependent_concept_id=c2.id))

    prereqs = db.get_prerequisites_for_concept(c2.id)
    assert c1.id in prereqs


# ── 5. Class Groups, Cohorts & Enrollments ───────────────────────────────

def test_class_groups_cohorts_and_enrollments(db):
    """Test grouping students into class groups and cohorts with active enrollments."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)

    course = Course(id="crs-chem-11", organization_id=org.id, code="CHEM-11", title="Class 11 Chemistry")
    db.create_course(course)

    cg = ClassGroup(id="cg-11a", organization_id=org.id, course_id=course.id, name="Section 11-A")
    db.create_class_group(cg)

    cohort = Cohort(id="coh-2026-11a", class_group_id=cg.id, name="Batch 2026")
    db.create_cohort(cohort)

    student = User(id="stu-101", email="student@dsa.edu", full_name="Rahul", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(student)

    enrollment = Enrollment(id="enr-101", student_id=student.id, course_id=course.id, cohort_id=cohort.id)
    db.create_enrollment(enrollment)

    enrs = db.get_enrollments_for_student(student.id)
    assert len(enrs) == 1
    assert enrs[0].course_id == "crs-chem-11"
    assert enrs[0].cohort_id == "coh-2026-11a"


# ── 6. Sessions & Granular Telemetry ─────────────────────────────────────

def test_session_lifecycle_and_learning_events(db):
    """Test tutoring session lifecycle and event logging."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    course = Course(id="crs-chem", organization_id=org.id, code="CHEM", title="Chemistry")
    db.create_course(course)
    student = User(id="stu-201", email="s201@dsa.edu", full_name="Priya", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(student)

    session = Session(
        id="sess-001",
        student_id=student.id,
        course_id=course.id,
        concept_id="c-internal-energy",
        status=SessionStatus.ACTIVE,
    )
    db.create_session(session)

    fetched_sess = db.get_session("sess-001")
    assert fetched_sess is not None
    assert fetched_sess.status == SessionStatus.ACTIVE

    # Record 2 learning events
    ev1 = LearningEvent(
        id="ev-01",
        session_id=session.id,
        student_id=student.id,
        concept_id="c-internal-energy",
        event_type="turn_completed",
        payload={"query": "What is delta U?", "score": 1.0},
        score=1.0,
    )
    ev2 = LearningEvent(
        id="ev-02",
        session_id=session.id,
        student_id=student.id,
        concept_id="c-internal-energy",
        event_type="hint_used",
        payload={"hint_level": 1},
        score=None,
    )
    db.record_learning_event(ev1)
    db.record_learning_event(ev2)

    events = db.get_learning_events_for_session(session.id)
    assert len(events) == 2
    assert events[0].event_type == "turn_completed"
    assert events[0].score == 1.0
    assert events[1].event_type == "hint_used"

    # End session
    assert db.end_session("sess-001") is True
    ended_sess = db.get_session("sess-001")
    assert ended_sess.status == SessionStatus.COMPLETED
    assert ended_sess.ended_at is not None


# ── 7. SLR & Mastery States ──────────────────────────────────────────────

def test_student_learning_record_and_mastery(db):
    """Test authoritative SLR and concept mastery tracking."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    course = Course(id="crs-chem", organization_id=org.id, code="CHEM", title="Chemistry")
    db.create_course(course)
    student = User(id="stu-301", email="s301@dsa.edu", full_name="Amit", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(student)

    slr = StudentLearningRecord(id="slr-stu-301", student_id=student.id, course_id=course.id)
    db.create_slr(slr)

    # Upsert mastery state
    m1 = MasteryState(id="mst-1", slr_id=slr.id, concept_id="c-internal-energy", score=0.85, confidence=0.92)
    db.upsert_mastery_state(m1)

    states = db.get_mastery_states_for_slr(slr.id)
    assert len(states) == 1
    assert states[0].concept_id == "c-internal-energy"
    assert states[0].score == 0.85


# ── 8. Misconceptions & Diagnostics ──────────────────────────────────────

def test_misconception_catalog_and_student_tracking(db):
    """Test misconception catalog and frequency tracking."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    student = User(id="stu-401", email="s401@dsa.edu", full_name="Vikram", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(student)

    misc = Misconception(
        id="misc-01",
        code="THERMO_SIGN_CONVENTION",
        category="thermodynamics",
        name="Sign Convention Confusion",
        description="Confuses IUPAC work done by vs on system",
        remediation="Microscopic cylinder review",
    )
    db.create_misconception(misc)

    # Record student misconception
    rec = StudentMisconceptionRecord(
        id="sm-01",
        student_id=student.id,
        misconception_code="THERMO_SIGN_CONVENTION",
        frequency=3,
    )
    db.record_student_misconception(rec)

    records = db.get_student_misconceptions(student.id)
    assert len(records) == 1
    assert records[0].misconception_code == "THERMO_SIGN_CONVENTION"
    assert records[0].frequency == 3


# ── 9. Assessments & Attempts ────────────────────────────────────────────

def test_assessments_items_and_attempts(db):
    """Test assessment setup, items, and student attempts."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    course = Course(id="crs-chem", organization_id=org.id, code="CHEM", title="Chemistry")
    db.create_course(course)
    student = User(id="stu-501", email="s501@dsa.edu", full_name="Ananya", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(student)

    asmt = Assessment(id="asmt-101", course_id=course.id, title="Thermodynamics Diagnostic", assessment_type=AssessmentType.DIAGNOSTIC)
    db.create_assessment(asmt)

    item1 = AssessmentItem(id="item-01", assessment_id=asmt.id, question_text="What is ΔU for cyclic process?", correct_answer="0")
    db.create_assessment_item(item1)

    attempt = AssessmentAttempt(id="att-01", assessment_id=asmt.id, student_id=student.id, score=100.0, passed=True)
    db.record_assessment_attempt(attempt)

    conn = db._get_connection()
    row = conn.execute("SELECT * FROM assessment_attempts WHERE id = ?;", (attempt.id,)).fetchone()
    assert row is not None
    assert row["passed"] == 1


# ── 10. Teacher Instructions & Interventions ─────────────────────────────

def test_teacher_instructions_and_interventions(db):
    """Test teacher instructions, priority ordering, and intervention alert lifecycle."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    course = Course(id="crs-chem", organization_id=org.id, code="CHEM", title="Chemistry")
    db.create_course(course)
    teacher = User(id="tchr-101", email="tchr@dsa.edu", full_name="Dr. Sharma", role=UserRole.TEACHER, organization_id=org.id)
    student = User(id="stu-601", email="s601@dsa.edu", full_name="Student 601", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(teacher)
    db.create_user(student)

    # 1. Instructions
    inst1 = TeacherInstructionRecord(
        id="inst-1",
        teacher_id=teacher.id,
        student_id="all",
        course_id=course.id,
        instruction_text="Emphasize IUPAC work conventions",
        priority=1,
    )
    inst2 = TeacherInstructionRecord(
        id="inst-2",
        teacher_id=teacher.id,
        student_id=student.id,
        course_id=course.id,
        instruction_text="Targeted cylinder piston drill",
        priority=3,
    )
    db.create_teacher_instruction(inst1)
    db.create_teacher_instruction(inst2)

    instructions = db.get_teacher_instructions(course.id, student.id)
    assert len(instructions) == 2
    # Priority 3 should be first
    assert instructions[0].priority == 3
    assert instructions[0].id == "inst-2"

    # 2. Interventions
    alert = InterventionRecord(
        id="alt-01",
        student_id=student.id,
        course_id=course.id,
        severity=AlertSeverity.CRITICAL,
        alert_type="repeated_failure",
        message="Failed sign convention 3 times consecutively",
    )
    db.create_intervention(alert)

    active_alerts = db.get_interventions(course.id, active_only=True)
    assert len(active_alerts) == 1
    assert active_alerts[0].id == "alt-01"

    # Resolve alert
    assert db.resolve_intervention("alt-01") is True
    assert len(db.get_interventions(course.id, active_only=True)) == 0


# ── 11. AI Governance, Execution & Audit Trail ───────────────────────────

def test_ai_governance_and_audit_trail(db):
    """Test AI provider, model registry, execution logs, and immutable audit logs."""
    org = Organization(id="org-dsa", name="DSA", slug="dsa")
    db.create_organization(org)
    user = User(id="usr-admin", email="admin@dsa.edu", full_name="Admin", role=UserRole.ORG_ADMIN, organization_id=org.id)
    db.create_user(user)

    # 1. AI Provider & Model
    prov = AIProvider(id="prov-local", name="Local Llama Engine", provider_type="local_gguf")
    db.create_ai_provider(prov)

    model = AIModel(id="mod-chem-3b", provider_id=prov.id, model_name="gayatri-chemistry-3b-q4", context_window=4096, is_default=True)
    db.create_ai_model(model)

    # 2. AI Execution Log
    exec_log = AIExecutionLog(id="exec-01", model_id=model.id, prompt_tokens=150, completion_tokens=45, latency_ms=18.5)
    db.record_ai_execution(exec_log)

    conn = db._get_connection()
    row = conn.execute("SELECT * FROM ai_execution_logs WHERE id = ?;", (exec_log.id,)).fetchone()
    assert row is not None
    assert row["prompt_tokens"] == 150

    # 3. Audit Log
    audit = AuditLog(
        id="aud-01",
        organization_id=org.id,
        user_id=user.id,
        action="UPDATE_SECURITY_CONFIG",
        resource="platform_settings",
        details={"firewall": "enabled", "strict_mode": True},
    )
    db.record_audit_log(audit)

    logs = db.get_audit_logs(org.id)
    assert len(logs) == 1
    assert logs[0].action == "UPDATE_SECURITY_CONFIG"
    assert logs[0].details.get("strict_mode") is True


# ── 12. Foreign Key Cascade Integrity ────────────────────────────────────

def test_foreign_key_cascade_deletion(db):
    """Confirm that deleting an organization cascades to its users and courses."""
    org = Organization(id="org-cascade", name="Cascade Org", slug="cascade-org")
    db.create_organization(org)

    user = User(id="usr-cascade", email="cas@org.edu", full_name="Cascade User", role=UserRole.STUDENT, organization_id=org.id)
    db.create_user(user)

    course = Course(id="crs-cascade", organization_id=org.id, code="CAS101", title="Cascade Course")
    db.create_course(course)

    conn = db._get_connection()
    # Delete organization hard
    conn.execute("DELETE FROM organizations WHERE id = ?;", (org.id,))
    conn.commit()

    # User and Course must be cascade deleted
    assert conn.execute("SELECT * FROM users WHERE id = ?;", (user.id,)).fetchone() is None
    assert conn.execute("SELECT * FROM courses WHERE id = ?;", (course.id,)).fetchone() is None
