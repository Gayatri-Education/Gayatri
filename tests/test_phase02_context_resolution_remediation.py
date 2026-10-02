"""Phase 02 Forensic Remediation Test Suite — Course, Enrollment, Version, and Context Resolution.

Audit Basis:
- Finding F-003 (P1): Tutor can create users/sessions/enrollments automatically.
- Finding F-010 (P1): Context failures are swallowed and tutor continues.
- Finding F-023 (P1): Missing learner/course context can be synthesized instead of rejected.

Invariants Verified:
- Invariant II1: No auto-enrollment in tutor orchestrator (EnrollmentError for both private & public).
- Invariant II2: No user auto-creation in tutor orchestrator.
- Invariant II3: Session identity & course isolation (cannot hijack another student's or course's session).
- Invariant II4: Unpublished/draft/archived course versions are strictly rejected.
- Invariant II5: Positive path: enrolled student on published version succeeds without synthetic defaults.
"""
import uuid
import pytest

from central_platform.auth.tokens import create_access_token
from central_platform.courses.service import CourseNotFoundError
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Enrollment,
    Organization,
    Session,
    SessionStatus,
    User,
    UserRole,
)
from central_platform.tutor.orchestrator import (
    EnrollmentError,
    GenericTutorOrchestrator,
    TutorTurnRequest,
)


@pytest.fixture
def context_env(tmp_path):
    """Isolated test environment for course/enrollment/version/context validation."""
    db_path = str(tmp_path / "context_test.db")
    db = PlatformDatabase(db_path)

    # 1. Organization
    org = Organization(id="org-ctx-test", name="Context Test Org", slug="ctx-test")
    db.create_organization(org)

    # 2. Existing Users
    student_1 = User(
        id="student-ctx-01",
        organization_id="org-ctx-test",
        email="s1@test.internal",
        full_name="Student Context One",
        role=UserRole.STUDENT,
    )
    student_2 = User(
        id="student-ctx-02",
        organization_id="org-ctx-test",
        email="s2@test.internal",
        full_name="Student Context Two",
        role=UserRole.STUDENT,
    )
    db.create_user(student_1)
    db.create_user(student_2)

    # 3. Courses
    public_course = Course(
        id="crs-public-math",
        organization_id="org-ctx-test",
        code="MATH101",
        title="Calculus I",
        visibility=CourseVisibility.PUBLIC,
    )
    private_course = Course(
        id="crs-private-physics",
        organization_id="org-ctx-test",
        code="PHYS201",
        title="Advanced Quantum Physics",
        visibility=CourseVisibility.PRIVATE,
    )
    db.create_course(public_course)
    db.create_course(private_course)

    # 4. Course Versions
    pub_ver = CourseVersion(
        id="ver-math-pub-1",
        course_id="crs-public-math",
        version_number="1.0",
        status=CourseStatus.PUBLISHED,
    )
    draft_ver = CourseVersion(
        id="ver-math-draft-2",
        course_id="crs-public-math",
        version_number="2.0-draft",
        status=CourseStatus.DRAFT,
    )
    db.create_course_version(pub_ver)
    db.create_course_version(draft_ver)

    # 5. Enrollments: Student 1 enrolled in Math, Student 2 enrolled in Physics
    db.create_enrollment(Enrollment(id="enr-s1-math", student_id="student-ctx-01", course_id="crs-public-math", is_active=True))
    db.create_enrollment(Enrollment(id="enr-s2-phys", student_id="student-ctx-02", course_id="crs-private-physics", is_active=True))

    return {
        "db": db,
        "student_1": student_1,
        "student_2": student_2,
        "public_course": public_course,
        "private_course": private_course,
        "pub_ver": pub_ver,
        "draft_ver": draft_ver,
    }


def test_F003_public_course_unenrolled_student_raises_enrollment_error(context_env):
    """F-003 Invariant: Even on PUBLIC courses, unenrolled student cannot turn without explicit prior enrollment."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    # Student 2 is NOT enrolled in public math course
    req = TutorTurnRequest(
        student_id="student-ctx-02",
        session_id="sess-ctx-unauth",
        course_id="crs-public-math",
        message="What is a limit in calculus?",
    )

    with pytest.raises(EnrollmentError) as exc_info:
        orchestrator.execute_turn(req)
    assert "not enrolled" in str(exc_info.value).lower()

    # Verify no auto-enrollment was secretly created
    enrs = db.get_enrollments_for_student("student-ctx-02")
    assert not any(e.course_id == "crs-public-math" for e in enrs)


def test_F003_tutor_never_auto_creates_user_in_db(context_env):
    """F-003 Invariant: Submitting a turn with an unregistered student_id must raise EnrollmentError and NEVER insert user."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    unregistered_sid = f"unregistered-{uuid.uuid4().hex[:6]}"
    req = TutorTurnRequest(
        student_id=unregistered_sid,
        session_id="sess-auto-user-test",
        course_id="crs-public-math",
        message="Hello from ghost student.",
    )

    with pytest.raises(EnrollmentError) as exc_info:
        orchestrator.execute_turn(req)
    assert "not enrolled" in str(exc_info.value).lower() or "not registered" in str(exc_info.value).lower()

    # Invariant check: database must NOT contain the unregistered user
    assert db.get_user(unregistered_sid) is None


def test_F003_session_belonging_to_another_student_raises_error(context_env):
    """F-003 Invariant: Session ID already owned by student A cannot be hijacked by student B."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    # Pre-create session owned by student 1
    shared_session_id = "sess-shared-001"
    db.create_session(
        Session(
            id=shared_session_id,
            student_id="student-ctx-01",
            course_id="crs-public-math",
            concept_id="limits",
            status=SessionStatus.ACTIVE,
        )
    )

    # Enroll student 2 in math as well so enrollment passes
    db.create_enrollment(Enrollment(id="enr-s2-math", student_id="student-ctx-02", course_id="crs-public-math", is_active=True))

    # Student 2 tries to submit turn on Student 1's session
    req = TutorTurnRequest(
        student_id="student-ctx-02",
        session_id=shared_session_id,
        course_id="crs-public-math",
        message="Sneaking into student 1 session.",
    )

    with pytest.raises(EnrollmentError, match="belongs to another student"):
        orchestrator.execute_turn(req)


def test_F003_session_belonging_to_another_course_raises_error(context_env):
    """F-003 Invariant: Session ID registered under Course A cannot be reused for Course B."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    # Enroll student 1 in physics too
    db.create_enrollment(Enrollment(id="enr-s1-phys", student_id="student-ctx-01", course_id="crs-private-physics", is_active=True))

    # Pre-create session for math
    session_id = "sess-s1-math-only"
    db.create_session(
        Session(
            id=session_id,
            student_id="student-ctx-01",
            course_id="crs-public-math",
            concept_id="limits",
            status=SessionStatus.ACTIVE,
        )
    )

    # Student 1 tries to use math session on physics course
    req = TutorTurnRequest(
        student_id="student-ctx-01",
        session_id=session_id,
        course_id="crs-private-physics",
        message="Asking quantum mechanics in math session.",
    )

    with pytest.raises(ValueError, match="belongs to course"):
        orchestrator.execute_turn(req)


def test_F023_unpublished_course_version_rejected(context_env):
    """F-023 Invariant: Requesting a DRAFT or unpublished version must be explicitly rejected."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    req = TutorTurnRequest(
        student_id="student-ctx-01",
        session_id="sess-draft-ver-test",
        course_id="crs-public-math",
        course_version_id="ver-math-draft-2",  # DRAFT version
        message="Explain derivatives.",
    )

    with pytest.raises(CourseNotFoundError, match="unpublished"):
        orchestrator.execute_turn(req)


def test_F023_enrolled_student_with_published_version_succeeds(context_env):
    """Positive Path: Enrolled student with published version resolves context cleanly."""
    db = context_env["db"]
    orchestrator = GenericTutorOrchestrator(db=db)

    req = TutorTurnRequest(
        student_id="student-ctx-01",
        session_id="sess-s1-valid-turn",
        course_id="crs-public-math",
        course_version_id="ver-math-pub-1",
        message="Can you explain the formal definition of a limit with epsilon and delta?",
    )

    result = orchestrator.execute_turn(req)
    assert result.status == "SUCCESS"
    assert result.course_id == "crs-public-math"
    assert result.state_committed is True
    assert result.validation_passed is True
