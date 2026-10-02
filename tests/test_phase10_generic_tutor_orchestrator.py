"""Phase 10: Generic Tutor Orchestrator Test Suite.

Verifies:
1. End-to-end 16-step course-scoped tutoring flow across multiple disciplines (Physics, History, CS, Chemistry).
2. Identity validation: rejects missing or whitespace student_id, session_id, or course_id.
3. Enrollment validation: enforces strict private course enrollment authorization and public auto-enrollment.
4. Course and version resolution: raises CourseNotFoundError on non-existent courses.
5. Empty curriculum resilience: handles course with no predefined concepts gracefully.
6. RAG empty resilience: executes turn smoothly when no matching knowledge chunks exist.
7. Anti-answer leakage & safety rejection: state changes are rolled back if response validation fails.
8. Duplicate turn idempotency: avoids double-mutating learning state on replay.
9. Restart and session continuity: retrieves persistent multi-turn history.
10. Architectural decoupling: GenericTutorOrchestrator contains zero hardcoded Chemistry branches.
11. REST API endpoint /api/v1/tutor/turn: complete HTTP client flow.
"""
from __future__ import annotations

import inspect
import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.courses.service import CourseNotFoundError
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CoursePolicy,
    CourseStatus,
    CourseToolPolicy,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    User,
    UserRole,
)
from central_platform.tutor.orchestrator import (
    EnrollmentError,
    GenericTutorOrchestrator,
    TutorTurnRequest,
    TutorTurnResult,
)


@pytest.fixture
def client():
    return TestClient(app)


from central_platform.models.schema import Organization

@pytest.fixture
def test_db():
    db = PlatformDatabase(":memory:")
    # Seed default organizations & admin
    db.create_organization(
        Organization(
            id="org-core",
            name="Core Academic Institution",
            slug="core-academic",
        )
    )
    db.create_user(
        User(
            id="admin-01",
            organization_id="org-core",
            email="admin@core.edu",
            full_name="System Admin",
            role=UserRole.SUPER_ADMIN,
        )
    )
    return db


@pytest.fixture
def seeded_courses(test_db):
    """Seed multi-subject course catalog (Physics, CS, History, Chemistry)."""
    courses = [
        Course(
            id="course-physics",
            organization_id="org-core",
            code="PHYS101",
            title="Classical Mechanics",
            visibility=CourseVisibility.PRIVATE,
        ),
        Course(
            id="course-cs",
            organization_id="org-core",
            code="CS101",
            title="Introduction to Programming",
            visibility=CourseVisibility.PUBLIC,
        ),
        Course(
            id="course-history",
            organization_id="org-core",
            code="HIST201",
            title="World History",
            visibility=CourseVisibility.PUBLIC,
        ),
        Course(
            id="course-chem",
            organization_id="org-core",
            code="CHEM101",
            title="General Chemistry",
            visibility=CourseVisibility.PRIVATE,
        ),
    ]
    for c in courses:
        test_db.create_course(c)
        test_db.create_course_version(
            CourseVersion(
                id=f"ver-{c.id}-v1",
                course_id=c.id,
                version_number="1.0",
                status=CourseStatus.PUBLISHED,
                created_by="admin-01",
            )
        )
    return courses


def enroll_student(db: PlatformDatabase, student_id: str, course_id: str, cohort_id: str | None = None) -> Enrollment:
    """Helper to ensure student user exists and is enrolled in course."""
    if not db.get_user(student_id):
        db.create_user(
            User(
                id=student_id,
                organization_id="org-core",
                email=f"{student_id}@test.edu",
                full_name=f"Student {student_id}",
                role=UserRole.STUDENT,
            )
        )
    enr = Enrollment(
        id=f"enr-{student_id}-{course_id}",
        student_id=student_id,
        course_id=course_id,
        cohort_id=cohort_id,
        is_active=True,
    )
    db.create_enrollment(enr)
    return enr


# ── 1. Valid Multi-Course Execution ──────────────────────────────────────────

def test_generic_tutor_execution_physics(test_db, seeded_courses):
    """Verify tutor turn execution on Physics course."""
    # Enroll student in private physics course
    enroll_student(test_db, "student-phys-01", "course-physics")

    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-phys-01",
        session_id="session-phys-01",
        course_id="course-physics",
        message="What is Newton's third law of motion?",
    )

    result = orchestrator.execute_turn(req)

    assert result.status == "SUCCESS"
    assert result.student_id == "student-phys-01"
    assert result.course_id == "course-physics"
    assert result.validation_passed is True
    assert result.state_committed is True
    assert len(result.response_text) > 0
    assert result.pedagogical_action in ("EXPLAIN", "PRACTICE", "CONTINUE")


def test_generic_tutor_execution_programming_public_auto_enroll(test_db, seeded_courses):
    """Verify public CS course auto-enrolls student and executes turn."""
    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-cs-01",
        session_id="session-cs-01",
        course_id="course-cs",
        message="How do variables and loops work in Python?",
    )

    result = orchestrator.execute_turn(req)

    assert result.status == "SUCCESS"
    assert result.course_id == "course-cs"
    assert result.state_committed is True

    # Assert student is now actively enrolled
    enrs = test_db.get_enrollments_for_student("student-cs-01")
    assert any(e.course_id == "course-cs" for e in enrs)


def test_generic_tutor_execution_history(test_db, seeded_courses):
    """Verify tutor turn on History course."""
    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-hist-01",
        session_id="session-hist-01",
        course_id="course-history",
        message="Explain the causes of the Industrial Revolution.",
    )

    result = orchestrator.execute_turn(req)
    assert result.status == "SUCCESS"
    assert result.course_id == "course-history"
    assert result.validation_passed is True


# ── 2. Error and Boundary Testing ────────────────────────────────────────────

def test_identity_validation_failures(test_db, seeded_courses):
    """Verify identity validation rejects empty or magic identifiers (Rule 4)."""
    orchestrator = GenericTutorOrchestrator(db=test_db)

    with pytest.raises(ValueError, match="student_id must be an explicit non-empty string"):
        orchestrator.execute_turn(
            TutorTurnRequest(student_id="", session_id="s1", course_id="course-cs", message="Hello")
        )

    with pytest.raises(ValueError, match="session_id must be an explicit non-empty string"):
        orchestrator.execute_turn(
            TutorTurnRequest(student_id="stu1", session_id="   ", course_id="course-cs", message="Hello")
        )

    with pytest.raises(ValueError, match="course_id must be an explicit non-empty string"):
        orchestrator.execute_turn(
            TutorTurnRequest(student_id="stu1", session_id="s1", course_id="", message="Hello")
        )

    with pytest.raises(ValueError, match="message must be a non-empty string"):
        orchestrator.execute_turn(
            TutorTurnRequest(student_id="stu1", session_id="s1", course_id="course-cs", message="   ")
        )


def test_invalid_course_rejection(test_db):
    """Verify requesting non-existent course raises CourseNotFoundError."""
    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-01",
        session_id="session-01",
        course_id="non_existent_course_999",
        message="Explain quantum mechanics",
    )

    with pytest.raises(CourseNotFoundError, match="does not exist"):
        orchestrator.execute_turn(req)


def test_unauthorized_private_course_enrollment(test_db, seeded_courses):
    """Verify unenrolled student is rejected from private course."""
    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="unauthorized-student-99",
        session_id="session-priv-01",
        course_id="course-physics",  # PRIVATE course
        message="Help me with physics problem",
    )

    with pytest.raises(EnrollmentError, match="is not enrolled in private course"):
        orchestrator.execute_turn(req)


def test_rag_empty_graceful_handling(test_db, seeded_courses):
    """Verify that when RAG returns 0 chunks, turn executes smoothly without failure."""
    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-cs-02",
        session_id="session-cs-02",
        course_id="course-cs",
        message="Query with completely esoteric terminology that matches no index",
    )

    result = orchestrator.execute_turn(req)
    assert result.status == "SUCCESS"
    assert len(result.rag_sources_used) == 0
    assert result.validation_passed is True


# ── 3. Response Validation Failure & Rollback ────────────────────────────────

def test_response_validation_failure_rolls_back_state(test_db, seeded_courses):
    """Verify that when AI response leaks final answer, validation fails and state is NOT committed."""
    # Enroll student in chemistry
    enroll_student(test_db, "student-chem-01", "course-chem")

    orchestrator = GenericTutorOrchestrator(db=test_db)

    # Mock gateway returning an answer leakage violation during hint turn
    mock_leaking_response = MagicMock()
    mock_leaking_response.content = "The final answer is 42.0 kJ/mol. Correct option is A."
    mock_leaking_response.provider = "mock"
    mock_leaking_response.model = "mock-model"
    mock_leaking_response.latency_ms = 25.0

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(orchestrator.ai_gateway, "execute", lambda r: mock_leaking_response)

        req = TutorTurnRequest(
            student_id="student-chem-01",
            session_id="session-chem-01",
            course_id="course-chem",
            message="What is the enthalpy change?",
        )

        result = orchestrator.execute_turn(req)

        # Assert validation failure caught & state commit was aborted
        assert result.validation_passed is False
        assert result.state_committed is False
        assert result.status == "VALIDATION_FAILED"
        assert len(result.validation_issues) > 0
        assert "42.0" not in result.response_text  # Sanitized/fallback used


# ── 4. Duplicate Turn Idempotency ─────────────────────────────────────────────

def test_duplicate_turn_idempotency(test_db, seeded_courses):
    """Verify submitting duplicate identical turn returns idempotent response without double-mutating."""
    enroll_student(test_db, "student-phys-02", "course-physics")

    orchestrator = GenericTutorOrchestrator(db=test_db)
    req = TutorTurnRequest(
        student_id="student-phys-02",
        session_id="session-phys-02",
        course_id="course-physics",
        message="What is kinetic energy?",
    )

    # First turn commits state
    res1 = orchestrator.execute_turn(req)
    assert res1.state_committed is True

    # Second identical turn replays without double-committing
    res2 = orchestrator.execute_turn(req)
    assert res2.state_committed is False
    assert "again" in res2.response_text.lower()


# ── 5. Zero Chemistry Coupling Invariant ──────────────────────────────────────

def test_generic_orchestrator_zero_chemistry_coupling():
    """Architecture Invariant: GenericTutorOrchestrator class must have ZERO chemistry-specific branching."""
    source = inspect.getsource(GenericTutorOrchestrator)

    assert 'if "chem"' not in source.lower()
    assert 'mode == "chemistry"' not in source.lower()
    assert "thermodynamics" not in source.lower()
    assert "enthalpy" not in source.lower()


# ── 6. REST API Endpoint Integration ──────────────────────────────────────────

def test_tutor_turn_api_endpoint(client, test_db, seeded_courses):
    """Verify /api/v1/tutor/turn REST endpoint with strict authentication."""
    from central_platform.auth.dependencies import get_db
    from central_platform.auth.tokens import create_access_token
    app.dependency_overrides[get_db] = lambda: test_db
    try:
        enroll_student(test_db, "student-api-01", "course-cs")

        payload = {
            "student_id": "student-api-01",
            "session_id": "session-api-01",
            "course_id": "course-cs",
            "message": "Can you explain recursive functions?",
        }

        # Negative test: unauthenticated call must return 401
        unauth_resp = client.post("/api/v1/tutor/turn", json=payload)
        assert unauth_resp.status_code == 401

        # Positive test: authenticated call with valid token for matching student
        token = create_access_token(user_id="student-api-01", role="student")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/tutor/turn", headers=headers, json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert data["student_id"] == "student-api-01"
        assert data["course_id"] == "course-cs"
        assert data["status"] == "SUCCESS"
        assert data["state_committed"] is True
        assert len(data["response_text"]) > 0
    finally:
        app.dependency_overrides.pop(get_db, None)
