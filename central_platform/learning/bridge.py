"""Authoritative Learning Engine Bridge (Phase 07).

Master Plan Section 16:
Connects existing working learning intelligence (BKT, mastery, LDG, difficulty,
misconceptions, spaced review, concept selection, adaptive engine) to the
central learning event store and Authoritative Student Learning Record (SLR).

Canonical Pipeline:
student action
→ learning event
→ learning engine
→ updated mastery
→ SLR
→ recommendation
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.learning.models import EngineActionResult, StudentActionPayload
from central_platform.models.schema import Course, Session, SessionStatus, User, UserRole
from central_platform.slr.models import AuthoritativeSLR
from central_platform.slr.service import SLRService

# Existing Core Learning & Tutor Intelligence
from core.learning.mastery import MasteryCalculator
from core.learning.misconceptions import (
    ALL_MISCONCEPTIONS,
    MisconceptionTracker,
    get_remediation_guidance,
)
from core.learning.policy import DifficultyPolicy
from core.learning.scheduler import SpacedReviewScheduler
from core.learning.selector import DEFAULT_PREREQUISITES_MAP, ConceptSelector
from core.tutor.adaptive import AdaptiveLearningEngine, StudentProfile
from core.tutor.state import LearningEvent as CoreLearningEvent, StudentConceptMastery


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class _StateManagerAdapter:
    """Adapter allowing ConceptSelector and legacy tools to query central database state."""

    def __init__(self, db: PlatformDatabase, slr: AuthoritativeSLR):
        self.db = db
        self.slr = slr
        self.conn = getattr(db, "_conn", None)

    def get_student_concept_mastery(self, student_id: str, concept_id: str) -> StudentConceptMastery:
        score = self.slr.mastery.concept_scores.get(concept_id, 0.50)
        confidence = self.slr.mastery.concept_confidences.get(concept_id, 0.80)
        return StudentConceptMastery(
            student_id=student_id,
            concept_id=concept_id,
            mastery=score,
            confidence=confidence,
            exposure_count=1,
            next_review_at="",
            difficulty_level=3.0,
        )


class LearningEngineBridge:
    """Bridges core learning intelligence with central event store and authoritative SLR."""

    def __init__(
        self,
        db: Optional[PlatformDatabase] = None,
        event_store: Optional[LearningEventStore] = None,
        slr_service: Optional[SLRService] = None,
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
        self.slr_service = (
            slr_service
            if slr_service is not None
            else SLRService(db=self.db, event_store=self.event_store)
        )

        # Preserved Learning Intelligence components
        self.mastery_calculator = MasteryCalculator()
        self.difficulty_policy = DifficultyPolicy()
        self.spaced_review_scheduler = SpacedReviewScheduler()
        self.concept_selector = ConceptSelector()

    def _ensure_session(
        self,
        student_id: str,
        course_id: str,
        concept_id: str,
        session_id: Optional[str] = None,
    ) -> str:
        """Resolve active session or create a new session for student activity."""
        self.slr_service._ensure_student_scaffolding(student_id, course_id)
        if session_id:
            existing = self.db.get_session(session_id)
            if existing:
                return existing.id

        sessions = self.db.get_sessions_for_student(student_id, limit=5)
        for s in sessions:
            if s.course_id == course_id and s.status == SessionStatus.ACTIVE:
                return s.id

        new_sess_id = f"sess-{uuid.uuid4().hex[:12]}"
        self.db.create_session(
            Session(
                id=new_sess_id,
                student_id=student_id,
                course_id=course_id,
                concept_id=concept_id,
                status=SessionStatus.ACTIVE,
            )
        )
        return new_sess_id


    def process_student_action(
        self,
        student_id: str,
        action: StudentActionPayload,
        course_id: Optional[str] = None,
    ) -> EngineActionResult:
        """Execute the canonical Master Plan Section 16 learning pipeline:
        student action
        → learning event
        → learning engine
        → updated mastery
        → SLR
        → recommendation
        """
        target_course = course_id or action.course_id or "crs-chem-101"
        concept_id = action.concept_id

        # 1. Misconception Detection & Catalog Mapping
        misc_code = action.misconception_code
        if not misc_code and action.correctness == "incorrect" and action.student_answer:
            misc_code = MisconceptionTracker.identify_misconception_from_error(
                concept_id=concept_id,
                student_answer=action.student_answer,
            )

        misconception_info: Optional[Dict[str, Any]] = None
        if misc_code:
            guidance = get_remediation_guidance(misc_code)
            desc = ALL_MISCONCEPTIONS.get(misc_code, f"Misconception {misc_code}")
            misconception_info = {
                "code": misc_code,
                "name": misc_code.replace("_", " ").title(),
                "description": desc,
                "guidance": guidance,
            }

        # 2. Convert to Central Learning Event & Ingest
        session_id = self._ensure_session(
            student_id=student_id,
            course_id=target_course,
            concept_id=concept_id,
            session_id=action.session_id,
        )

        event_type = LearningEventType.ANSWER_SUBMITTED.value
        if action.action_type == "hint_requested":
            event_type = LearningEventType.HINT_REQUESTED.value
        elif action.action_type == "misconception_exhibited" or (misc_code and action.correctness == "incorrect"):
            event_type = LearningEventType.MISCONCEPTION_DETECTED.value
        elif action.action_type in ("concept_reviewed", "concept_introduced"):
            event_type = LearningEventType.CONCEPT_INTRODUCED.value
        elif action.correctness is not None:
            event_type = LearningEventType.ANSWER_SUBMITTED.value

        score = action.score
        if score is None:
            if action.correctness == "correct":
                score = 1.0
            elif action.correctness == "partially_correct":
                score = 0.5
            elif action.correctness == "incorrect":
                score = 0.0

        event_id = str(uuid.uuid4())
        ingest_req = LearningEventIngest(
            event_id=event_id,
            student_id=student_id,
            course_id=target_course,
            session_id=session_id,
            concept_id=concept_id,
            event_type=event_type,
            score=score,
            payload={
                "correctness": action.correctness or "correct",
                "question_id": action.question_id or "",
                "student_answer": action.student_answer or "",
                "hint_level": action.hint_level,
                "hint_used": action.hint_level,
                "difficulty": action.difficulty or 3.0,
                "response_time_ms": action.response_time_ms or 0.0,
                "misconception_code": misc_code or "",
                **(action.metadata or {}),
            },
        )
        stored_event, _ = self.event_store.ingest_event(ingest_req)

        # 3. Retrieve Current SLR State & Form Core Learning Events
        current_slr = self.slr_service.get_authoritative_slr(student_id, target_course)
        prev_mastery = current_slr.mastery.concept_scores.get(concept_id, 0.50)

        # Gather history for this concept from event store
        raw_events = self.event_store.get_student_events(student_id, target_course, limit=100)
        core_events: List[CoreLearningEvent] = []
        for ev in raw_events:
            if ev.concept_id == concept_id or not core_events:
                p = ev.payload or {}
                core_events.append(
                    CoreLearningEvent(
                        event_id=ev.id,
                        student_id=ev.student_id,
                        session_id=ev.session_id,
                        turn_id=p.get("turn_id", ev.id),
                        concept_id=ev.concept_id or concept_id,
                        question_id=p.get("question_id", ""),
                        timestamp=ev.created_at,
                        difficulty=float(p.get("difficulty", 3.0)),
                        correctness=str(p.get("correctness", "correct")).lower(),
                        confidence=float(ev.score if ev.score is not None else 0.8),
                        hint_used=int(p.get("hint_used", p.get("hint_level", 0))),
                        response_time=float(p.get("response_time_ms", 0.0)) / 1000.0,
                        misconception_code=p.get("misconception_code", ""),
                        source="central_bridge",
                    )
                )

        # 4. Learning Engine Processing:
        # 4a. BKT / Mastery Delta Calculation
        db_miscs = self.db.get_student_misconceptions(student_id)
        is_repeated = any(m.misconception_code == misc_code and m.frequency >= 2 for m in db_miscs) if misc_code else False

        if action.correctness:
            delta = AdaptiveLearningEngine.evaluate_mastery_delta(
                result=action.correctness,
                hint_level=action.hint_level,
                is_repeated_misconception=is_repeated,
            )
        elif action.action_type == "hint_requested":
            delta = -0.01
        else:
            delta = 0.0

        new_mastery = max(0.0, min(1.0, round(prev_mastery + delta, 4)))

        # When evidence pool grows, blend with multi-factor evidence calculation
        if len(core_events) >= 5:
            mf_score = self.mastery_calculator.compute_mastery(core_events)
            new_mastery = max(0.0, min(1.0, round(0.6 * new_mastery + 0.4 * mf_score, 4)))

        # 4b. Difficulty Policy Progression
        curr_diff = int(round(action.difficulty)) if action.difficulty else 3
        curr_diff = max(1, min(5, curr_diff))
        diff_decision = self.difficulty_policy.evaluate_next_difficulty(
            events=core_events,
            current_difficulty=curr_diff,
        )
        new_difficulty = diff_decision.new_difficulty
        difficulty_label = diff_decision.difficulty_label

        # 4c. Spaced Review Scheduling
        corr_str = action.correctness or "correct"
        interval_days, next_review_at = self.spaced_review_scheduler.calculate_next_review(
            current_interval_days=1,
            correctness=corr_str,
            hint_used=action.hint_level,
        )

        # 4d. Adaptive Pedagogical Decision
        prereqs = DEFAULT_PREREQUISITES_MAP.get(concept_id, [])
        prereq_masteries = {p: current_slr.mastery.concept_scores.get(p, 0.50) for p in prereqs}

        student_profile = StudentProfile(
            student_id=student_id,
            mastery={**current_slr.mastery.concept_scores, concept_id: new_mastery},
            misconceptions=[m.code for m in current_slr.misconceptions],
        )

        pedagogical_decision = AdaptiveLearningEngine.decide_next_action(
            concept_id=concept_id,
            student=student_profile,
            prerequisites=prereqs,
            prereq_masteries=prereq_masteries,
        )

        pedagogical_action = pedagogical_decision["action"]
        recommended_mode = pedagogical_decision.get("recommended_mode", "QUESTION")
        target_concept = pedagogical_decision.get("target_concept", concept_id)
        pedagogical_reason = pedagogical_decision.get("reason", "")

        # 4e. LDG Concept Candidate Selection & Ranking
        adapter = _StateManagerAdapter(self.db, current_slr)
        candidate_ids = list(dict.fromkeys([concept_id, *prereqs, target_concept, "chem_thermo_first_law", "chem_thermo_enthalpy"]))
        candidate_rankings: List[Dict[str, Any]] = []
        try:
            selection_res = self.concept_selector.select_next_concept(
                student_id=student_id,
                candidate_concept_ids=candidate_ids,
                state_manager=adapter,  # type: ignore
            )
            candidate_rankings = selection_res.candidate_rankings
        except Exception:
            candidate_rankings = []

        # 5. Persist to Central Platform & Update Authoritative SLR
        # Update concept mastery in central DB
        self.slr_service.update_concept_mastery(
            student_id=student_id,
            concept_id=concept_id,
            score=new_mastery,
            course_id=target_course,
        )

        # Record misconception if detected
        if misc_code:
            self.slr_service.record_student_misconception(
                student_id=student_id,
                misconception_code=misc_code,
                course_id=target_course,
            )

        # Fetch authoritative updated SLR
        updated_slr = self.slr_service.get_authoritative_slr(student_id, target_course)

        # 6. Construct and Return Canonical Result
        return EngineActionResult(
            event_id=event_id,
            student_id=student_id,
            concept_id=concept_id,
            course_id=target_course,
            mastery_score=new_mastery,
            mastery_delta=delta,
            difficulty_level=new_difficulty,
            difficulty_label=difficulty_label,
            next_review_at=next_review_at,
            pedagogical_action=pedagogical_action,
            target_concept=target_concept,
            pedagogical_reason=pedagogical_reason,
            recommended_mode=recommended_mode,
            misconception=misconception_info,
            candidate_concepts=candidate_rankings,
            slr=updated_slr,
            recommendations=updated_slr.recommendations,
            alerts=updated_slr.alerts,
            timestamp=_now_iso(),
        )
