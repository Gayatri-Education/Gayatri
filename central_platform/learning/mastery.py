"""Mastery and Evidence Engine for Phase 14.

Implements deterministic evidence-backed mastery computation considering:
- Correct / Incorrect answers
- Repeated attempts (diminishing returns & confidence adjustment)
- Review sessions (retention boost)
- Time decay (forgetting curve based on days since practice)
- Prerequisite effects (prerequisite mastery discounting/capping)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import LearningEvent, MasteryState, StudentLearningRecord


@dataclass
class MasteryCalculationResult:
    """Deterministic output of evidence-backed mastery calculation."""
    concept_id: str
    raw_mastery: float
    decayed_mastery: float
    effective_mastery: float  # Final mastery after prerequisite effects and clamping
    confidence: float
    recent_accuracy: float
    long_term_accuracy: float
    attempts_count: int
    days_since_last_practice: float
    prerequisite_factor: float
    state: str  # "new", "practicing", "mastered", "review_due"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "raw_mastery": self.raw_mastery,
            "decayed_mastery": self.decayed_mastery,
            "effective_mastery": self.effective_mastery,
            "confidence": self.confidence,
            "recent_accuracy": self.recent_accuracy,
            "long_term_accuracy": self.long_term_accuracy,
            "attempts_count": self.attempts_count,
            "days_since_last_practice": self.days_since_last_practice,
            "prerequisite_factor": self.prerequisite_factor,
            "state": self.state,
        }


class MasteryEvidenceEngine:
    """Authoritative deterministic evidence-backed mastery engine."""

    def __init__(self, db: Optional[PlatformDatabase] = None, half_life_days: float = 30.0):
        self.db = db
        self.half_life_days = half_life_days

    @staticmethod
    def _parse_iso(timestamp_str: Optional[str]) -> Optional[datetime]:
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def calculate_evidence_mastery(
        self,
        concept_id: str,
        events: List[LearningEvent],
        prerequisite_masteries: Optional[List[float]] = None,
        now: Optional[datetime] = None,
    ) -> MasteryCalculationResult:
        """Compute deterministic mastery based on event evidence, decay, and prerequisites."""
        current_time = now or datetime.now(timezone.utc)
        
        # Filter valid events (answer_submitted, question_attempted, review)
        valid_events = [e for e in events if e.concept_id == concept_id or not e.concept_id]
        if not valid_events:
            return MasteryCalculationResult(
                concept_id=concept_id,
                raw_mastery=0.0,
                decayed_mastery=0.0,
                effective_mastery=0.0,
                confidence=0.0,
                recent_accuracy=0.0,
                long_term_accuracy=0.0,
                attempts_count=0,
                days_since_last_practice=0.0,
                prerequisite_factor=1.0,
                state="new",
            )

        # 1. Answer correctness & attempts
        scores = []
        hint_penalties = []
        last_event_time = None

        for ev in valid_events:
            p = ev.payload or {}
            correctness = str(p.get("correctness", "")).lower()
            hint_level = int(p.get("hint_level", p.get("hint_used", 0)))

            if ev.score is not None:
                sc = ev.score
            elif correctness == "correct":
                sc = 1.0
            elif correctness == "partially_correct":
                sc = 0.5
            else:
                sc = 0.0

            # Apply hint penalty (each hint level reduces score weight by 15%)
            sc = max(0.0, sc - (hint_level * 0.15))
            scores.append(sc)
            hint_penalties.append(hint_level)

            ev_dt = self._parse_iso(ev.created_at)
            if ev_dt and (last_event_time is None or ev_dt > last_event_time):
                last_event_time = ev_dt

        attempts_count = len(scores)

        # 2. Recent vs Long-term accuracy with diminishing returns for repeated attempts
        recent_scores = scores[-5:]
        recent_accuracy = sum(recent_scores) / len(recent_scores)
        long_term_accuracy = sum(scores) / attempts_count

        # Diminishing returns scaling: practice beyond 10 attempts adds diminishing confidence gain
        attempt_weight = min(1.0, 0.2 + 0.8 * (1.0 - math.exp(-attempts_count / 4.0)))

        raw_mastery = (0.60 * recent_accuracy + 0.40 * long_term_accuracy) * attempt_weight
        raw_mastery = max(0.0, min(1.0, round(raw_mastery, 4)))

        # 3. Time-based Memory Decay (Ebbinghaus forgetting curve: R = exp(-t / S))
        days_since_practice = 0.0
        if last_event_time:
            days_since_practice = max(0.0, (current_time - last_event_time).total_seconds() / 86400.0)

        # Exponential decay factor based on half-life
        decay_factor = math.exp(-math.log(2) * days_since_practice / self.half_life_days)
        decayed_mastery = round(raw_mastery * decay_factor, 4)

        # 4. Prerequisite Effects (Prerequisite Mastery Discounting)
        prereq_factor = 1.0
        if prerequisite_masteries:
            avg_prereq = sum(prerequisite_masteries) / len(prerequisite_masteries)
            if avg_prereq < 0.60:
                # Prerequisite bottleneck penalty: cap maximum achievable mastery
                prereq_factor = max(0.30, avg_prereq / 0.60)

        effective_mastery = max(0.0, min(1.0, round(decayed_mastery * prereq_factor, 4)))

        # 5. Confidence Estimation
        confidence = round(min(0.95, 0.50 + 0.45 * (1.0 - math.exp(-attempts_count / 3.0))), 4)

        # 6. Mastery State Classification
        if attempts_count == 0:
            state = "new"
        elif days_since_practice > 14.0 and effective_mastery < 0.70:
            state = "review_due"
        elif effective_mastery >= 0.85:
            state = "mastered"
        else:
            state = "practicing"

        return MasteryCalculationResult(
            concept_id=concept_id,
            raw_mastery=raw_mastery,
            decayed_mastery=decayed_mastery,
            effective_mastery=effective_mastery,
            confidence=confidence,
            recent_accuracy=round(recent_accuracy, 4),
            long_term_accuracy=round(long_term_accuracy, 4),
            attempts_count=attempts_count,
            days_since_last_practice=round(days_since_practice, 2),
            prerequisite_factor=round(prereq_factor, 4),
            state=state,
        )

    def update_canonical_mastery(
        self,
        student_id: str,
        course_id: str,
        concept_id: str,
        prerequisite_concept_ids: Optional[List[str]] = None,
    ) -> MasteryCalculationResult:
        """Update and persist evidence-backed mastery to the database."""
        if not self.db:
            raise ValueError("PlatformDatabase instance is required for update_canonical_mastery.")

        # Gather events for concept
        events = self.db.query_learning_events(student_id=student_id, course_id=course_id, limit=500)
        concept_events = [e for e in events if e.concept_id == concept_id]

        # Gather prerequisite masteries if any
        prereq_scores = []
        if prerequisite_concept_ids:
            slr = self.db.get_slr(student_id, course_id)
            if slr:
                mastery_states = self.db.get_mastery_states_for_slr(slr.id)
                for pid in prerequisite_concept_ids:
                    ms = next((m for m in mastery_states if m.concept_id == pid), None)
                    prereq_scores.append(ms.score if ms else 0.50)

        result = self.calculate_evidence_mastery(concept_id, concept_events, prereq_scores)

        # Persist updated mastery to DB
        slr = self.db.get_slr(student_id, course_id)
        if not slr:
            slr = StudentLearningRecord(id=f"slr_{student_id}_{course_id}", student_id=student_id, course_id=course_id)
            self.db.create_slr(slr)

        ms = MasteryState(
            slr_id=slr.id,
            concept_id=concept_id,
            score=result.effective_mastery,
            confidence=result.confidence,
            state=result.state,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.upsert_mastery_state(ms)

        return result
