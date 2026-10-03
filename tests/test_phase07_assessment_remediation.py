"""Phase 7: Assessment Correctness and Learner Evidence Verification Suite.

Master Plan Section 12 / Section 28 Requirements:
1. Fail-closed entity validation (No silent auto-provisioning of courses/students/orgs).
2. Deterministic numerical grading edge cases (0, -0, 1e-3, 1E3, NaN, Infinity, units, multiple numbers).
3. Deterministic MCQ and Boolean grading equivalence and normalization.
4. Subjective rubric evaluation transparency (dynamic confidence, documented rule-based evaluator limitations).
5. Attempt lifecycle and SLR synchronization:
   - In-progress attempts do NOT advance SLR concept mastery or emit learning events.
   - Mismatched student ID submission rejected.
   - Double-submission of finalized attempts rejected.
   - Finalized submission updates authoritative SLR concept mastery and learning event store.
"""

import math
import pytest
from central_platform.assessment.grading import (
    AIAssistedGrader,
    AssessmentGradingEngine,
    DeterministicGrader,
)
from central_platform.assessment.models import (
    AssessmentType,
    AttemptStatus,
    Rubric,
    RubricCriterion,
)
from central_platform.assessment.service import AssessmentService
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import (
    Assessment,
    Course,
    Organization,
    QuestionBankItem,
    User,
    UserRole,
)
from central_platform.slr.service import SLRService


@pytest.fixture
def test_db():
    db = PlatformDatabase(":memory:")
    # Seed known organizations, courses, and students
    db.create_organization(Organization(id="org-academics", name="Academic Institution", slug="academics"))
    db.create_organization(Organization(id="org-other", name="Other Institution", slug="other"))

    db.create_course(Course(id="crs-physics-101", organization_id="org-academics", code="PHYS101", title="Physics I"))
    db.create_course(Course(id="crs-math-201", organization_id="org-academics", code="MATH201", title="Calculus II"))

    db.create_user(User(id="stu-phys-01", email="phys01@academics.edu", full_name="Alice Student", role=UserRole.STUDENT, organization_id="org-academics"))
    db.create_user(User(id="stu-other-01", email="other@other.edu", full_name="Foreign Student", role=UserRole.STUDENT, organization_id="org-other"))
    db.create_user(User(id="tch-phys-01", email="tch01@academics.edu", full_name="Dr. Newton", role=UserRole.TEACHER, organization_id="org-academics"))
    return db


@pytest.fixture
def assessment_service(test_db):
    event_store = LearningEventStore(test_db)
    slr_service = SLRService(test_db, event_store)
    return AssessmentService(db=test_db, event_store=event_store, slr_service=slr_service, allow_auto_provision=False)


# ── 1. Fail-Closed Entity Validation (No Silent Auto-Provisioning) ────────────

def test_entity_validation_missing_course_rejected(assessment_service):
    """Creating items or assessments with non-existent course must fail closed."""
    q_item = QuestionBankItem(
        id="qb-ghost-01",
        course_id="crs-non-existent",
        concept_id="quantum_gravity",
        question_text="Sample question",
        item_type="MCQ",
        correct_answer="A",
    )
    with pytest.raises(ValueError, match="Course 'crs-non-existent' not found"):
        assessment_service.create_question(q_item)

    asmt = Assessment(
        id="asmt-ghost-01",
        course_id="crs-non-existent",
        title="Ghost Assessment",
    )
    with pytest.raises(ValueError, match="Course 'crs-non-existent' not found"):
        assessment_service.create_assessment(asmt)


def test_entity_validation_missing_student_rejected(assessment_service):
    """Starting an attempt for a non-existent student must fail closed."""
    asmt = Assessment(
        id="asmt-valid-01",
        course_id="crs-physics-101",
        title="Physics Midterm",
    )
    assessment_service.create_assessment(asmt)

    with pytest.raises(ValueError, match="Student 'stu-ghost-99' not found"):
        assessment_service.start_attempt("asmt-valid-01", "stu-ghost-99")


def test_entity_validation_wrong_organization_rejected(assessment_service):
    """Starting an attempt where student organization does not match assessment org must fail closed."""
    asmt = Assessment(
        id="asmt-org-scoped",
        course_id="crs-physics-101",
        organization_id="org-academics",
        title="Scoped Physics Exam",
    )
    assessment_service.create_assessment(asmt)

    # Student belongs to org-other, assessment is org-academics
    with pytest.raises(ValueError, match="belongs to organization 'org-other', not 'org-academics'"):
        assessment_service.start_attempt("asmt-org-scoped", "stu-other-01")


# ── 2. Deterministic Numerical Grading Edge Cases ────────────────────────────

def test_numerical_zero_and_negative_zero():
    """Verify 0, -0, and +0 evaluate as equivalent zero magnitude."""
    is_corr, score, _ = DeterministicGrader.grade_numerical("0", "0")
    assert is_corr is True
    assert score == 1.0

    is_corr, score, _ = DeterministicGrader.grade_numerical("-0", "0")
    assert is_corr is True
    assert score == 1.0

    is_corr, score, _ = DeterministicGrader.grade_numerical("+0.0", "0.0")
    assert is_corr is True
    assert score == 1.0


def test_numerical_scientific_notation():
    """Verify scientific notation handling (1e-3, 1E3, 1.5e-4)."""
    # 1e-3 == 0.001
    is_corr, score, _ = DeterministicGrader.grade_numerical("1e-3", "0.001")
    assert is_corr is True
    assert score == 1.0

    # 1E3 == 1000.0
    is_corr, score, _ = DeterministicGrader.grade_numerical("1E3", "1000")
    assert is_corr is True
    assert score == 1.0

    # 1.5e-4 vs 0.00015
    is_corr, score, _ = DeterministicGrader.grade_numerical("1.5e-4", "0.00015")
    assert is_corr is True


def test_numerical_nan_and_infinity_rejection():
    """Adversarial test: NaN, Infinity, and inf must be rejected."""
    for bad_val in ["NaN", "nan", "Infinity", "-Infinity", "inf", "-inf"]:
        is_corr, score, fb = DeterministicGrader.grade_numerical(bad_val, "10.0")
        assert is_corr is False
        assert score == 0.0
        assert "NaN" in fb or "Infinity" in fb


def test_numerical_units_only_rejected():
    """Adversarial test: Unit string without magnitude must fail numerical parsing."""
    for unit_only in ["kJ", "m/s", "kg", "seconds", "%"]:
        is_corr, score, fb = DeterministicGrader.grade_numerical(unit_only, "50.0 kJ")
        assert is_corr is False
        assert score == 0.0
        assert "without numerical magnitude" in fb or "Could not parse" in fb


def test_numerical_multiple_numbers_in_explanation():
    """Do not accept first number blindly if multiple numbers exist without designation."""
    # Ambiguous explanation with multiple numbers -> reject
    ambiguous = "I calculated 15 first and then changed it to 30."
    is_corr, score, fb = DeterministicGrader.grade_numerical(ambiguous, "30.0")
    assert is_corr is False
    assert score == 0.0
    assert "multiple numerical values" in fb

    # Explicit answer designation -> correctly resolves
    designated = "Step 1 gave 15, but final answer = 30."
    is_corr, score, fb = DeterministicGrader.grade_numerical(designated, "30.0")
    assert is_corr is True
    assert score == 1.0


def test_numerical_unit_verification():
    """Verify correct value with wrong unit fails, correct value with correct unit passes."""
    # Correct value with correct unit -> Pass
    is_corr, score, _ = DeterministicGrader.grade_numerical("-110.5 kJ", "-110.5 kJ")
    assert is_corr is True
    assert score == 1.0

    # Correct value with wrong unit -> Fail
    is_corr, score, fb = DeterministicGrader.grade_numerical("-110.5 J", "-110.5 kJ")
    assert is_corr is False
    assert score == 0.0
    assert "Incorrect unit" in fb

    # Wrong value with correct unit -> Fail
    is_corr, score, fb = DeterministicGrader.grade_numerical("-50.0 kJ", "-110.5 kJ")
    assert is_corr is False
    assert score == 0.0
    assert "Incorrect calculation" in fb

    # Missing unit when expected -> Fail
    is_corr, score, fb = DeterministicGrader.grade_numerical("-110.5", "-110.5 kJ")
    assert is_corr is False
    assert "Missing required unit" in fb


# ── 3. Deterministic MCQ and Boolean Grading ─────────────────────────────────

def test_mcq_letter_and_content_equivalence():
    """Verify MCQ grading handles letters, parenthesized letters, and option text."""
    options = ["Newton", "Joule", "Watt", "Pascal"]

    # Option A (index 0) is "Newton"
    is_corr, score, _ = DeterministicGrader.grade_mcq("A", "Newton", options)
    assert is_corr is True

    is_corr, score, _ = DeterministicGrader.grade_mcq("(a)", "Newton", options)
    assert is_corr is True

    is_corr, score, _ = DeterministicGrader.grade_mcq("Option A", "Newton", options)
    assert is_corr is True

    is_corr, score, _ = DeterministicGrader.grade_mcq("newton", "Newton", options)
    assert is_corr is True

    is_corr, score, _ = DeterministicGrader.grade_mcq("B", "Newton", options)
    assert is_corr is False


def test_boolean_grading_normalization():
    """Verify True/False, T/F, yes/no normalization."""
    for truthy in ["True", "true", "T", "t", "yes", "1"]:
        is_corr, score, _ = DeterministicGrader.grade_boolean(truthy, "True")
        assert is_corr is True
        assert score == 1.0

    for falsy in ["False", "false", "F", "f", "no", "0"]:
        is_corr, score, _ = DeterministicGrader.grade_boolean(falsy, "False")
        assert is_corr is True
        assert score == 1.0

    is_corr, score, _ = DeterministicGrader.grade_boolean("False", "True")
    assert is_corr is False


# ── 4. Subjective Rubric Evaluation Transparency ─────────────────────────────

def test_rubric_evaluation_dynamic_confidence_and_limitations():
    """Verify rubric scoring calculates dynamic confidence and documents rule-based limitations."""
    q_essay = QuestionBankItem(
        id="qb-essay-transparency",
        course_id="crs-physics-101",
        concept_id="newtons_second_law",
        question_text="Explain the relationship between net force, mass, and acceleration.",
        item_type="SHORT_ANSWER",
        correct_answer="Net force equals mass times acceleration (F = ma).",
        difficulty=3,
    )

    # 1. High keyword coverage response
    ans_good = "Net force is directly proportional to acceleration and inversely to mass, following F = ma."
    res_good = AIAssistedGrader.grade_with_rubric(q_essay, ans_good)
    assert res_good.ai_graded is True
    # Confidence must be dynamically derived, not hardcoded 0.92
    assert 0.50 <= res_good.ai_confidence <= 0.99
    # Rationale must document Rule-Based Rubric Engine limitations
    assert "Rule-Based Rubric Engine" in res_good.ai_rationale
    assert "limitations" in res_good.ai_rationale.lower()

    # 2. Blank answer submitted
    res_blank = AIAssistedGrader.grade_with_rubric(q_essay, "")
    assert res_blank.is_correct is False
    assert res_blank.score == 0.0


# ── 5. Attempt Lifecycle and SLR Synchronization ─────────────────────────────

def test_in_progress_attempt_does_not_alter_slr(assessment_service, test_db):
    """Invariant: An in-progress assessment attempt must NOT alter SLR mastery or emit learning events."""
    q = QuestionBankItem(
        id="qb-phys-law",
        course_id="crs-physics-101",
        concept_id="phys_newton_law",
        question_text="Force equals mass times what?",
        item_type="MCQ",
        correct_answer="Acceleration",
        difficulty=2,
    )
    assessment_service.create_question(q)

    asmt = Assessment(
        id="asmt-phys-quiz",
        course_id="crs-physics-101",
        title="Newton Quiz",
        item_ids=["qb-phys-law"],
    )
    assessment_service.create_assessment(asmt)

    # Student starts attempt
    attempt = assessment_service.start_attempt("asmt-phys-quiz", "stu-phys-01")
    assert attempt.status == AttemptStatus.IN_PROGRESS.value

    # Verify ZERO learning events were emitted
    events = assessment_service.event_store.get_student_events("stu-phys-01")
    assert len(events) == 0

    # Verify SLR concept mastery is UNASSESSED / INSUFFICIENT_EVIDENCE (0.0)
    slr = assessment_service.slr_service.get_authoritative_slr("stu-phys-01", "crs-physics-101")
    assert slr.mastery.evidence_status == "INSUFFICIENT_EVIDENCE"
    assert slr.mastery.overall_score == 0.0
    assert "phys_newton_law" not in slr.mastery.concept_scores


def test_submit_attempt_updates_slr_and_learning_events(assessment_service):
    """Submitting finalized attempt ingests learning events and authoritatively updates SLR."""
    q = QuestionBankItem(
        id="qb-phys-sub",
        course_id="crs-physics-101",
        concept_id="phys_acceleration",
        question_text="What is acceleration?",
        item_type="MCQ",
        correct_answer="Rate of change of velocity",
        difficulty=2,
    )
    assessment_service.create_question(q)

    asmt = Assessment(
        id="asmt-phys-sub",
        course_id="crs-physics-101",
        title="Acceleration Test",
        item_ids=["qb-phys-sub"],
    )
    assessment_service.create_assessment(asmt)

    attempt = assessment_service.start_attempt("asmt-phys-sub", "stu-phys-01")

    # Submit correct answer
    completed = assessment_service.submit_attempt(
        attempt_id=attempt.id,
        answers={"qb-phys-sub": "Rate of change of velocity"},
        student_id="stu-phys-01",
    )
    assert completed.status == AttemptStatus.GRADED.value
    assert completed.passed is True

    # 1. Verify Learning Events persisted
    events = assessment_service.event_store.get_student_events("stu-phys-01")
    types = [e.event_type for e in events]
    assert LearningEventType.QUESTION_ATTEMPTED.value in types
    assert LearningEventType.ASSESSMENT_COMPLETED.value in types

    # 2. Verify SLR updated authoritatively with evidence
    slr = assessment_service.slr_service.get_authoritative_slr("stu-phys-01", "crs-physics-101")
    assert slr.mastery.overall_score > 0.0
    assert "phys_acceleration" in slr.mastery.concept_scores
    assert slr.mastery.concept_scores["phys_acceleration"] == 1.0


def test_adversarial_attempt_student_mismatch_and_double_submit(assessment_service):
    """Adversarial test: Submitting for another student or re-submitting finalized attempt is rejected."""
    asmt = Assessment(
        id="asmt-phys-sec",
        course_id="crs-physics-101",
        title="Security Test",
    )
    assessment_service.create_assessment(asmt)

    attempt = assessment_service.start_attempt("asmt-phys-sec", "stu-phys-01")

    # Mismatched student ID attempt
    with pytest.raises(ValueError, match="Student ID mismatch"):
        assessment_service.submit_attempt(attempt.id, answers={}, student_id="stu-impostor")

    # Submit validly
    assessment_service.submit_attempt(attempt.id, answers={}, student_id="stu-phys-01")

    # Double-submit attempt -> Must be rejected
    with pytest.raises(ValueError, match="already finalized"):
        assessment_service.submit_attempt(attempt.id, answers={}, student_id="stu-phys-01")
