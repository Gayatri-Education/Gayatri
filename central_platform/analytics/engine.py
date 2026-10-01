"""Centralized Platform Analytics and Reporting Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class MetricRecord:
    metric_id: str
    entity_type: str  # student, cohort, course, org, ai, intervention
    entity_id: str
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnalyticsEngine:
    """Central analytics engine deriving unified metrics for all platform entities."""

    def __init__(self):
        self._metrics: List[MetricRecord] = []

    def record_metric(self, entity_type: str, entity_id: str, metric_name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> MetricRecord:
        record = MetricRecord(
            metric_id=f"met-{len(self._metrics) + 1}",
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            value=value,
            metadata=metadata or {},
        )
        self._metrics.append(record)
        return record

    def get_student_analytics(self, student_id: str) -> Dict[str, Any]:
        records = [m for m in self._metrics if m.entity_type == "student" and m.entity_id == student_id]
        if not records:
            return {"student_id": student_id, "mastery_avg": 0.0, "sessions_count": 0, "velocity": 0.0}

        mastery_vals = [m.value for m in records if m.metric_name == "mastery_score"]
        sessions = [m for m in records if m.metric_name == "session_completed"]

        return {
            "student_id": student_id,
            "mastery_avg": sum(mastery_vals) / len(mastery_vals) if mastery_vals else 0.0,
            "sessions_count": len(sessions),
            "velocity": len(sessions) * 1.5,
        }

    def get_cohort_analytics(self, cohort_id: str) -> Dict[str, Any]:
        records = [m for m in self._metrics if m.entity_type == "cohort" and m.entity_id == cohort_id]
        scores = [m.value for m in records if m.metric_name == "cohort_mastery_avg"]
        return {
            "cohort_id": cohort_id,
            "average_mastery": sum(scores) / len(scores) if scores else 0.0,
            "recorded_metrics_count": len(records),
        }

    def get_organization_analytics(self, org_id: str) -> Dict[str, Any]:
        records = [m for m in self._metrics if m.entity_type == "org" and m.entity_id == org_id]
        return {
            "organization_id": org_id,
            "active_students": sum(int(m.value) for m in records if m.metric_name == "active_students"),
            "total_courses": sum(int(m.value) for m in records if m.metric_name == "total_courses"),
        }

    def get_ai_usage_analytics(self) -> Dict[str, Any]:
        ai_records = [m for m in self._metrics if m.entity_type == "ai"]
        tokens = sum(m.value for m in ai_records if m.metric_name == "tokens_consumed")
        costs = sum(m.value for m in ai_records if m.metric_name == "cost_usd")

        return {
            "total_tokens_consumed": tokens,
            "total_cost_usd": costs,
            "total_ai_calls": len([m for m in ai_records if m.metric_name == "call_executed"]),
        }

    def get_intervention_analytics(self) -> Dict[str, Any]:
        records = [m for m in self._metrics if m.entity_type == "intervention"]
        resolved = sum(1 for m in records if m.metric_name == "intervention_resolved")
        raised = sum(1 for m in records if m.metric_name == "intervention_raised")

        return {
            "interventions_raised": raised,
            "interventions_resolved": resolved,
            "resolution_rate": (resolved / raised) * 100.0 if raised > 0 else 0.0,
        }


# ── Multi-Level Evidence-Based Learning Health Engine (Phase 35) ─────────────

class LearningHealthLevel(str, Enum):
    EXCELLENT = "excellent"        # >= 85% mastery, low misconception
    GOOD = "good"                  # 70% - 84% mastery
    NEEDS_ATTENTION = "attention"  # 55% - 69% mastery
    AT_RISK = "at_risk"            # < 55% mastery or high active misconceptions


@dataclass
class StudentHealthMetric:
    """Individual student learning health metric derived from learning events."""
    student_id: str
    student_name: str = ""
    mastery_score: float = 0.0
    misconception_count: int = 0
    recent_velocity: float = 1.0  # Concepts mastered per week
    attendance_pct: float = 100.0
    health_level: LearningHealthLevel = LearningHealthLevel.GOOD
    evidence_summary: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["health_level"] = (
            self.health_level.value
            if isinstance(self.health_level, LearningHealthLevel)
            else self.health_level
        )
        return d


@dataclass
class ClassHealthMetric:
    """Cohort / Class level learning health metric."""
    class_id: str
    course_name: str = ""
    enrolled_count: int = 0
    average_mastery: float = 0.0
    at_risk_count: int = 0
    health_level: LearningHealthLevel = LearningHealthLevel.GOOD

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["health_level"] = (
            self.health_level.value
            if isinstance(self.health_level, LearningHealthLevel)
            else self.health_level
        )
        return d


@dataclass
class SectionHealthMetric:
    """Academic section level learning health metric."""
    section_id: str
    section_name: str = ""
    student_count: int = 0
    average_mastery: float = 0.0
    health_level: LearningHealthLevel = LearningHealthLevel.GOOD

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["health_level"] = (
            self.health_level.value
            if isinstance(self.health_level, LearningHealthLevel)
            else self.health_level
        )
        return d


@dataclass
class InstitutionHealthMetric:
    """Organization / Institution wide learning health metric."""
    org_id: str
    org_name: str = ""
    total_students: int = 0
    overall_mastery: float = 0.0
    active_interventions_count: int = 0
    health_level: LearningHealthLevel = LearningHealthLevel.GOOD

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["health_level"] = (
            self.health_level.value
            if isinstance(self.health_level, LearningHealthLevel)
            else self.health_level
        )
        return d


class LearningAnalyticsEngine:
    """Authoritative Learning Analytics Computation Engine."""

    @classmethod
    def classify_health_level(cls, mastery: float, misconception_count: int = 0) -> LearningHealthLevel:
        if misconception_count >= 3 or mastery < 55.0:
            return LearningHealthLevel.AT_RISK
        elif mastery >= 85.0:
            return LearningHealthLevel.EXCELLENT
        elif mastery >= 70.0:
            return LearningHealthLevel.GOOD
        else:
            return LearningHealthLevel.NEEDS_ATTENTION

    @classmethod
    def compute_student_learning_health(
        cls,
        student_id: str,
        student_name: str = "Student",
        learning_events: Optional[List[Dict[str, Any]]] = None,
        attendance_pct: float = 95.0,
    ) -> StudentHealthMetric:
        events = learning_events or []
        if not events:
            return StudentHealthMetric(
                student_id=student_id,
                student_name=student_name,
                mastery_score=75.0,
                misconception_count=0,
                recent_velocity=0.0,
                attendance_pct=attendance_pct,
                health_level=LearningHealthLevel.GOOD,
                evidence_summary=["Initial baseline assessment active."],
            )

        total_score = sum(e.get("score", 0.0) for e in events)
        mastery = total_score / len(events) if len(events) > 0 else 75.0
        misconceptions = sum(1 for e in events if e.get("misconception_detected"))

        health = cls.classify_health_level(mastery, misconceptions)

        evidence = [
            f"Evaluated across {len(events)} learning interactions.",
            f"Average score: {mastery:.1f}%.",
        ]
        if misconceptions > 0:
            evidence.append(f"Detected {misconceptions} misconception events requiring remediation.")

        return StudentHealthMetric(
            student_id=student_id,
            student_name=student_name,
            mastery_score=round(mastery, 1),
            misconception_count=misconceptions,
            recent_velocity=round(len(events) / 2.0, 1),
            attendance_pct=attendance_pct,
            health_level=health,
            evidence_summary=evidence,
        )

    @classmethod
    def compute_class_learning_health(
        cls,
        class_id: str,
        course_name: str,
        student_metrics: List[StudentHealthMetric],
    ) -> ClassHealthMetric:
        if not student_metrics:
            return ClassHealthMetric(class_id=class_id, course_name=course_name)

        avg_mastery = sum(s.mastery_score for s in student_metrics) / len(student_metrics)
        at_risk = sum(1 for s in student_metrics if s.health_level == LearningHealthLevel.AT_RISK)
        health = cls.classify_health_level(avg_mastery, at_risk)

        return ClassHealthMetric(
            class_id=class_id,
            course_name=course_name,
            enrolled_count=len(student_metrics),
            average_mastery=round(avg_mastery, 1),
            at_risk_count=at_risk,
            health_level=health,
        )

    @classmethod
    def compute_section_learning_health(
        cls,
        section_id: str,
        section_name: str,
        student_metrics: List[StudentHealthMetric],
    ) -> SectionHealthMetric:
        if not student_metrics:
            return SectionHealthMetric(section_id=section_id, section_name=section_name)

        avg_mastery = sum(s.mastery_score for s in student_metrics) / len(student_metrics)
        at_risk = sum(1 for s in student_metrics if s.health_level == LearningHealthLevel.AT_RISK)
        health = cls.classify_health_level(avg_mastery, at_risk)

        return SectionHealthMetric(
            section_id=section_id,
            section_name=section_name,
            student_count=len(student_metrics),
            average_mastery=round(avg_mastery, 1),
            health_level=health,
        )

    @classmethod
    def compute_institution_learning_health(
        cls,
        org_id: str,
        org_name: str,
        class_metrics: List[ClassHealthMetric],
    ) -> InstitutionHealthMetric:
        if not class_metrics:
            return InstitutionHealthMetric(org_id=org_id, org_name=org_name)

        total_students = sum(c.enrolled_count for c in class_metrics)
        overall_mastery = (
            sum(c.average_mastery * c.enrolled_count for c in class_metrics) / total_students
            if total_students > 0
            else 0.0
        )
        total_interventions = sum(c.at_risk_count for c in class_metrics)
        health = cls.classify_health_level(overall_mastery, total_interventions)

        return InstitutionHealthMetric(
            org_id=org_id,
            org_name=org_name,
            total_students=total_students,
            overall_mastery=round(overall_mastery, 1),
            active_interventions_count=total_interventions,
            health_level=health,
        )

