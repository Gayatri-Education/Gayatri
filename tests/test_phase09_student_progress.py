"""Tests for Phase 09: Student Progress API + UI (Section 18).

Master Plan Section 18 Verification Suite:
- Expose learning progress directly from Authoritative SLR data
- All 14 Section 18 canonical learning progress dimensions verified:
  1. overall_mastery
  2. topic_mastery
  3. concept_heatmap
  4. recent_sessions
  5. recent_activity
  6. weak_areas
  7. misconceptions
  8. accuracy_trends
  9. mastery_trends
  10. question_type_performance
  11. review_due
  12. recommendations (strictly policy-generated, no free-form LLM text)
  13. session_summary
  14. learning_streak
- All 8 mandatory UI states verified in dashboard HTML:
  1. loading
  2. empty
  3. success
  4. partial_data
  5. offline
  6. api_error
  7. permission_error
  8. retry
- RBAC boundary enforcement: student self-access only (403 for cross-student)
- Empty state resilience for brand new students with 0 events
- API endpoints:
  - GET /api/v1/students/{student_id}/progress
  - GET /api/v1/students/{student_id}/progress/heatmap
  - GET /api/v1/students/{student_id}/progress/summary
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.progress.models import (
    AccuracyTrendPoint,
    HeatmapNode,
    LearningStreak,
    MasteryTrendPoint,
    QuestionTypeMetric,
    ReviewDueItem,
    SessionSummary,
    StudentProgressReport,
    TopicMastery,
    WeakArea,
)
from central_platform.progress.service import StudentProgressService
from central_platform.slr.service import SLRService


@pytest.fixture
def managed_db(tmp_path):
    """Provide isolated platform database."""
    db_file = tmp_path / "test_phase09_progress.db"
    db = PlatformDatabase(db_path=str(db_file))
    yield db
    db.close()


@pytest.fixture
def progress_service(managed_db):
    """Provide StudentProgressService wired to isolated database."""
    event_store = LearningEventStore(db=managed_db)
    slr_service = SLRService(db=managed_db, event_store=event_store)
    return StudentProgressService(db=managed_db, event_store=event_store, slr_service=slr_service)


@pytest.fixture
def populated_student(managed_db, progress_service):
    """Seed student with realistic events across chemistry topics and question types."""
    student_id = "stu_progress_alice"
    course_id = "crs-chem-101"
    event_store = progress_service.event_store
    slr_service = progress_service.slr_service

    slr_service._ensure_student_scaffolding(student_id, course_id)

    # Ingest diverse events
    events = [
        # Thermodynamics - numerical
        LearningEventIngest(
            event_id="ev_prog_01",
            student_id=student_id,
            session_id="sess_prog_1",
            course_id=course_id,
            concept_id="chem_thermo_first_law",
            event_type="question_attempted",
            payload={
                "question_id": "q1",
                "question_type": "numerical",
                "correctness": "correct",
                "score": 1.0,
                "hint_level": 0,
                "response_time_ms": 15000,
            },
        ),
        LearningEventIngest(
            event_id="ev_prog_02",
            student_id=student_id,
            session_id="sess_prog_1",
            course_id=course_id,
            concept_id="chem_thermo_first_law",
            event_type="question_attempted",
            payload={
                "question_id": "q2",
                "question_type": "numerical",
                "correctness": "correct",
                "score": 1.0,
                "hint_level": 1,
                "response_time_ms": 18000,
            },
        ),
        LearningEventIngest(
            event_id="ev_prog_02b",
            student_id=student_id,
            session_id="sess_prog_1",
            course_id=course_id,
            concept_id="chem_thermo_first_law",
            event_type="question_attempted",
            payload={
                "question_id": "q2b",
                "question_type": "numerical",
                "correctness": "correct",
                "score": 1.0,
                "hint_level": 0,
                "response_time_ms": 14000,
            },
        ),
        # Inorganic Chemistry - conceptual with misconception
        LearningEventIngest(
            event_id="ev_prog_03",
            student_id=student_id,
            session_id="sess_prog_2",
            course_id=course_id,
            concept_id="chem_inorg_bonding_lewis",
            event_type="question_attempted",
            payload={
                "question_id": "q3",
                "question_type": "conceptual",
                "correctness": "incorrect",
                "score": 0.0,
                "hint_level": 0,
                "misconception_code": "OCTET_EXPANSION_CONFUSION",
                "response_time_ms": 22000,
            },
        ),
        # Inorganic Chemistry - equation balancing
        LearningEventIngest(
            event_id="ev_prog_04",
            student_id=student_id,
            session_id="sess_prog_2",
            course_id=course_id,
            concept_id="chem_inorg_balancing",
            event_type="question_attempted",
            payload={
                "question_id": "q4",
                "question_type": "equation_balancing",
                "correctness": "correct",
                "score": 1.0,
                "hint_level": 0,
                "response_time_ms": 12000,
            },
        ),
        # Spaced review due event for Hess's Law
        LearningEventIngest(
            event_id="ev_prog_05",
            student_id=student_id,
            session_id="sess_prog_1",
            course_id=course_id,
            concept_id="chem_thermo_hess_law",
            event_type="question_attempted",
            payload={
                "question_id": "q5",
                "question_type": "numerical",
                "correctness": "correct",
                "score": 1.0,
                "hint_level": 0,
                "next_review_at": "2020-01-01T00:00:00Z",  # Overdue
            },
        ),
    ]

    for ev in events:
        event_store.ingest_event(ev)

    # Update database mastery states for concepts via SLR service
    slr_service.update_concept_mastery(student_id, "chem_thermo_first_law", 0.90, course_id, 0.85)
    slr_service.update_concept_mastery(student_id, "chem_inorg_bonding_lewis", 0.40, course_id, 0.70)
    slr_service.update_concept_mastery(student_id, "chem_inorg_balancing", 0.80, course_id, 0.80)
    slr_service.update_concept_mastery(student_id, "chem_thermo_hess_law", 0.75, course_id, 0.75)

    # Log misconception
    slr_service.record_student_misconception(
        student_id=student_id,
        misconception_code="OCTET_EXPANSION_CONFUSION",
        course_id=course_id,
    )

    return student_id, course_id


def test_progress_service_all_14_dimensions(progress_service, populated_student):
    """Verifies that StudentProgressService populates all 14 Section 18 dimensions."""
    student_id, course_id = populated_student

    report = progress_service.get_student_progress(student_id, course_id)
    assert isinstance(report, StudentProgressReport)

    # 1. Overall Mastery
    assert 0.0 <= report.overall_mastery <= 1.0

    # 2. Topic Mastery
    assert len(report.topic_mastery) > 0
    for topic in report.topic_mastery:
        assert isinstance(topic, TopicMastery)
        assert topic.topic_name
        assert topic.concept_count >= 1
        assert 0.0 <= topic.mastery_score <= 1.0
        assert topic.status in ("LEARNING", "PRACTICING", "PROFICIENT", "MASTERED")

    # 3. Concept Heatmap
    assert len(report.concept_heatmap) >= 4
    for node in report.concept_heatmap:
        assert isinstance(node, HeatmapNode)
        assert node.concept_id
        assert node.concept_name
        assert node.domain in ("Thermodynamics", "Inorganic Chemistry", "Stoichiometry & Physical", "Physical Chemistry", "General Chemistry")
        assert 0.0 <= node.mastery_score <= 1.0
        assert node.color.startswith("#")
        assert node.status in ("NEW", "LEARNING", "PRACTICING", "PROFICIENT", "MASTERED", "REVIEW_DUE")

    # 4. Recent Sessions
    assert isinstance(report.recent_sessions, list)
    assert len(report.recent_sessions) >= 1

    # 5. Recent Activity
    assert isinstance(report.recent_activity, list)
    assert len(report.recent_activity) >= 1

    # 6. Weak Areas (< 0.60 mastery)
    assert isinstance(report.weak_areas, list)
    assert any(w.concept_id == "chem_inorg_bonding_lewis" for w in report.weak_areas)
    for weak in report.weak_areas:
        assert isinstance(weak, WeakArea)
        assert weak.mastery_score < 0.60
        assert weak.mastery_gap > 0.40
        assert weak.recommended_action

    # 7. Misconceptions
    assert isinstance(report.misconceptions, list)
    assert any(m["code"] == "OCTET_EXPANSION_CONFUSION" for m in report.misconceptions)

    # 8. Accuracy Trends
    assert isinstance(report.accuracy_trends, list)
    assert len(report.accuracy_trends) >= 1
    for pt in report.accuracy_trends:
        assert isinstance(pt, AccuracyTrendPoint)
        assert 0.0 <= pt.accuracy <= 1.0

    # 9. Mastery Trends
    assert isinstance(report.mastery_trends, list)
    assert len(report.mastery_trends) >= 1
    for pt in report.mastery_trends:
        assert isinstance(pt, MasteryTrendPoint)
        assert 0.0 <= pt.mastery <= 1.0

    # 10. Question-Type Performance
    assert isinstance(report.question_type_performance, dict)
    assert "numerical" in report.question_type_performance
    assert "conceptual" in report.question_type_performance
    assert "equation_balancing" in report.question_type_performance
    num_metric = report.question_type_performance["numerical"]
    assert isinstance(num_metric, QuestionTypeMetric)
    assert num_metric.attempts >= 2
    assert num_metric.accuracy == 1.0

    # 11. Review Due
    assert isinstance(report.review_due, list)
    assert any(r.concept_id == "chem_thermo_hess_law" for r in report.review_due)
    for rev in report.review_due:
        assert isinstance(rev, ReviewDueItem)
        assert rev.overdue_days >= 1

    # 12. Recommendations (Strictly policy-driven, no free-form LLM text)
    assert isinstance(report.recommendations, list)
    assert len(report.recommendations) >= 1
    for r in report.recommendations:
        assert "action_type" in r
        assert "concept_id" in r
        assert "priority" in r
        assert "reason" in r
        # Non-negotiable: action_type must match canonical learning policy actions
        assert r["action_type"] in (
            "remediate_prerequisite",
            "practice_numerical",
            "practice_concept",
            "advance_concept",
            "spaced_review",
            "remedial_instruction",
            "review",
        )

    # 13. Latest Session Summary
    assert report.session_summary is not None
    assert isinstance(report.session_summary, SessionSummary)
    assert report.session_summary.session_id

    # 14. Learning Streak
    assert isinstance(report.learning_streak, LearningStreak)
    assert report.learning_streak.current_streak_days >= 1
    assert report.learning_streak.longest_streak_days >= 1

    # Verify serialization to dictionary
    d = report.to_dict()
    assert d["student_id"] == student_id
    assert d["course_id"] == course_id
    assert "overall_mastery" in d
    assert "topic_mastery" in d
    assert "concept_heatmap" in d
    assert "recent_sessions" in d
    assert "recent_activity" in d
    assert "weak_areas" in d
    assert "misconceptions" in d
    assert "accuracy_trends" in d
    assert "mastery_trends" in d
    assert "question_type_performance" in d
    assert "review_due" in d
    assert "recommendations" in d
    assert "session_summary" in d
    assert "learning_streak" in d


def test_empty_student_progress_state(progress_service):
    """Verifies that a brand new student with zero events yields a valid empty state without crashes."""
    student_id = "stu_fresh_new_01"
    course_id = "crs-chem-101"

    report = progress_service.get_student_progress(student_id, course_id)
    assert report.student_id == student_id
    assert report.overall_mastery == 0.50  # Neutral baseline
    assert len(report.weak_areas) == 0  # No weak areas because exposure is 0
    assert len(report.misconceptions) == 0
    assert report.learning_streak.current_streak_days == 0
    assert len(report.recent_activity) == 0

    # Ensure clean dictionary serialization
    d = report.to_dict()
    assert d["student_id"] == student_id
    assert d["overall_mastery"] == 0.50


def test_topic_mastery_aggregation(progress_service, populated_student):
    """Verifies that concepts are correctly aggregated into curriculum chapters with weighted averages."""
    student_id, course_id = populated_student
    report = progress_service.get_student_progress(student_id, course_id)

    topics_by_name = {t.topic_name: t for t in report.topic_mastery}
    assert "Thermodynamics" in topics_by_name
    assert "Inorganic Chemistry" in topics_by_name

    thermo = topics_by_name["Thermodynamics"]
    assert thermo.concept_count >= 2
    # thermo first law = 0.90, hess law = 0.75 -> avg should be ~0.825 (>= 0.80 -> MASTERED)
    assert thermo.mastery_score >= 0.70
    assert thermo.status in ("PROFICIENT", "MASTERED")

    inorg = topics_by_name["Inorganic Chemistry"]
    assert inorg.concept_count >= 2
    assert inorg.status in ("PRACTICING", "PROFICIENT")


def test_concept_heatmap_generation(progress_service, populated_student):
    """Verifies concept heatmap node categorization, color encoding, and review flags."""
    student_id, course_id = populated_student
    report = progress_service.get_student_progress(student_id, course_id)

    nodes_by_id = {n.concept_id: n for n in report.concept_heatmap}
    assert "chem_thermo_first_law" in nodes_by_id
    assert "chem_thermo_hess_law" in nodes_by_id
    assert "chem_inorg_bonding_lewis" in nodes_by_id

    # Hess's Law has overdue review
    hess_node = nodes_by_id["chem_thermo_hess_law"]
    assert hess_node.is_review_due is True
    assert hess_node.status == "REVIEW_DUE"
    assert hess_node.color == "#8b5cf6"  # Purple review color

    # First Law has 0.90 mastery and multiple exposures -> MASTERED
    first_law_node = nodes_by_id["chem_thermo_first_law"]
    assert first_law_node.mastery_score == 0.90
    assert first_law_node.status == "MASTERED"
    assert first_law_node.color == "#10b981"  # Emerald green


def test_policy_driven_recommendations(progress_service, populated_student):
    """Verifies that all recommendations derive deterministically from learning policy without LLM hallucinations."""
    student_id, course_id = populated_student
    report = progress_service.get_student_progress(student_id, course_id)

    assert len(report.recommendations) > 0
    allowed_actions = {
        "remediate_prerequisite",
        "practice_numerical",
        "practice_concept",
        "advance_concept",
        "spaced_review",
        "remedial_instruction",
        "review",
    }
    for rec in report.recommendations:
        assert rec["action_type"] in allowed_actions
        assert isinstance(rec["priority"], int)
        assert len(rec["reason"]) > 5
        # Ensure reasons are deterministic pedagogical statements
        assert any(
            kw in rec["reason"].lower()
            for kw in ("mastery", "misconception", "review", "threshold", "practice", "advance")
        )


def test_question_type_performance_breakdown(progress_service, populated_student):
    """Verifies accurate calculation of attempts and accuracy per question type."""
    student_id, course_id = populated_student
    report = progress_service.get_student_progress(student_id, course_id)

    qtypes = report.question_type_performance
    assert "numerical" in qtypes
    assert "conceptual" in qtypes
    assert "equation_balancing" in qtypes

    # Numerical: 3 attempts on first law, 1 on hess law = 4 correct out of 4 = 1.0 acc
    assert qtypes["numerical"].attempts == 4
    assert qtypes["numerical"].correct == 4
    assert qtypes["numerical"].accuracy == 1.0

    # Conceptual: 1 incorrect attempt = 0.0 acc
    assert qtypes["conceptual"].attempts == 1
    assert qtypes["conceptual"].correct == 0
    assert qtypes["conceptual"].accuracy == 0.0

    # Equation balancing: 1 correct attempt = 1.0 acc
    assert qtypes["equation_balancing"].attempts == 1
    assert qtypes["equation_balancing"].correct == 1
    assert qtypes["equation_balancing"].accuracy == 1.0


def test_learning_streak_calculation(progress_service, populated_student):
    """Verifies computation of active days and learning streaks."""
    student_id, course_id = populated_student
    report = progress_service.get_student_progress(student_id, course_id)

    streak = report.learning_streak
    assert streak.current_streak_days >= 1
    assert streak.longest_streak_days >= streak.current_streak_days
    assert streak.active_days_last_30 >= 1
    assert len(streak.last_active_date) == 10  # YYYY-MM-DD


def test_api_student_progress_endpoints(progress_service, populated_student, monkeypatch):
    """Verifies REST API endpoints GET /progress, /heatmap, and /summary."""
    student_id, course_id = populated_student

    # Patch route-level progress service to use the fixture-populated service
    monkeypatch.setattr("central_platform.api.routes.students._progress_service", progress_service)

    client = TestClient(app)
    token = create_access_token(user_id=student_id, role="STUDENT", organization_id="org-default")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Full 14-dimension progress report
    res_prog = client.get(f"/api/v1/students/{student_id}/progress?course_id={course_id}", headers=headers)
    assert res_prog.status_code == 200
    data_prog = res_prog.json()
    assert data_prog["ok"] is True
    report_dict = data_prog["data"]
    assert report_dict["student_id"] == student_id
    assert "overall_mastery" in report_dict
    assert "topic_mastery" in report_dict
    assert "concept_heatmap" in report_dict
    assert "question_type_performance" in report_dict
    assert "learning_streak" in report_dict
    assert "recommendations" in report_dict

    # 2. Granular Concept Heatmap
    res_heat = client.get(f"/api/v1/students/{student_id}/progress/heatmap?course_id={course_id}", headers=headers)
    assert res_heat.status_code == 200
    data_heat = res_heat.json()
    assert data_heat["ok"] is True
    assert isinstance(data_heat["data"], list)
    assert len(data_heat["data"]) >= 4

    # 3. High-level Summary
    res_sum = client.get(f"/api/v1/students/{student_id}/progress/summary?course_id={course_id}", headers=headers)
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    assert data_sum["ok"] is True
    sum_dict = data_sum["data"]
    assert sum_dict["student_id"] == student_id
    assert "overall_mastery" in sum_dict
    assert "topic_mastery" in sum_dict
    assert "learning_streak" in sum_dict
    assert "weak_areas_count" in sum_dict
    assert "review_due_count" in sum_dict


def test_api_student_progress_rbac_forbidden():
    """Verifies RBAC boundary: Student A cannot inspect Student B's progress."""
    student_a = "stu_alice_secured"
    student_b = "stu_bob_secured"

    client = TestClient(app)
    token_a = create_access_token(user_id=student_a, role="STUDENT", organization_id="org-default")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Alice tries to inspect Bob's progress
    res = client.get(f"/api/v1/students/{student_b}/progress", headers=headers_a)
    assert res.status_code == 403
    err = res.json()
    assert err["ok"] is False
    assert "students may only access their own records" in err["error"]["message"].lower()


def test_student_dashboard_html_and_8_ui_states():
    """Verifies that app/ui/student_dashboard.html implements all 14 dimensions and all 8 mandatory states."""
    html_path = os.path.join("app", "ui", "student_dashboard.html")
    assert os.path.exists(html_path), "student_dashboard.html must exist in app/ui/"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Verify all 14 dimensions are represented in DOM / script
    assert "statOverallMastery" in content, "Overall mastery element missing"
    assert "topicMasteryGrid" in content, "Topic mastery grid missing"
    assert "conceptHeatmapGrid" in content, "Concept heatmap grid missing"
    assert "recentSessionsList" in content, "Recent sessions list missing"
    assert "recentActivityList" in content, "Recent activity list missing"
    assert "weakAreasList" in content, "Weak areas list missing"
    assert "misconceptionsList" in content, "Misconceptions list missing"
    assert "accuracyTrendsBox" in content, "Accuracy trends element missing"
    assert "masteryTrendsBox" in content, "Mastery trends element missing"
    assert "questionTypeBody" in content, "Question-type performance table missing"
    assert "reviewDueList" in content, "Review due list missing"
    assert "recommendationsList" in content, "Recommendations list missing"
    assert "cardSessionSummary" in content, "Session summary element missing"
    assert "cardLearningStreak" in content, "Learning streak element missing"

    # 2. Verify all 8 mandatory UI states are defined
    # 1. loading
    assert "stateLoading" in content, "loading state element missing"
    # 2. empty
    assert "stateEmpty" in content, "empty state element missing"
    # 3. success
    assert "stateSuccess" in content, "success state element missing"
    # 4. partial_data
    assert "statePartialData" in content, "partial_data state element missing"
    # 5. offline
    assert "stateOffline" in content, "offline state element missing"
    # 6. api_error
    assert "stateApiError" in content, "api_error state element missing"
    # 7. permission_error
    assert "statePermissionError" in content, "permission_error state element missing"
    # 8. retry
    assert "StudentDashboardController.retry" in content or "btnRetryBanner" in content, "retry action missing"
