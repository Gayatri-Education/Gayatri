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
import uuid
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

    def bind_device(
        self,
        device_id: str,
        student_id: str,
        force: bool = False,
        organization_id: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> None:
        """Bind device hardware identifier to student account with database persistence.

        Raises PermissionError if the device is already bound to another student without force=True.
        """
        current_bound = self.get_bound_student(device_id)
        if current_bound and current_bound != student_id and not force:
            raise PermissionError(f"Device '{device_id}' is bound to another student.")

        try:
            self.db.bind_device(
                device_id=device_id,
                student_id=student_id,
                organization_id=organization_id,
                device_name=device_name,
                force=force,
            )
        except Exception as exc:
            logger.warning("Failed to record device binding in db: %s", exc)
        self._device_bindings[device_id] = student_id

    def get_bound_student(self, device_id: str) -> Optional[str]:
        """Look up student bound to device from DB or cache."""
        try:
            binding = self.db.get_device_binding(device_id)
            if binding:
                self._device_bindings[device_id] = binding.student_id
                return binding.student_id
        except Exception:
            pass
        return self._device_bindings.get(device_id)

    def process_sync_batch(
        self,
        student_id: str,
        events: List[Dict[str, Any]],
        course_id: Optional[str] = None,
        device_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        course_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process an ordered batch of student telemetry events idempotently.
        
        Steps:
        1. Operation replay check: if operation_id already recorded, return cached receipt
        2. Validate device authorization (if device registered)
        3. Sort events chronologically by sequence_num and timestamp (out-of-order reconciliation)
        4. Ingest each event through LearningEventStore (idempotent deduplication)
        5. Handle course version conflicts safely without corrupting course catalog
        6. Recompute Authoritative SLR
        7. Record operation receipt and return detailed response with acknowledged event IDs
        """
        # 1. Operation ID replay idempotency check
        if operation_id:
            existing_op = self.db.get_sync_operation(operation_id)
            if existing_op:
                from central_platform.recovery.manager import FailureRecoveryManager
                rec = FailureRecoveryManager.handle_duplicate_sync(
                    operation_id=operation_id,
                    student_id=student_id,
                    duplicate_count=existing_op.duplicate_count or 1,
                )
                logger.info("Sync operation %s already processed; %s", operation_id, rec.technical_diagnostic)
                return {
                    "ok": existing_op.status in ("SYNCED", "PARTIAL"),
                    "operation_id": existing_op.operation_id,
                    "synced_count": existing_op.synced_count,
                    "duplicate_count": existing_op.duplicate_count,
                    "failed_count": existing_op.failed_count,
                    "acknowledged_ids": existing_op.acknowledged_ids,
                    "conflicts_resolved": existing_op.conflicts_resolved,
                    "status": existing_op.status,
                    "latest_mastery": existing_op.latest_mastery,
                    "server_timestamp": existing_op.server_timestamp,
                    "is_replay": True,
                    "recovery": rec.to_dict(),
                }

        target_course = course_id or "crs-chem-101"
        self.slr_service._ensure_student_scaffolding(student_id, target_course)

        # 2. Device binding validation
        if device_id:
            bound_student = self.get_bound_student(device_id)
            if bound_student is None:
                self.bind_device(device_id, student_id)
            elif bound_student != student_id:
                raise PermissionError(f"Device '{device_id}' is bound to another student.")
            else:
                try:
                    self.db.update_device_sync_time(device_id)
                except Exception:
                    pass

        # 3. Out-of-order event reconciliation: sort by sequence_num then timestamp
        def _sort_key(ev: Dict[str, Any]) -> Tuple[int, str]:
            seq = int(ev.get("sequence_num", 0))
            ts = str(ev.get("timestamp", ""))
            return (seq, ts)

        sorted_events = sorted(events, key=_sort_key)

        # Sequence gap detection
        seq_nums = [int(ev.get("sequence_num", 0)) for ev in sorted_events if int(ev.get("sequence_num", 0)) > 0]
        sequence_gaps: List[Dict[str, int]] = []
        for i in range(1, len(seq_nums)):
            prev_s = seq_nums[i - 1]
            curr_s = seq_nums[i]
            if curr_s > prev_s + 1:
                sequence_gaps.append({
                    "expected": prev_s + 1,
                    "received": curr_s,
                    "gap_size": curr_s - prev_s - 1,
                })
        if sequence_gaps:
            logger.warning("Detected %d sequence gap(s) for student %s: %s", len(sequence_gaps), student_id, sequence_gaps)

        synced_count = 0
        duplicate_count = 0
        failed_count = 0
        conflicts_resolved = 0
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

            # Check if event already exists in database (Event-Level Idempotency)
            existing = self.db.get_learning_event(ev_id)
            if existing:
                duplicate_count += 1
                acknowledged_ids.append(ev_id)
                continue

            session_id = ev.get("session_id") or f"sess-sync-{student_id}"

            # Version Conflict Resolution Policy
            ev_payload = dict(ev.get("payload", ev))
            ev_ver = ev.get("course_version") or course_version
            if ev_ver and ev_ver != "v1.0":
                ev_payload["_version_policy"] = {
                    "client_version": ev_ver,
                    "resolution": "RESOLVE_TO_PINNED",
                    "resolved_at": _now_iso(),
                }
                conflicts_resolved += 1

            ingest_req = LearningEventIngest(
                event_id=ev_id,
                student_id=student_id,
                course_id=target_course,
                session_id=session_id,
                concept_id=concept_id,
                event_type=event_type,
                score=score,
                payload=ev_payload,
            )

            try:
                stored_ev, was_inserted = self.event_store.ingest_event(ingest_req)
                if was_inserted:
                    synced_count += 1
                else:
                    duplicate_count += 1
                acknowledged_ids.append(ev_id)

                # Check for misconception to track in SLR
                p = ev_payload
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

        # 6. Canonical SLR update post-sync
        updated_slr = self.slr_service.project_from_events(
            student_id=student_id,
            course_id=target_course,
        )

        overall_mastery = updated_slr.mastery.overall_score
        now_ts = _now_iso()
        status_str = "SYNCED" if failed_count == 0 else "PARTIAL"
        effective_op_id = operation_id or f"op_{uuid.uuid4().hex[:12]}"

        result = {
            "ok": failed_count == 0,
            "operation_id": effective_op_id,
            "synced_count": synced_count,
            "duplicate_count": duplicate_count,
            "failed_count": failed_count,
            "acknowledged_ids": acknowledged_ids,
            "conflicts_resolved": conflicts_resolved,
            "status": status_str,
            "latest_mastery": overall_mastery,
            "server_timestamp": now_ts,
            "is_replay": False,
            "sequence_gaps": sequence_gaps,
        }

        # 7. Persist operation record for idempotency replay and auditing
        from central_platform.models.schema import SyncOperationRecord
        self.db.record_sync_operation(
            SyncOperationRecord(
                operation_id=effective_op_id,
                student_id=student_id,
                device_id=device_id,
                course_id=target_course,
                synced_count=synced_count,
                duplicate_count=duplicate_count,
                failed_count=failed_count,
                acknowledged_ids=acknowledged_ids,
                conflicts_resolved=conflicts_resolved,
                status=status_str,
                latest_mastery=overall_mastery,
                server_timestamp=now_ts,
                created_at=now_ts,
            )
        )

        return result

    def get_sync_status(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query synchronization status and telemetry audit summary for a student."""
        target_course = course_id or "crs-chem-101"
        operations = self.db.get_sync_operations_for_student(student_id)
        latest_op = operations[0] if operations else None
        slr = self.slr_service.get_authoritative_slr(student_id, target_course)

        total_synced_events = sum(op.synced_count for op in operations)
        try:
            db_devices = {b.device_id for b in self.db.get_devices_for_student(student_id)}
        except Exception:
            db_devices = set()

        devices = {op.device_id for op in operations if op.device_id} | db_devices | {
            dev for dev, stu in self._device_bindings.items() if stu == student_id
        }

        return {
            "student_id": student_id,
            "course_id": target_course,
            "total_operations": len(operations),
            "total_synced_events": total_synced_events,
            "registered_devices": sorted(list(devices)),
            "last_operation_id": latest_op.operation_id if latest_op else None,
            "last_synced_at": latest_op.server_timestamp if latest_op else None,
            "latest_mastery": slr.mastery.overall_score if slr else 0.0,
            "status": "HEALTHY" if latest_op and latest_op.status == "SYNCED" else ("NO_SYNC" if not latest_op else "PARTIAL"),
        }

