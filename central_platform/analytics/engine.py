"""Centralized Platform Analytics and Reporting Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
