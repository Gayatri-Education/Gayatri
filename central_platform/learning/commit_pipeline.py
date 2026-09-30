"""State Commit Pipeline for Phase 20.

Guarantees transactional state integrity:
- Learning state changes (mastery, misconceptions, learning events) are staged in a buffer.
- Response / evaluation results are validated via ResponseValidatorEngine.
- Only if validation PASSES are state changes committed atomically to the database.
- Failed or invalid AI requests cannot corrupt persistent database state.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from central_platform.ai.response_validator import ResponseValidatorEngine, ValidationResult
from central_platform.db import PlatformDatabase
from central_platform.models.schema import LearningEvent, MasteryState, StudentMisconceptionRecord

logger = logging.getLogger("gayatri.commit_pipeline")


@dataclass
class StagedStateChanges:
    """In-memory buffer of proposed learning state mutations."""
    student_id: str
    course_id: str
    mastery_updates: List[MasteryState] = field(default_factory=list)
    misconception_records: List[StudentMisconceptionRecord] = field(default_factory=list)
    learning_events: List[LearningEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not (self.mastery_updates or self.misconception_records or self.learning_events)


@dataclass
class CommitResult:
    """Result of state commit operation."""
    committed: bool
    reason: str
    staged_summary: Dict[str, int]
    validation_result: Optional[ValidationResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "committed": self.committed,
            "reason": self.reason,
            "staged_summary": self.staged_summary,
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
        }


class StateCommitPipeline:
    """Authoritative Two-Phase State Commit Pipeline."""

    def __init__(self, db: PlatformDatabase):
        self.db = db
        self.validator = ResponseValidatorEngine()

    def stage_changes(
        self,
        student_id: str,
        course_id: str,
        mastery_updates: Optional[List[MasteryState]] = None,
        misconception_records: Optional[List[StudentMisconceptionRecord]] = None,
        learning_events: Optional[List[LearningEvent]] = None,
    ) -> StagedStateChanges:
        """Create an isolated in-memory buffer of proposed state mutations."""
        return StagedStateChanges(
            student_id=student_id,
            course_id=course_id,
            mastery_updates=mastery_updates or [],
            misconception_records=misconception_records or [],
            learning_events=learning_events or [],
        )

    def validate_and_commit(
        self,
        staged: StagedStateChanges,
        generated_response: str,
        target_concept: Optional[str] = None,
        rag_sources_required: bool = False,
    ) -> CommitResult:
        """Validate AI response and atomically commit staged changes only if validation passes."""
        summary = {
            "mastery_updates": len(staged.mastery_updates),
            "misconception_records": len(staged.misconception_records),
            "learning_events": len(staged.learning_events),
        }

        # 1. Validate generated AI response using ResponseValidatorEngine
        val_result = self.validator.validate_response(
            generated_response=generated_response,
            target_concept=target_concept,
            rag_sources_required=rag_sources_required,
        )

        # 2. Rejection Guard: If validation fails, DO NOT COMMIT to database
        if not val_result.is_valid:
            logger.warning(
                f"State commit ABORTED for student {staged.student_id}: AI response failed validation ({len(val_result.issues)} issues)."
            )
            return CommitResult(
                committed=False,
                reason="AI response failed validation. State changes rolled back.",
                staged_summary=summary,
                validation_result=val_result,
            )

        # 3. Transactional Commit to Database
        try:
            # Commit mastery updates
            for ms in staged.mastery_updates:
                self.db.upsert_mastery_state(ms)

            # Commit misconception records
            for sm in staged.misconception_records:
                self.db.record_student_misconception(sm)

            # Commit learning events
            for ev in staged.learning_events:
                self.db.record_learning_event(ev)

            logger.info(f"State commit SUCCESSFUL for student {staged.student_id}: {summary}")
            return CommitResult(
                committed=True,
                reason="Validation passed. All staged state changes committed successfully.",
                staged_summary=summary,
                validation_result=val_result,
            )
        except Exception as exc:
            logger.error(f"Database commit failed during state persistence: {exc}")
            return CommitResult(
                committed=False,
                reason=f"Database commit error: {exc}",
                staged_summary=summary,
                validation_result=val_result,
            )
