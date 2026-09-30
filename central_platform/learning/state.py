"""Canonical Learning State Manager for Phase 11.

Consolidates TutorContext, StudentProfile, TutorStateManager, SQLite mastery,
LDG, and event storage into one authoritative persistent model + session runtime state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
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
    """Authoritative consolidated persistent state for a student in a course.
    Replaces legacy StudentProfile."""
    slr: StudentLearningRecord
    mastery: Dict[str, MasteryState] = field(default_factory=dict)
    misconceptions: List[Misconception] = field(default_factory=list)
    recent_events: List[LearningEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "slr": self.slr.to_dict(),
            "mastery": {k: asdict(v) for k, v in self.mastery.items()},
            "misconceptions": [asdict(m) for m in self.misconceptions],
            "recent_events": [asdict(e) for e in self.recent_events]
        }


class LearningStateManager:
    """Authoritative state manager consolidating all student state interactions."""
    
    def __init__(self, db: PlatformDatabase):
        self.db = db
        # In-memory fast cache for live sessions
        self._active_sessions: Dict[str, SessionRuntimeState] = {}

    def get_canonical_state(self, student_id: str, course_id: str) -> CanonicalLearningState:
        """Fetch the unified persistent state for a student."""
        # 1. Fetch SLR
        slr = self.db.get_slr(student_id, course_id)
        if not slr:
            slr_id = f"slr_{uuid.uuid4().hex[:8]}"
            slr = StudentLearningRecord(id=slr_id, student_id=student_id, course_id=course_id)
            self.db.create_slr(slr)
            
        # 2. Fetch Mastery
        mastery_list = self.db.get_mastery_states_for_slr(slr.id)
        mastery_dict = {m.concept_id: m for m in mastery_list}
        
        # 3. Fetch Misconceptions (currently all unresolved for this SLR)
        # Note: DB might not have get_unresolved_misconceptions_for_slr, so we'll mock or add it
        misconceptions = [] # self.db.get_misconceptions(slr.id)
        
        # 4. Fetch Events
        events = [] # To be implemented via specific query
        
        return CanonicalLearningState(
            slr=slr,
            mastery=mastery_dict,
            misconceptions=misconceptions,
            recent_events=events
        )

    def update_mastery(self, student_id: str, course_id: str, concept_id: str, score: float, confidence: float = 0.8) -> MasteryState:
        """Idempotently update mastery in the canonical store."""
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
                last_practiced_at=now
            )
            self.db.upsert_mastery_state(ms)
            
        return ms

    def initialize_session(self, student_id: str, course_id: str, concept_id: str) -> SessionRuntimeState:
        """Start a new learning session and return its runtime state."""
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        sess = Session(
            id=session_id,
            student_id=student_id,
            course_id=course_id,
            concept_id=concept_id,
            status=SessionStatus.ACTIVE
        )
        self.db.create_session(sess)
        
        runtime = SessionRuntimeState(
            session_id=session_id,
            student_id=student_id,
            course_id=course_id,
            concept_id=concept_id
        )
        self._active_sessions[session_id] = runtime
        return runtime

    def get_session_runtime(self, session_id: str) -> Optional[SessionRuntimeState]:
        """Fetch active runtime state."""
        return self._active_sessions.get(session_id)

    def log_event(self, session_id: str, event_type: str, data: Dict[str, Any]) -> LearningEvent:
        """Log an immutable learning event attached to a session."""
        sess = self.db.get_session(session_id)
        if not sess:
            raise ValueError(f"Session {session_id} not found.")
            
        event = LearningEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            student_id=sess.student_id,
            course_id=sess.course_id,
            concept_id=sess.concept_id,
            event_type=event_type,
            payload=data
        )
        self.db.record_learning_event(event)
        return event

    def end_session(self, session_id: str) -> None:
        """End a session and flush runtime state."""
        self.db.end_session(session_id)
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
