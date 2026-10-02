"""Phase 11: Generic Assessment & Evaluation Engine Test Suite.

Verifies:
1. Generic item types (MCQ, Numerical, Boolean, Rubric, Code execution).
2. Uncertain answers (ambiguous single words like "idk", "maybe", empty input).
3. Malformed answers (invalid numerical format, syntax error in code).
4. Unit mismatch evaluation (correct number, wrong unit -> PARTIALLY_CORRECT with error_type="unit").
5. Anti-answer-leakage service: active student payloads strip answers, rubrics, and explanations.
6. Course and version scoping: assessments strictly isolated between courses with zero cross-talk.
7. Teacher manual review and score adjustment lifecycle.
8. Targeted remediation recommendations without cross-course contamination.
9. Architecture Invariant: Generic evaluator modules contain zero hardcoded chemistry keywords.
"""
from __future__ import annotations

import inspect
import pytest

from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)
from central_platform.assessment.evaluators.code import CodeExecutionEvaluator
from central_platform.assessment.evaluators.deterministic import (
    BooleanEvaluator,
    MCQEvaluator,
    NumericalEvaluator,
)
from central_platform.assessment.evaluators.registry import (
    DEFAULT_EVALUATOR_REGISTRY,
    EvaluatorRegistry,
)
from central_platform.assessment.evaluators.rubric import RubricEvaluator
from central_platform.assessment.models import (
    AssessmentType,
    AttemptStatus,
    Rubric,
    RubricCriterion,
)
from central_platform.assessment.sanitizer import AssessmentSanitizer
from central_platform.assessment.service import AssessmentService
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Assessment,
    AssessmentAttempt,
    AssessmentItem,
    Course,
    CourseStatus,
    CourseVersion,
    CourseVisibility,
    Organization,
    QuestionBankItem,
    User,
    UserRole,
)


@pytest.fixture
def test_db():
    db = PlatformDatabase(":memory:")
    # Seed default organizations & admin
    db.create_organization(
        Organization(
            id="org-core",
            name="Core Academic Institution",
            slug="core-academic",
        )
    )
    db.create_user(
        User(
            id="teacher-01",
            organization_id="org-core",
            email="teacher@core.edu",
            full_name="Prof. Johnson",
            role=UserRole.TEACHER,
        )
    )
    db.create_user(
        User(
            id="student-phys-01",
            organization_id="org-core",
            email="stu-phys@core.edu",
            full_name="Alice Physics",
            role=UserRole.STUDENT,
        )
    )
    db.create_user(
        User(
            id="student-cs-01",
            organization_id="org-core",
            email="stu-cs@core.edu",
            full_name="Bob Coder",
            role=UserRole.STUDENT,
        )
    )
    # Seed courses used in tests
    db.create_course(
        Course(
            id="course-phys-1",
            organization_id="org-core",
            code="PHYS101",
            title="Physics I",
        )
    )
    db.create_course(
        Course(
            id="course-cs-1",
            organization_id="org-core",
            code="CS101",
            title="Computer Science I",
        )
    )
    return db


@pytest.fixture
def assessment_service(test_db):
    return AssessmentService(db=test_db)


# ── 1. Generic Deterministic Evaluators ────────────────────────────────────────

def test_generic_mcq_evaluation():
    """Verify MCQEvaluator across option letter, content match, and numeric indices."""
    evaluator = MCQEvaluator()
    item = QuestionBankItem(
        id="q-mcq-1",
        course_id="course-physics",
        concept_id="newton_laws",
        question_text="What is the unit of force in SI units?",
        item_type="MCQ",
        options=["Joule", "Newton", "Watt", "Pascal"],
        correct_answer="Newton",
        difficulty=1,
    )

    # 1. Option content match
    res1 = evaluator.evaluate(item, "Newton")
    assert res1.outcome == EvaluationStatus.CORRECT
    assert res1.score == 1.0

    # 2. Option letter index ('B' -> Newton)
    res2 = evaluator.evaluate(item, "B")
    assert res2.outcome == EvaluationStatus.CORRECT
    assert res2.score == 1.0

    # 3. Option index (1-based: "2")
    res3 = evaluator.evaluate(item, "2")
    assert res3.outcome == EvaluationStatus.CORRECT
    assert res3.score == 1.0

    # 4. Incorrect option
    res4 = evaluator.evaluate(item, "A")
    assert res4.outcome == EvaluationStatus.INCORRECT
    assert res4.score == 0.0


def test_generic_numerical_evaluation():
    """Verify NumericalEvaluator handles calculations with tolerance."""
    evaluator = NumericalEvaluator()
    item = QuestionBankItem(
        id="q-num-1",
        course_id="course-physics",
        concept_id="kinematics",
        question_text="Calculate velocity after 3s with initial v=0 and a=9.8 m/s^2.",
        item_type="NUMERICAL",
        correct_answer="29.4",
        difficulty=2,
    )

    # Exact
    res1 = evaluator.evaluate(item, "29.4")
    assert res1.outcome == EvaluationStatus.CORRECT
    assert res1.score == 1.0

    # Within 2% tolerance (e.g. 29.5 -> ~0.34% diff)
    res2 = evaluator.evaluate(item, "29.5")
    assert res2.outcome == EvaluationStatus.CORRECT
    assert res2.score == 1.0

    # Out of tolerance (e.g. 35.0)
    res3 = evaluator.evaluate(item, "35.0")
    assert res3.outcome == EvaluationStatus.INCORRECT
    assert res3.score == 0.0
    assert res3.error_type == "arithmetic"


def test_numerical_unit_mismatch():
    """Verify NumericalEvaluator checks unit matching and awards PARTIALLY_CORRECT on mismatch."""
    evaluator = NumericalEvaluator()
    item = QuestionBankItem(
        id="q-num-unit",
        course_id="course-physics",
        concept_id="kinematics",
        question_text="Calculate speed (expected in m/s).",
        item_type="NUMERICAL",
        correct_answer="50.0 m/s",
        difficulty=2,
    )

    # Correct number with correct unit
    res_correct = evaluator.evaluate(item, "50.0 m/s")
    assert res_correct.outcome == EvaluationStatus.CORRECT
    assert res_correct.score == 1.0
    assert res_correct.error_type == "none"

    # Correct number but wrong or missing unit
    res_missing_unit = evaluator.evaluate(item, "50.0 km/h")
    assert res_missing_unit.outcome == EvaluationStatus.PARTIALLY_CORRECT
    assert res_missing_unit.score == 0.7
    assert res_missing_unit.error_type == "unit"
    assert "unit" in res_missing_unit.feedback.lower()


def test_boolean_evaluation():
    """Verify BooleanEvaluator handles True/False and Boolean representations."""
    evaluator = BooleanEvaluator()
    item = QuestionBankItem(
        id="q-bool-1",
        course_id="course-cs",
        concept_id="boolean_logic",
        question_text="Is Python a dynamically typed language?",
        item_type="BOOLEAN",
        correct_answer="True",
        difficulty=1,
    )

    res_t = evaluator.evaluate(item, "true")
    assert res_t.outcome == EvaluationStatus.CORRECT
    assert res_t.score == 1.0

    res_f = evaluator.evaluate(item, "false")
    assert res_f.outcome == EvaluationStatus.INCORRECT
    assert res_f.score == 0.0

    res_malformed = evaluator.evaluate(item, "not sure at all")
    assert res_malformed.outcome == EvaluationStatus.UNCERTAIN
    assert res_malformed.error_type == "malformed"


# ── 2. Code Execution and Syntax Evaluator ─────────────────────────────────────

def test_code_execution_evaluation():
    """Verify CodeExecutionEvaluator parses syntax and tests output."""
    evaluator = CodeExecutionEvaluator()
    item = QuestionBankItem(
        id="q-code-1",
        course_id="course-cs",
        concept_id="loops",
        question_text="Print numbers 0 to 2 each on a new line.",
        item_type="CODE",
        correct_answer="0\n1\n2",
        difficulty=2,
    )

    # 1. Valid code producing expected output
    code_valid = "for i in range(3):\n    print(i)"
    res1 = evaluator.evaluate(item, code_valid)
    assert res1.outcome == EvaluationStatus.CORRECT
    assert res1.score == 1.0

    # 2. Syntax error in code
    code_syntax_err = "for i in range(3)\n    print(i)"
    res2 = evaluator.evaluate(item, code_syntax_err)
    assert res2.outcome == EvaluationStatus.INCORRECT
    assert res2.error_type == "syntax"
    assert "Syntax Error" in res2.feedback

    # 3. Valid syntax but incorrect output
    code_wrong = "print('Hello World')"
    res3 = evaluator.evaluate(item, code_wrong)
    assert res3.outcome == EvaluationStatus.INCORRECT
    assert res3.error_type == "conceptual"
    assert "Output mismatch" in res3.feedback


# ── 3. Rubric & Dynamic Misconception Evaluator ────────────────────────────────

def test_rubric_evaluation_with_dynamic_misconceptions():
    """Verify RubricEvaluator checks criteria and identifies dynamically supplied misconceptions."""
    evaluator = RubricEvaluator()
    item = QuestionBankItem(
        id="q-rubric-phys",
        course_id="course-physics",
        concept_id="newton_third_law",
        question_text="Why don't action and reaction forces cancel each other out?",
        item_type="SHORT_ANSWER",
        correct_answer="Action and reaction forces act on two different interacting bodies, so they cannot cancel.",
        difficulty=3,
    )

    # Context with Physics-specific misconceptions
    physics_misconceptions = {
        "MISCON_FORCES_CANCEL_SAME_BODY": {
            "keywords": ["act on the same body", "act on same object", "cancel on the same body", "applied to identical object"],
            "feedback": "Misconception: Action and reaction forces act on DIFFERENT interacting objects, not the same body.",
        }
    }

    # 1. Submission exhibiting the physics misconception
    miscon_ans = "They cancel because they act on the same body in opposite directions."
    res_miscon = evaluator.evaluate(item, miscon_ans, context={"misconceptions": physics_misconceptions})
    assert res_miscon.misconception_code == "MISCON_FORCES_CANCEL_SAME_BODY"
    assert "DIFFERENT interacting objects" in res_miscon.feedback
    assert res_miscon.outcome in (EvaluationStatus.PARTIALLY_CORRECT, EvaluationStatus.INCORRECT)

    # 2. Accurate explanation
    accurate_ans = "Action and reaction forces do not cancel because they act on different bodies."
    res_acc = evaluator.evaluate(item, accurate_ans)
    assert res_acc.outcome == EvaluationStatus.CORRECT
    assert res_acc.score >= 0.70
    assert res_acc.misconception_code is None


# ── 4. Uncertain and Malformed Answers ─────────────────────────────────────────

def test_uncertain_and_malformed_answers():
    """Verify evaluators reliably return UNCERTAIN for ambiguous words and empty answers."""
    registry = DEFAULT_EVALUATOR_REGISTRY

    mcq_item = QuestionBankItem(id="q1", course_id="crs-test-01", item_type="MCQ", question_text="Q?", correct_answer="B")
    num_item = QuestionBankItem(id="q2", course_id="crs-test-01", item_type="NUMERICAL", question_text="Q?", correct_answer="42")
    rubric_item = QuestionBankItem(id="q3", course_id="crs-test-01", item_type="SHORT_ANSWER", question_text="Q?", correct_answer="Gravity")

    # Empty answer
    assert registry.evaluate(mcq_item, "").outcome == EvaluationStatus.UNCERTAIN
    assert registry.evaluate(num_item, "").outcome == EvaluationStatus.UNCERTAIN
    assert registry.evaluate(rubric_item, "").outcome == EvaluationStatus.UNCERTAIN

    # Ambiguous tokens ("idk", "maybe")
    assert registry.evaluate(mcq_item, "idk").outcome == EvaluationStatus.UNCERTAIN
    assert registry.evaluate(rubric_item, "dunno").outcome == EvaluationStatus.UNCERTAIN

    # Malformed non-numeric input for numerical item
    res_num_malformed = registry.evaluate(num_item, "not a number at all")
    assert res_num_malformed.outcome == EvaluationStatus.UNCERTAIN
    assert res_num_malformed.error_type == "malformed"


# ── 5. Anti-Answer-Leakage Sanitizer Service ───────────────────────────────────

def test_anti_answer_leakage_sanitizer():
    """Verify AssessmentSanitizer removes answer keys, rubrics, and explanations from student payloads."""
    item = QuestionBankItem(
        id="qb-secure-01",
        course_id="course-physics",
        concept_id="kinematics",
        question_text="Calculate acceleration.",
        item_type="NUMERICAL",
        correct_answer="9.8 m/s^2",
        explanation="a = (v - u) / t",
        rubric={"criteria": {"accuracy": {"max_points": 4}}},
        hints=["Use standard gravitational constant near Earth surface."],
    )

    assessment = Assessment(
        id="asmt-midterm-01",
        course_id="course-physics",
        title="Physics Midterm",
        assessment_type=AssessmentType.FORMATIVE,
        total_marks=100.0,
        item_ids=["qb-secure-01"],
    )

    # 1. Sanitize single item (without hints)
    sanitized_item = AssessmentSanitizer.sanitize_item_for_student(item, allow_hints=False)
    assert "correct_answer" not in sanitized_item
    assert "explanation" not in sanitized_item
    assert "rubric" not in sanitized_item
    assert "hints" not in sanitized_item
    assert sanitized_item["question_text"] == "Calculate acceleration."

    # 2. Sanitize whole assessment payload
    sanitized_assessment = AssessmentSanitizer.sanitize_assessment_for_student(
        assessment, [item], allow_hints=False
    )
    assert sanitized_assessment["id"] == "asmt-midterm-01"
    assert len(sanitized_assessment["items"]) == 1
    assert "correct_answer" not in sanitized_assessment["items"][0]

    # 3. Invariant verification
    assert AssessmentSanitizer.verify_no_leakage(sanitized_assessment) is True

    # Leaking payload should fail verification
    leaking_payload = dict(sanitized_assessment)
    leaking_payload["correct_answer"] = "9.8"
    assert AssessmentSanitizer.verify_no_leakage(leaking_payload) is False


# ── 6. Course & Version Isolation ─────────────────────────────────────────────

def test_course_and_version_scoping(assessment_service, test_db):
    """Verify assessments, question banks, and attempts are strictly scoped to course/version."""
    # Seed courses
    c_phys = Course(id="course-phys-1", organization_id="org-core", code="PHYS101", title="Physics I")
    c_cs = Course(id="course-cs-1", organization_id="org-core", code="CS101", title="Computer Science I")
    test_db.create_course(c_phys)
    test_db.create_course(c_cs)

    # Create questions for both courses
    q_phys = QuestionBankItem(
        id="q-phys-scoped",
        course_id="course-phys-1",
        concept_id="phys_kinematics",
        question_text="Physics question",
        item_type="MCQ",
        correct_answer="A",
    )
    q_cs = QuestionBankItem(
        id="q-cs-scoped",
        course_id="course-cs-1",
        concept_id="cs_syntax",
        question_text="CS question",
        item_type="MCQ",
        correct_answer="B",
    )
    assessment_service.create_question(q_phys)
    assessment_service.create_question(q_cs)

    # Verify listing is scoped by course
    phys_items = assessment_service.list_questions(course_id="course-phys-1")
    cs_items = assessment_service.list_questions(course_id="course-cs-1")

    assert len(phys_items) == 1
    assert phys_items[0].id == "q-phys-scoped"
    assert len(cs_items) == 1
    assert cs_items[0].id == "q-cs-scoped"

    # Create and list assessments per course
    asmt_phys = Assessment(
        id="asmt-phys",
        course_id="course-phys-1",
        title="Physics Exam",
        item_ids=["q-phys-scoped"],
    )
    asmt_cs = Assessment(
        id="asmt-cs",
        course_id="course-cs-1",
        title="CS Exam",
        item_ids=["q-cs-scoped"],
    )
    assessment_service.create_assessment(asmt_phys)
    assessment_service.create_assessment(asmt_cs)

    assert len(assessment_service.list_assessments(course_id="course-phys-1")) == 1
    assert len(assessment_service.list_assessments(course_id="course-cs-1")) == 1


# ── 7. Teacher Review and Manual Score Adjustment ──────────────────────────────

def test_teacher_review_and_score_adjustment(assessment_service, test_db):
    """Verify teacher review workflow: adjustments, feedback, and approval."""
    # Create question and assessment
    q = QuestionBankItem(
        id="q-essay-rev",
        course_id="course-phys-1",
        concept_id="optics",
        question_text="Explain total internal reflection.",
        item_type="SHORT_ANSWER",
        correct_answer="Angle of incidence exceeds critical angle in a denser medium.",
        difficulty=3,
    )
    assessment_service.create_question(q)

    asmt = Assessment(
        id="asmt-rev-test",
        course_id="course-phys-1",
        title="Optics Quiz",
        total_marks=10.0,
        passing_score=75.0,
        item_ids=["q-essay-rev"],
    )
    assessment_service.create_assessment(asmt)

    # Student submits attempt
    attempt = assessment_service.start_attempt("asmt-rev-test", "student-phys-01")
    sub_res = assessment_service.submit_attempt(
        attempt.id,
        answers={"q-essay-rev": "Light reflects inside when angle is very big."},
    )
    assert sub_res.passed is False

    # Teacher reviews and adjusts score manually
    rev_attempt = assessment_service.review_attempt(
        attempt_id=attempt.id,
        teacher_id="teacher-01",
        score_adjustments={"q-essay-rev": 8.0},
        teacher_feedback="Good intuition, but remember to mention the critical angle.",
        approved=True,
    )

    assert rev_attempt.status == AttemptStatus.GRADED.value
    assert rev_attempt.teacher_id == "teacher-01"
    assert rev_attempt.score == 8.0
    assert rev_attempt.teacher_feedback == "Good intuition, but remember to mention the critical angle."


# ── 8. Remediation Recommendations Course Isolation ───────────────────────────

def test_remediation_recommendations_course_isolation(assessment_service, test_db):
    """Verify weak concepts and reassessments are strictly isolated to the student's tested course."""
    q_cs1 = QuestionBankItem(
        id="q-cs-rec-1",
        course_id="course-cs-1",
        concept_id="cs_recursion",
        question_text="What is a base case in recursion?",
        item_type="MCQ",
        correct_answer="A",
    )
    assessment_service.create_question(q_cs1)

    asmt_cs = Assessment(
        id="asmt-cs-rec",
        course_id="course-cs-1",
        title="Recursion Quiz",
        item_ids=["q-cs-rec-1"],
    )
    assessment_service.create_assessment(asmt_cs)

    attempt = assessment_service.start_attempt("asmt-cs-rec", "student-cs-01")
    # Wrong answer
    res = assessment_service.submit_attempt(attempt.id, answers={"q-cs-rec-1": "Z"})

    recs = res.reassessment_recommendations
    assert "cs_recursion" in recs
    # Invariant: Must not recommend concepts from other courses (e.g. physics or chemistry)
    assert not any("phys" in str(r) or "chem" in str(r) for r in recs)


# ── 9. Zero Chemistry Coupling Invariant ──────────────────────────────────────

def test_evaluator_registry_zero_hardcoded_chemistry_branching():
    """Architecture Invariant: Generic evaluator modules must contain ZERO hardcoded chemistry keywords."""
    from central_platform.assessment.evaluators import (
        base,
        code,
        deterministic,
        registry,
        rubric,
    )

    modules_to_check = [base, deterministic, code, rubric, registry]
    for mod in modules_to_check:
        src = inspect.getsource(mod).lower()
        assert 'if "chem"' not in src, f"{mod.__name__} contains hardcoded chemistry check"
        assert 'mode == "chemistry"' not in src, f"{mod.__name__} contains hardcoded chemistry mode"
        assert "thermodynamics" not in src, f"{mod.__name__} contains thermodynamics keyword"
        assert "enthalpy" not in src, f"{mod.__name__} contains enthalpy keyword"
