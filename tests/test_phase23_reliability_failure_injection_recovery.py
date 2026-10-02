"""Phase 23 Test Suite: Reliability, Failure Injection & Recovery.

Governing Document: GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md (Section 12.23)
Plan: docs/reports/PHASE_23_PLAN.md

12 failure-injection test suites proving safe degradation, non-silent failure handling,
observable status, safe user messages, technical diagnostics, retryability, and rollback decisions:
 1. Missing model
 2. Corrupt model
 3. Provider timeout
 4. Provider malformed response
 5. RAG unavailable
 6. DB unavailable
 7. Broken migration
 8. Broken upload
 9. Interrupted publish
10. Expired instruction
11. Duplicate sync
12. App crash mid-turn
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    Organization,
    TeacherInstructionRecord,
    User,
    UserRole,
)
from central_platform.recovery.manager import (
    CommitDecision,
    FailureCategory,
    FailureRecoveryManager,
    RecoveryResult,
    RecoveryStatus,
)
from central_platform.tutor.orchestrator import (
    GenericTutorOrchestrator,
    TutorTurnRequest,
    TutorTurnResult,
)
from central_platform.courses.service import CourseService
from central_platform.sync.service import SyncService
from central_platform.teacher.instruction import (
    TeacherInstruction,
    TeacherInstructionEngine,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def recovery_env():
    """Isolated database and domain services for failure injection testing."""
    db = PlatformDatabase(db_path=":memory:")

    # Seed baseline organization, user, and course
    org = Organization(id="org-rec-01", name="Resilience Academy", slug="rec-academy")
    db.create_organization(org)

    student = User(
        id="usr-rec-student",
        email="student@rec.edu",
        full_name="Reliability Student",
        role=UserRole.STUDENT,
        organization_id="org-rec-01",
    )
    admin = User(
        id="usr-rec-admin",
        email="admin@rec.edu",
        full_name="Reliability Admin",
        role=UserRole.ORG_ADMIN,
        organization_id="org-rec-01",
    )
    db.create_user(student)
    db.create_user(admin)

    course = Course(
        id="crs-rec-101",
        organization_id="org-rec-01",
        code="REL-101",
        title="Software Reliability",
        visibility=CourseVisibility.PUBLIC,
    )
    db.create_course(course)

    enrollment = Enrollment(
        id="enr-rec-01",
        student_id=student.id,
        course_id=course.id,
        is_active=True,
    )
    db.create_enrollment(enrollment)

    return {"db": db, "student": student, "admin": admin, "course": course}


# ── 1. Injected Failure: Missing Model ────────────────────────────────────────

def test_inject_missing_model():
    """Trigger: Primary model weights file not found on disk.
    Expected: Classification=MISSING_MODEL, Status=DEGRADED_FALLBACK, Fallback=LocalSLM,
              safe user message, technical diagnostic, retryable=True, decision=NOOP.
    """
    missing_err = FileNotFoundError("Model file 'models/Qwen2.5-7B-Instruct.gguf' not found.")
    res = FailureRecoveryManager.handle_model_failure(
        error=missing_err,
        is_missing=True,
        model_name="Qwen2.5-7B-Instruct",
    )

    assert res.failure_category == FailureCategory.MISSING_MODEL
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    assert "Qwen2.5-0.5B" in res.fallback_used
    assert "offline" in res.user_message.lower() or "unavailable" in res.user_message.lower()
    assert "Missing model file" in res.technical_diagnostic
    assert res.retryable is True
    assert res.commit_decision == CommitDecision.NOOP

    d = res.to_dict()
    assert d["failure_category"] == "missing_model"
    assert d["status"] == "degraded_fallback"
    assert d["commit_decision"] == "noop"


# ── 2. Injected Failure: Corrupt Model ────────────────────────────────────────

def test_inject_corrupt_model():
    """Trigger: Model file exists but GGUF header checksum or magic bytes are invalid.
    Expected: Classification=CORRUPT_MODEL, Status=DEGRADED_FALLBACK, Fallback=LocalSLM,
              retryable=False (corrupt weights cannot self-heal without redownload), decision=ROLLBACK.
    """
    corrupt_err = ValueError("Invalid GGUF magic bytes: 0xDEADBEEF; checksum mismatch.")
    res = FailureRecoveryManager.handle_model_failure(
        error=corrupt_err,
        is_corrupt=True,
        model_name="Corrupt-Model-v1",
    )

    assert res.failure_category == FailureCategory.CORRUPT_MODEL
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res.retryable is False
    assert res.commit_decision == CommitDecision.ROLLBACK
    assert "Corrupt model weights/checksum" in res.technical_diagnostic
    assert "damaged" in res.user_message.lower() or "switched" in res.user_message.lower()


# ── 3. Injected Failure: Provider Timeout ────────────────────────────────────

def test_inject_provider_timeout():
    """Trigger: Cloud provider API times out after retry exhaustion (e.g. 3 attempts).
    Expected: Classification=PROVIDER_TIMEOUT, Fallback=LocalFirstRouter,
              retryable=True, decision=NOOP, safe user message indicating local tutor fallback.
    """
    timeout_err = TimeoutError("HTTP 504 Gateway Timeout on provider endpoint.")
    res = FailureRecoveryManager.handle_provider_timeout(
        error=timeout_err,
        max_retries=3,
        provider="cloud_openai",
    )

    assert res.failure_category == FailureCategory.PROVIDER_TIMEOUT
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res.fallback_used == "LocalFirstRouter"
    assert res.retryable is True
    assert res.commit_decision == CommitDecision.NOOP
    assert "taking longer than expected" in res.user_message
    assert "Timeout connecting to cloud_openai after 3 retries" in res.technical_diagnostic
    assert res.data["mode"] == "LOCAL_ONLY"


# ── 4. Injected Failure: Provider Malformed Response ─────────────────────────

def test_inject_provider_malformed_response():
    """Trigger: Provider returns malformed output (markdown fences, trailing commas, or raw text).
    Expected: Self-healing JSON repair succeeds for fences and regex, falls back to text wrapper,
              returns status=RECOVERED and decision=COMMIT when self-healed.
    """
    # 4a. Markdown fence with trailing comma
    fenced_raw = "```json\n{\n  \"explanation\": \"Newton third law\",\n  \"confidence\": 0.9,\n}\n```"
    res_fenced = FailureRecoveryManager.repair_malformed_model_output(fenced_raw)
    assert res_fenced.failure_category == FailureCategory.MALFORMED_MODEL_OUTPUT
    assert res_fenced.status == RecoveryStatus.RECOVERED
    assert res_fenced.commit_decision == CommitDecision.COMMIT
    assert res_fenced.data["explanation"] == "Newton third law"
    assert res_fenced.data["confidence"] == 0.9

    # 4b. Regex brace extraction
    brace_raw = "The answer is: {\"summary\": \"Photosynthesis converts light to sugar\"} according to botany."
    res_brace = FailureRecoveryManager.repair_malformed_model_output(brace_raw)
    assert res_brace.status == RecoveryStatus.RECOVERED
    assert res_brace.commit_decision == CommitDecision.COMMIT
    assert res_brace.data["summary"] == "Photosynthesis converts light to sugar"

    # 4c. Completely unrepairable text
    unrepairable_raw = "I am completely unable to produce JSON."
    res_plain = FailureRecoveryManager.repair_malformed_model_output(unrepairable_raw)
    assert res_plain.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res_plain.commit_decision == CommitDecision.ROLLBACK
    assert res_plain.data["text"] == unrepairable_raw


# ── 5. Injected Failure: RAG Unavailable ─────────────────────────────────────

def test_inject_rag_unavailable(recovery_env):
    """Trigger: Vector database connection error or RAG search failure.
    Expected: Classification=RAG_FAILURE, Fallback=CurriculumDirectContext,
              turn continues with syllabus context, retryable=True, decision=NOOP.
    """
    rag_err = ConnectionError("ChromaDB connection refused on port 8000.")
    res = FailureRecoveryManager.handle_rag_failure(
        error=rag_err,
        fallback_concept="Error Handling Patterns",
        course_id=recovery_env["course"].id,
    )

    assert res.failure_category == FailureCategory.RAG_FAILURE
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res.fallback_used == "CurriculumDirectContext"
    assert res.retryable is True
    assert res.commit_decision == CommitDecision.NOOP
    assert "temporarily unreachable" in res.user_message
    assert "ChromaDB connection refused" in res.technical_diagnostic
    assert res.data["rag_active"] is False


# ── 6. Injected Failure: Database Unavailable ────────────────────────────────

def test_inject_database_unavailable():
    """Trigger: Database disk I/O error or SQLite busy/locked state.
    Expected: Classification=DATABASE_FAILURE, Fallback=InMemorySnapshotCache,
              retryable=True, decision=ROLLBACK, uncommitted writes aborted.
    """
    db_err = Exception("database is locked: resource temporarily unavailable")
    snapshot = {"student_id": "usr-rec-student", "active_session": "sess-rec-01"}
    res = FailureRecoveryManager.handle_database_failure(
        error=db_err,
        cached_state=snapshot,
        operation="upsert_mastery_state",
    )

    assert res.failure_category == FailureCategory.DATABASE_FAILURE
    assert res.status == RecoveryStatus.DEGRADED_FALLBACK
    assert res.fallback_used == "InMemorySnapshotCache"
    assert res.retryable is True
    assert res.commit_decision == CommitDecision.ROLLBACK
    assert "temporarily busy" in res.user_message
    assert "upsert_mastery_state failed" in res.technical_diagnostic
    assert res.data["read_only"] is True


# ── 7. Injected Failure: Broken Migration ────────────────────────────────────

def test_inject_broken_migration():
    """Trigger: Migration script syntax error or broken DDL constraint midway through execution.
    Expected: Classification=BROKEN_MIGRATION, Fallback=SchemaRollback, Status=UNRECOVERABLE,
              retryable=False (until script is repaired), decision=ROLLBACK.
    """
    migration_err = RuntimeError("near 'CONSTRAIN': syntax error at line 42")
    res = FailureRecoveryManager.handle_broken_migration(
        error=migration_err,
        migration_version="004",
        script_name="004_add_audit_partitioning.sql",
    )

    assert res.failure_category == FailureCategory.BROKEN_MIGRATION
    assert res.status == RecoveryStatus.UNRECOVERABLE
    assert res.fallback_used == "SchemaRollback"
    assert res.retryable is False
    assert res.commit_decision == CommitDecision.ROLLBACK
    assert "safely preserved without data loss" in res.user_message
    assert "004_add_audit_partitioning.sql" in res.technical_diagnostic


# ── 8. Injected Failure: Broken Upload ───────────────────────────────────────

def test_inject_broken_upload():
    """Trigger: Upload stream truncated unexpectedly or content SHA-256 does not match payload.
    Expected: Classification=BROKEN_UPLOAD, Fallback=UploadBufferPurge,
              retryable=True, decision=ROLLBACK, partial bytes discarded.
    """
    upload_err = IOError("Client disconnected unexpectedly while transmitting multipart chunk.")
    res = FailureRecoveryManager.handle_broken_upload(
        error=upload_err,
        filename="textbook_ch4_physics.pdf",
        partial_bytes=65536,
    )

    assert res.failure_category == FailureCategory.BROKEN_UPLOAD
    assert res.status == RecoveryStatus.UNRECOVERABLE
    assert res.fallback_used == "UploadBufferPurge"
    assert res.retryable is True
    assert res.commit_decision == CommitDecision.ROLLBACK
    assert "interrupted" in res.user_message
    assert "65536 bytes" in res.technical_diagnostic
    assert res.data["partial_bytes"] == 65536


# ── 9. Injected Failure: Interrupted Publish ─────────────────────────────────

def test_inject_interrupted_publish(recovery_env):
    """Trigger: Course version publish fails during audit logging or notification dispatch.
    Expected: Classification=INTERRUPTED_PUBLISH, Fallback=RevertToDraft,
              retryable=True, decision=ROLLBACK, version preserved in DRAFT status.
    """
    db = recovery_env["db"]
    admin = recovery_env["admin"]
    course = recovery_env["course"]
    svc = CourseService(db)

    # Create draft version
    ver = svc.create_course_version(actor=admin, course_id=course.id, version_number="1.0")
    assert ver.status == CourseStatus.DRAFT

    # Simulate crash during audit log recording inside publish
    publish_err = RuntimeError("Audit log persistence service crashed.")
    with patch.object(db, "publish_course_version", side_effect=publish_err):
        with pytest.raises(RuntimeError):
            svc.approve_and_publish_version(actor=admin, version_id=ver.id)

    # Verify version remains safely in DRAFT state — not corrupted
    persisted_ver = db.get_course_version(ver.id)
    assert persisted_ver.status == CourseStatus.DRAFT

    # Verify recovery result directly
    rec = FailureRecoveryManager.handle_interrupted_publish(
        error=publish_err,
        version_id=ver.id,
        course_id=course.id,
        pre_status="DRAFT",
    )
    assert rec.failure_category == FailureCategory.INTERRUPTED_PUBLISH
    assert rec.commit_decision == CommitDecision.ROLLBACK
    assert rec.retryable is True
    assert "preserved in its previous state" in rec.user_message


# ── 10. Injected Failure: Expired Instruction ────────────────────────────────

def test_inject_expired_instruction(recovery_env):
    """Trigger: Teacher instruction with expires_at in the past is evaluated during context resolution.
    Expected: Instruction marked EXPIRED (is_active=False), excluded from candidate directives,
              Classification=EXPIRED_INSTRUCTION, decision=NOOP.
    """
    db = recovery_env["db"]
    course = recovery_env["course"]
    engine = TeacherInstructionEngine(db)

    past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    expired_inst = TeacherInstructionRecord(
        id="inst-expired-001",
        teacher_id="usr-rec-admin",
        course_id=course.id,
        organization_id=course.organization_id,
        instruction_text="Focus on basic loop syntax.",
        expires_at=past_time,
        is_active=True,
    )
    db.create_teacher_instruction(expired_inst)

    # Resolve instructions with current time
    resolved = engine.resolve_hierarchical_instructions(
        course_id=course.id,
        organization_id=course.organization_id,
    )

    # Expired instruction must NOT be in active resolved directives
    assert not any(i.instruction_id == "inst-expired-001" or getattr(i, "id", None) == "inst-expired-001" for i in resolved), (
        "Expired instruction must be excluded from active pedagogical context."
    )

    # Verify recovery result
    rec = FailureRecoveryManager.handle_expired_instruction(
        instruction_id="inst-expired-001",
        course_id=course.id,
        expires_at=past_time,
    )
    assert rec.failure_category == FailureCategory.EXPIRED_INSTRUCTION
    assert rec.status == RecoveryStatus.RECOVERED
    assert rec.commit_decision == CommitDecision.NOOP
    assert rec.retryable is False
    assert "safely excluded" in rec.user_message


# ── 11. Injected Failure: Duplicate Sync ─────────────────────────────────────

def test_inject_duplicate_sync(recovery_env):
    """Trigger: Client resends an identical batch with the same operation_id.
    Expected: Classification=DUPLICATE_SYNC, status=RECOVERED, decision=NOOP,
              idempotent receipt returned without duplicating events.
    """
    db = recovery_env["db"]
    student = recovery_env["student"]
    course = recovery_env["course"]
    sync_svc = SyncService(db=db)

    events = [
        {
            "event_id": "evt-dup-101",
            "event_type": "turn_completed",
            "concept_id": "concept-async-io",
            "timestamp": "2026-10-02T10:00:00Z",
        }
    ]

    # First execution
    res1 = sync_svc.process_sync_batch(
        student_id=student.id,
        events=events,
        course_id=course.id,
        operation_id="op-dup-test-01",
    )
    assert res1["ok"] is True
    assert res1["synced_count"] == 1
    assert res1["is_replay"] is False

    # Second execution (duplicate sync replay)
    res2 = sync_svc.process_sync_batch(
        student_id=student.id,
        events=events,
        course_id=course.id,
        operation_id="op-dup-test-01",
    )
    assert res2["ok"] is True
    assert res2["is_replay"] is True
    assert "recovery" in res2
    assert res2["recovery"]["failure_category"] == "duplicate_sync"
    assert res2["recovery"]["commit_decision"] == "noop"
    assert res2["recovery"]["retryable"] is False

    # Verify database was NOT duplicated
    all_events = db.query_learning_events(student_id=student.id, course_id=course.id)
    assert len(all_events) == 1, "Duplicate sync must not insert duplicate events."


# ── 12. Injected Failure: App Crash Mid-Turn ─────────────────────────────────

def test_inject_app_crash_mid_turn(recovery_env):
    """Trigger: Unhandled exception occurs during step 12/13 of tutor turn lifecycle.
    Expected: Handled via handle_crash_mid_turn, status=CRASH_RECOVERED,
              state_committed=False, safe user message, technical diagnostic logged,
              zero orphaned learning events or partial mastery in database.
    """
    db = recovery_env["db"]
    student = recovery_env["student"]
    course = recovery_env["course"]
    orchestrator = GenericTutorOrchestrator(db=db)

    turn_req = TutorTurnRequest(
        student_id=student.id,
        session_id="sess-crash-001",
        course_id=course.id,
        message="Explain deadlock prevention in distributed systems.",
    )

    # Inject crash during AI execution
    crash_error = MemoryError("CUDA out of host memory allocating attention buffer.")
    with patch.object(orchestrator.ai_gateway, "execute", side_effect=crash_error):
        result: TutorTurnResult = orchestrator.execute_turn(turn_req)

    # 1. Turn must NOT raise unhandled 500 — must recover gracefully
    assert result.status == "CRASH_RECOVERED"
    assert result.validation_passed is False
    assert result.state_committed is False
    assert result.pedagogical_action == "SAFE_ERROR_RECOVERY"
    assert "interruption occurred" in result.response_text.lower() or "preserved" in result.response_text.lower()

    # 2. Technical diagnostic must be captured in validation_issues
    assert len(result.validation_issues) >= 1
    issue = result.validation_issues[0]
    assert issue["code"] == "APP_CRASH_MID_TURN"
    assert "CUDA out of host memory" in issue["message"]

    # 3. State integrity verification: zero orphaned events in DB
    events = db.query_learning_events(student_id=student.id, course_id=course.id)
    assert len(events) == 0, "Crashed turn must rollback all state changes — 0 events committed."

    # 4. RecoveryResult contract verification
    rec = FailureRecoveryManager.handle_crash_mid_turn(
        error=crash_error,
        turn_id=result.turn_id,
        student_id=student.id,
        step="ORCHESTRATOR_EXECUTE_TURN",
    )
    assert rec.failure_category == FailureCategory.APP_CRASH_MID_TURN
    assert rec.status == RecoveryStatus.DEGRADED_FALLBACK
    assert rec.retryable is True
    assert rec.commit_decision == CommitDecision.ROLLBACK
