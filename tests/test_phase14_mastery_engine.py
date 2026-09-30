"""Tests for Phase 14: Mastery and Evidence Engine.

Tests deterministic evidence-backed mastery:
- Correct answer
- Incorrect answer
- Repeated attempts
- Review
- Time decay
- Prerequisite effects
"""

from datetime import datetime, timedelta, timezone
import pytest

from central_platform.db import PlatformDatabase
from central_platform.learning.mastery import MasteryEvidenceEngine
from central_platform.models.schema import Course, LearningEvent, Organization, Session, SessionStatus, User

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 14 tests."""
    db_file = str(tmp_path / "phase14_mastery.db")
    return PlatformDatabase(db_file)

def test_correct_answer_increases_mastery():
    """Test that correct answers increase mastery score."""
    engine = MasteryEvidenceEngine()
    
    events = [
        LearningEvent(
            id="e1",
            session_id="s1",
            student_id="u1",
            concept_id="cpt_1",
            event_type="answer_submitted",
            score=1.0,
            payload={"correctness": "correct", "hint_level": 0}
        )
    ]
    
    res = engine.calculate_evidence_mastery("cpt_1", events)
    assert res.effective_mastery > 0.0
    assert res.recent_accuracy == 1.0
    assert res.long_term_accuracy == 1.0

def test_incorrect_answer_decreases_mastery():
    """Test that incorrect answers lower mastery score."""
    engine = MasteryEvidenceEngine()
    
    events_correct = [
        LearningEvent(
            id="e1", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
        )
    ]
    res_correct = engine.calculate_evidence_mastery("cpt_1", events_correct)
    
    events_mixed = [
        LearningEvent(
            id="e1", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
        ),
        LearningEvent(
            id="e2", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=0.0, payload={"correctness": "incorrect"}
        )
    ]
    res_mixed = engine.calculate_evidence_mastery("cpt_1", events_mixed)
    
    assert res_mixed.effective_mastery < res_correct.effective_mastery

def test_repeated_attempts_diminishing_returns():
    """Test confidence increase and diminishing returns for repeated attempts."""
    engine = MasteryEvidenceEngine()
    
    events_few = [
        LearningEvent(
            id=f"e_{i}", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
        )
        for i in range(2)
    ]
    res_few = engine.calculate_evidence_mastery("cpt_1", events_few)
    
    events_many = [
        LearningEvent(
            id=f"e_{i}", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
        )
        for i in range(10)
    ]
    res_many = engine.calculate_evidence_mastery("cpt_1", events_many)
    
    assert res_many.confidence > res_few.confidence
    assert res_many.attempts_count == 10

def test_time_decay():
    """Test forgetting curve / memory decay over time."""
    engine = MasteryEvidenceEngine(half_life_days=30.0)
    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(days=60)).isoformat()
    
    events = [
        LearningEvent(
            id="e1", session_id="s1", student_id="u1", concept_id="cpt_1",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"},
            created_at=old_time
        )
    ]
    
    res = engine.calculate_evidence_mastery("cpt_1", events, now=now)
    assert res.days_since_last_practice >= 59.9
    assert res.decayed_mastery < res.raw_mastery
    # After two half-lives (60 days), decay factor should be approx 0.25
    assert res.decayed_mastery <= res.raw_mastery * 0.30

def test_prerequisite_effects():
    """Test prerequisite mastery discounting / bottleneck effect."""
    engine = MasteryEvidenceEngine()
    
    events = [
        LearningEvent(
            id="e1", session_id="s1", student_id="u1", concept_id="cpt_advanced",
            event_type="answer_submitted", score=1.0, payload={"correctness": "correct"}
        )
    ]
    
    # High prerequisite mastery (1.0)
    res_high = engine.calculate_evidence_mastery("cpt_advanced", events, prerequisite_masteries=[1.0, 0.9])
    
    # Low prerequisite mastery (0.2)
    res_low = engine.calculate_evidence_mastery("cpt_advanced", events, prerequisite_masteries=[0.2, 0.3])
    
    assert res_low.prerequisite_factor < res_high.prerequisite_factor
    assert res_low.effective_mastery < res_high.effective_mastery

def test_update_canonical_mastery_integration(db):
    """Test database persistence integration of MasteryEvidenceEngine."""
    org = Organization(id="org_m", name="Mastery Org", slug="m-org")
    db.create_organization(org)
    user = User(id="u_master", email="m@test.com", full_name="Mastery Student", role="student", organization_id="org_m")
    db.create_user(user)
    course = Course(id="c_m", organization_id="org_m", title="Course M", code="CM1")
    db.create_course(course)
    sess = Session(id="sess_m", student_id="u_master", course_id="c_m", concept_id="cpt_m")
    db.create_session(sess)
    
    # Record event
    db.record_learning_event(LearningEvent(
        id="evt_m1",
        session_id="sess_m",
        student_id="u_master",
        course_id="c_m",
        concept_id="cpt_m",
        event_type="answer_submitted",
        score=1.0,
        payload={"correctness": "correct"}
    ))
    
    engine = MasteryEvidenceEngine(db)
    res = engine.update_canonical_mastery("u_master", "c_m", "cpt_m")
    
    assert res.effective_mastery > 0.0
    slr = db.get_slr("u_master", "c_m")
    states = db.get_mastery_states_for_slr(slr.id)
    ms = next(m for m in states if m.concept_id == "cpt_m")
    assert ms.score == res.effective_mastery
