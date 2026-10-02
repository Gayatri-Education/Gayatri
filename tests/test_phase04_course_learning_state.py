"""Tests for Phase 04: Course-Scoped Student Learning State & Sessions (Section 12.4).

Verifies:
1. Cross-Course Contamination Matrix: Same student, same concept name ("thermo"), two courses.
2. Strict isolation: Mastery and events in Course A do not leak into Course B.
3. Session and telemetry scoping: Sessions and events carry course_id and course_version_id.
4. Idempotent telemetry: Duplicate event IDs are ignored without double-counting.
5. State persistence & exact recovery: Re-instantiating state manager restores exact state.
6. Validation gates: Empty course_id or student_id is rejected with ValueError.
"""

from pathlib import Path
import pytest
import sqlite3

from central_platform.db import PlatformDatabase
from central_platform.learning.state import (
    LearningStateManager,
    CanonicalLearningState,
    SessionRuntimeState,
)
from central_platform.models.schema import (
    CourseLearningContext,
    Session,
    SessionStatus,
    LearningEvent,
    StudentLearningRecord,
    MasteryState,
    Organization,
    Course,
    User,
    UserRole,
)


@pytest.fixture
def clean_platform_db(tmp_path):
    """Fixture providing a fresh isolated PlatformDatabase with test organization, courses, and students."""
    db_file = tmp_path / "test_phase04.db"
    db = PlatformDatabase(db_path=str(db_file))

    # Seed organization
    db.create_organization(Organization(id="org_dps", name="Delhi Public School", slug="dps"))

    # Seed courses
    for cid, code, title in [
        ("course_chem", "CHEM101", "Chemistry"),
        ("course_phys", "PHYS101", "Physics"),
        ("course_prog", "CS101", "Programming"),
    ]:
        db.create_course(Course(id=cid, organization_id="org_dps", code=code, title=title))

    # Seed students
    for sid in [
        "usr_student_01",
        "student_multicourse_01",
        "student_session_01",
        "student_idem_01",
        "student_restart_01",
        "student_01",
    ]:
        db.create_user(User(id=sid, email=f"{sid}@dps.edu", full_name=f"Student {sid}", role=UserRole.STUDENT, organization_id="org_dps"))

    return db




def test_course_learning_context_validation():
    """Verify CourseLearningContext requires non-empty student_id and course_id."""
    # Valid context
    ctx = CourseLearningContext(
        student_id="usr_student_01",
        course_id="course_chem_101",
        course_version_id="1.0",
        organization_id="org_dps",
    )
    ctx.validate()
    assert ctx.student_id == "usr_student_01"
    assert ctx.course_id == "course_chem_101"

    # Missing student_id
    with pytest.raises(ValueError, match="non-empty student_id"):
        CourseLearningContext(student_id="", course_id="course_chem_101").validate()

    # Missing course_id
    with pytest.raises(ValueError, match="non-empty course_id"):
        CourseLearningContext(student_id="usr_student_01", course_id="").validate()


def test_cross_course_mastery_isolation(clean_platform_db):
    """Verify that a student practicing the same concept name in Course A and Course B has completely isolated mastery."""
    db = clean_platform_db
    sm = LearningStateManager(db)
    student_id = "student_multicourse_01"

    # Step 1: Student practices "thermo" in Chemistry (Course A) -> achieves 0.92 mastery
    sm.update_mastery(
        student_id=student_id,
        course_id="course_chem",
        concept_id="thermo",
        score=0.92,
        confidence=0.85,
    )

    # Step 2: Verify Chemistry state reflects 0.92
    chem_state = sm.get_canonical_state(student_id=student_id, course_id="course_chem")
    assert "thermo" in chem_state.mastery
    assert chem_state.mastery["thermo"].score == 0.92

    # Step 3: Check Physics (Course B) state for the SAME student and SAME concept name
    # Physics must have NO mastery entry or default state, completely untouched by Chemistry
    phys_state = sm.get_canonical_state(student_id=student_id, course_id="course_phys")
    assert "thermo" not in phys_state.mastery or phys_state.mastery["thermo"].score == 0.50
    assert chem_state.slr.id != phys_state.slr.id, "SLR records must be distinct per course"

    # Step 4: Student now practices "thermo" in Physics (Course B) -> achieves 0.45 mastery
    sm.update_mastery(
        student_id=student_id,
        course_id="course_phys",
        concept_id="thermo",
        score=0.45,
        confidence=0.70,
    )

    # Step 5: Verify Physics reflects 0.45, and Chemistry STILL reflects 0.92
    phys_state_updated = sm.get_canonical_state(student_id=student_id, course_id="course_phys")
    chem_state_checked = sm.get_canonical_state(student_id=student_id, course_id="course_chem")

    assert phys_state_updated.mastery["thermo"].score == 0.45
    assert chem_state_checked.mastery["thermo"].score == 0.92, "Course A mastery must not be affected by Course B updates"


def test_session_and_event_scoping_and_isolation(clean_platform_db):
    """Verify sessions and learning events are scoped to their respective course and version."""
    db = clean_platform_db
    sm = LearningStateManager(db)
    student_id = "student_session_01"

    # 1. Initialize session in Chemistry version 1.0
    ctx_chem = CourseLearningContext(
        student_id=student_id,
        course_id="course_chem",
        course_version_id="1.0",
        organization_id="org_dps",
    )
    sess_chem = sm.initialize_session(ctx_chem, concept_id="chem_thermo_hess")
    assert sess_chem.course_id == "course_chem"
    assert sess_chem.course_version_id == "1.0"

    # 2. Log event in Chemistry session
    evt_chem = sm.log_event(
        session_id=sess_chem.session_id,
        event_type="question_answered",
        data={"question_id": "q_chem_01", "correct": True},
        event_id="evt_chem_001",
    )
    assert evt_chem.course_id == "course_chem"
    assert evt_chem.course_version_id == "1.0"

    # 3. Initialize session in Physics version 2.0
    ctx_phys = CourseLearningContext(
        student_id=student_id,
        course_id="course_phys",
        course_version_id="2.0",
        organization_id="org_dps",
    )
    sess_phys = sm.initialize_session(ctx_phys, concept_id="phys_newton_laws")
    assert sess_phys.course_id == "course_phys"
    assert sess_phys.course_version_id == "2.0"

    # 4. Log event in Physics session
    evt_phys = sm.log_event(
        session_id=sess_phys.session_id,
        event_type="question_answered",
        data={"question_id": "q_phys_01", "correct": False},
        event_id="evt_phys_001",
    )
    assert evt_phys.course_id == "course_phys"
    assert evt_phys.course_version_id == "2.0"

    # 5. Query sessions for Chemistry vs Physics
    chem_sessions = db.get_sessions_for_student(student_id=student_id, course_id="course_chem")
    phys_sessions = db.get_sessions_for_student(student_id=student_id, course_id="course_phys")

    assert len(chem_sessions) == 1
    assert chem_sessions[0].id == sess_chem.session_id
    assert chem_sessions[0].course_version_id == "1.0"

    assert len(phys_sessions) == 1
    assert phys_sessions[0].id == sess_phys.session_id
    assert phys_sessions[0].course_version_id == "2.0"

    # 6. Verify event isolation in CanonicalLearningState
    chem_state = sm.get_canonical_state(student_id=student_id, course_id="course_chem")
    phys_state = sm.get_canonical_state(student_id=student_id, course_id="course_phys")

    chem_event_ids = [e.id for e in chem_state.recent_events]
    phys_event_ids = [e.id for e in phys_state.recent_events]

    assert "evt_chem_001" in chem_event_ids
    assert "evt_phys_001" not in chem_event_ids

    assert "evt_phys_001" in phys_event_ids
    assert "evt_chem_001" not in phys_event_ids


def test_idempotent_event_telemetry(clean_platform_db):
    """Verify that logging duplicate events with the same event_id is idempotent and prevents double-counting."""
    db = clean_platform_db
    sm = LearningStateManager(db)

    sess = sm.initialize_session(student_id="student_idem_01", course_id="course_chem", concept_id="chem_bonding")

    # Log event once
    evt1 = sm.log_event(
        session_id=sess.session_id,
        event_type="quiz_completed",
        data={"score": 85},
        event_id="evt_unique_12345",
    )
    assert evt1.id == "evt_unique_12345"

    # Log event second time with identical event_id (e.g. client network retry)
    evt2 = sm.log_event(
        session_id=sess.session_id,
        event_type="quiz_completed",
        data={"score": 85},
        event_id="evt_unique_12345",
    )
    assert evt2.id == "evt_unique_12345"

    # Verify database contains exactly one event record
    events = db.get_learning_events_for_session(sess.session_id)
    assert len(events) == 1, "Duplicate event_id must be idempotently ignored"


def test_state_persistence_and_exact_recovery(clean_platform_db, tmp_path):
    """Verify that re-instantiating the state manager or restarting the process preserves multi-course state without drift."""
    db = clean_platform_db
    db_path = db.db_path
    sm1 = LearningStateManager(db)

    student_id = "student_restart_01"

    # Set up records across Chemistry and Programming
    sm1.update_mastery(student_id, "course_chem", "chem_inorg", 0.88, 0.90)
    sm1.update_mastery(student_id, "course_prog", "py_recursion", 0.76, 0.80)

    sess_chem = sm1.initialize_session(student_id, "course_chem", "chem_inorg", course_version_id="1.1")
    sm1.log_event(sess_chem.session_id, "attempt", {"result": "success"}, event_id="evt_rec_01")

    # Simulate restart by instantiating a completely new PlatformDatabase and LearningStateManager
    db_reopened = PlatformDatabase(db_path)
    sm2 = LearningStateManager(db_reopened)

    # Verify exact state is restored for Chemistry
    recovered_chem = sm2.get_canonical_state(student_id, "course_chem")
    assert recovered_chem.mastery["chem_inorg"].score == 0.88
    assert recovered_chem.mastery["chem_inorg"].confidence == 0.90
    assert any(e.id == "evt_rec_01" for e in recovered_chem.recent_events)

    # Verify exact state is restored for Programming
    recovered_prog = sm2.get_canonical_state(student_id, "course_prog")
    assert recovered_prog.mastery["py_recursion"].score == 0.76
    assert recovered_prog.mastery["py_recursion"].confidence == 0.80
    assert "chem_inorg" not in recovered_prog.mastery

    # Verify get_student_courses returns both courses
    courses = sm2.get_student_courses(student_id)
    assert set(courses) == {"course_chem", "course_prog"}


def test_missing_course_id_validation_gate(clean_platform_db):
    """Verify that operations without explicit course_id are rejected with ValueError."""
    sm = LearningStateManager(clean_platform_db)

    with pytest.raises(ValueError, match="course_id must not be empty"):
        sm.get_canonical_state(student_id="student_01", course_id="")

    with pytest.raises(ValueError, match="course_id must not be empty"):
        sm.initialize_session(student_id_or_context="student_01", course_id="", concept_id="c1")

    with pytest.raises(ValueError, match="course_id must not be empty"):
        sm.update_mastery(student_id="student_01", course_id="", concept_id="c1", score=0.8)
