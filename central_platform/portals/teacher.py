"""Gayatri AI Platform — Teacher Portal Backend Manager (Phase 28).

Provides data contracts, tab definitions, cohort summaries, learning health records,
and AI Copilot descriptors for the Teacher Portal UI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TeacherPortalTab(str, Enum):
    CLASS_OVERVIEW = "class_overview"
    STUDENTS = "students"
    LEARNING_HEALTH = "learning_health"
    STUDENT_PROFILE = "student_profile"
    INTERVENTIONS = "interventions"
    ASSESSMENTS = "assessments"
    TEACHER_INSTRUCTIONS = "teacher_instructions"
    AI_COPILOT = "ai_copilot"


@dataclass
class ClassOverviewSummary:
    """Cohort summary metrics for teacher view."""
    course_id: str
    course_name: str = "Chemistry 101"
    enrolled_count: int = 24
    average_mastery_pct: int = 76
    at_risk_count: int = 3
    active_interventions: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudentHealthRecord:
    student_id: str
    student_name: str
    mastery_score: float
    risk_level: str  # "high", "medium", "low"
    active_misconception_count: int
    last_active: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TeacherPortalController:
    """Authoritative Teacher Portal Backend Manager."""

    @classmethod
    def get_supported_tabs(cls) -> List[Dict[str, str]]:
        return [
            {"tab": TeacherPortalTab.CLASS_OVERVIEW.value, "label": "Class Overview"},
            {"tab": TeacherPortalTab.STUDENTS.value, "label": "Students"},
            {"tab": TeacherPortalTab.LEARNING_HEALTH.value, "label": "Learning Health"},
            {"tab": TeacherPortalTab.STUDENT_PROFILE.value, "label": "Student Profile"},
            {"tab": TeacherPortalTab.INTERVENTIONS.value, "label": "Interventions"},
            {"tab": TeacherPortalTab.ASSESSMENTS.value, "label": "Assessments"},
            {"tab": TeacherPortalTab.TEACHER_INSTRUCTIONS.value, "label": "Teacher Instructions"},
            {"tab": TeacherPortalTab.AI_COPILOT.value, "label": "AI Copilot"},
        ]

    @classmethod
    def get_class_overview(cls, course_id: str) -> ClassOverviewSummary:
        return ClassOverviewSummary(course_id=course_id)
