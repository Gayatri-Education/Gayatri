"""Teacher Portal MVP service providing class health, student details, and cohort analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TeacherDashboardOverview:
    total_students: int
    students_needing_attention: int
    average_mastery: float
    active_alerts_count: int
    class_health_status: str  # Excellent, Good, Attention Needed, Critical


class TeacherPortalService:
    """Service handling Teacher Web Portal data queries and cohort metrics."""

    def __init__(self):
        self._students: dict[str, dict] = {}

    def register_student_snapshot(
        self, student_id: str, name: str, course_id: str, mastery: float, needs_attention: bool = False
    ) -> None:
        self._students[student_id] = {
            "id": student_id,
            "name": name,
            "course_id": course_id,
            "mastery": mastery,
            "needs_attention": needs_attention,
        }

    def get_dashboard_overview(self, course_id: str) -> TeacherDashboardOverview:
        relevant = [s for s in self._students.values() if s["course_id"] == course_id]
        if not relevant:
            return TeacherDashboardOverview(0, 0, 0.0, 0, "No Data")

        total = len(relevant)
        needing_attention = sum(1 for s in relevant if s["needs_attention"] or s["mastery"] < 0.5)
        avg_mastery = round(sum(s["mastery"] for s in relevant) / total, 3)

        if needing_attention == 0 and avg_mastery >= 0.8:
            health = "Excellent"
        elif needing_attention / total <= 0.35:
            health = "Good"
        elif needing_attention / total <= 0.60:
            health = "Attention Needed"
        else:
            health = "Critical"

        return TeacherDashboardOverview(
            total_students=total,
            students_needing_attention=needing_attention,
            average_mastery=avg_mastery,
            active_alerts_count=needing_attention,
            class_health_status=health,
        )

    def get_students_needing_attention(self, course_id: str) -> List[dict]:
        return [
            s for s in self._students.values()
            if s["course_id"] == course_id and (s["needs_attention"] or s["mastery"] < 0.5)
        ]
