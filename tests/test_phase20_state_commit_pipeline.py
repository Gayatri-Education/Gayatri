"""Tests for Phase 20: State Commit Pipeline.

Tests atomic two-phase commit:
- Staging state mutations in memory
- Validation check using ResponseValidatorEngine
- Atomic commit on validation success
- Rollback and database corruption prevention on validation failure
"""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.learning.commit_pipeline import StateCommitPipeline
from central_platform.models.schema import (
    Course,
    LearningEvent,
    MasteryState,
    Organization,
    Session,
    SessionStatus,
    StudentLearningRecord,
    User,
)

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 20 tests."""
    db_file = str(tmp_path / "phase20_commit.db")
    return PlatformDatabase(db_file)

def seed_db(db):
    org = Organization(id="org_c", name="Commit Org", slug="commit-org")
    db.create_organization(org)
    user = User(id="u_commit", email="uc@test.com", full_name="Commit Student", role="student", organization_id="org_c")
    db.create_user(user)
    course = Course(id="c_commit", organization_id="org_c", title="Chemistry Commit", code="CC1")
    db.create_course(course)
    slr = StudentLearningRecord(id="slr_commit", student_id="u_commit", course_id="c_commit")
    db.create_slr(slr)
    sess = Session(id="sess_c", student_id="u_commit", course_id="c_commit", concept_id="cpt_commit", status=SessionStatus.ACTIVE)
    db.create_session(sess)

def test_successful_validation_commits_state(db):
    """Test that valid AI response commits staged state changes to database."""
    seed_db(db)
    pipeline = StateCommitPipeline(db)
    
    ms = MasteryState(slr_id="slr_commit", concept_id="cpt_commit", score=0.85, confidence=0.90)
    ev = LearningEvent(
        id="evt_c1", session_id="sess_c", student_id="u_commit", course_id="c_commit",
        concept_id="cpt_commit", event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
    )
    
    staged = pipeline.stage_changes("u_commit", "c_commit", mastery_updates=[ms], learning_events=[ev])
    
    valid_resp = "Thermodynamics is the study of heat, work, and energy transformations."
    res = pipeline.validate_and_commit(staged, generated_response=valid_resp, target_concept="Thermodynamics")
    
    assert res.committed is True
    assert res.staged_summary["mastery_updates"] == 1
    assert res.staged_summary["learning_events"] == 1
    
    # Verify DB persistence
    states = db.get_mastery_states_for_slr("slr_commit")
    assert len(states) == 1
    assert states[0].score == 0.85
    
    events = db.query_learning_events(student_id="u_commit", course_id="c_commit")
    assert len(events) == 1

def test_failed_validation_aborts_commit(db):
    """Test that invalid AI response (safety violation) aborts state commit and protects DB."""
    seed_db(db)
    pipeline = StateCommitPipeline(db)
    
    ms = MasteryState(slr_id="slr_commit", concept_id="cpt_commit", score=0.99, confidence=0.99)
    ev = LearningEvent(
        id="evt_c2", session_id="sess_c", student_id="u_commit", course_id="c_commit",
        concept_id="cpt_commit", event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
    )
    
    staged = pipeline.stage_changes("u_commit", "c_commit", mastery_updates=[ms], learning_events=[ev])
    
    # Dangerous response (safety violation)
    invalid_resp = "To synthesize methamphetamine or make a chemical bomb..."
    res = pipeline.validate_and_commit(staged, generated_response=invalid_resp)
    
    assert res.committed is False
    assert "failed validation" in res.reason
    
    # Verify DB is completely uncorrupted (no mastery or events written)
    states = db.get_mastery_states_for_slr("slr_commit")
    assert len(states) == 0
    
    events = db.query_learning_events(student_id="u_commit", course_id="c_commit")
    assert len(events) == 0

def test_empty_response_aborts_commit(db):
    """Test that empty AI response aborts state commit."""
    seed_db(db)
    pipeline = StateCommitPipeline(db)
    
    ms = MasteryState(slr_id="slr_commit", concept_id="cpt_commit", score=0.75)
    staged = pipeline.stage_changes("u_commit", "c_commit", mastery_updates=[ms])
    
    res = pipeline.validate_and_commit(staged, generated_response="")
    assert res.committed is False
    
    states = db.get_mastery_states_for_slr("slr_commit")
    assert len(states) == 0
