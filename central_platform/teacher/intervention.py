"""Teacher Intervention System with multi-status lifecycle, deterministic trigger evaluation, and audit logging.

Implements Master Plan Section 21 (Phase 12):
- 5 Lifecycle Statuses: OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, DISMISSED
- 6 Authoritative Trigger Types:
  1. persistent_misconception
  2. declining_performance
  3. long_inactivity
  4. repeated_failed_assessment
  5. low_prerequisite_mastery
  6. teacher_created
- Auditable trigger evidence invariant: Zero automatic interventions without concrete evidence.
- Priority levels: CRITICAL, HIGH, MEDIUM, LOW
- Teacher notes & resolution logging
- Backwards compatibility with TeacherAlert and bridge slots
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.central_platform.teacher.intervention")


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


class InterventionStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class InterventionPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InterventionTriggerType(str, Enum):
    PERSISTENT_MISCONCEPTION = "persistent_misconception"
    DECLINING_PERFORMANCE = "declining_performance"
    LONG_INACTIVITY = "long_inactivity"
    REPEATED_FAILED_ASSESSMENT = "repeated_failed_assessment"
    LOW_PREREQUISITE_MASTERY = "low_prerequisite_mastery"
    TEACHER_CREATED = "teacher_created"


@dataclass
class TeacherNote:
    note_id: str
    author_id: str
    author_name: str
    text: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TeacherAlert:
    """Legacy alert entity preserved for backward compatibility."""
    alert_id: str
    student_id: str
    course_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.DETECTED
    assigned_teacher_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value if hasattr(self.severity, "value") else str(self.severity)
        d["status"] = self.status.value if hasattr(self.status, "value") else str(self.status)
        return d


@dataclass
class TeacherIntervention:
    """Canonical Teacher Intervention entity with full Section 21 fields."""
    intervention_id: str
    student_id: str
    course_id: str
    reason: str
    priority: str = InterventionPriority.MEDIUM.value
    assigned_teacher: Optional[str] = None
    trigger_type: str = InterventionTriggerType.TEACHER_CREATED.value
    trigger_evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    due_at: Optional[str] = None
    status: str = InterventionStatus.OPEN.value
    resolution: Optional[str] = None
    teacher_notes: List[Dict[str, Any]] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    dismissed_at: Optional[str] = None
    dismissed_by: Optional[str] = None
    dismissal_reason: Optional[str] = None

    def __post_init__(self):
        if not self.audit_trail:
            self.audit_trail = [
                {
                    "action": "created",
                    "actor_id": self.assigned_teacher or "system",
                    "timestamp": self.created_at,
                    "status": self.status,
                    "details": f"Intervention initialized via {self.trigger_type}",
                }
            ]

    def to_dict(self) -> dict:
        return asdict(self)


class TeacherInterventionEngine:
    """Manages intervention queue, lifecycle state machine, notes, and trigger evaluation."""

    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self._alerts: dict[str, TeacherAlert] = {}
        self._interventions: dict[str, TeacherIntervention] = {}

    # ── Legacy Alert Methods (Backward Compatibility) ──────────────────────
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

    # ── Section 21 Teacher Intervention Methods ────────────────────────────
    def create_intervention(
        self,
        intervention: TeacherIntervention,
        actor_id: Optional[str] = None,
    ) -> TeacherIntervention:
        """Create a new intervention with non-negotiable auditable evidence invariant."""
        # Non-negotiable rule: No automatic intervention without evidence
        if intervention.trigger_type != InterventionTriggerType.TEACHER_CREATED.value:
            if not intervention.trigger_evidence:
                raise ValueError(
                    f"Invariant violation: Automatic intervention of type '{intervention.trigger_type}' "
                    f"cannot be created without concrete auditable trigger evidence."
                )

        now = datetime.now(timezone.utc).isoformat()
        actor = actor_id or intervention.assigned_teacher or "system"
        intervention.audit_trail.append({
            "action": "registered",
            "actor_id": actor,
            "timestamp": now,
            "status": intervention.status,
            "details": "Registered in active intervention queue",
        })

        self._interventions[intervention.intervention_id] = intervention

        if self.db and hasattr(self.db, "create_intervention"):
            try:
                from central_platform.models.schema import InterventionRecord
                rec = InterventionRecord(
                    id=intervention.intervention_id,
                    student_id=intervention.student_id,
                    course_id=intervention.course_id,
                    message=intervention.reason,
                    status=intervention.status,
                    created_at=intervention.created_at,
                    resolved_at=intervention.resolved_at,
                    reason=intervention.reason,
                    priority=intervention.priority,
                    assigned_teacher=intervention.assigned_teacher,
                    due_at=intervention.due_at,
                    resolution=intervention.resolution,
                    teacher_notes=intervention.teacher_notes,
                    trigger_type=intervention.trigger_type,
                    trigger_evidence=intervention.trigger_evidence,
                    audit_trail=intervention.audit_trail,
                )
                self.db.create_intervention(rec)
            except Exception as exc:
                logger.warning("Failed to persist teacher intervention %s to DB: %s", intervention.intervention_id, exc)

        return intervention

    def get_intervention(self, intervention_id: str) -> Optional[TeacherIntervention]:
        """Retrieve single intervention by ID."""
        return self._interventions.get(intervention_id)

    def get_interventions(
        self,
        course_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_teacher: Optional[str] = None,
    ) -> List[TeacherIntervention]:
        """List interventions matching multi-parameter criteria."""
        results = []
        for itv in self._interventions.values():
            if course_id and itv.course_id != course_id and itv.course_id not in ("all", "*"):
                continue
            if student_id and itv.student_id != student_id and itv.student_id not in ("all", "*"):
                continue
            if status and itv.status != status:
                continue
            if priority and itv.priority != priority:
                continue
            if assigned_teacher and itv.assigned_teacher and itv.assigned_teacher != assigned_teacher:
                continue
            results.append(itv)

        # Sort priority (CRITICAL -> HIGH -> MEDIUM -> LOW), then created_at desc
        priority_weights = {
            InterventionPriority.CRITICAL.value: 4,
            InterventionPriority.HIGH.value: 3,
            InterventionPriority.MEDIUM.value: 2,
            InterventionPriority.LOW.value: 1,
        }
        return sorted(
            results,
            key=lambda x: (priority_weights.get(x.priority, 0), x.created_at),
            reverse=True,
        )

    def transition_intervention_status(
        self,
        intervention_id: str,
        new_status: str,
        actor_id: str,
        reason: str = "",
    ) -> Optional[TeacherIntervention]:
        """Transition intervention through the 5 mandatory lifecycle states."""
        itv = self._interventions.get(intervention_id)
        if not itv:
            return None

        valid_statuses = {s.value for s in InterventionStatus}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of: {valid_statuses}")

        now = datetime.now(timezone.utc).isoformat()
        old_status = itv.status
        itv.status = new_status

        itv.audit_trail.append({
            "action": "status_changed",
            "actor_id": actor_id,
            "timestamp": now,
            "from_status": old_status,
            "to_status": new_status,
            "reason": reason or f"Status changed from {old_status} to {new_status}",
        })

        return itv

    def add_note(
        self,
        intervention_id: str,
        author_id: str,
        text: str,
        author_name: str = "Teacher",
    ) -> Optional[TeacherIntervention]:
        """Append an educator note with provenance and audit trail."""
        itv = self._interventions.get(intervention_id)
        if not itv:
            return None

        now = datetime.now(timezone.utc).isoformat()
        note = {
            "note_id": f"note-{uuid.uuid4().hex[:6]}",
            "author_id": author_id,
            "author_name": author_name,
            "text": text,
            "created_at": now,
        }
        itv.teacher_notes.append(note)

        itv.audit_trail.append({
            "action": "note_added",
            "actor_id": author_id,
            "timestamp": now,
            "note_id": note["note_id"],
        })

        return itv

    def resolve_intervention(
        self,
        intervention_id: str,
        actor_id: str,
        resolution_note: str,
    ) -> Optional[TeacherIntervention]:
        """Formally resolve an intervention with mandatory resolution explanation."""
        itv = self._interventions.get(intervention_id)
        if not itv:
            return None

        if not resolution_note or not resolution_note.strip():
            raise ValueError("Resolution note cannot be empty when resolving an intervention.")

        now = datetime.now(timezone.utc).isoformat()
        itv.status = InterventionStatus.RESOLVED.value
        itv.resolution = resolution_note.strip()
        itv.resolved_at = now
        itv.resolved_by = actor_id

        # Also add as a teacher note
        itv.teacher_notes.append({
            "note_id": f"note-res-{uuid.uuid4().hex[:6]}",
            "author_id": actor_id,
            "author_name": "Teacher",
            "text": f"Resolution: {resolution_note.strip()}",
            "created_at": now,
        })

        itv.audit_trail.append({
            "action": "resolved",
            "actor_id": actor_id,
            "timestamp": now,
            "resolution": resolution_note.strip(),
        })

        return itv

    def dismiss_intervention(
        self,
        intervention_id: str,
        actor_id: str,
        reason: str,
    ) -> Optional[TeacherIntervention]:
        """Dismiss an intervention with mandatory auditable rationale."""
        itv = self._interventions.get(intervention_id)
        if not itv:
            return None

        if not reason or not reason.strip():
            raise ValueError("Dismissal reason cannot be empty when dismissing an intervention.")

        now = datetime.now(timezone.utc).isoformat()
        itv.status = InterventionStatus.DISMISSED.value
        itv.dismissal_reason = reason.strip()
        itv.dismissed_at = now
        itv.dismissed_by = actor_id

        itv.audit_trail.append({
            "action": "dismissed",
            "actor_id": actor_id,
            "timestamp": now,
            "reason": reason.strip(),
        })

        return itv

    def evaluate_triggers_for_student(
        self,
        student_id: str,
        course_id: str,
        slr: Optional[Any] = None,
        recent_events: Optional[List[Any]] = None,
    ) -> List[TeacherIntervention]:
        """Evaluate SLR and telemetry events to deterministically trigger interventions with evidence."""
        generated: List[TeacherIntervention] = []
        now = datetime.now(timezone.utc)

        if not slr:
            return generated

        # Extract data from SLR
        slr_dict = slr.to_dict() if hasattr(slr, "to_dict") else {}
        misconceptions = slr_dict.get("misconceptions", [])
        mastery_states = slr_dict.get("mastery_states", {})
        recent_sessions = slr_dict.get("recent_sessions", [])
        assessment_results = slr_dict.get("assessment_results", [])

        # Trigger 1: Persistent Misconceptions (active or seen multiple times)
        for m in misconceptions:
            active = m.get("active", True)
            occurrence_count = m.get("occurrence_count", 1)
            misc_id = m.get("id") or m.get("misconception_id", "unknown")
            concept_id = m.get("concept_id", "general")

            if active and occurrence_count >= 2:
                itv = TeacherIntervention(
                    intervention_id=f"itv-misc-{uuid.uuid4().hex[:6]}",
                    student_id=student_id,
                    course_id=course_id,
                    reason=f"Persistent misconception '{misc_id}' detected across {occurrence_count} attempts on concept '{concept_id}'.",
                    priority=InterventionPriority.CRITICAL.value if occurrence_count >= 3 else InterventionPriority.HIGH.value,
                    trigger_type=InterventionTriggerType.PERSISTENT_MISCONCEPTION.value,
                    trigger_evidence={
                        "misconception_id": misc_id,
                        "concept_id": concept_id,
                        "occurrence_count": occurrence_count,
                        "last_detected": m.get("last_detected"),
                    },
                    due_at=(now + timedelta(days=2)).isoformat(),
                )
                generated.append(itv)

        # Trigger 2: Declining Performance
        # Check if accuracy dropped significantly over recent events
        if recent_events and len(recent_events) >= 5:
            recent_attempts = [e for e in recent_events if getattr(e, "event_type", "") in ("question_attempted", "assessment_submitted")]
            if len(recent_attempts) >= 4:
                first_half = recent_attempts[:len(recent_attempts)//2]
                second_half = recent_attempts[len(recent_attempts)//2:]
                
                score_first = sum(e.payload.get("score", 0.0) for e in first_half) / max(len(first_half), 1)
                score_second = sum(e.payload.get("score", 0.0) for e in second_half) / max(len(second_half), 1)

                if (score_first - score_second) >= 0.25 and score_second < 0.60:
                    itv = TeacherIntervention(
                        intervention_id=f"itv-decline-{uuid.uuid4().hex[:6]}",
                        student_id=student_id,
                        course_id=course_id,
                        reason=f"Performance declined from {score_first:.0%} to {score_second:.0%} over recent session attempts.",
                        priority=InterventionPriority.HIGH.value,
                        trigger_type=InterventionTriggerType.DECLINING_PERFORMANCE.value,
                        trigger_evidence={
                            "baseline_score": score_first,
                            "recent_score": score_second,
                            "score_drop": round(score_first - score_second, 2),
                            "attempts_analyzed": len(recent_attempts),
                        },
                        due_at=(now + timedelta(days=3)).isoformat(),
                    )
                    generated.append(itv)

        # Trigger 3: Repeated Failed Assessment
        failed_assessments = [
            a for a in assessment_results if a.get("score", 1.0) < 0.50 or a.get("passed") is False
        ]
        if len(failed_assessments) >= 2:
            itv = TeacherIntervention(
                intervention_id=f"itv-asm-{uuid.uuid4().hex[:6]}",
                student_id=student_id,
                course_id=course_id,
                reason=f"Student failed {len(failed_assessments)} consecutive assessment attempts.",
                priority=InterventionPriority.HIGH.value,
                trigger_type=InterventionTriggerType.REPEATED_FAILED_ASSESSMENT.value,
                trigger_evidence={
                    "failed_count": len(failed_assessments),
                    "failed_assessments": [a.get("assessment_id") or a.get("id") for a in failed_assessments],
                },
                due_at=(now + timedelta(days=2)).isoformat(),
            )
            generated.append(itv)

        # Trigger 4: Low Prerequisite Mastery
        # If any prerequisite in SLR has mastery < 0.40 while student is active
        for cid, m_data in mastery_states.items():
            val = m_data.get("p_mastery", 0.0) if isinstance(m_data, dict) else getattr(m_data, "p_mastery", 0.0)
            if 0 < val < 0.40 and "prereq" in cid.lower():
                itv = TeacherIntervention(
                    intervention_id=f"itv-prereq-{uuid.uuid4().hex[:6]}",
                    student_id=student_id,
                    course_id=course_id,
                    reason=f"Low prerequisite mastery ({val:.0%}) detected for '{cid}'.",
                    priority=InterventionPriority.MEDIUM.value,
                    trigger_type=InterventionTriggerType.LOW_PREREQUISITE_MASTERY.value,
                    trigger_evidence={
                        "concept_id": cid,
                        "mastery": val,
                        "threshold": 0.40,
                    },
                    due_at=(now + timedelta(days=5)).isoformat(),
                )
                generated.append(itv)

        # Trigger 5: Long Inactivity
        if recent_sessions:
            last_session = recent_sessions[0]
            last_date_str = last_session.get("end_time") or last_session.get("start_time")
            if last_date_str:
                try:
                    last_dt = datetime.fromisoformat(last_date_str.replace("Z", "+00:00"))
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    days_idle = (now - last_dt).days
                    if days_idle >= 7:
                        itv = TeacherIntervention(
                            intervention_id=f"itv-inact-{uuid.uuid4().hex[:6]}",
                            student_id=student_id,
                            course_id=course_id,
                            reason=f"Student inactive for {days_idle} days in course '{course_id}'.",
                            priority=InterventionPriority.MEDIUM.value,
                            trigger_type=InterventionTriggerType.LONG_INACTIVITY.value,
                            trigger_evidence={
                                "days_inactive": days_idle,
                                "last_active": last_date_str,
                            },
                            due_at=(now + timedelta(days=3)).isoformat(),
                        )
                        generated.append(itv)
                except Exception as exc:
                    logger.debug("Failed to calculate inactivity for student %s: %s", student_id, exc)

        # Register each generated intervention into queue
        for itv in generated:
            self.create_intervention(itv, actor_id="telemetry_engine")

        return generated
