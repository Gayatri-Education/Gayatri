"""Tests for Phase 28 — Teacher Portal UI.

Verifies:
- Teacher CSS & JS asset existence (teacher.css, teacher.js)
- CSS layout rules (class overview grid, student roster table, risk badges, interventions, instructions, copilot panel)
- Teacher JS controller functions (switchTeacherTab, renderClassOverview, triggerCopilotAnalysis)
- Python backend TeacherPortalController, TeacherPortalTab, ClassOverviewSummary, and StudentHealthRecord
"""
import pytest
from pathlib import Path

from central_platform.portals.teacher import (
    ClassOverviewSummary,
    StudentHealthRecord,
    TeacherPortalController,
    TeacherPortalTab,
)


@pytest.fixture
def teacher_paths():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "app" / "ui" / "design_system"
    return {
        "teacher_css": ds_dir / "teacher.css",
        "teacher_js": ds_dir / "teacher.js",
    }


def test_teacher_files_exist(teacher_paths):
    assert teacher_paths["teacher_css"].exists()
    assert teacher_paths["teacher_js"].exists()


def test_teacher_css_rules(teacher_paths):
    css = teacher_paths["teacher_css"].read_text(encoding="utf-8")

    # Verify key Teacher Portal components in CSS
    assert ".teacher-portal-container" in css
    assert ".teacher-nav-tabs" in css
    assert ".class-overview-grid" in css
    assert ".student-roster-table" in css
    assert ".health-risk-badge" in css
    assert ".intervention-card" in css
    assert ".copilot-panel" in css


def test_teacher_js_controller(teacher_paths):
    js = teacher_paths["teacher_js"].read_text(encoding="utf-8")

    # Verify JS controller functions
    assert "switchTeacherTab" in js
    assert "renderClassOverview" in js
    assert "triggerCopilotAnalysis" in js


def test_python_teacher_portal_tabs():
    tabs = TeacherPortalController.get_supported_tabs()
    assert len(tabs) == 8
    tab_names = {t["tab"] for t in tabs}
    assert "class_overview" in tab_names
    assert "students" in tab_names
    assert "learning_health" in tab_names
    assert "student_profile" in tab_names
    assert "interventions" in tab_names
    assert "assessments" in tab_names
    assert "teacher_instructions" in tab_names
    assert "ai_copilot" in tab_names


def test_class_overview_summary():
    summary = TeacherPortalController.get_class_overview("crs-101")
    d = summary.to_dict()
    assert d["course_id"] == "crs-101"
    assert d["enrolled_count"] == 24
    assert d["average_mastery_pct"] == 76
    assert d["at_risk_count"] == 3


def test_student_health_record():
    rec = StudentHealthRecord(
        student_id="s1",
        student_name="Rahul Sharma",
        mastery_score=0.45,
        risk_level="high",
        active_misconception_count=2,
        last_active="2026-10-01T08:00:00Z"
    )
    d = rec.to_dict()
    assert d["student_id"] == "s1"
    assert d["risk_level"] == "high"
