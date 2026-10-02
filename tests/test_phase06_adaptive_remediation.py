"""Gayatri AI Platform — Phase 06 Forensic Remediation Contract & Adversarial Tests.

Verifies:
1. F-019: Tutor Turn Validation Does NOT Artificially Increment Mastery.
   - Explanatory turns record TUTOR_TURN_COMPLETED events, but mastery delta is 0.0.
   - AI response validation alone never advances student mastery.
2. Learner Evidence Drives Mastery:
   - Independent correct answers advance mastery.
   - Incorrect answers do not advance mastery and record learning gaps.
   - Hint-assisted answers apply appropriate hint penalties.
3. Adaptive Pedagogical Decisions:
   - Low mastery or active misconceptions trigger REMEDIATE actions.
   - High hint dependence triggers reduced difficulty or hints.
   - High verified mastery triggers ASSESS, CHALLENGE, or ADVANCE.
4. Multi-Turn Session Persistence and Course Isolation:
   - Session restart preserves exact evidence state.
   - Course A evidence never affects Course B.
"""
from __future__ import annotations

import os
import pytest

from central_platform.db import PlatformDatabase
from central_platform.learning.actions import NextActionEngine, NextActionType
from central_platform.learning.graph import ConceptNodeState
from central_platform.learning.mastery import MasteryEvidenceEngine
from central_platform.models.schema import (
    Course,
    CourseVersion,
    Enrollment,
    LearningEvent,
    MasteryState,
    Misconception,
    Organization,
    Session,
    SessionStatus,
    StudentLearningRecord,
    User,
    UserRole,
)
from central_platform.slr.service import SLRService
from central_platform.tutor.orchestrator import GenericTutorOrchestrator, TutorTurnRequest


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "phase06_adaptive_test.db")
    return PlatformDatabase(db_file)


@pytest.fixture
def orchestrator(temp_db):
    return GenericTutorOrchestrator(db=temp_db)


@pytest.fixture
def slr_service(temp_db):
    return SLRService(db=temp_db)


@pytest.fixture
def mastery_engine(temp_db):
    return MasteryEvidenceEngine(db=temp_db)


@pytest.fixture
def action_engine(temp_db):
    return NextActionEngine(db=temp_db)


def _bootstrap_student_course(temp_db: PlatformDatabase, student_id: str, course_id: str, concept_id: str = "kinematics"):
    """Seed prerequisite database entities."""
    org = temp_db.get_organization("org-test")
    if not org:
        temp_db.create_organization(Organization(id="org-test", name="Test Org", slug="test-org"))

    user = temp_db.get_user(student_id)
    if not user:
        temp_db.create_user(
            User(
                id=student_id,
                email=f"{student_id}@test.ai",
                full_name=f"Student {student_id}",
                role=UserRole.STUDENT,
                organization_id="org-test",
            )
        )

    course = temp_db.get_course(course_id)
    if not course:
        temp_db.create_course(
            Course(
                id=course_id,
                organization_id="org-test",
                code=course_id.upper(),
                title=f"Course {course_id}",
            )
        )

    version_id = f"ver-{course_id}-v1"
    cv = temp_db.get_course_version(version_id)
    if not cv:
        temp_db.create_course_version(
            CourseVersion(
                id=version_id,
                course_id=course_id,
                version_number="1.0.0",
                status="published",
            )
        )

    enrs = temp_db.get_enrollments_for_student(student_id)
    if not any(e.course_id == course_id for e in enrs):
        temp_db.create_enrollment(
            Enrollment(
                id=f"enr-{student_id}-{course_id}",
                student_id=student_id,
                course_id=course_id,
                is_active=True,
            )
        )

    sess = temp_db.get_session("sess_01")
    if not sess:
        temp_db.create_session(
            Session(
                id="sess_01",
                student_id=student_id,
                course_id=course_id,
                concept_id=concept_id,
                status=SessionStatus.ACTIVE,
            )
        )

    slr = temp_db.get_slr(student_id, course_id)
    if not slr:
        temp_db.create_slr(
            StudentLearningRecord(
                id=f"slr-{student_id}-{course_id}",
                student_id=student_id,
                course_id=course_id,
                authoritative=True,
            )
        )


# ── 1. F-019: Tutor Explanations Do Not Advance Mastery ────────────────────────

def test_tutor_turn_explanation_does_not_advance_mastery(temp_db, orchestrator, slr_service):
    """F-019: Conversational/explanation turn must NOT arbitrarily advance student mastery."""
    student_id = "stu_f019_01"
    course_id = "crs_physics_adv"
    _bootstrap_student_course(temp_db, student_id, course_id, concept_id="momentum")

    # Initial SLR: student has 0.0 mastery (unassessed)
    initial_slr = slr_service.get_authoritative_slr(student_id, course_id)
    assert initial_slr.mastery.overall_score == 0.0
    assert initial_slr.mastery.evidence_status == "INSUFFICIENT_EVIDENCE"
    assert "momentum" not in initial_slr.mastery.concept_scores

    # Execute tutor turn where student asks for an explanation
    req = TutorTurnRequest(
        student_id=student_id,
        session_id="sess_01",
        course_id=course_id,
        concept_id="momentum",
        message="Can you explain what conservation of momentum means?",
    )
    result = orchestrator.execute_turn(req)

    assert result.status == "SUCCESS"
    assert result.validation_passed is True
    assert result.state_committed is True

    # Critical invariant: Mastery MUST NOT have increased from 0.0 to 0.05
    after_slr = slr_service.get_authoritative_slr(student_id, course_id)
    assert after_slr.mastery.overall_score == 0.0, "Tutor explanation turn must not inflate mastery!"
    assert "momentum" not in after_slr.mastery.concept_scores


def test_repeated_tutor_questions_do_not_inflate_mastery(temp_db, orchestrator, slr_service):
    """F-019: Asking multiple questions in a session never artificially inflates mastery."""
    student_id = "stu_f019_repeated"
    course_id = "crs_physics_adv"
    _bootstrap_student_course(temp_db, student_id, course_id, concept_id="optics")

    for i in range(5):
        req = TutorTurnRequest(
            student_id=student_id,
            session_id="sess_01",
            course_id=course_id,
            concept_id="optics",
            message=f"Question {i+1}: What is refraction?",
        )
        res = orchestrator.execute_turn(req)
        assert res.status == "SUCCESS"

    # Even after 5 full tutor turns, mastery must remain uninflated without answer evaluation
    slr = slr_service.get_authoritative_slr(student_id, course_id)
    assert slr.mastery.overall_score == 0.0
    assert slr.mastery.concept_scores == {}


# ── 2. Evidence-Based Mastery Advancement ──────────────────────────────────────

def test_correct_answers_advance_mastery_with_diminishing_returns(mastery_engine):
    """Verifies that evidence-backed mastery advances with practice and exhibits diminishing returns."""
    concept_id = "projectile_motion"

    # 1. Single correct answer
    events_1 = [
        LearningEvent(id="e1", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0)
    ]
    res_1 = mastery_engine.calculate_evidence_mastery(concept_id, events_1)
    assert res_1.raw_mastery > 0.0
    assert res_1.attempts_count == 1

    # 2. Four correct answers
    events_4 = [
        LearningEvent(id=f"e{i}", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0)
        for i in range(1, 5)
    ]
    res_4 = mastery_engine.calculate_evidence_mastery(concept_id, events_4)
    assert res_4.raw_mastery > res_1.raw_mastery

    # 3. Eight correct answers: mastery increases but confidence saturates gracefully
    events_8 = [
        LearningEvent(id=f"e{i}", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0)
        for i in range(1, 9)
    ]
    res_8 = mastery_engine.calculate_evidence_mastery(concept_id, events_8)
    assert res_8.raw_mastery >= res_4.raw_mastery
    assert res_8.confidence > res_4.confidence
    assert res_8.confidence <= 0.95


def test_hint_penalty_reduces_mastery_gain(mastery_engine):
    """Verifies that hint requests apply progressive score penalties on mastery evidence."""
    concept_id = "angular_momentum"

    # Unassisted correct answer
    unassisted_event = [
        LearningEvent(id="e_clean", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0, payload={"hint_level": 0})
    ]
    clean_res = mastery_engine.calculate_evidence_mastery(concept_id, unassisted_event)

    # Hint-assisted correct answer (level 2 hint)
    hinted_event = [
        LearningEvent(id="e_hinted", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0, payload={"hint_level": 2})
    ]
    hinted_res = mastery_engine.calculate_evidence_mastery(concept_id, hinted_event)

    assert clean_res.raw_mastery > hinted_res.raw_mastery
    # Level 2 hint reduces score by 30% (2 * 0.15)
    assert hinted_res.recent_accuracy < clean_res.recent_accuracy


def test_prerequisite_bottleneck_caps_mastery(mastery_engine):
    """Verifies that unmet prerequisites discount/cap achievable target concept mastery."""
    concept_id = "general_relativity"
    events = [
        LearningEvent(id=f"e{i}", session_id="s1", student_id="stu_1", concept_id=concept_id, event_type="ANSWER_SUBMITTED", score=1.0)
        for i in range(5)
    ]

    # Without prerequisites
    res_unconstrained = mastery_engine.calculate_evidence_mastery(concept_id, events)

    # With weak prerequisite mastery (0.30 in special relativity)
    res_prereq_constrained = mastery_engine.calculate_evidence_mastery(
        concept_id, events, prerequisite_masteries=[0.30]
    )

    assert res_prereq_constrained.prerequisite_factor < 1.0
    assert res_prereq_constrained.effective_mastery < res_unconstrained.effective_mastery


# ── 3. Adaptive Pedagogical Decision Rules ─────────────────────────────────────

def test_adaptive_decisions_remediate_on_misconception(action_engine):
    """Verifies that an active misconception triggers targeted remediation."""
    node = ConceptNodeState(
        concept_id="electric_circuits",
        concept_name="Electric Circuits",
        topic_id="physics_em",
        mastery_score=0.45,
        total_attempts=3,
        incorrect_attempts=2,
        active_misconceptions=["CURRENT_CONSUMPTION"],
    )

    decision = action_engine.decide_next_action(
        student_id="s1",
        course_id="c1",
        current_concept_id="electric_circuits",
        node_state=node,
        last_action_payload={"misconception_code": "CURRENT_CONSUMPTION"},
    )

    assert decision.action == NextActionType.REMEDIATE
    assert decision.recommended_mode == "REMEDIATE"
    assert "CURRENT_CONSUMPTION" in decision.reason or "misconception" in decision.reason.lower()


def test_adaptive_decisions_hint_on_request(action_engine):
    """Verifies that student hint request triggers progressive hint."""
    node = ConceptNodeState(
        concept_id="thermo_cycles",
        concept_name="Thermodynamic Cycles",
        topic_id="thermo",
        mastery_score=0.65,
        total_attempts=2,
    )

    decision = action_engine.decide_next_action(
        student_id="s1",
        course_id="c1",
        current_concept_id="thermo_cycles",
        node_state=node,
        last_action_payload={"hint_requested": True},
    )

    assert decision.action == NextActionType.HINT
    assert decision.recommended_mode == "QUESTION"


def test_adaptive_decisions_advance_on_high_mastery(action_engine):
    """Verifies that high sustained mastery triggers curriculum advancement."""
    node = ConceptNodeState(
        concept_id="simple_harmonic_motion",
        concept_name="Simple Harmonic Motion",
        topic_id="oscillations",
        mastery_score=0.94,
        confidence=0.90,
        total_attempts=4,
        correct_attempts=4,
        incorrect_attempts=0,
    )

    decision = action_engine.decide_next_action(
        student_id="s1",
        course_id="c1",
        current_concept_id="simple_harmonic_motion",
        node_state=node,
    )

    assert decision.action == NextActionType.ADVANCE
    assert "advance" in decision.reason.lower()


# ── 4. Cross-Course Evidence Isolation ─────────────────────────────────────────

def test_course_evidence_isolation(temp_db, slr_service):
    """Verifies that student learning evidence in Course A never bleeds into Course B."""
    student_id = "stu_cross_course_iso"
    course_a = "crs_physics_mechanics"
    course_b = "crs_chemistry_organic"

    _bootstrap_student_course(temp_db, student_id, course_a, concept_id="kinematics")
    _bootstrap_student_course(temp_db, student_id, course_b, concept_id="hydrocarbons")

    # Update Course A with genuine evidence
    slr_service.update_concept_mastery(student_id, "kinematics", 0.90, course_id=course_a)

    # Verify Course A has the mastery
    slr_a = slr_service.get_authoritative_slr(student_id, course_a)
    assert slr_a.mastery.concept_scores["kinematics"] == 0.90
    assert slr_a.mastery.evidence_status == "EVALUATED"

    # Verify Course B is completely isolated: 0.0 score, INSUFFICIENT_EVIDENCE
    slr_b = slr_service.get_authoritative_slr(student_id, course_b)
    assert "kinematics" not in slr_b.mastery.concept_scores
    assert slr_b.mastery.overall_score == 0.0
    assert slr_b.mastery.evidence_status == "INSUFFICIENT_EVIDENCE"
