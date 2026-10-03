"""Gayatri AI Platform — Phase 05 Forensic Remediation Contract & Adversarial Tests.

Verifies:
1. F-015: Single Unified Database Transaction & Atomic Rollback.
   - Zero partial writes on failure (fault injection at each step: after mastery, after misconceptions, after events).
   - Complete atomic commit on success.
2. F-016: Event Deduplication & Database-level Idempotency.
   - External learning events enforce unique durable identifiers.
   - Duplicate events are deduplicated without corrupting state.
3. F-017: Authoritative SLR & Elimination of Fabricated Defaults.
   - No fake Chemistry baseline (0.50 score, 0.85 retention, chem_thermo_first_law concept).
   - Unassessed learner yields INSUFFICIENT_EVIDENCE, score 0.0, empty concept_scores.
   - Real evidence produces EVALUATED status and true calculated mastery.
4. F-018: Multi-Tenant Scoping and Course Isolation.
   - State records strictly scoped by student_id and course_id.
5. Nested Transaction & Savepoint semantics in PlatformDatabase.
"""
from __future__ import annotations

import os
import uuid
import pytest

from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.learning.commit_pipeline import StateCommitPipeline, StagedStateChanges
from central_platform.models.schema import (
    Course,
    Enrollment,
    LearningEvent,
    MasteryState,
    Misconception,
    Organization,
    Session,
    SessionStatus,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    User,
    UserRole,
)
from central_platform.slr.service import SLRService


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "phase05_remediation_test.db")
    return PlatformDatabase(db_file)


@pytest.fixture
def slr_service(temp_db):
    event_store = LearningEventStore(db=temp_db)
    return SLRService(db=temp_db, event_store=event_store)


@pytest.fixture
def commit_pipeline(temp_db):
    return StateCommitPipeline(db=temp_db)


def _bootstrap_entities(db: PlatformDatabase, student_id: str, course_id: str, session_id: str = "sess_01", misc_code: str = ""):
    """Seed base relational entities for test isolation."""
    org = db.get_organization("org-test")
    if not org:
        db.create_organization(Organization(id="org-test", name="Test Org", slug="test-org"))

    user = db.get_user(student_id)
    if not user:
        db.create_user(
            User(
                id=student_id,
                email=f"{student_id}@test.ai",
                full_name=f"Student {student_id}",
                role=UserRole.STUDENT,
                organization_id="org-test",
            )
        )

    course = db.get_course(course_id)
    if not course:
        db.create_course(
            Course(
                id=course_id,
                organization_id="org-test",
                code=course_id.upper(),
                title=f"Course {course_id}",
            )
        )

    enr = db.get_enrollments_for_student(student_id)
    if not any(e.course_id == course_id for e in enr):
        db.create_enrollment(
            Enrollment(
                id=f"enr-{student_id}-{course_id}",
                student_id=student_id,
                course_id=course_id,
                is_active=True,
            )
        )

    sess = db.get_session(session_id)
    if not sess:
        db.create_session(
            Session(
                id=session_id,
                student_id=student_id,
                course_id=course_id,
                concept_id="",
                status=SessionStatus.ACTIVE,
            )
        )

    if misc_code:
        m = db.get_misconception_by_code(misc_code)
        if not m:
            db.create_misconception(
                Misconception(
                    id=f"misc-{misc_code.lower()}",
                    code=misc_code,
                    category="physics",
                    name=misc_code,
                    description="",
                    remediation="",
                )
            )

    slr = db.get_slr(student_id, course_id)
    if not slr:
        db.create_slr(
            StudentLearningRecord(
                id=f"slr-{student_id}-{course_id}",
                student_id=student_id,
                course_id=course_id,
                authoritative=True,
            )
        )


# ── 1. F-015: Atomic Single DB Transaction & Fault Injection ───────────────────

def test_atomic_transaction_full_success(temp_db, commit_pipeline):
    """Positive test: Successful commit writes all staged entities atomically."""
    student_id = "stu_atomic_01"
    course_id = "crs_physics_101"
    _bootstrap_entities(temp_db, student_id, course_id, session_id="sess_01", misc_code="SPEED_VS_VELOCITY")

    slr_id = f"slr-{student_id}-{course_id}"
    ms = MasteryState(id="mst_01", slr_id=slr_id, concept_id="kinematics_velocity", score=0.85, confidence=0.90)
    sm = StudentMisconceptionRecord(id="smr_01", student_id=student_id, misconception_code="SPEED_VS_VELOCITY", frequency=1)
    ev = LearningEvent(id="ev_01", session_id="sess_01", student_id=student_id, course_id=course_id, concept_id="kinematics_velocity", event_type="QUESTION_ATTEMPTED")

    staged = commit_pipeline.stage_changes(
        student_id=student_id,
        course_id=course_id,
        mastery_updates=[ms],
        misconception_records=[sm],
        learning_events=[ev],
    )

    result = commit_pipeline.validate_and_commit(
        staged=staged,
        generated_response="Velocity is speed with direction.",
        target_concept="kinematics_velocity",
    )

    assert result.committed is True
    # Verify all records persisted
    mastery_states = temp_db.get_mastery_states_for_slr(slr_id)
    assert len(mastery_states) == 1
    assert mastery_states[0].concept_id == "kinematics_velocity"
    assert mastery_states[0].score == 0.85

    misconceptions = temp_db.get_student_misconceptions(student_id)
    assert len(misconceptions) == 1
    assert misconceptions[0].misconception_code == "SPEED_VS_VELOCITY"

    event = temp_db.get_learning_event("ev_01")
    assert event is not None
    assert event.concept_id == "kinematics_velocity"


def test_fault_injection_after_mastery_zero_partial_writes(temp_db, commit_pipeline):
    """Adversarial F-015: Fault injected after mastery write triggers full rollback."""
    student_id = "stu_atomic_fault_01"
    course_id = "crs_physics_101"
    _bootstrap_entities(temp_db, student_id, course_id, session_id="sess_01", misc_code="ACCEL_DECEL")

    slr_id = f"slr-{student_id}-{course_id}"
    ms = MasteryState(id="mst_f1", slr_id=slr_id, concept_id="kinematics_accel", score=0.75, confidence=0.80)
    sm = StudentMisconceptionRecord(id="smr_f1", student_id=student_id, misconception_code="ACCEL_DECEL", frequency=1)
    ev = LearningEvent(id="ev_f1", session_id="sess_01", student_id=student_id, course_id=course_id, concept_id="kinematics_accel", event_type="QUESTION_ATTEMPTED")

    staged = commit_pipeline.stage_changes(
        student_id=student_id,
        course_id=course_id,
        mastery_updates=[ms],
        misconception_records=[sm],
        learning_events=[ev],
    )

    result = commit_pipeline.validate_and_commit(
        staged=staged,
        generated_response="Acceleration is the rate of change of velocity.",
        target_concept="kinematics_accel",
        fault_injection_point="after_mastery",
    )

    assert result.committed is False
    assert "Fault injected after mastery" in result.reason

    # ZERO PARTIAL WRITES: Mastery MUST be rolled back
    mastery_states = temp_db.get_mastery_states_for_slr(slr_id)
    assert len(mastery_states) == 0, "Mastery state should have been rolled back!"

    # Misconceptions and events must also be empty
    misconceptions = temp_db.get_student_misconceptions(student_id)
    assert len(misconceptions) == 0
    assert temp_db.get_learning_event("ev_f1") is None


def test_fault_injection_after_misconceptions_zero_partial_writes(temp_db, commit_pipeline):
    """Adversarial F-015: Fault injected after misconceptions triggers full rollback."""
    student_id = "stu_atomic_fault_02"
    course_id = "crs_physics_101"
    _bootstrap_entities(temp_db, student_id, course_id, session_id="sess_01", misc_code="FRICTION_ALWAYS_OPPOSES")

    slr_id = f"slr-{student_id}-{course_id}"
    ms = MasteryState(id="mst_f2", slr_id=slr_id, concept_id="forces_friction", score=0.60, confidence=0.80)
    sm = StudentMisconceptionRecord(id="smr_f2", student_id=student_id, misconception_code="FRICTION_ALWAYS_OPPOSES", frequency=1)
    ev = LearningEvent(id="ev_f2", session_id="sess_01", student_id=student_id, course_id=course_id, concept_id="forces_friction", event_type="QUESTION_ATTEMPTED")

    staged = commit_pipeline.stage_changes(
        student_id=student_id,
        course_id=course_id,
        mastery_updates=[ms],
        misconception_records=[sm],
        learning_events=[ev],
    )

    result = commit_pipeline.validate_and_commit(
        staged=staged,
        generated_response="Friction can oppose relative motion.",
        target_concept="forces_friction",
        fault_injection_point="after_misconceptions",
    )

    assert result.committed is False
    assert "Fault injected after misconception" in result.reason

    # ZERO PARTIAL WRITES: Neither mastery nor misconceptions may remain
    assert len(temp_db.get_mastery_states_for_slr(slr_id)) == 0
    assert len(temp_db.get_student_misconceptions(student_id)) == 0
    assert temp_db.get_learning_event("ev_f2") is None


def test_fault_injection_after_events_zero_partial_writes(temp_db, commit_pipeline):
    """Adversarial F-015: Fault injected after events triggers full rollback."""
    student_id = "stu_atomic_fault_03"
    course_id = "crs_physics_101"
    _bootstrap_entities(temp_db, student_id, course_id, session_id="sess_01", misc_code="HEAVIER_FALLS_FASTER")

    slr_id = f"slr-{student_id}-{course_id}"
    ms = MasteryState(id="mst_f3", slr_id=slr_id, concept_id="gravity", score=0.90, confidence=0.85)
    sm = StudentMisconceptionRecord(id="smr_f3", student_id=student_id, misconception_code="HEAVIER_FALLS_FASTER", frequency=1)
    ev = LearningEvent(id="ev_f3", session_id="sess_01", student_id=student_id, course_id=course_id, concept_id="gravity", event_type="QUESTION_ATTEMPTED")

    staged = commit_pipeline.stage_changes(
        student_id=student_id,
        course_id=course_id,
        mastery_updates=[ms],
        misconception_records=[sm],
        learning_events=[ev],
    )

    result = commit_pipeline.validate_and_commit(
        staged=staged,
        generated_response="All objects fall at the same rate in a vacuum.",
        target_concept="gravity",
        fault_injection_point="after_events",
    )

    assert result.committed is False
    assert "Fault injected after learning events" in result.reason

    # ZERO PARTIAL WRITES: None of the 3 entity types may remain in database
    assert len(temp_db.get_mastery_states_for_slr(slr_id)) == 0
    assert len(temp_db.get_student_misconceptions(student_id)) == 0
    assert temp_db.get_learning_event("ev_f3") is None


# ── 2. F-016: Database-Level Idempotency ────────────────────────────────────────

def test_event_deduplication_idempotency(temp_db):
    """Test F-016: Event uniqueness and deduplication at database level."""
    session_id = "sess_idem_01"
    student_id = "stu_idem_01"
    course_id = "crs_chem_101"
    _bootstrap_entities(temp_db, student_id, course_id, session_id=session_id)

    ev1 = LearningEvent(
        id="evt_unique_101",
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        concept_id="gas_laws",
        event_type="QUESTION_ATTEMPTED",
        score=0.9,
    )
    # First write
    temp_db.record_learning_event(ev1)

    # Duplicate write with identical ID (idempotent ignore)
    ev1_dup = LearningEvent(
        id="evt_unique_101",
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        concept_id="gas_laws",
        event_type="QUESTION_ATTEMPTED",
        score=0.5, # Divergent score to test duplicate rejection
    )
    temp_db.record_learning_event(ev1_dup)

    # Verify only original event exists and original score remains intact
    fetched = temp_db.get_learning_event("evt_unique_101")
    assert fetched is not None
    assert fetched.score == 0.9


# ── 3. F-017: Authoritative SLR & Elimination of Fabricated Defaults ───────────

def test_unassessed_learner_has_insufficient_evidence_status(slr_service):
    """Test F-017: Brand new student has INSUFFICIENT_EVIDENCE, score 0.0, empty concept_scores."""
    student_id = "stu_clean_unassessed_01"
    slr = slr_service.get_authoritative_slr(student_id, course_id="crs_math_101")

    assert slr.mastery.evidence_status == "INSUFFICIENT_EVIDENCE"
    assert slr.mastery.overall_score == 0.0
    assert slr.mastery.retention_rate == 0.0
    # ZERO fabricated Chemistry concepts
    assert slr.mastery.concept_scores == {}
    assert "chem_thermo_first_law" not in slr.mastery.concept_scores


def test_real_evidence_produces_evaluated_status_and_correct_score(slr_service):
    """Test F-017: SLR reflects real evidence when mastery is recorded."""
    student_id = "stu_real_evidence_01"
    course_id = "crs_math_101"

    # Update actual concept mastery
    slr = slr_service.update_concept_mastery(
        student_id=student_id,
        concept_id="calculus_derivatives",
        score=0.88,
        course_id=course_id,
        confidence=0.92,
    )

    assert slr.mastery.evidence_status == "EVALUATED"
    assert slr.mastery.overall_score == 0.88
    assert slr.mastery.concept_scores == {"calculus_derivatives": 0.88}
    assert "chem_thermo_first_law" not in slr.mastery.concept_scores


# ── 4. F-018: Multi-Tenant Scoping and Course Isolation ────────────────────────

def test_multi_course_slr_isolation(slr_service):
    """Test F-018: Concept mastery in Course A does not bleed into Course B for the same student."""
    student_id = "stu_multi_course_01"
    course_a = "crs_biology_101"
    course_b = "crs_physics_101"

    # Update Course A
    slr_service.update_concept_mastery(student_id, "bio_cell_membrane", 0.95, course_id=course_a)

    # Check Course A SLR
    slr_a = slr_service.get_authoritative_slr(student_id, course_id=course_a)
    assert "bio_cell_membrane" in slr_a.mastery.concept_scores
    assert slr_a.mastery.overall_score == 0.95

    # Check Course B SLR: Must have ZERO records from Course A
    slr_b = slr_service.get_authoritative_slr(student_id, course_id=course_b)
    assert "bio_cell_membrane" not in slr_b.mastery.concept_scores
    assert slr_b.mastery.overall_score == 0.0
    assert slr_b.mastery.evidence_status == "INSUFFICIENT_EVIDENCE"


# ── 5. PlatformDatabase Nested Transaction & Savepoint Semantics ───────────────

def test_database_nested_savepoints(temp_db):
    """Test PlatformDatabase nested savepoint rollback and commit semantics."""
    student_id = "stu_savepoint_01"
    course_id = "crs_sp_01"
    _bootstrap_entities(temp_db, student_id, course_id)

    slr_id = f"slr-{student_id}-{course_id}"

    with temp_db.transaction():
        # Outer write 1
        temp_db.upsert_mastery_state(MasteryState(id="mst_sp_1", slr_id=slr_id, concept_id="sp_concept_1", score=0.8, confidence=0.8))

        # Inner transaction that rolls back
        try:
            with temp_db.transaction():
                temp_db.upsert_mastery_state(MasteryState(id="mst_sp_2", slr_id=slr_id, concept_id="sp_concept_2", score=0.4, confidence=0.8))
                raise ValueError("Inner failure")
        except ValueError:
            pass # Inner failure handled

        # Outer write 2
        temp_db.upsert_mastery_state(MasteryState(id="mst_sp_3", slr_id=slr_id, concept_id="sp_concept_3", score=0.9, confidence=0.8))

    # Outer committed: sp_concept_1 and sp_concept_3 exist; sp_concept_2 was rolled back
    states = temp_db.get_mastery_states_for_slr(slr_id)
    cids = {s.concept_id for s in states}
    assert "sp_concept_1" in cids
    assert "sp_concept_3" in cids
    assert "sp_concept_2" not in cids, "Inner rolled back savepoint leaked into database!"
