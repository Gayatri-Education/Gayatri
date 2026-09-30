"""Tests for Phase 11: Canonical Learning State."""

import pytest
from central_platform.learning.state import LearningStateManager, SessionRuntimeState, CanonicalLearningState
from central_platform.models.schema import User, Course, Organization, SessionStatus
from central_platform.db import PlatformDatabase

@pytest.fixture
def db(tmp_path):
    """Provide a fresh isolated database."""
    db_file = str(tmp_path / "phase11_test.db")
    return PlatformDatabase(db_file)

def test_canonical_learning_state(db):
    org = Organization(id="org_test", name="Test", slug="test")
    db.create_organization(org)
    student = User(id="u_student", organization_id="org_test", full_name="Student", email="s@s.com", role="student")
    db.create_user(student)
    course = Course(id="c1", organization_id="org_test", title="Course 1", code="C1")
    db.create_course(course)
    
    manager = LearningStateManager(db)
    
    # Get canonical state for new student (should auto-create SLR)
    state = manager.get_canonical_state("u_student", "c1")
    assert state.slr.student_id == "u_student"
    assert len(state.mastery) == 0
    
    # Update mastery
    manager.update_mastery("u_student", "c1", "concept_1", 0.75, 0.9)
    
    state2 = manager.get_canonical_state("u_student", "c1")
    assert "concept_1" in state2.mastery
    assert state2.mastery["concept_1"].score == 0.75
    
def test_session_runtime_state(db):
    org = Organization(id="org_test", name="Test", slug="test")
    db.create_organization(org)
    student = User(id="u_student", organization_id="org_test", full_name="Student", email="s@s.com", role="student")
    db.create_user(student)
    course = Course(id="c1", organization_id="org_test", title="Course 1", code="C1")
    db.create_course(course)
    
    manager = LearningStateManager(db)
    
    runtime = manager.initialize_session("u_student", "c1", "concept_1")
    assert runtime.session_id.startswith("sess_")
    assert runtime.mode == "EXPLAIN"
    
    fetched = manager.get_session_runtime(runtime.session_id)
    assert fetched == runtime
    
    # Log event
    evt = manager.log_event(runtime.session_id, "answer_submitted", {"correct": True})
    assert evt.event_type == "answer_submitted"
    assert evt.session_id == runtime.session_id
    
    # End session
    manager.end_session(runtime.session_id)
    assert manager.get_session_runtime(runtime.session_id) is None
    
    sess_in_db = db.get_session(runtime.session_id)
    assert sess_in_db.status == SessionStatus.COMPLETED
