"""Gayatri AI Platform — Resilience & Failure Recovery Manager (Phase 23 & Phase 38).

Provides automated fallback policies, degraded execution modes, and self-healing
recovery handlers with strict contracts:
1. classification (failure_category)
2. observable status (status)
3. safe user message (user_message)
4. technical diagnostic (technical_diagnostic)
5. retryability (retryable)
6. rollback/commit decision (commit_decision)

Covering 12 failure domains:
- Missing model / local model unavailable
- Corrupt model weights/checksum
- Provider API timeout
- Provider malformed response / output repair
- RAG retrieval failure / unavailable
- Database unavailable / connection dropped
- Broken migration / schema rollback
- Broken upload / buffer purge
- Interrupted publish / draft revert
- Expired instruction / context pruning
- Duplicate sync / idempotent receipt
- App crash mid-turn / state rollback
- Payment gateway transaction failure
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.central_platform.recovery")


class FailureCategory(str, Enum):
    # Phase 23 Core Categories
    MISSING_MODEL = "missing_model"
    CORRUPT_MODEL = "corrupt_model"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_MALFORMED = "provider_malformed"
    RAG_UNAVAILABLE = "rag_unavailable"
    DATABASE_UNAVAILABLE = "database_unavailable"
    BROKEN_MIGRATION = "broken_migration"
    BROKEN_UPLOAD = "broken_upload"
    INTERRUPTED_PUBLISH = "interrupted_publish"
    EXPIRED_INSTRUCTION = "expired_instruction"
    DUPLICATE_SYNC = "duplicate_sync"
    APP_CRASH_MID_TURN = "app_crash_mid_turn"

    # Pre-existing / Subsystem Categories
    MODEL_UNAVAILABLE = "model_unavailable"
    RAG_FAILURE = "rag_failure"
    DATABASE_FAILURE = "database_failure"
    MALFORMED_MODEL_OUTPUT = "malformed_model_output"
    NETWORK_FAILURE = "network_failure"
    INTERRUPTED_TRANSACTION = "interrupted_transaction"
    INVALID_CURRICULUM = "invalid_curriculum"
    PAYMENT_FAILURE = "payment_failure"


class RecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    DEGRADED_FALLBACK = "degraded_fallback"
    UNRECOVERABLE = "unrecoverable"


class CommitDecision(str, Enum):
    COMMIT = "commit"
    ROLLBACK = "rollback"
    NOOP = "noop"
    RETRY = "retry"


@dataclass
class RecoveryResult:
    """Standardized response from failure recovery execution.
    
    Adheres strictly to Phase 23 Section 12.23 specifications:
    - classification (failure_category)
    - observable status (status)
    - safe user message (user_message)
    - technical diagnostic (technical_diagnostic)
    - retryability (retryable)
    - rollback/commit decision (commit_decision)
    """
    failure_category: FailureCategory
    status: RecoveryStatus
    fallback_used: str
    message: str
    user_message: str = ""
    technical_diagnostic: str = ""
    retryable: bool = False
    commit_decision: CommitDecision = CommitDecision.NOOP
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.user_message:
            self.user_message = self.message
        if not self.technical_diagnostic:
            self.technical_diagnostic = str(
                self.data.get("original_error") or self.data.get("error") or self.message
            )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["failure_category"] = (
            self.failure_category.value
            if hasattr(self.failure_category, "value")
            else str(self.failure_category)
        )
        d["status"] = (
            self.status.value
            if hasattr(self.status, "value")
            else str(self.status)
        )
        d["commit_decision"] = (
            self.commit_decision.value
            if hasattr(self.commit_decision, "value")
            else str(self.commit_decision)
        )
        return d


class FailureRecoveryManager:
    """Authoritative Failure Recovery & Degraded Execution Handler."""

    @classmethod
    def handle_model_failure(
        cls,
        error: Exception,
        is_corrupt: bool = False,
        is_missing: bool = False,
        model_name: Optional[str] = None,
    ) -> RecoveryResult:
        """Handle missing or corrupted AI models."""
        fallback_model = "Qwen2.5-0.5B-Instruct-GGUF"
        if is_corrupt:
            category = FailureCategory.CORRUPT_MODEL
            msg = f"Primary model integrity check failed ({error}). Switched to verified fallback engine."
            user_msg = "The primary AI model file is damaged. Switched to offline backup engine."
            tech_diag = f"Corrupt model weights/checksum for '{model_name or 'primary'}': {error}"
            retryable = False
            decision = CommitDecision.ROLLBACK
        elif is_missing:
            category = FailureCategory.MISSING_MODEL
            msg = f"Primary model not found ({error}). Falling back to local SLM {fallback_model}."
            user_msg = "The requested AI model is temporarily unavailable. Continuing in standard offline mode."
            tech_diag = f"Missing model file '{model_name or 'primary'}': {error}"
            retryable = True
            decision = CommitDecision.NOOP
        else:
            category = FailureCategory.MODEL_UNAVAILABLE
            msg = f"Primary model execution failed ({error}). Falling back to lightweight local SLM {fallback_model}."
            user_msg = "Primary AI model execution failed. Switched to local SLM backup."
            tech_diag = f"Execution failed on '{model_name or 'primary'}': {error}"
            retryable = True
            decision = CommitDecision.NOOP

        return RecoveryResult(
            failure_category=category,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used=fallback_model,
            message=msg,
            user_message=user_msg,
            technical_diagnostic=tech_diag,
            retryable=retryable,
            commit_decision=decision,
            data={"active_model": fallback_model, "original_error": str(error), "model_name": model_name or "primary"},
        )

    @classmethod
    def handle_provider_timeout(
        cls,
        error: Exception,
        max_retries: int = 3,
        provider: str = "cloud",
    ) -> RecoveryResult:
        """Handle provider API timeout after retry exhaustion."""
        msg = f"Provider API timeout after {max_retries} retries ({error}). Switched to local offline router."
        return RecoveryResult(
            failure_category=FailureCategory.PROVIDER_TIMEOUT,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="LocalFirstRouter",
            message=msg,
            user_message="The cloud provider is taking longer than expected. Continuing with local offline tutor.",
            technical_diagnostic=f"Timeout connecting to {provider} after {max_retries} retries: {error}",
            retryable=True,
            commit_decision=CommitDecision.NOOP,
            data={"mode": "LOCAL_ONLY", "error": str(error), "provider": provider, "retries": max_retries},
        )

    @classmethod
    def handle_rag_failure(
        cls,
        error: Exception,
        fallback_concept: str = "General Knowledge",
        course_id: Optional[str] = None,
    ) -> RecoveryResult:
        """Handle vector index/RAG retrieval failure by degrading to syllabus context."""
        msg = f"RAG vector retrieval failed ({error}). Falling back to structured curriculum context for '{fallback_concept}'."
        return RecoveryResult(
            failure_category=FailureCategory.RAG_FAILURE,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="CurriculumDirectContext",
            message=msg,
            user_message="Reference materials are temporarily unreachable; continuing using course syllabus.",
            technical_diagnostic=f"RAG retrieval error for course '{course_id or 'unknown'}' on concept '{fallback_concept}': {error}",
            retryable=True,
            commit_decision=CommitDecision.NOOP,
            data={"concept": fallback_concept, "course_id": course_id, "rag_active": False, "error": str(error)},
        )

    @classmethod
    def handle_database_failure(
        cls,
        error: Exception,
        cached_state: Optional[Dict[str, Any]] = None,
        operation: str = "query",
    ) -> RecoveryResult:
        """Handle database query/write failure with read-only in-memory snapshot."""
        msg = f"Database query failed ({error}). Using read-only in-memory state snapshot."
        data_dict = {"read_only": True, "operation": operation, "error": str(error)}
        if cached_state:
            data_dict.update(cached_state)
        return RecoveryResult(
            failure_category=FailureCategory.DATABASE_FAILURE,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="InMemorySnapshotCache",
            message=msg,
            user_message="Database is temporarily busy; using cached session data in read-only mode.",
            technical_diagnostic=f"Database {operation} failed: {error}",
            retryable=True,
            commit_decision=CommitDecision.ROLLBACK,
            data=data_dict,
        )

    @classmethod
    def handle_broken_migration(
        cls,
        error: Exception,
        migration_version: str = "unknown",
        script_name: str = "",
    ) -> RecoveryResult:
        """Handle migration failure by rolling back schema to pre-migration baseline."""
        msg = f"Database migration {migration_version} failed ({error}). Rolled back to previous verified schema."
        return RecoveryResult(
            failure_category=FailureCategory.BROKEN_MIGRATION,
            status=RecoveryStatus.UNRECOVERABLE,
            fallback_used="SchemaRollback",
            message=msg,
            user_message="Database update was interrupted. System schema was safely preserved without data loss.",
            technical_diagnostic=f"Migration error in script '{script_name}' (version {migration_version}): {error}",
            retryable=False,
            commit_decision=CommitDecision.ROLLBACK,
            data={"migration_version": migration_version, "script_name": script_name, "error": str(error)},
        )

    @classmethod
    def handle_broken_upload(
        cls,
        error: Exception,
        filename: str = "",
        partial_bytes: int = 0,
    ) -> RecoveryResult:
        """Handle interrupted or damaged file uploads by purging partial buffers."""
        msg = f"Upload of '{filename}' failed ({error}). Discarded partial buffer ({partial_bytes} bytes)."
        return RecoveryResult(
            failure_category=FailureCategory.BROKEN_UPLOAD,
            status=RecoveryStatus.UNRECOVERABLE,
            fallback_used="UploadBufferPurge",
            message=msg,
            user_message="File upload was interrupted. Partial data was cleaned up; please try uploading again.",
            technical_diagnostic=f"Upload stream failure on '{filename}' at {partial_bytes} bytes: {error}",
            retryable=True,
            commit_decision=CommitDecision.ROLLBACK,
            data={"filename": filename, "partial_bytes": partial_bytes, "error": str(error)},
        )

    @classmethod
    def handle_interrupted_publish(
        cls,
        error: Exception,
        version_id: str = "",
        course_id: str = "",
        pre_status: str = "DRAFT",
    ) -> RecoveryResult:
        """Handle interrupted course publishing by preserving pre-publish draft state."""
        msg = f"Publishing course version '{version_id}' interrupted ({error}). Reverted to status '{pre_status}'."
        return RecoveryResult(
            failure_category=FailureCategory.INTERRUPTED_PUBLISH,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="RevertToDraft",
            message=msg,
            user_message="Course publishing could not be completed. The version has been preserved in its previous state.",
            technical_diagnostic=f"Publishing transaction for version '{version_id}' of course '{course_id}' aborted: {error}",
            retryable=True,
            commit_decision=CommitDecision.ROLLBACK,
            data={"version_id": version_id, "course_id": course_id, "reverted_status": pre_status, "error": str(error)},
        )

    @classmethod
    def handle_expired_instruction(
        cls,
        instruction_id: str,
        course_id: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> RecoveryResult:
        """Handle expired teacher instruction by pruning it from active tutoring context."""
        msg = f"Teacher instruction '{instruction_id}' expired at {expires_at or 'past'}. Omitted from context."
        return RecoveryResult(
            failure_category=FailureCategory.EXPIRED_INSTRUCTION,
            status=RecoveryStatus.RECOVERED,
            fallback_used="InstructionPruning",
            message=msg,
            user_message="An expired teaching guideline was safely excluded from the active tutoring turn.",
            technical_diagnostic=f"Instruction {instruction_id} exceeded expiration timestamp ({expires_at}); marked EXPIRED and excluded.",
            retryable=False,
            commit_decision=CommitDecision.NOOP,
            data={"instruction_id": instruction_id, "course_id": course_id, "expires_at": expires_at},
        )

    @classmethod
    def handle_duplicate_sync(
        cls,
        operation_id: str,
        student_id: str = "",
        duplicate_count: int = 1,
    ) -> RecoveryResult:
        """Handle duplicate sync batch by returning idempotent cached receipt."""
        msg = f"Duplicate sync operation '{operation_id}' received. Returned cached idempotency receipt."
        return RecoveryResult(
            failure_category=FailureCategory.DUPLICATE_SYNC,
            status=RecoveryStatus.RECOVERED,
            fallback_used="IdempotentReceiptCache",
            message=msg,
            user_message="Your offline progress was already synchronized. Returning confirmed receipt.",
            technical_diagnostic=f"Sync batch operation_id='{operation_id}' already executed; duplicate_count={duplicate_count}.",
            retryable=False,
            commit_decision=CommitDecision.NOOP,
            data={"operation_id": operation_id, "student_id": student_id, "duplicate_count": duplicate_count, "is_replay": True},
        )

    @classmethod
    def handle_crash_mid_turn(
        cls,
        error: Exception,
        turn_id: str = "",
        student_id: str = "",
        step: str = "EXECUTION",
    ) -> RecoveryResult:
        """Handle unexpected mid-turn crash by discarding staged state and redirecting gracefully."""
        msg = f"Turn '{turn_id}' encountered unexpected crash at step '{step}' ({error}). Staged state discarded."
        return RecoveryResult(
            failure_category=FailureCategory.APP_CRASH_MID_TURN,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="StateRollbackAndPedagogicalRedirect",
            message=msg,
            user_message="An unexpected interruption occurred during the tutoring turn. Your learning progress was safely preserved.",
            technical_diagnostic=f"Unhandled exception during turn '{turn_id}' (student='{student_id}') at step '{step}': {error}",
            retryable=True,
            commit_decision=CommitDecision.ROLLBACK,
            data={"turn_id": turn_id, "student_id": student_id, "step": step, "error": str(error)},
        )

    @classmethod
    def repair_malformed_model_output(cls, raw_text: str) -> RecoveryResult:
        """Self-healing JSON repair for malformed LLM outputs."""
        if not raw_text or not raw_text.strip():
            return RecoveryResult(
                failure_category=FailureCategory.MALFORMED_MODEL_OUTPUT,
                status=RecoveryStatus.DEGRADED_FALLBACK,
                fallback_used="DefaultJsonPayload",
                message="Empty output received. Supplied default fallback schema.",
                user_message="Empty model response received; provided default pedagogical payload.",
                technical_diagnostic="Empty string received from LLM.",
                retryable=True,
                commit_decision=CommitDecision.ROLLBACK,
                data={"explanation": raw_text or ""},
            )

        # 1. Direct parse
        try:
            parsed = json.loads(raw_text)
            return RecoveryResult(
                failure_category=FailureCategory.MALFORMED_MODEL_OUTPUT,
                status=RecoveryStatus.RECOVERED,
                fallback_used="DirectParse",
                message="Output is valid JSON.",
                user_message="Output formatted as valid JSON.",
                technical_diagnostic="JSON parsed cleanly on direct parse pass.",
                retryable=False,
                commit_decision=CommitDecision.COMMIT,
                data=parsed if isinstance(parsed, dict) else {"content": parsed},
            )
        except json.JSONDecodeError:
            pass

        # 2. Extract JSON block inside markdown code fences
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            candidate = match.group(1)
            candidate_clean = re.sub(r",\s*([\}\]])", r"\1", candidate)
            try:
                parsed = json.loads(candidate_clean)
                return RecoveryResult(
                    failure_category=FailureCategory.MALFORMED_MODEL_OUTPUT,
                    status=RecoveryStatus.RECOVERED,
                    fallback_used="MarkdownFenceExtractor",
                    message="Extracted and repaired JSON from markdown fences.",
                    user_message="Formatted response recovered from markdown code fence.",
                    technical_diagnostic="Extracted JSON block from markdown fence; trailing commas stripped.",
                    retryable=False,
                    commit_decision=CommitDecision.COMMIT,
                    data=parsed if isinstance(parsed, dict) else {"content": parsed},
                )
            except json.JSONDecodeError:
                pass

        # 3. Extract balanced pair of curly braces
        match_brace = re.search(r"(\{.*?\})", raw_text, re.DOTALL)
        if match_brace:
            candidate = match_brace.group(1)
            candidate_clean = re.sub(r",\s*([\}\]])", r"\1", candidate)
            try:
                parsed = json.loads(candidate_clean)
                return RecoveryResult(
                    failure_category=FailureCategory.MALFORMED_MODEL_OUTPUT,
                    status=RecoveryStatus.RECOVERED,
                    fallback_used="BraceRegexExtractor",
                    message="Extracted JSON via brace regex matching.",
                    user_message="Formatted response recovered via regex extraction.",
                    technical_diagnostic="Extracted balanced curly braces via regex; repaired trailing commas.",
                    retryable=False,
                    commit_decision=CommitDecision.COMMIT,
                    data=parsed if isinstance(parsed, dict) else {"content": parsed},
                )
            except json.JSONDecodeError:
                pass

        # 4. Fallback text wrapper
        return RecoveryResult(
            failure_category=FailureCategory.MALFORMED_MODEL_OUTPUT,
            status=RecoveryStatus.DEGRADED_FALLBACK,
            fallback_used="PlainTextWrapper",
            message="Unrepairable JSON output. Wrapped raw text as plain string content.",
            user_message="Response could not be parsed as structured JSON; wrapped raw text safely.",
            technical_diagnostic=f"Unrepairable JSON syntax: {raw_text[:120]}...",
            retryable=False,
            commit_decision=CommitDecision.ROLLBACK,
            data={"text": raw_text.strip()},
        )

    @classmethod
    def handle_payment_failure(cls, error: Exception, transaction_id: str) -> RecoveryResult:
        msg = f"Payment gateway transaction '{transaction_id}' failed ({error}). Rolled back ledger state."
        return RecoveryResult(
            failure_category=FailureCategory.PAYMENT_FAILURE,
            status=RecoveryStatus.RECOVERED,
            fallback_used="LedgerRollback",
            message=msg,
            user_message="Payment could not be processed. No funds were deducted, and the transaction was safely cancelled.",
            technical_diagnostic=f"Payment transaction '{transaction_id}' error: {error}",
            retryable=True,
            commit_decision=CommitDecision.ROLLBACK,
            data={"transaction_id": transaction_id, "status": "failed_rolled_back", "error": str(error)},
        )
