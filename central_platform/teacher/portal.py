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
    mastered_count: int = 0
    progressing_count: int = 0
    critical_count: int = 0
    top_misconceptions: List[dict] = field(default_factory=list)
    chapter_averages: Dict[str, float] = field(default_factory=dict)
    active_students_today: int = 0
    critical_alerts_count: int = 0
    mastery_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        d = asdict(self)
        if not d.get("mastery_distribution"):
            d["mastery_distribution"] = {
                "Mastered": self.mastered_count,
                "Progressing": self.progressing_count,
                "Critical": self.critical_count,
            }
        return d


class TeacherPortalService:
    """Service handling Teacher Web Portal data queries and cohort metrics."""

    def __init__(self):
        self._students: dict[str, dict] = {}

    def register_student_snapshot(
        self,
        student_id: str,
        name: str,
        course_id: str,
        mastery: float,
        needs_attention: bool = False,
        misconceptions: Optional[List[str]] = None,
        hint_count: int = 0,
        retention_rate: float = 0.85,
        chapter_mastery: Optional[Dict[str, float]] = None,
        recent_activity: Optional[str] = None,
    ) -> None:
        self._students[student_id] = {
            "id": student_id,
            "student_id": student_id,
            "name": name,
            "student_name": name,
            "course_id": course_id,
            "mastery": round(mastery, 2),
            "needs_attention": needs_attention or (mastery < 0.5),
            "misconceptions": misconceptions or [],
            "hint_count": hint_count,
            "retention_rate": round(retention_rate, 2),
            "chapter_mastery": chapter_mastery or {
                "Thermodynamics": round(mastery, 2),
                "Chemical Bonding": round(min(1.0, mastery + 0.05), 2),
                "Coordination Chemistry": round(max(0.2, mastery - 0.1), 2),
                "Periodic Trends": round(min(1.0, mastery + 0.1), 2),
            },
            "recent_activity": recent_activity or "Practicing NCERT Questions",
        }

    def update_student_snapshot(
        self,
        student_id: str,
        student_name: Optional[str] = None,
        name: Optional[str] = None,
        course_id: str = "crs-chem-101",
        mastery: float = 0.5,
        needs_attention: bool = False,
        misconceptions: Optional[List[str]] = None,
        hint_count: int = 0,
        retention_rate: float = 0.85,
        chapter_mastery: Optional[Dict[str, float]] = None,
        recent_activity: Optional[str] = None,
    ) -> None:
        """Alias/flexible update for register_student_snapshot."""
        self.register_student_snapshot(
            student_id=student_id,
            name=student_name or name or self._students.get(student_id, {}).get("name", student_id),
            course_id=course_id,
            mastery=mastery,
            needs_attention=needs_attention,
            misconceptions=misconceptions,
            hint_count=hint_count,
            retention_rate=retention_rate,
            chapter_mastery=chapter_mastery,
            recent_activity=recent_activity,
        )

    def get_dashboard_overview(self, course_id: str) -> TeacherDashboardOverview:
        relevant = [s for s in self._students.values() if s["course_id"] == course_id]
        if not relevant:
            return TeacherDashboardOverview(0, 0, 0.0, 0, "No Data")

        total = len(relevant)
        needing_attention = sum(1 for s in relevant if s["needs_attention"] or s["mastery"] < 0.5)
        avg_mastery = round(sum(s["mastery"] for s in relevant) / total, 3)

        mastered = sum(1 for s in relevant if s["mastery"] >= 0.8)
        progressing = sum(1 for s in relevant if 0.5 <= s["mastery"] < 0.8)
        critical = sum(1 for s in relevant if s["mastery"] < 0.5)

        if needing_attention == 0 and avg_mastery >= 0.8:
            health = "Excellent"
        elif needing_attention / total <= 0.35:
            health = "Good"
        elif needing_attention / total <= 0.60:
            health = "Attention Needed"
        else:
            health = "Critical"

        # Calculate class-wide chapter averages
        chapter_totals: dict[str, list[float]] = {}
        for s in relevant:
            for ch, score in s.get("chapter_mastery", {}).items():
                chapter_totals.setdefault(ch, []).append(score)
        chapter_avgs = {
            ch: round(sum(scores) / len(scores), 2)
            for ch, scores in chapter_totals.items()
        }

        # Calculate misconception frequencies
        misc_counts: dict[str, int] = {}
        for s in relevant:
            for m in s.get("misconceptions", []):
                misc_counts[m] = misc_counts.get(m, 0) + 1
        top_misc = [
            {"code": code, "count": count}
            for code, count in sorted(misc_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        dist = {
            "Mastered": mastered,
            "Progressing": progressing,
            "Critical": critical,
        }

        return TeacherDashboardOverview(
            total_students=total,
            students_needing_attention=needing_attention,
            average_mastery=avg_mastery,
            active_alerts_count=needing_attention,
            class_health_status=health,
            mastered_count=mastered,
            progressing_count=progressing,
            critical_count=critical,
            top_misconceptions=top_misc,
            chapter_averages=chapter_avgs,
            active_students_today=total,
            critical_alerts_count=critical,
            mastery_distribution=dist,
        )

    def get_students_needing_attention(self, course_id: str) -> List[dict]:
        return [
            s for s in self._students.values()
            if s["course_id"] == course_id and (s["needs_attention"] or s["mastery"] < 0.5)
        ]

    def get_all_students(self, course_id: Optional[str] = None) -> List[dict]:
        if course_id:
            return [s for s in self._students.values() if s["course_id"] == course_id]
        return list(self._students.values())

    def get_misconception_summary(self, course_id: str) -> List[dict]:
        overview = self.get_dashboard_overview(course_id)
        return overview.top_misconceptions
