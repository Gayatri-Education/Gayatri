"""Tests for Phase 12: Learning Event System.

Tests normalized event creation, validation, persistence, querying, and integration.
"""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest, BatchLearningEventIngest, LearningEventFilter
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.learning.state import LearningStateManager
from central_platform.models.schema import User, Course, Organization, SessionStatus

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 12 tests."""
    db_file = str(tmp_path / "phase12_events.db")
    return PlatformDatabase(db_file)

def test_event_creation_and_validation():
    """Test LearningEventIngest validation and payload normalization."""
    ingest = LearningEventIngest(
        event_id="evt_norm_1",
        student_id="std_101",
        organization_id="org_1",
        course_id="crs_chem",
        session_id="sess_1",
        event_type=LearningEventType.ANSWER_SUBMITTED,
        turn_id="turn_1",
        concept_id="cpt_thermo",
        correctness="correct",
        score=1.0,
        hint_used=0,
        difficulty=3.0,
    )
    
    assert ingest.event_id == "evt_norm_1"
    assert ingest.payload["turn_id"] == "turn_1"
    assert ingest.payload["concept_id"] == "cpt_thermo"
    assert ingest.payload["correctness"] == "correct"
    assert ingest.payload["score"] == 1.0

def test_invalid_event_type_raises():
    """Test that invalid event types raise validation errors."""
    with pytest.raises(ValueError):
        LearningEventIngest(
            event_id="evt_bad",
            student_id="std_1",
            session_id="sess_1",
            event_type="INVALID_EVENT_TYPE_STRING",
        )

def test_event_persistence_and_querying(db):
    """Test append-only event persistence and filtering in store."""
    store = LearningEventStore(db)
    
    ingest = LearningEventIngest(
        event_id="evt_p1",
        student_id="std_200",
        organization_id="org_test",
        course_id="crs_phys",
        session_id="sess_phys_1",
        event_type=LearningEventType.QUESTION_ATTEMPTED,
        concept_id="cpt_kinematics",
        score=0.8,
    )
    
    event, created = store.ingest_event(ingest)
    assert created is True
    assert event.id == "evt_p1"
    assert event.concept_id == "cpt_kinematics"
    
    # Test deduplication
    dup_event, dup_created = store.ingest_event(ingest)
    assert dup_created is False
    assert dup_event.id == "evt_p1"
    
    # Query events
    events = store.get_student_events(student_id="std_200", course_id="crs_phys")
    assert len(events) == 1
    assert events[0].id == "evt_p1"

def test_batch_event_ingestion(db):
    """Test batch event ingestion."""
    store = LearningEventStore(db)
    
    batch = BatchLearningEventIngest(
        events=[
            LearningEventIngest(
                event_id="evt_b1",
                student_id="std_300",
                session_id="sess_b",
                event_type=LearningEventType.CONCEPT_INTRODUCED,
                concept_id="cpt_vectors",
            ),
            LearningEventIngest(
                event_id="evt_b2",
                student_id="std_300",
                session_id="sess_b",
                event_type=LearningEventType.HINT_REQUESTED,
                concept_id="cpt_vectors",
            ),
        ]
    )
    
    res = store.ingest_batch(batch)
    assert res["total"] == 2
    assert res["inserted"] == 2
    assert res["deduplicated"] == 0

def test_learning_state_manager_queries_recent_events(db):
    """Test that LearningStateManager populates recent_events in CanonicalLearningState."""
    org = Organization(id="org_test", name="Test Org", slug="test-org")
    db.create_organization(org)
    user = User(id="std_400", email="s400@test.com", full_name="Student 400", role="student", organization_id="org_test")
    db.create_user(user)
    course = Course(id="crs_test", organization_id="org_test", title="Test Course", code="TC101")
    db.create_course(course)
    
    mgr = LearningStateManager(db)
    sess_state = mgr.initialize_session("std_400", "crs_test", "cpt_algebra")
    
    # Log 2 events via manager
    mgr.log_event(sess_state.session_id, "question_attempted", {"score": 0.5})
    mgr.log_event(sess_state.session_id, "answer_submitted", {"score": 1.0, "correctness": "correct"})
    
    canonical = mgr.get_canonical_state("std_400", "crs_test")
    assert len(canonical.recent_events) == 2
    event_types = {e.event_type for e in canonical.recent_events}
    assert event_types == {"question_attempted", "answer_submitted"}
