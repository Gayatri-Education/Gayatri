"""Phase 19: Authoritative Assessment Platform Comprehensive Verification Suite.

Master Plan Section 28 Requirements:
1. Question Bank management (CRUD, filtering, difficulties 1-5, Bloom levels, Rubrics).
2. Diagnostic, Formative, Summative, and Adaptive assessment generation & lifecycle.
3. Assignment distribution to courses, cohorts, and class groups.
4. Deterministic grading (MCQ, Numerical range tolerance, Boolean).
5. AI-assisted rubric grading (Weighted criteria, performance levels, misconception detection).
6. Computerized Adaptive Testing (CAT) item selection, difficulty ladder, and concept coverage.
7. CRITICAL INVARIANT: Every assessment attempt and question event feeds the Learning Event Store.
8. Teacher review, item-level score override, comments, and sign-off.
9. Targeted reassessment generation for weak concepts.
10. Full HTTP REST API compliance across all assessment endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import create_app
from central_platform.assessment.adaptive import AdaptiveTestingEngine
from central_platform.assessment.grading import AIAssistedGrader, AssessmentGradingEngine, DeterministicGrader
from central_platform.assessment.models import (
    AssessmentType,
    AttemptStatus,
    QuestionType,
    Rubric,
    RubricCriterion,
)
from central_platform.assessment.rubrics import RubricEngine
from central_platform.assessment.service import AssessmentService
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import (
    Assessment,
    Assignment,
    Course,
    Organization,
    QuestionBankItem,
    User,
    UserRole,
)


@pytest.fixture
def test_db():
    db = PlatformDatabase(":memory:")
    # Seed org, course, and user
    db.create_organization(Organization(id="org-test", name="Test Org", slug="test-org"))
    db.create_course(Course(id="crs-chem-101", organization_id="org-test", code="CHEM101", title="Thermodynamics"))
    db.create_user(User(id="usr-stu-01", email="student@test.com", full_name="Student One", role=UserRole.STUDENT, organization_id="org-test"))
    db.create_user(User(id="usr-tch-01", email="teacher@test.com", full_name="Teacher One", role=UserRole.TEACHER, organization_id="org-test"))
    return db


@pytest.fixture
def assessment_service(test_db):
    event_store = LearningEventStore(test_db)
    return AssessmentService(db=test_db, event_store=event_store)


from central_platform.api.routes.assessments import get_assessment_service


@pytest.fixture
def api_client(assessment_service):
    app = create_app()
    app.dependency_overrides[get_assessment_service] = lambda: assessment_service
    return TestClient(app)


# ── 1. Question Bank Tests ───────────────────────────────────────────────────

def test_question_bank_crud_and_filtering(assessment_service):
    """Verify question bank creation, retrieval, and multi-attribute filtering."""
    q1 = QuestionBankItem(
        id="qb-thermo-01",
        course_id="crs-chem-101",
        concept_id="chem_thermo_first_law",
        question_text="What is the internal energy change for a cyclic process?",
        item_type="MCQ",
        options=["0 J", "100 J", "Infinity", "Undefined"],
        correct_answer="0 J",
        difficulty=1,
        bloom_level="recall",
        tags=["thermodynamics", "first_law"],
    )
    q2 = QuestionBankItem(
        id="qb-thermo-02",
        course_id="crs-chem-101",
        concept_id="chem_thermo_enthalpy",
        question_text="Calculate ΔH given ΔU = -100 kJ and PΔV = -10.5 kJ.",
        item_type="NUMERICAL",
        correct_answer="-110.5",
        difficulty=3,
        bloom_level="application",
        tags=["thermodynamics", "enthalpy"],
    )
    assessment_service.create_question(q1)
    assessment_service.create_question(q2)

    # Test retrieval
    fetched = assessment_service.get_question("qb-thermo-01")
    assert fetched is not None
    assert fetched.question_text == "What is the internal energy change for a cyclic process?"
    assert fetched.difficulty == 1

    # Test filtering by concept
    first_law_items = assessment_service.list_questions(concept_id="chem_thermo_first_law")
    assert len(first_law_items) == 1
    assert first_law_items[0].id == "qb-thermo-01"

    # Test filtering by difficulty
    diff3_items = assessment_service.list_questions(difficulty=3)
    assert len(diff3_items) == 1
    assert diff3_items[0].id == "qb-thermo-02"


# ── 2. Deterministic & AI-Assisted Grading ───────────────────────────────────

def test_deterministic_grading_mcq_and_numerical():
    """Verify exact, normalized MCQ and numerical tolerance evaluation."""
    # MCQ
    is_corr, score, fb = DeterministicGrader.grade_mcq("0 J", "0 J")
    assert is_corr is True
    assert score == 1.0

    is_corr, score, fb = DeterministicGrader.grade_mcq("100 J", "0 J")
    assert is_corr is False

    # Numerical with 2% tolerance
    is_corr, score, fb = DeterministicGrader.grade_numerical("-110.5", "-110.5")
    assert is_corr is True

    # -112.0 is within ~1.35% of -110.5 -> Should pass 2% tolerance
    is_corr, score, fb = DeterministicGrader.grade_numerical("-112.0", "-110.5", tolerance_pct=2.0)
    assert is_corr is True

    # -150.0 is way off -> Should fail
    is_corr, score, fb = DeterministicGrader.grade_numerical("-150.0", "-110.5", tolerance_pct=2.0)
    assert is_corr is False


def test_ai_assisted_rubric_grading_and_misconceptions():
    """Verify rubric scoring and detection of misconceptions in free-form answers."""
    q_essay = QuestionBankItem(
        id="qb-essay-01",
        course_id="crs-chem-101",
        concept_id="chem_thermo_first_law",
        question_text="Explain why heat and work are path functions rather than state functions.",
        item_type="SHORT_ANSWER",
        correct_answer="Heat and work depend on the specific path taken between states.",
        difficulty=3,
    )

    # 1. Answer exhibiting known misconception
    miscon_ans = "Heat is work and they are identical state properties that do not depend on the path."
    res = AIAssistedGrader.grade_with_rubric(q_essay, miscon_ans)
    assert res.ai_graded is True
    assert res.misconception_code == "MISCON_THERMO_HEAT_WORK_CONFUSION"
    assert "Misconception identified" in res.feedback

    # 2. Accurate conceptual answer
    correct_ans = "Heat and work are path functions because their values depend on the specific thermodynamic path taken."
    res_corr = AIAssistedGrader.grade_with_rubric(q_essay, correct_ans)
    assert res_corr.is_correct is True
    assert res_corr.score > 0.0


# ── 3. Computerized Adaptive Testing (CAT) ───────────────────────────────────

def test_adaptive_testing_engine_progression():
    """Verify adaptive engine adjusts difficulty up on success, down on failure, and covers concepts."""
    q1 = QuestionBankItem(id="q1", course_id="crs-chem-101", concept_id="c1", question_text="Q1", difficulty=2)
    q2 = QuestionBankItem(id="q2", course_id="crs-chem-101", concept_id="c2", question_text="Q2", difficulty=3)
    q3 = QuestionBankItem(id="q3", course_id="crs-chem-101", concept_id="c3", question_text="Q3", difficulty=4)
    q4 = QuestionBankItem(id="q4", course_id="crs-chem-101", concept_id="c1", question_text="Q4", difficulty=1)

    all_items = [q1, q2, q3, q4]
    state = AdaptiveTestingEngine.initialize_state(target_concepts=["c1", "c2", "c3"], initial_difficulty=2)

    # First item selected should match initial difficulty 2
    first_item = AdaptiveTestingEngine.select_next_item(all_items, state)
    assert first_item.id == "q1"

    # Answer correctly -> difficulty goes 2 -> 3
    state = AdaptiveTestingEngine.update_state_on_response(state, first_item, is_correct=True)
    assert state.current_difficulty == 3
    assert "c1" in state.tested_concepts

    # Next item should match difficulty 3 and remaining concepts (c2, c3)
    next_item = AdaptiveTestingEngine.select_next_item(all_items, state)
    assert next_item.id == "q2"

    # Answer incorrectly -> difficulty goes 3 -> 2
    state = AdaptiveTestingEngine.update_state_on_response(state, next_item, is_correct=False)
    assert state.current_difficulty == 2


# ── 4. Assessment Attempt Lifecycle & Learning Events Invariant ──────────────

def test_assessment_attempt_submission_feeds_learning_events(assessment_service, test_db):
    """Verify that submitting an assessment creates authoritative learning events and updates SLR."""
    q1 = QuestionBankItem(
        id="qb-01",
        course_id="crs-chem-101",
        concept_id="chem_thermo_first_law",
        question_text="First law question",
        item_type="MCQ",
        correct_answer="A",
        difficulty=2,
    )
    q2 = QuestionBankItem(
        id="qb-02",
        course_id="crs-chem-101",
        concept_id="chem_thermo_enthalpy",
        question_text="Enthalpy calculation",
        item_type="NUMERICAL",
        correct_answer="-50.0",
        difficulty=2,
    )
    assessment_service.create_question(q1)
    assessment_service.create_question(q2)

    # Create Summative Assessment
    asmt = Assessment(
        id="asmt-summative-01",
        course_id="crs-chem-101",
        title="Midterm Exam",
        assessment_type=AssessmentType.SUMMATIVE,
        item_ids=["qb-01", "qb-02"],
        total_marks=20.0,
        passing_score=70.0,
    )
    assessment_service.create_assessment(asmt)

    # Start Attempt
    attempt = assessment_service.start_attempt("asmt-summative-01", "usr-stu-01")
    assert attempt.status == AttemptStatus.IN_PROGRESS.value

    # Submit Attempt (1 correct, 1 incorrect)
    answers = {"qb-01": "A", "qb-02": "-999.0"}
    completed_attempt = assessment_service.submit_attempt(attempt.id, answers)

    assert completed_attempt.status == AttemptStatus.GRADED.value
    assert completed_attempt.score > 0.0
    assert "qb-01" in completed_attempt.item_results
    assert completed_attempt.item_results["qb-01"]["is_correct"] is True
    assert completed_attempt.item_results["qb-02"]["is_correct"] is False
    assert "chem_thermo_enthalpy" in completed_attempt.reassessment_recommendations

    # ── CRITICAL INVARIANT: Verify Learning Events in Event Store ───────────
    events = assessment_service.event_store.query_events()
    event_types = [e.event_type for e in events]
    assert LearningEventType.QUESTION_ATTEMPTED.value in event_types
    assert LearningEventType.ASSESSMENT_COMPLETED.value in event_types


# ── 5. Teacher Review & Reassessment Generation ──────────────────────────────

def test_teacher_review_and_targeted_reassessment(assessment_service):
    """Verify teacher can adjust scores and system automatically generates targeted reassessment."""
    q1 = QuestionBankItem(
        id="qb-rev-01",
        course_id="crs-chem-101",
        concept_id="chem_thermo_first_law",
        question_text="Derive first law formula",
        item_type="SHORT_ANSWER",
        correct_answer="ΔU = q + w",
        difficulty=3,
    )
    assessment_service.create_question(q1)

    asmt = Assessment(
        id="asmt-rev-01",
        course_id="crs-chem-101",
        title="Derivation Test",
        assessment_type=AssessmentType.FORMATIVE,
        item_ids=["qb-rev-01"],
        total_marks=10.0,
    )
    assessment_service.create_assessment(asmt)

    attempt = assessment_service.start_attempt("asmt-rev-01", "usr-stu-01")
    completed = assessment_service.submit_attempt(attempt.id, {"qb-rev-01": "Partial derivation without work"})

    # Teacher reviews and adjusts score from whatever AI gave to 5.0 points
    reviewed = assessment_service.teacher_review_attempt(
        attempt_id=completed.id,
        teacher_id="usr-tch-01",
        item_score_adjustments={"qb-rev-01": 5.0},
        teacher_comments="Good intuition, please include work signs next time.",
    )
    assert reviewed.status == "reviewed"
    assert reviewed.score == 5.0
    assert reviewed.teacher_review["teacher_id"] == "usr-tch-01"

    # Generate Targeted Reassessment for weak concepts
    re_asmt, reassessment_rec = assessment_service.generate_reassessment(completed.id, target_score=80.0)
    assert re_asmt.assessment_type == AssessmentType.REASSESSMENT
    assert "chem_thermo_first_law" in re_asmt.config["target_concepts"]
    assert reassessment_rec.student_id == "usr-stu-01"
    assert reassessment_rec.target_score == 80.0


# ── 6. Full HTTP REST API Endpoints ──────────────────────────────────────────

def test_http_assessment_api_endpoints(api_client):
    """Verify FastAPI routes for Question Bank, Assessments, Assignments, Attempts, and Reassessments."""
    # 1. Create Question Bank Item
    q_resp = api_client.post(
        "/api/v1/assessments/items",
        json={
            "course_id": "crs-chem-101",
            "question_text": "What is ΔH for exothermic reaction?",
            "item_type": "MCQ",
            "options": ["Negative (<0)", "Positive (>0)", "Zero", "Undefined"],
            "correct_answer": "Negative (<0)",
            "difficulty": 2,
            "concept_id": "chem_thermo_enthalpy",
        },
    )
    assert q_resp.status_code == 201
    q_data = q_resp.json()["data"]
    item_id = q_data["id"]

    # 2. Create Assessment Definition
    asmt_resp = api_client.post(
        "/api/v1/assessments",
        json={
            "course_id": "crs-chem-101",
            "title": "Enthalpy & Heat Quiz",
            "assessment_type": "formative",
            "item_ids": [item_id],
            "passing_score": 75.0,
        },
    )
    assert asmt_resp.status_code == 201
    asmt_id = asmt_resp.json()["data"]["id"]

    # 3. Create Assignment
    assign_resp = api_client.post(
        "/api/v1/assessments/assignments",
        json={
            "course_id": "crs-chem-101",
            "assessment_id": asmt_id,
            "title": "Weekly Homework 1",
            "instructions": "Complete before Friday.",
        },
    )
    assert assign_resp.status_code == 201

    # 4. Start Attempt
    start_resp = api_client.post(
        "/api/v1/assessments/attempts/start",
        json={
            "assessment_id": asmt_id,
            "student_id": "usr-stu-01",
        },
    )
    assert start_resp.status_code == 201
    attempt_id = start_resp.json()["data"]["attempt_id"]

    # 5. Submit Attempt
    sub_resp = api_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/submit",
        json={
            "answers": {item_id: "Negative (<0)"},
            "student_id": "usr-stu-01",
        },
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()["data"]
    assert sub_data["status"] == "graded"
    assert sub_data["passed"] is True

    # 6. Teacher Review via API
    rev_resp = api_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/teacher-review",
        json={
            "item_score_adjustments": {item_id: 4.0},
            "teacher_comments": "Verified and approved.",
        },
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["data"]["status"] == "reviewed"

    # 7. Generate Reassessment via API
    re_resp = api_client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/reassess",
        json={
            "original_attempt_id": attempt_id,
            "target_score": 85.0,
        },
    )
    assert re_resp.status_code == 201
    assert re_resp.json()["data"]["target_score"] == 85.0
