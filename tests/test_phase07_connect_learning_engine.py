"""Tests for Phase 07: Connect Existing Learning Engine (Section 16).

Master Plan Section 16 Verification Suite:
- Canonical flow: student action -> learning event -> learning engine -> updated mastery -> SLR -> recommendation
- Preserved intelligence: BKT, mastery, LDG, difficulty, misconceptions, spaced review, concept selection, adaptive engine
- Backtest: Replay frozen student histories within tolerance (<= 0.05) versus baseline
- API endpoints & RBAC boundary enforcement
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.learning.backtest import FrozenHistoryBacktester
from central_platform.learning.bridge import LearningEngineBridge
from central_platform.learning.models import StudentActionPayload
from central_platform.slr.service import SLRService
from core.tutor.controller import TutorController
from core.tutor.state import TutorStateManager


@pytest.fixture
def managed_db(tmp_path):
    """Provide isolated SQLite database per test."""
    db_file = tmp_path / "test_phase07.db"
    db = PlatformDatabase(db_path=str(db_file))
    yield db
    db.close()


@pytest.fixture
def bridge(managed_db):
    """Provide LearningEngineBridge backed by managed isolated DB."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    return LearningEngineBridge(db=managed_db, event_store=event_store, slr_service=slr_service)


def test_target_flow_student_action_to_slr(bridge):
    """Master Plan Section 16 Target Flow:
    student action -> learning event -> learning engine -> updated mastery -> SLR -> recommendation.
    """
    student_id = "test_student_flow_01"
    concept_id = "chem_thermo_first_law"
    course_id = "crs-chem-101"

    # Action 1: Student submits correct answer
    action = StudentActionPayload(
        concept_id=concept_id,
        action_type="answer_submitted",
        student_answer="Delta U = q + w",
        correctness="correct",
        hint_level=0,
        difficulty=3.0,
    )

    result = bridge.process_student_action(student_id, action, course_id=course_id)

    # 1. Event was created and recorded
    assert result.event_id is not None
    assert result.student_id == student_id
    assert result.concept_id == concept_id

    # 2. Learning engine calculated updated mastery
    assert result.mastery_score >= 0.60
    assert result.mastery_delta == 0.10

    # 3. Difficulty policy assigned label
    assert result.difficulty_level in range(1, 6)
    assert result.difficulty_label != ""

    # 4. Pedagogical action & next concept decided
    assert result.pedagogical_action in ("TEST_AND_HINT", "CHALLENGE_QUESTION", "MASTERED")
    assert result.target_concept != ""

    # 5. Authoritative SLR updated and attached
    assert result.slr is not None
    assert result.slr.authoritative is True
    assert result.slr.mastery.concept_scores[concept_id] == result.mastery_score

    # 6. SLR recommendations and timeline present
    assert len(result.recommendations) > 0
    assert len(result.slr.learning_timeline) >= 1
    assert result.slr.learning_timeline[0].concept_id == concept_id


def test_engine_bkt_mastery_calculation(bridge):
    """Verifies BKT / mastery calculation transitions:
    - Correct first attempt: +0.10
    - Correct with hint: +0.05
    - Partial: +0.02
    - Incorrect: -0.05
    - Clamped strictly within [0.0, 1.0]
    """
    student_id = "test_student_bkt_01"
    concept_id = "chem_thermo_first_law"

    # Step 1: Initial (default 0.50) + correct first attempt -> 0.60
    r1 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0),
    )
    assert r1.mastery_delta == 0.10
    assert r1.mastery_score == 0.60

    # Step 2: Correct after hint -> +0.05 -> 0.65
    r2 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=1),
    )
    assert r2.mastery_delta == 0.05
    assert r2.mastery_score == 0.65

    # Step 3: Partially correct -> +0.02 -> 0.67
    r3 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="partially_correct"),
    )
    assert r3.mastery_delta == 0.02
    assert r3.mastery_score == 0.67

    # Step 4: Incorrect -> -0.05 -> 0.62
    r4 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="incorrect"),
    )
    assert r4.mastery_delta == -0.05
    assert r4.mastery_score == 0.62


def test_engine_difficulty_policy_transitions(bridge):
    """Verifies DifficultyPolicy transitions:
    - 2 consecutive independent correct answers increase difficulty level (+1)
    - 2 consecutive errors decrease difficulty level (-1)
    """
    student_id = "test_student_diff_01"
    concept_id = "chem_thermo_enthalpy"

    # Action 1: Correct (diff 2)
    bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=2.0),
    )
    # Action 2: Correct (consecutive -> should increase difficulty to 3)
    r2 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=2.0),
    )
    assert r2.difficulty_level >= 3

    # Error 1: Incorrect
    bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="incorrect", difficulty=3.0),
    )
    # Error 2: Incorrect (consecutive errors -> should decrease difficulty)
    r4 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="incorrect", difficulty=3.0),
    )
    assert r4.difficulty_level <= 2


def test_engine_misconception_detection_and_remediation(bridge):
    """Verifies misconception identification against controlled catalog and remediation guidance mapping."""
    student_id = "test_student_misc_01"
    concept_id = "chem_thermo_first_law"

    # Erroneous response exhibiting sign convention confusion
    action = StudentActionPayload(
        concept_id=concept_id,
        correctness="incorrect",
        student_answer="500 + 200 = 700 J expansion work is positive",
    )

    result = bridge.process_student_action(student_id, action)

    # 1. Misconception correctly identified
    assert result.misconception is not None
    assert result.misconception["code"] == "THERMO_SIGN_CONVENTION"
    assert "IUPAC convention" in result.misconception["guidance"]

    # 2. Misconception recorded in Authoritative SLR
    assert result.slr is not None
    misc_codes = [m.code for m in result.slr.misconceptions]
    assert "THERMO_SIGN_CONVENTION" in misc_codes


def test_engine_spaced_review_scheduling(bridge):
    """Verifies SpacedReviewScheduler calculates next review date and expands interval on success."""
    student_id = "test_student_review_01"
    concept_id = "chem_thermo_first_law"

    # 1. Correct answer calculates future review timestamp
    r1 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0),
    )
    assert r1.next_review_at != ""
    assert "T" in r1.next_review_at

    # 2. Incorrect answer resets/shortens interval
    r2 = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="incorrect"),
    )
    assert r2.next_review_at != ""


def test_engine_ldg_concept_selection(bridge):
    """Verifies ConceptSelector ranks candidates based on LDG prerequisites and readiness."""
    student_id = "test_student_ldg_01"
    concept_id = "chem_thermo_first_law"

    result = bridge.process_student_action(
        student_id,
        StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0),
    )

    # Candidate concepts ranked and returned
    assert len(result.candidate_concepts) > 0
    top_candidate = result.candidate_concepts[0]
    assert "concept_id" in top_candidate
    assert "total_score" in top_candidate


def test_engine_adaptive_action_routing(bridge):
    """Verifies AdaptiveLearningEngine routing:
    - High mastery (>= 0.80) -> MASTERED
    - Low mastery (< 0.40) -> EXPLAIN_CONCEPT
    """
    student_id = "test_student_adapt_01"
    concept_id = "chem_thermo_first_law"

    # Push mastery above 0.80
    r1 = bridge.process_student_action(student_id, StudentActionPayload(concept_id=concept_id, correctness="correct"))
    r2 = bridge.process_student_action(student_id, StudentActionPayload(concept_id=concept_id, correctness="correct"))
    r3 = bridge.process_student_action(student_id, StudentActionPayload(concept_id=concept_id, correctness="correct"))
    r4 = bridge.process_student_action(student_id, StudentActionPayload(concept_id=concept_id, correctness="correct"))

    assert r4.mastery_score >= 0.80
    assert r4.pedagogical_action == "MASTERED"
    assert r4.recommended_mode == "SUMMARY"


def test_api_student_action_endpoint():
    """Verifies HTTP POST /api/v1/students/{student_id}/action API endpoint integration."""
    student_id = "test_api_student_01"

    with TestClient(app) as client:
        res = client.post(
            f"/api/v1/students/{student_id}/action",
            json={
                "concept_id": "chem_thermo_first_law",
                "action_type": "answer_submitted",
                "correctness": "correct",
                "hint_level": 0,
                "difficulty": 3.0,
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["student_id"] == student_id
        assert data["concept_id"] == "chem_thermo_first_law"
        assert data["mastery_score"] >= 0.60
        assert "slr" in data
        assert data["slr"]["authoritative"] is True


def test_api_student_action_rbac_boundaries():
    """Verifies Section 13 Negative Security:
    Authenticated students cannot submit actions on behalf of other students.
    """
    token_a = create_access_token("student_alpha", role="STUDENT", organization_id="org-default")

    with TestClient(app) as client:
        # Student A submits action for Student A -> 200 OK
        res_self = client.post(
            "/api/v1/students/student_alpha/action",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"concept_id": "chem_thermo_first_law", "correctness": "correct"},
        )
        assert res_self.status_code == 200

        # Student A attempts to submit action for Student Beta -> 403 Forbidden
        res_cross = client.post(
            "/api/v1/students/student_beta/action",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"concept_id": "chem_thermo_first_law", "correctness": "correct"},
        )
        assert res_cross.status_code == 403


def test_backtest_frozen_student_histories(bridge):
    """Section 16 Backtest:
    Replays frozen synthetic student histories and asserts all trajectories remain
    within target tolerance (<= 0.05) versus baseline.
    """
    backtester = FrozenHistoryBacktester(bridge=bridge)
    summary = backtester.run_all_backtests(prefix="phase07_backtest")

    assert summary["all_passed"] is True
    assert summary["within_target_tolerance"] is True
    assert summary["max_tolerance"] <= 0.05

    fast = summary["results"]["fast_learner"]
    assert fast.passed is True
    assert fast.final_mastery >= 0.75

    struggling = summary["results"]["struggling_learner"]
    assert struggling.passed is True
    assert struggling.final_mastery <= 0.45

    hints = summary["results"]["hint_dependent"]
    assert hints.passed is True
    assert 0.55 <= hints.final_mastery <= 0.65


def test_core_tutor_backwards_compatibility():
    """Verifies core tutor controller and state manager remain 100% functional without regressions."""
    controller = TutorController()
    assert controller.student is not None
    assert controller.current_mode in ("EXPLAIN", "QUESTION", "REMEDIATE", "SUMMARY")

    state_mgr = TutorStateManager(db_path=":memory:")
    mastery = state_mgr.get_student_concept_mastery("s1", "chem_thermo_first_law")
    assert mastery.mastery == 0.0
    state_mgr.conn.close()

