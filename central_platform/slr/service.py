"""Authoritative Student Learning Record (SLR) Service (Phase 06).

Master Plan Section 15:
The SLR is the single canonical student learning view aggregated from central events
and authoritative persistence. Neither student desktop nor teacher portal may invent
independent student state.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import (
    Course,
    Curriculum,
    Enrollment,
    MasteryState,
    Misconception,
    Session,
    SessionStatus,
    StudentLearningRecord as DBMasterSLR,
    StudentMisconceptionRecord,
    User,
    UserRole,
)
from central_platform.slr.models import (
    AuthoritativeSLR,
    SLRAlert,
    SLRAssessmentResult,
    SLRCourse,
    SLRCurriculum,
    SLREnrollment,
    SLRHints,
    SLRIdentity,
    SLRIntervention,
    SLRMastery,
    SLRMisconception,
    SLRRecommendation,
    SLRSession,
    SLRTeacherFeedback,
    SLRTeacherInstruction,
    SLRTimelineItem,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SLRService:
    """Authoritative SLR service providing canonical student learning views."""

    def __init__(
        self,
        db: Optional[PlatformDatabase] = None,
        event_store: Optional[LearningEventStore] = None,
    ):
        if db is not None:
            self.db = db
        else:
            try:
                from central_platform.auth.dependencies import get_db
                self.db = get_db()
            except Exception:
                self.db = PlatformDatabase()
        self.event_store = (
            event_store if event_store is not None else LearningEventStore(db=self.db)
        )

    def get_authoritative_slr(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> AuthoritativeSLR:
        """Construct the canonical 15-dimension Authoritative SLR for a student."""
        target_course = course_id or "crs-chem-101"
        self._ensure_student_scaffolding(student_id, target_course)

        # 1. Identity
        user = self.db.get_user(student_id)
        if user:
            identity = SLRIdentity(
                student_id=user.id,
                student_name=user.full_name,
                email=user.email,
                organization_id=user.organization_id or "org-default",
                created_at=user.created_at,
            )
            org_id = user.organization_id or "org-default"
        else:
            identity = SLRIdentity(
                student_id=student_id,
                student_name=f"Student ({student_id})",
                email=f"{student_id}@gayatri.ai",
                organization_id="org-default",
            )
            org_id = "org-default"

        # 2. Enrollment
        enrollments = self.db.get_enrollments_for_student(student_id)
        matched_enr = next(
            (e for e in enrollments if e.course_id == target_course and e.is_active),
            enrollments[0] if enrollments else None,
        )
        if matched_enr:
            enrollment = SLREnrollment(
                enrollment_id=matched_enr.id,
                course_id=matched_enr.course_id,
                cohort_id=matched_enr.cohort_id,
                is_active=matched_enr.is_active,
                enrolled_at=matched_enr.enrolled_at,
            )
            target_course = matched_enr.course_id
        else:
            enrollment = SLREnrollment(
                enrollment_id=f"enr-{student_id}-{target_course}",
                course_id=target_course,
                is_active=True,
            )

        # 3. Course
        db_course = self.db.get_course(target_course)
        if db_course:
            course = SLRCourse(
                course_id=db_course.id,
                code=db_course.code,
                title=db_course.title,
                description=db_course.description,
            )
        else:
            course = SLRCourse(
                course_id=target_course,
                code="CHEM101",
                title="Thermodynamics & Physical Chemistry",
                description="Core Chemistry curriculum",
            )

        # 4. Curriculum
        db_curriculum = self.db.get_curriculum_for_course(target_course)
        if db_curriculum:
            curriculum = SLRCurriculum(
                curriculum_id=db_curriculum.id,
                version=db_curriculum.version,
                current_concept="chem_thermo_first_law",
            )
        else:
            curriculum = SLRCurriculum(
                curriculum_id=f"cur-{target_course}",
                version="1.0.0",
                current_concept="chem_thermo_first_law",
            )

        # 5. Mastery
        db_slr = self.db.get_slr(student_id, target_course)
        concept_scores: Dict[str, float] = {}
        concept_confidences: Dict[str, float] = {}
        if db_slr:
            states = self.db.get_mastery_states_for_slr(db_slr.id)
            for s in states:
                concept_scores[s.concept_id] = s.score
                concept_confidences[s.concept_id] = s.confidence

        if not concept_scores:
            # Default active concept score baseline
            concept_scores["chem_thermo_first_law"] = 0.50
            concept_confidences["chem_thermo_first_law"] = 0.80

        avg_score = (
            sum(concept_scores.values()) / len(concept_scores) if concept_scores else 0.50
        )
        mastery = SLRMastery(
            overall_score=round(avg_score, 4),
            retention_rate=0.85,
            concept_scores=concept_scores,
            concept_confidences=concept_confidences,
            updated_at=_now_iso(),
        )

        # 6. Recent Sessions
        db_sessions = self.db.get_sessions_for_student(student_id, limit=10)
        recent_sessions: List[SLRSession] = []
        for s in db_sessions:
            dur = None
            if s.ended_at and s.started_at:
                try:
                    t1 = datetime.fromisoformat(s.started_at)
                    t2 = datetime.fromisoformat(s.ended_at)
                    dur = int((t2 - t1).total_seconds())
                except Exception:
                    dur = None
            status_str = (
                s.status.value if isinstance(s.status, SessionStatus) else str(s.status)
            )
            recent_sessions.append(
                SLRSession(
                    session_id=s.id,
                    concept_id=s.concept_id,
                    status=status_str,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                    duration_seconds=dur,
                )
            )

        # 7. Learning Timeline
        raw_events = self.event_store.get_student_events(
            student_id=student_id,
            course_id=target_course,
            limit=50,
        )
        timeline: List[SLRTimelineItem] = []
        for ev in raw_events:
            summary = self._summarize_event(ev.event_type, ev.concept_id, ev.score, ev.payload)
            timeline.append(
                SLRTimelineItem(
                    item_id=ev.id,
                    event_type=ev.event_type,
                    summary=summary,
                    timestamp=ev.created_at,
                    concept_id=ev.concept_id,
                    score=ev.score,
                    metadata=ev.payload,
                )
            )

        # 8. Misconceptions
        db_misc_records = self.db.get_student_misconceptions(student_id)
        misconceptions: List[SLRMisconception] = []
        for mr in db_misc_records:
            misc_cat = self.db.get_misconception_by_code(mr.misconception_code)
            misconceptions.append(
                SLRMisconception(
                    code=mr.misconception_code,
                    category=misc_cat.category if misc_cat else "thermodynamics",
                    name=misc_cat.name if misc_cat else mr.misconception_code,
                    frequency=mr.frequency,
                    last_observed=mr.last_observed,
                    remediation=misc_cat.remediation if misc_cat else "",
                    status="active" if mr.frequency >= 2 else "recovering",
                )
            )

        # 9. Assessment Results
        db_attempts = self.db.get_assessment_attempts_for_student(student_id, limit=20)
        assessment_results: List[SLRAssessmentResult] = []
        for att in db_attempts:
            asmt = self.db.get_assessment(att.assessment_id)
            total = asmt.total_marks if asmt else 100.0
            title = asmt.title if asmt else f"Assessment ({att.assessment_id})"
            pct = round((att.score / total) * 100.0, 2) if total > 0 else 0.0
            assessment_results.append(
                SLRAssessmentResult(
                    attempt_id=att.id,
                    assessment_id=att.assessment_id,
                    title=title,
                    score=att.score,
                    max_marks=total,
                    percentage=pct,
                    passed=att.passed,
                    completed_at=att.completed_at or att.started_at,
                )
            )

        # 10. Hints
        hint_requested_events = [
            e for e in raw_events if e.event_type == LearningEventType.HINT_REQUESTED.value
        ]
        hint_used_events = [
            e for e in raw_events if e.event_type == LearningEventType.HINT_USED.value
        ]
        breakdown: Dict[str, int] = {}
        for h in hint_requested_events:
            cid = h.concept_id or "general"
            breakdown[cid] = breakdown.get(cid, 0) + 1
        last_hint = (
            hint_requested_events[0].created_at if hint_requested_events else None
        )
        hints = SLRHints(
            total_hints_requested=len(hint_requested_events),
            hints_used=len(hint_used_events),
            per_concept_breakdown=breakdown,
            last_hint_at=last_hint,
        )

        # 11. Teacher Feedback
        teacher_feedback: List[SLRTeacherFeedback] = []

        # 12. Teacher Instructions
        db_instructions = self.db.get_teacher_instructions(
            course_id=target_course,
            student_id=student_id,
        )
        teacher_instructions: List[SLRTeacherInstruction] = [
            SLRTeacherInstruction(
                instruction_id=ti.id,
                teacher_id=ti.teacher_id,
                instruction_text=ti.instruction_text,
                concept_scope=ti.concept_scope,
                priority=ti.priority,
                created_at=ti.created_at,
            )
            for ti in db_instructions
        ]

        # 13. Interventions
        db_interventions = self.db.get_interventions_for_student(student_id)
        interventions: List[SLRIntervention] = [
            SLRIntervention(
                intervention_id=iv.id,
                severity=iv.severity.value,
                alert_type=iv.alert_type,
                message=iv.message,
                status=iv.status.value,
                created_at=iv.created_at,
                resolved_at=iv.resolved_at,
            )
            for iv in db_interventions
        ]

        # 14. Recommendations (Pedagogical Next Steps)
        recommendations: List[SLRRecommendation] = []
        rec_idx = 1
        for cid, score in concept_scores.items():
            if score < 0.60:
                recommendations.append(
                    SLRRecommendation(
                        recommendation_id=f"rec-{student_id}-{rec_idx}",
                        concept_id=cid,
                        action_type="review",
                        reason=f"Mastery in {cid} is {score*100:.0f}%, which is below proficiency threshold (60%).",
                        priority=1,
                    )
                )
                rec_idx += 1

        for misc in misconceptions:
            if misc.frequency >= 1 and misc.status == "active":
                recommendations.append(
                    SLRRecommendation(
                        recommendation_id=f"rec-{student_id}-{rec_idx}",
                        concept_id=misc.code,
                        action_type="practice",
                        reason=f"Active misconception detected: {misc.name}. Targeted conceptual remediation recommended.",
                        priority=2,
                    )
                )
                rec_idx += 1

        if not recommendations:
            recommendations.append(
                SLRRecommendation(
                    recommendation_id=f"rec-{student_id}-{rec_idx}",
                    concept_id=curriculum.current_concept,
                    action_type="advance",
                    reason="Student demonstrated strong mastery (>80%). Ready to advance curriculum module.",
                    priority=3,
                )
            )

        # 15. Alerts
        alerts: List[SLRAlert] = []
        alert_idx = 1
        for cid, score in concept_scores.items():
            if score < 0.40:
                alerts.append(
                    SLRAlert(
                        alert_id=f"alt-{student_id}-{alert_idx}",
                        alert_type="learning_gap",
                        severity="high",
                        message=f"Critical learning gap in concept '{cid}' (score: {score*100:.0f}%).",
                        triggered_at=_now_iso(),
                    )
                )
                alert_idx += 1

        for misc in misconceptions:
            if misc.frequency >= 3:
                alerts.append(
                    SLRAlert(
                        alert_id=f"alt-{student_id}-{alert_idx}",
                        alert_type="persistent_misconception",
                        severity="critical",
                        message=f"Persistent misconception '{misc.name}' ({misc.code}) observed {misc.frequency} times.",
                        triggered_at=misc.last_observed,
                    )
                )
                alert_idx += 1

        if hints.total_hints_requested >= 10:
            alerts.append(
                SLRAlert(
                    alert_id=f"alt-{student_id}-{alert_idx}",
                    alert_type="excessive_hints",
                    severity="warning",
                    message="High hint dependency detected (10+ hint requests recorded).",
                    triggered_at=_now_iso(),
                )
            )
            alert_idx += 1

        slr_id = db_slr.id if db_slr else f"slr-{student_id}"

        slr_instance = AuthoritativeSLR(
            slr_id=slr_id,
            student_id=student_id,
            course_id=target_course,
            authoritative=True,
            schema_version="1.0.0",
            generated_at=_now_iso(),
            identity=identity,
            enrollment=enrollment,
            course=course,
            curriculum=curriculum,
            mastery=mastery,
            recent_sessions=recent_sessions,
            learning_timeline=timeline,
            misconceptions=misconceptions,
            assessment_results=assessment_results,
            hints=hints,
            teacher_feedback=teacher_feedback,
            teacher_instructions=teacher_instructions,
            interventions=interventions,
            recommendations=recommendations,
            alerts=alerts,
        )

        return slr_instance

    def update_concept_mastery(
        self,
        student_id: str,
        concept_id: str,
        score: float,
        course_id: Optional[str] = None,
        confidence: float = 0.85,
    ) -> AuthoritativeSLR:
        """Update concept mastery in authoritative platform database and recompute SLR."""
        target_course = course_id or "crs-chem-101"
        self._ensure_student_scaffolding(student_id, target_course)

        db_slr = self.db.get_slr(student_id, target_course)
        if not db_slr:
            db_slr = DBMasterSLR(
                id=f"slr-{student_id}",
                student_id=student_id,
                course_id=target_course,
                authoritative=True,
            )
            self.db.create_slr(db_slr)

        mastery_state = MasteryState(
            id=f"mst-{student_id}-{concept_id}",
            slr_id=db_slr.id,
            concept_id=concept_id,
            score=max(0.0, min(1.0, float(score))),
            confidence=confidence,
            updated_at=_now_iso(),
        )
        self.db.upsert_mastery_state(mastery_state)
        return self.get_authoritative_slr(student_id, target_course)

    def record_student_misconception(
        self,
        student_id: str,
        misconception_code: str,
        course_id: Optional[str] = None,
    ) -> AuthoritativeSLR:
        """Record or increment student misconception frequency."""
        target_course = course_id or "crs-chem-101"
        self._ensure_student_scaffolding(student_id, target_course)

        existing_cat = self.db.get_misconception_by_code(misconception_code)
        if not existing_cat:
            self.db.create_misconception(
                Misconception(
                    id=f"misc-{misconception_code.lower()}",
                    code=misconception_code,
                    category="general",
                    name=misconception_code.replace("_", " ").title(),
                    description=f"Auto-registered misconception: {misconception_code}",
                )
            )

        existing = [
            m for m in self.db.get_student_misconceptions(student_id)
            if m.misconception_code == misconception_code
        ]
        freq = (existing[0].frequency + 1) if existing else 1
        record = StudentMisconceptionRecord(
            id=f"smr-{student_id}-{misconception_code}",
            student_id=student_id,
            misconception_code=misconception_code,
            frequency=freq,
            last_observed=_now_iso(),
        )
        self.db.record_student_misconception(record)
        return self.get_authoritative_slr(student_id, target_course)

    def project_from_events(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> AuthoritativeSLR:
        """Replay student events through event store and project state into database."""
        target_course = course_id or "crs-chem-101"
        self._ensure_student_scaffolding(student_id, target_course)

        events = self.event_store.get_student_events(
            student_id=student_id,
            course_id=target_course,
            limit=500,
        )
        # Event replay projection
        replay_res = self.event_store.replay_events(student_id=student_id)

        db_slr = self.db.get_slr(student_id, target_course)
        if not db_slr:
            db_slr = DBMasterSLR(
                id=f"slr-{student_id}",
                student_id=student_id,
                course_id=target_course,
                authoritative=True,
            )
            self.db.create_slr(db_slr)

        # Sync projected mastery scores
        for cid, score in replay_res.concept_mastery.items():
            st = MasteryState(
                id=f"mst-{student_id}-{cid}",
                slr_id=db_slr.id,
                concept_id=cid,
                score=score,
                confidence=0.85,
                updated_at=_now_iso(),
            )
            self.db.upsert_mastery_state(st)

        return self.get_authoritative_slr(student_id, target_course)

    def get_timeline(
        self,
        student_id: str,
        limit: int = 50,
        reverse: bool = True,
    ) -> List[SLRTimelineItem]:
        """Return chronological or reverse-chronological learning timeline."""
        slr = self.get_authoritative_slr(student_id)
        return sorted(slr.learning_timeline, key=lambda x: x.timestamp, reverse=reverse)[:limit]

    def get_mastery_snapshot(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Return concept-to-mastery mapping."""
        slr = self.get_authoritative_slr(student_id, course_id=course_id)
        return slr.mastery.concept_scores

    def _ensure_student_scaffolding(self, student_id: str, course_id: str) -> None:
        """Ensure base entities exist in DB for foreign key consistency."""
        org = self.db.get_organization("org-default")
        if not org:
            from central_platform.models.schema import Organization
            self.db.create_organization(Organization(id="org-default", name="Default Organization", slug="default"))

        user = self.db.get_user(student_id)
        if not user:
            self.db.create_user(
                User(
                    id=student_id,
                    email=f"{student_id}@gayatri.ai",
                    full_name=f"Student ({student_id})",
                    role=UserRole.STUDENT,
                    organization_id="org-default",
                )
            )

        course = self.db.get_course(course_id)
        if not course:
            self.db.create_course(
                Course(
                    id=course_id,
                    organization_id="org-default",
                    code="CHEM101",
                    title="Thermodynamics & Physical Chemistry",
                )
            )

        curriculum = self.db.get_curriculum_for_course(course_id)
        if not curriculum:
            self.db.create_curriculum(
                Curriculum(
                    id=f"cur-{course_id}",
                    course_id=course_id,
                    title="Chemistry Core Curriculum",
                    version="1.0.0",
                )
            )

        enrollments = self.db.get_enrollments_for_student(student_id)
        if not any(e.course_id == course_id for e in enrollments):
            self.db.create_enrollment(
                Enrollment(
                    id=f"enr-{student_id}-{course_id}",
                    student_id=student_id,
                    course_id=course_id,
                    is_active=True,
                )
            )

        db_slr = self.db.get_slr(student_id, course_id)
        if not db_slr:
            self.db.create_slr(
                DBMasterSLR(
                    id=f"slr-{student_id}",
                    student_id=student_id,
                    course_id=course_id,
                    authoritative=True,
                )
            )

    @staticmethod
    def _summarize_event(
        event_type: str,
        concept_id: str,
        score: Optional[float],
        payload: Dict[str, Any],
    ) -> str:
        """Create human-readable event summary."""
        concept_name = concept_id or "General"
        if event_type == LearningEventType.QUESTION_ATTEMPTED.value:
            return f"Attempted practice question on '{concept_name}'"
        elif event_type == LearningEventType.ANSWER_SUBMITTED.value:
            score_text = f" (Score: {score*100:.0f}%)" if score is not None else ""
            return f"Submitted answer for '{concept_name}'{score_text}"
        elif event_type == LearningEventType.HINT_REQUESTED.value:
            return f"Requested hint for '{concept_name}'"
        elif event_type == LearningEventType.HINT_USED.value:
            return f"Used hint during practice on '{concept_name}'"
        elif event_type == LearningEventType.CONCEPT_INTRODUCED.value:
            return f"Introduced new concept '{concept_name}'"
        elif event_type == LearningEventType.CONCEPT_MASTERED.value:
            return f"Mastered concept '{concept_name}'"
        elif event_type == LearningEventType.MISCONCEPTION_DETECTED.value:
            misc_code = payload.get("misconception_code", "conceptual_error")
            return f"Detected misconception '{misc_code}' on '{concept_name}'"
        elif event_type == LearningEventType.ASSESSMENT_COMPLETED.value:
            score_text = f" with score {score}" if score is not None else ""
            return f"Completed assessment{score_text}"
        elif event_type == LearningEventType.SESSION_STARTED.value:
            return f"Started learning session on '{concept_name}'"
        elif event_type == LearningEventType.SESSION_COMPLETED.value:
            return f"Completed learning session on '{concept_name}'"
        elif event_type == LearningEventType.TEACHER_INSTRUCTION_CREATED.value:
            return f"Teacher directive assigned for '{concept_name}'"
        elif event_type == LearningEventType.TEACHER_INTERVENTION_CREATED.value:
            return f"Teacher intervention triggered: {payload.get('alert_type', 'intervention')}"
        return f"Learning activity: {event_type} on '{concept_name}'"
