"""Phase 29 — Parent Portal UI & Backend Manager Unit Tests."""

from pathlib import Path
import pytest
from central_platform.portals.parent import (
    ParentPortalTab,
    ChildDescriptor,
    ChildProgressSummary,
    AttendanceSummary,
    ParentPortalController,
)


def test_parent_portal_css_and_js_exist():
    css_path = Path("app/ui/design_system/parent.css")
    js_path = Path("app/ui/design_system/parent.js")
    assert css_path.exists(), "parent.css must exist"
    assert js_path.exists(), "parent.js must exist"

    css_content = css_path.read_text(encoding="utf-8")
    assert ".parent-portal" in css_content
    assert ".child-selector" in css_content

    js_content = js_path.read_text(encoding="utf-8")
    assert "GayatriParent" in js_content


def test_parent_portal_tab_enum():
    assert len(ParentPortalTab) == 8
    assert ParentPortalTab.PROGRESS.value == "progress"
    assert ParentPortalTab.ATTENDANCE.value == "attendance"
    assert ParentPortalTab.FEES.value == "fees"


def test_parent_portal_controller_tabs():
    tabs = ParentPortalController.get_supported_tabs()
    assert len(tabs) == 8
    tab_keys = [t["tab"] for t in tabs]
    assert "progress" in tab_keys
    assert "attendance" in tab_keys
    assert "teacher_updates" in tab_keys


def test_parent_portal_controller_linked_children():
    children = ParentPortalController.get_linked_children("parent_001")
    assert len(children) >= 1
    child = children[0]
    assert isinstance(child, ChildDescriptor)
    assert child.child_id == "child_101"
    d = child.to_dict()
    assert "name" in d
    assert "grade" in d


def test_parent_portal_controller_progress_and_attendance():
    progress = ParentPortalController.get_child_progress("child_101")
    assert isinstance(progress, ChildProgressSummary)
    assert progress.overall_mastery_pct == 84

    attendance = ParentPortalController.get_child_attendance("child_101")
    assert isinstance(attendance, AttendanceSummary)
    assert attendance.attendance_percentage == 95.7 or attendance.attendance_percentage > 90
    d = attendance.to_dict()
    assert "attendance_percentage" in d
