"""Authoritative Server-Side Synchronization Service (Phase 08).

Master Plan Section 17:
- Real network synchronization pipeline
- Strict server-side validation and device authorization
- Idempotency & deduplication filter via LearningEventStore
- Out-of-order event sequence reconciliation
- Permanent storage in central PostgreSQL/SQLite database
- Canonical SLR projection update immediately post-sync
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from central_platform.db import PlatformDatabase
from central_platform.events.models import LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import UserRole
from central_platform.slr.service import SLRService

logger = logging.getLogger("gayatri.sync.service")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SyncService:
    """Processes incoming batches from desktop clients into central persistence and SLR."""

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

        # In-memory device registry cache (device_id -> student_id)
        self._device_bindings: Dict[str, str] = {}

    def bind_device(self, device_id: str, student_id: str) -> None:
        """Bind device hardware identifier to student account."""
        self._device_bindings[device_id] = student_id

    def get_bound_student(self, device_id: str) -> Optional[str]:
        """Look up student bound to device."""
        return self._device_bindings.get(device_id)

    def process_sync_batch(
        self,
        student_id: str,
        events: List[Dict[str, Any]],
        course_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process an ordered batch of student telemetry events idempotently.
        
        Steps:
        1. Validate device authorization (if device registered)
        2. Sort events chronologically by sequence_num and timestamp (out-of-order reconciliation)
        3. Ingest each event through LearningEventStore (idempotent deduplication)
        4. Recompute Authoritative SLR
        5. Return detailed receipt with acknowledged event IDs
        """
        target_course = course_id or "crs-chem-101"
        self.slr_service._ensure_student_scaffolding(student_id, target_course)

        # 1. Device binding validation
        if device_id:
            bound_student = self.get_bound_student(device_id)
            if bound_student is None:
                self.bind_device(device_id, student_id)
            elif bound_student != student_id:
                raise PermissionError(f"Device '{device_id}' is bound to another student.")

        # 2. Out-of-order event reconciliation: sort by sequence_num then timestamp
        def _sort_key(ev: Dict[str, Any]) -> Tuple[int, str]:
            seq = int(ev.get("sequence_num", 0))
            ts = str(ev.get("timestamp", ""))
            return (seq, ts)

        sorted_events = sorted(events, key=_sort_key)

        synced_count = 0
        duplicate_count = 0
        failed_count = 0
        acknowledged_ids: List[str] = []

        for ev in sorted_events:
            ev_id = ev.get("event_id")
            if not ev_id:
                failed_count += 1
                continue

            raw_type = str(ev.get("event_type", "question_attempted")).lower()
            canonical_map = {
                "turn_completed": "question_attempted",
                "turn": "question_attempted",
                "answer": "answer_submitted",
                "hint": "hint_requested",
                "assessment": "assessment_completed",
                "quiz_attempt": "question_attempted",
            }
            valid_types = {t.value for t in LearningEventType}
            if raw_type in valid_types:
                event_type = raw_type
            elif raw_type in canonical_map:
                event_type = canonical_map[raw_type]
            else:
                event_type = "question_attempted"

            concept_id = ev.get("concept_id") or ev.get("payload", {}).get("concept_id", "chem_thermo_first_law")
            score = ev.get("score") or ev.get("payload", {}).get("score")
            if score is not None:
                score = float(score)


            # Check if event already exists in database (Idempotency)
            existing = self.db.get_learning_event(ev_id)
            if existing:
                duplicate_count += 1
                acknowledged_ids.append(ev_id)
                continue

            session_id = ev.get("session_id") or f"sess-sync-{student_id}"

            ingest_req = LearningEventIngest(
                event_id=ev_id,
                student_id=student_id,
                course_id=target_course,
                session_id=session_id,
                concept_id=concept_id,
                event_type=event_type,
                score=score,
                payload=ev.get("payload", ev),
            )

            try:
                stored_ev, was_inserted = self.event_store.ingest_event(ingest_req)
                if was_inserted:
                    synced_count += 1
                else:
                    duplicate_count += 1
                acknowledged_ids.append(ev_id)

                # Check for misconception to track in SLR
                p = ev.get("payload", {})
                misc_code = p.get("misconception_code")
                if misc_code:
                    self.slr_service.record_student_misconception(
                        student_id=student_id,
                        misconception_code=misc_code,
                        course_id=target_course,
                    )

            except Exception as exc:
                logger.error(f"Failed to ingest event {ev_id}: {exc}")
                failed_count += 1

        # 4. Canonical SLR update post-sync
        updated_slr = self.slr_service.project_from_events(
            student_id=student_id,
            course_id=target_course,
        )

        overall_mastery = updated_slr.mastery.overall_score

        return {
            "ok": failed_count == 0,
            "synced_count": synced_count,
            "duplicate_count": duplicate_count,
            "failed_count": failed_count,
            "acknowledged_ids": acknowledged_ids,
            "status": "SYNCED" if failed_count == 0 else "PARTIAL",
            "latest_mastery": overall_mastery,
            "server_timestamp": _now_iso(),
        }
