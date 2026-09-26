"""Unit and integration test suite for Phase 15: Platform Analytics & Reporting."""

import pytest
from central_platform.analytics import AnalyticsEngine


@pytest.fixture
def analytics_engine():
    engine = AnalyticsEngine()
    # Populate sample data
    engine.record_metric("student", "stu-1", "mastery_score", 0.85)
    engine.record_metric("student", "stu-1", "mastery_score", 0.90)
    engine.record_metric("student", "stu-1", "session_completed", 1.0)
    engine.record_metric("cohort", "coh-1", "cohort_mastery_avg", 0.78)
    engine.record_metric("org", "org-1", "active_students", 120.0)
    engine.record_metric("org", "org-1", "total_courses", 15.0)
    engine.record_metric("ai", "global", "tokens_consumed", 4500.0)
    engine.record_metric("ai", "global", "cost_usd", 0.045)
    engine.record_metric("ai", "global", "call_executed", 1.0)
    engine.record_metric("intervention", "int-1", "intervention_raised", 1.0)
    engine.record_metric("intervention", "int-1", "intervention_resolved", 1.0)
    return engine


def test_student_analytics_aggregation(analytics_engine):
    stats = analytics_engine.get_student_analytics("stu-1")
    assert stats["student_id"] == "stu-1"
    assert stats["mastery_avg"] == 0.875
    assert stats["sessions_count"] == 1
    assert stats["velocity"] > 0


def test_cohort_analytics_aggregation(analytics_engine):
    stats = analytics_engine.get_cohort_analytics("coh-1")
    assert stats["cohort_id"] == "coh-1"
    assert stats["average_mastery"] == 0.78


def test_organization_analytics_aggregation(analytics_engine):
    stats = analytics_engine.get_organization_analytics("org-1")
    assert stats["organization_id"] == "org-1"
    assert stats["active_students"] == 120
    assert stats["total_courses"] == 15


def test_ai_usage_analytics_aggregation(analytics_engine):
    stats = analytics_engine.get_ai_usage_analytics()
    assert stats["total_tokens_consumed"] == 4500.0
    assert stats["total_cost_usd"] == 0.045
    assert stats["total_ai_calls"] == 1


def test_intervention_analytics_aggregation(analytics_engine):
    stats = analytics_engine.get_intervention_analytics()
    assert stats["interventions_raised"] == 1
    assert stats["interventions_resolved"] == 1
    assert stats["resolution_rate"] == 100.0
