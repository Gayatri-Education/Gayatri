"""Canonical Learning State Manager (Phase 04 - Course-Scoped & Version-Aware).

Consolidates TutorContext, StudentProfile, TutorStateManager, SQLite mastery,
LDG, and event storage into one authoritative persistent model + session runtime state.
Enforces strict cross-course isolation and course-scoped student progress.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    CourseLearningContext,
    StudentLearningRecord,
    MasteryState,
    Misconception,
    Session,
    SessionStatus,
    LearningEvent,
)


@dataclass
class SessionRuntimeState:
    """Ephemeral runtime state for a live tutoring session.
    Replaces legacy TutorContext."""
    session_id: str
    student_id: str
    course_id: str
    concept_id: str
    course_version_id: Optional[str] = None
    course_offering_id: Optional[str] = None
    class_id: Optional[str] = None
    mode: str = "EXPLAIN"
    waiting_for_answer: bool = False
    last_response_type: str = "explain"
    consecutive_errors: int = 0
    hints_used: int = 0
    recovery_mode: bool = False
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalLearningState:
    """Authoritative consolidated persistent state for a student in a specific course.
    Replaces legacy StudentProfile."""
    slr: StudentLearningRecord
    mastery: Dict[str, MasteryState] = field(default_factory=dict)
    misconceptions: List[Misconception] = field(default_factory=list)
    recent_events: List[LearningEvent] = field(default_factory=list)
    course_version_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slr": self.slr.to_dict(),
            "mastery": {k: asdict(v) for k, v in self.mastery.items()},
            "misconceptions": [asdict(m) for m in self.misconceptions],
            "recent_events": [asdict(e) for e in self.recent_events],
            "course_version_id": self.course_version_id,
        }


class LearningStateManager:
    """Authoritative state manager consolidating all student state interactions."""

    def __init__(self, db: PlatformDatabase):
        self.db = db
        # In-memory fast cache for live sessions
        self._active_sessions: Dict[str, SessionRuntimeState] = {}

    def get_canonical_state(
        self,
        student_id: str,
        course_id: str,
        course_version_id: Optional[str] = None,
    ) -> CanonicalLearningState:
        """Fetch the unified persistent state for a student strictly scoped to a course."""
        if not student_id or not str(student_id).strip():
            raise ValueError("student_id must not be empty when querying learning state.")
        if not course_id or not str(course_id).strip():
            raise ValueError("course_id must not be empty when querying learning state.")

        # 1. Fetch or create SLR for this (student_id, course_id)
        slr = self.db.get_slr(student_id, course_id)
        if not slr:
            slr_id = f"slr_{uuid.uuid4().hex[:8]}"
            slr = StudentLearningRecord(id=slr_id, student_id=student_id, course_id=course_id)
            self.db.create_slr(slr)

        # 2. Fetch Mastery exclusively tied to this course's SLR
        mastery_list = self.db.get_mastery_states_for_slr(slr.id)
        mastery_dict = {m.concept_id: m for m in mastery_list}

        # 3. Fetch Misconceptions
        student_miscs = self.db.get_student_misconceptions(student_id)
        misconceptions = []
        for sm in student_miscs:
            m = self.db.get_misconception_by_code(sm.misconception_code)
            if m:
                misconceptions.append(m)

        # 4. Fetch Recent Events scoped strictly to this course
        events = self.db.query_learning_events(student_id=student_id, course_id=course_id, limit=20)

        return CanonicalLearningState(
            slr=slr,
            mastery=mastery_dict,
            misconceptions=misconceptions,
            recent_events=events,
            course_version_id=course_version_id,
        )

    def update_mastery(
        self,
        student_id: str,
        course_id: str,
        concept_id: str,
        score: float,
        confidence: float = 0.8,
    ) -> MasteryState:
        """Idempotently update mastery in the canonical store strictly scoped to (student_id, course_id)."""
        if not student_id or not str(student_id).strip():
            raise ValueError("student_id must not be empty when updating mastery.")
        if not course_id or not str(course_id).strip():
            raise ValueError("course_id must not be empty when updating mastery.")

        slr = self.db.get_slr(student_id, course_id)
        if not slr:
            state = self.get_canonical_state(student_id, course_id)
            slr = state.slr

        mastery_list = self.db.get_mastery_states_for_slr(slr.id)
        ms = next((m for m in mastery_list if m.concept_id == concept_id), None)

        now = datetime.now(timezone.utc).isoformat()
        if ms:
            ms.score = score
            ms.confidence = confidence
            ms.updated_at = now
            ms.last_practiced_at = now
            self.db.upsert_mastery_state(ms)
        else:
            ms = MasteryState(
                slr_id=slr.id,
                concept_id=concept_id,
                score=score,
                confidence=confidence,
                updated_at=now,
                last_practiced_at=now,
            )
            self.db.upsert_mastery_state(ms)

        return ms

    def initialize_session(
        self,
        student_id: Union[str, CourseLearningContext, None] = None,
        course_id: Optional[str] = None,
        concept_id: str = "",
        course_version_id: Optional[str] = None,
        course_offering_id: Optional[str] = None,
        class_id: Optional[str] = None,
        context: Optional[CourseLearningContext] = None,
        student_id_or_context: Union[str, CourseLearningContext, None] = None,
    ) -> SessionRuntimeState:
        """Start a new learning session with authoritative course and version binding."""
        effective_student_id = student_id if student_id is not None else student_id_or_context
        if context is not None:
            ctx = context
            ctx.validate()
            s_id = ctx.student_id
            c_id = ctx.course_id
            v_id = ctx.course_version_id
            off_id = ctx.course_offering_id
            cls_id = ctx.class_id
        elif isinstance(effective_student_id, CourseLearningContext):
            ctx = effective_student_id
            ctx.validate()
            s_id = ctx.student_id
            c_id = ctx.course_id
            v_id = ctx.course_version_id
            off_id = ctx.course_offering_id
            cls_id = ctx.class_id
        else:
            s_id = effective_student_id
            c_id = course_id
            v_id = course_version_id
            off_id = course_offering_id
            cls_id = class_id



        if not s_id or not str(s_id).strip():
            raise ValueError("student_id must not be empty when initializing session.")
        if not c_id or not str(c_id).strip():
            raise ValueError("course_id must not be empty when initializing session.")

        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        sess = Session(
            id=session_id,
            student_id=s_id,
            course_id=c_id,
            concept_id=concept_id,
            course_version_id=v_id,
            course_offering_id=off_id,
            class_id=cls_id,
            status=SessionStatus.ACTIVE,
        )
        self.db.create_session(sess)

        runtime = SessionRuntimeState(
            session_id=session_id,
            student_id=s_id,
            course_id=c_id,
            concept_id=concept_id,
            course_version_id=v_id,
            course_offering_id=off_id,
            class_id=cls_id,
        )
        self._active_sessions[session_id] = runtime
        return runtime

    def get_session_runtime(self, session_id: str) -> Optional[SessionRuntimeState]:
        """Fetch active runtime state, looking up from DB if not in in-memory cache."""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        sess = self.db.get_session(session_id)
        if sess and sess.status == SessionStatus.ACTIVE:
            runtime = SessionRuntimeState(
                session_id=sess.id,
                student_id=sess.student_id,
                course_id=sess.course_id,
                concept_id=sess.concept_id,
                course_version_id=sess.course_version_id,
                course_offering_id=sess.course_offering_id,
                class_id=sess.class_id,
                started_at=sess.started_at,
            )
            self._active_sessions[session_id] = runtime
            return runtime
        return None

    def log_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> LearningEvent:
        """Log an immutable, course-scoped learning event attached to a session (idempotent)."""
        sess = self.db.get_session(session_id)
        if not sess:
            raise ValueError(f"Session {session_id} not found.")

        eid = event_id or f"evt_{uuid.uuid4().hex[:8]}"
        event = LearningEvent(
            id=eid,
            session_id=session_id,
            student_id=sess.student_id,
            course_id=sess.course_id,
            course_version_id=sess.course_version_id,
            concept_id=sess.concept_id,
            event_type=event_type,
            payload=data,
        )
        self.db.record_learning_event(event)
        return event

    def end_session(self, session_id: str) -> None:
        """End a session and flush runtime state."""
        self.db.end_session(session_id)
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def get_student_courses(self, student_id: str) -> List[str]:
        """Return distinct course IDs in which the student has learning records."""
        with self.db._get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT course_id FROM student_learning_records WHERE student_id = ?;",
                (student_id,),
            ).fetchall()
            return [r["course_id"] for r in rows]
