"""Adaptive Teacher Intervention Queue and Alert System."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    DETECTED = "detected"
    DELIVERED = "delivered"
    SEEN = "seen"
    ACKNOWLEDGED = "acknowledged"
    ACTIONED = "actioned"
    RESOLVED = "resolved"


@dataclass
class TeacherAlert:
    alert_id: str
    student_id: str
    course_id: str
    alert_type: str  # repeated_failure, prerequisite_weakness, mastery_regression
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.DETECTED
    assigned_teacher_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        from dataclasses import asdict
        d = asdict(self)
        d["severity"] = self.severity.value if hasattr(self.severity, "value") else str(self.severity)
        d["status"] = self.status.value if hasattr(self.status, "value") else str(self.status)
        return d


class TeacherInterventionEngine:
    """Manages alert queues and teacher intervention lifecycle transitions."""

    def __init__(self):
        self._alerts: dict[str, TeacherAlert] = {}

    def raise_alert(self, alert: TeacherAlert) -> TeacherAlert:
        self._alerts[alert.alert_id] = alert
        return alert

    def get_alerts_for_teacher(self, teacher_id: Optional[str] = None, course_id: Optional[str] = None) -> List[TeacherAlert]:
        res = []
        for alert in self._alerts.values():
            if course_id and alert.course_id != course_id:
                continue
            if teacher_id and alert.assigned_teacher_id and alert.assigned_teacher_id != teacher_id:
                continue
            res.append(alert)
        return res

    def transition_alert_status(self, alert_id: str, new_status: AlertStatus) -> bool:
        if alert_id in self._alerts:
            self._alerts[alert_id].status = new_status
            return True
        return False

    def resolve_alert(self, alert_id: str, note: str = "") -> bool:
        return self.transition_alert_status(alert_id, AlertStatus.RESOLVED)

    def get_all_alerts(self, course_id: Optional[str] = None) -> List[TeacherAlert]:
        alerts = list(self._alerts.values())
        if course_id:
            alerts = [a for a in alerts if a.course_id == course_id]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)

