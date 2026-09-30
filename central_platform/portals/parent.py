"""Gayatri AI Platform — Parent Portal Backend Manager (Phase 29).

Provides data contracts, tab definitions, child selectors, progress summaries,
attendance summaries, and fee status descriptors for the Parent Portal UI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ParentPortalTab(str, Enum):
    PROGRESS = "progress"
    ATTENDANCE = "attendance"
    ASSIGNMENTS = "assignments"
    ASSESSMENTS = "assessments"
    TEACHER_UPDATES = "teacher_updates"
    RECOMMENDATIONS = "recommendations"
    FEES = "fees"
    NOTIFICATIONS = "notifications"


@dataclass
class ChildDescriptor:
    """Descriptor representing a child linked to a parent account."""
    child_id: str
    name: str = "Aarav Sharma"
    grade: str = "Grade 10"
    school_name: str = "Gayatri Vidyalaya"
    avatar_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChildProgressSummary:
    """Academic progress overview for a selected child."""
    child_id: str
    overall_mastery_pct: int = 84
    attendance_pct: float = 96.5
    pending_assignments_count: int = 2
    upcoming_assessments_count: int = 1
    recent_achievements: List[str] = field(default_factory=lambda: [
        "Mastered Organic Chemistry Module 3",
        "Scored 92% in Physics Quiz #4"
    ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AttendanceSummary:
    """Detailed attendance metrics for a child."""
    child_id: str
    present_days: int = 110
    absent_days: int = 4
    tardy_days: int = 1
    total_days: int = 115

    @property
    def attendance_percentage(self) -> float:
        if self.total_days == 0:
            return 100.0
        return round((self.present_days / self.total_days) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["attendance_percentage"] = self.attendance_percentage
        return d


class ParentPortalController:
    """Authoritative Parent Portal Backend Manager."""

    @classmethod
    def get_supported_tabs(cls) -> List[Dict[str, str]]:
        return [
            {"tab": ParentPortalTab.PROGRESS.value, "label": "Child Progress"},
            {"tab": ParentPortalTab.ATTENDANCE.value, "label": "Attendance"},
            {"tab": ParentPortalTab.ASSIGNMENTS.value, "label": "Assignments"},
            {"tab": ParentPortalTab.ASSESSMENTS.value, "label": "Assessments"},
            {"tab": ParentPortalTab.TEACHER_UPDATES.value, "label": "Teacher Updates"},
            {"tab": ParentPortalTab.RECOMMENDATIONS.value, "label": "Recommendations"},
            {"tab": ParentPortalTab.FEES.value, "label": "Fees & Payments"},
            {"tab": ParentPortalTab.NOTIFICATIONS.value, "label": "Notifications"},
        ]

    @classmethod
    def get_linked_children(cls, parent_id: str) -> List[ChildDescriptor]:
        return [
            ChildDescriptor(child_id="child_101", name="Aarav Sharma", grade="Grade 10"),
            ChildDescriptor(child_id="child_102", name="Ananya Sharma", grade="Grade 7")
        ]

    @classmethod
    def get_child_progress(cls, child_id: str) -> ChildProgressSummary:
        return ChildProgressSummary(child_id=child_id)

    @classmethod
    def get_child_attendance(cls, child_id: str) -> AttendanceSummary:
        return AttendanceSummary(child_id=child_id)
