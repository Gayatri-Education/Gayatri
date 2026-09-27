"""Phase 05 Test Suite — Central Learning Event System & Event Store Verification.

Master Plan Section 14:
1. Taxonomy: All 20 canonical learning event types validated and accepted.
2. Rejection: Invalid event types and corrupt payloads rejected with 422.
3. Schema: Strict verification of event_id, student_id, organization_id, course_id, session_id,
   event_type, timestamp, source, payload, schema_version.
4. Idempotency: Duplicate event_id ingestion returns DEDUPLICATED without duplicate records.
5. Immutability: Events cannot be modified or deleted.
6. Time-Series Querying: Filtering by student, session, course, event_type, and time ranges.
7. Security Boundaries: Student self-access and tenant boundaries enforced (403 Forbidden).
8. Replayability: Chronological event stream replay accurately reconstructs student pedagogical state.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.models import (
    BatchLearningEventIngest,
    LearningEventFilter,
    LearningEventIngest,
)
from central_platform.events.store import LearningEventStore
from central_platform.events.types import (
    ASSESSMENT_EVENTS,
    HINT_EVENTS,
    MASTERY_EVENTS,
    MISCONCEPTION_EVENTS,
    QA_EVENTS,
    SESSION_EVENTS,
    TEACHER_EVENTS,
    LearningEventType,
)
from central_platform.models.schema import LearningEvent


@pytest.fixture(scope="module")
def client():
    """Create test client for platform API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def event_store(tmp_path):
    """Provide a fresh isolated database and event store."""
    db_file = str(tmp_path / "events_test.db")
    db = PlatformDatabase(db_file)
    store = LearningEventStore(db)
    yield store
    db.close()


# ── 1. Taxonomy: 20 Canonical Event Types ──────────────────────────────────

def test_all_20_canonical_event_types_defined():
    """Verify that all 20 canonical event types from Master Plan Section 14 are defined."""
    assert len(LearningEventType) == 20

    expected_types = [
        "session_started",
        "session_completed",
        "question_attempted",
        "answer_submitted",
        "answer_corrected",
        "hint_requested",
        "hint_used",
        "concept_introduced",
        "concept_reinforced",
        "concept_mastered",
        "misconception_detected",
        "misconception_recovered",
        "review_completed",
        "assessment_started",
        "assessment_completed",
        "teacher_instruction_created",
        "teacher_intervention_created",
        "teacher_feedback_added",
        "assignment_created",
        "assignment_completed",
    ]

    for t in expected_types:
        assert LearningEventType(t) is not None
        assert t in [e.value for e in LearningEventType]


def test_ingest_all_20_canonical_events(event_store):
    """Verify that each of the 20 canonical event types can be successfully ingested and retrieved."""
    student_id = "std-canon-01"
    session_id = "sess-canon-01"

    for idx, etype in enumerate(LearningEventType):
        req = LearningEventIngest(
            event_id=f"ev-canon-{idx:02d}",
            student_id=student_id,
            session_id=session_id,
            event_type=etype,
            payload={"turn": idx, "type_name": etype.value},
            concept_id="chem_thermo_first_law",
        )
        ev, was_new = event_store.ingest_event(req)
        assert was_new is True
        assert ev.event_type == etype.value
        assert ev.id == f"ev-canon-{idx:02d}"

    # Verify all 20 events are retrievable
    stored_events = event_store.query_events(LearningEventFilter(student_id=student_id, limit=50))
    assert len(stored_events) == 20


def test_invalid_event_type_rejection(client):
    """Verify that uncanonical event types are rejected with 422 Unprocessable Entity."""
    invalid_payload = {
        "event_id": "ev-invalid-99",
        "student_id": "std-01",
        "session_id": "sess-01",
        "event_type": "completely_unsupported_event_type",
    }
    resp = client.post("/api/v1/learning/events", json=invalid_payload)
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False


# ── 2. Idempotency & Immutability ──────────────────────────────────────────

def test_idempotent_event_ingestion(client):
    """Verify duplicate event_id ingestion returns DEDUPLICATED status without duplicating data."""
    event_payload = {
        "event_id": "ev-idempotent-001",
        "student_id": "std-idem-01",
        "session_id": "sess-idem-01",
        "event_type": "question_attempted",
        "concept_id": "chem_thermo_enthalpy",
        "payload": {"question_id": "q-101"},
    }

    # First ingestion
    r1 = client.post("/api/v1/learning/events", json=event_payload)
    assert r1.status_code == 201
    assert r1.json()["data"]["status"] == "RECORDED"
    assert r1.json()["data"]["inserted"] is True

    # Second duplicate ingestion with same event_id
    r2 = client.post("/api/v1/learning/events", json=event_payload)
    assert r2.status_code == 201
    assert r2.json()["data"]["status"] == "DEDUPLICATED"
    assert r2.json()["data"]["deduplicated"] is True

    # Verify query returns exactly 1 record
    r_query = client.get("/api/v1/learning/events?student_id=std-idem-01")
    assert r_query.status_code == 200
    events = r_query.json()["data"]
    assert len([e for e in events if e["event_id"] == "ev-idempotent-001"]) == 1


def test_batch_ingestion_and_deduplication(client):
    """Verify batch ingestion handles multiple events and deduplicates existing ones."""
    batch_payload = {
        "events": [
            {
                "event_id": "batch-ev-01",
                "student_id": "std-batch-01",
                "session_id": "sess-batch-01",
                "event_type": "session_started",
            },
            {
                "event_id": "batch-ev-02",
                "student_id": "std-batch-01",
                "session_id": "sess-batch-01",
                "event_type": "concept_introduced",
                "concept_id": "chem_thermo_work",
            },
            {
                "event_id": "batch-ev-01",  # duplicate of first
                "student_id": "std-batch-01",
                "session_id": "sess-batch-01",
                "event_type": "session_started",
            },
        ]
    }

    resp = client.post("/api/v1/learning/events/batch", json=batch_payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["total"] == 3
    assert data["inserted"] == 2
    assert data["deduplicated"] == 1


def test_immutability_guards(event_store):
    """Verify that event records cannot be modified or deleted."""
    req = LearningEventIngest(
        event_id="ev-immutable-01",
        student_id="std-imm",
        session_id="sess-imm",
        event_type=LearningEventType.CONCEPT_INTRODUCED,
    )
    event_store.ingest_event(req)

    with pytest.raises(PermissionError, match="immutable and cannot be updated"):
        event_store.update_event("ev-immutable-01", {"score": 1.0})

    with pytest.raises(PermissionError, match="immutable and cannot be deleted"):
        event_store.delete_event("ev-immutable-01")


# ── 3. Time-Series Querying & Filtering ────────────────────────────────────

def test_time_series_event_querying(event_store):
    """Verify filtering by event_type, session, and chronological ordering."""
    student_id = "std-filter-01"

    # Ingest sequence
    event_store.ingest_event(
        LearningEventIngest(
            event_id="ev-ts-1",
            student_id=student_id,
            session_id="sess-A",
            event_type=LearningEventType.SESSION_STARTED,
            timestamp="2026-09-27T10:00:00Z",
        )
    )
    event_store.ingest_event(
        LearningEventIngest(
            event_id="ev-ts-2",
            student_id=student_id,
            session_id="sess-A",
            event_type=LearningEventType.QUESTION_ATTEMPTED,
            timestamp="2026-09-27T10:01:00Z",
        )
    )
    event_store.ingest_event(
        LearningEventIngest(
            event_id="ev-ts-3",
            student_id=student_id,
            session_id="sess-B",
            event_type=LearningEventType.SESSION_STARTED,
            timestamp="2026-09-27T11:00:00Z",
        )
    )

    # Filter by session
    sess_a_events = event_store.query_events(
        LearningEventFilter(student_id=student_id, session_id="sess-A")
    )
    assert len(sess_a_events) == 2
    assert [e.id for e in sess_a_events] == ["ev-ts-1", "ev-ts-2"]

    # Filter by event_type
    started_events = event_store.query_events(
        LearningEventFilter(student_id=student_id, event_type="session_started")
    )
    assert len(started_events) == 2

    # Filter by date range
    range_events = event_store.query_events(
        LearningEventFilter(
            student_id=student_id,
            since="2026-09-27T10:00:30Z",
            until="2026-09-27T10:30:00Z",
        )
    )
    assert len(range_events) == 1
    assert range_events[0].id == "ev-ts-2"


# ── 4. Student Scoping & Security Boundaries (Section 13 & 14) ────────────

def test_security_cross_student_event_ingestion_blocked(client):
    """Verify authenticated student cannot ingest events for another student (403 Forbidden)."""
    alice_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )

    tampered_event = {
        "event_id": "ev-spoof-01",
        "student_id": "student_bob",  # Spoofed target
        "organization_id": "org-central",
        "session_id": "sess-bob-01",
        "event_type": "answer_submitted",
        "payload": {"score": 1.0},
    }

    resp = client.post(
        "/api/v1/learning/events",
        headers={"Authorization": f"Bearer {alice_token}"},
        json=tampered_event,
    )
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]


def test_security_cross_student_event_query_blocked(client):
    """Verify authenticated student cannot query another student's events (403 Forbidden)."""
    alice_token = create_access_token(
        user_id="student_alice",
        role="student",
        organization_id="org-central",
    )

    resp = client.get(
        "/api/v1/learning/events?student_id=student_bob",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]


# ── 5. Chronological Event Replay Projection ──────────────────────────────

def test_chronological_event_replay_projection(client):
    """Verify full chronological replay reconstructing mastery, misconceptions, and hint usage."""
    student_id = "std-replay-project-01"
    session_id = "sess-replay-01"

    event_sequence = [
        {
            "event_id": "r-01",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "session_started",
            "timestamp": "2026-09-27T12:00:00Z",
        },
        {
            "event_id": "r-02",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "concept_introduced",
            "concept_id": "chem_thermo_first_law",
            "timestamp": "2026-09-27T12:01:00Z",
        },
        {
            "event_id": "r-03",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "question_attempted",
            "concept_id": "chem_thermo_first_law",
            "timestamp": "2026-09-27T12:02:00Z",
        },
        {
            "event_id": "r-04",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "misconception_detected",
            "concept_id": "chem_thermo_first_law",
            "payload": {"misconception_code": "HEAT_WORK_CONFUSION"},
            "timestamp": "2026-09-27T12:03:00Z",
        },
        {
            "event_id": "r-05",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "hint_used",
            "timestamp": "2026-09-27T12:04:00Z",
        },
        {
            "event_id": "r-06",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "misconception_recovered",
            "concept_id": "chem_thermo_first_law",
            "payload": {"misconception_code": "HEAT_WORK_CONFUSION"},
            "timestamp": "2026-09-27T12:05:00Z",
        },
        {
            "event_id": "r-07",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "answer_corrected",
            "concept_id": "chem_thermo_first_law",
            "payload": {"correctness": "correct", "score": 1.0},
            "timestamp": "2026-09-27T12:06:00Z",
        },
        {
            "event_id": "r-08",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "concept_mastered",
            "concept_id": "chem_thermo_first_law",
            "timestamp": "2026-09-27T12:07:00Z",
        },
        {
            "event_id": "r-09",
            "student_id": student_id,
            "session_id": session_id,
            "event_type": "session_completed",
            "timestamp": "2026-09-27T12:08:00Z",
        },
    ]

    # Ingest event stream via batch endpoint
    r_batch = client.post("/api/v1/learning/events/batch", json={"events": event_sequence})
    assert r_batch.status_code == 201
    assert r_batch.json()["data"]["inserted"] == 9

    # Trigger replay projection endpoint
    r_replay = client.post(f"/api/v1/learning/events/replay?student_id={student_id}")
    assert r_replay.status_code == 200
    proj = r_replay.json()["data"]

    # Verify reconstructed state
    assert proj["student_id"] == student_id
    assert proj["total_events"] == 9
    assert proj["questions_attempted"] == 1
    assert proj["questions_correct"] == 1
    assert proj["hints_used"] == 1
    assert "chem_thermo_first_law" in proj["concepts_introduced"]
    assert "chem_thermo_first_law" in proj["concepts_mastered"]
    # The misconception was detected then recovered -> active must be empty, recovered must contain it
    assert "HEAT_WORK_CONFUSION" not in proj["active_misconceptions"]
    assert "HEAT_WORK_CONFUSION" in proj["recovered_misconceptions"]
    assert proj["current_mastery"] > 0.50
