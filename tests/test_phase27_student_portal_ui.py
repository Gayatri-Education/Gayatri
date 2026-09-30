"""Tests for Phase 27 — Student Portal UI.

Verifies:
- Student CSS & JS asset existence (student.css, student.js)
- CSS layout rules (dashboard grid, curriculum tree, graph nodes, review queue, activity stream, notifications)
- Student JS controller functions (switchStudentTab, renderDashboardStats, renderReviewQueue, startReview)
- Python backend StudentPortalController, StudentPortalTab, StudentDashboardSummary, and ReviewQueueItem
"""
import pytest
from pathlib import Path

from central_platform.portals.student import (
    ReviewQueueItem,
    StudentDashboardSummary,
    StudentPortalController,
    StudentPortalTab,
)


@pytest.fixture
def student_paths():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "app" / "ui" / "design_system"
    return {
        "student_css": ds_dir / "student.css",
        "student_js": ds_dir / "student.js",
    }


def test_student_files_exist(student_paths):
    assert student_paths["student_css"].exists()
    assert student_paths["student_js"].exists()


def test_student_css_rules(student_paths):
    css = student_paths["student_css"].read_text(encoding="utf-8")

    # Verify key Student Portal components in CSS
    assert ".student-portal-container" in css
    assert ".student-nav-tabs" in css
    assert ".student-dashboard-grid" in css
    assert ".graph-node" in css
    assert ".review-queue-list" in css
    assert ".notification-card" in css


def test_student_js_controller(student_paths):
    js = student_paths["student_js"].read_text(encoding="utf-8")

    # Verify JS controller functions
    assert "switchStudentTab" in js
    assert "renderDashboardStats" in js
    assert "renderReviewQueue" in js
    assert "startReview" in js


def test_python_student_portal_tabs():
    tabs = StudentPortalController.get_supported_tabs()
    assert len(tabs) == 10
    tab_names = {t["tab"] for t in tabs}
    assert "dashboard" in tab_names
    assert "curriculum" in tab_names
    assert "learning_graph" in tab_names
    assert "progress" in tab_names
    assert "review_queue" in tab_names
    assert "assignments" in tab_names
    assert "assessments" in tab_names
    assert "activity" in tab_names
    assert "profile" in tab_names
    assert "notifications" in tab_names


def test_student_dashboard_summary():
    summary = StudentPortalController.get_dashboard_summary("std-01", "crs-101")
    d = summary.to_dict()
    assert d["student_id"] == "std-01"
    assert d["course_id"] == "crs-101"
    assert d["mastery_pct"] == 74
    assert d["streak_days"] == 12


def test_review_queue_item():
    item = ReviewQueueItem(
        concept_id="c-thermo",
        concept_name="First Law of Thermodynamics",
        subject="Chemistry",
        retainability=0.65,
        next_review_due="2026-10-02"
    )
    d = item.to_dict()
    assert d["concept_id"] == "c-thermo"
    assert d["retainability"] == 0.65
