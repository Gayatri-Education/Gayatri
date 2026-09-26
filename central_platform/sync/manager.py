"""Offline event sync queue, device binding, and idempotency manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SyncEvent:
    event_id: str
    student_id: str
    device_id: str
    event_type: str
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence_num: int = 1


class SyncManager:
    """Manages local event queueing, idempotency checking, and server sync reconciliation."""

    def __init__(self):
        self._processed_event_ids: set[str] = set()
        self._local_queue: list[SyncEvent] = []
        self._device_bindings: dict[str, str] = {}  # device_id -> student_id

    def bind_device(self, device_id: str, student_id: str) -> None:
        self._device_bindings[device_id] = student_id

    def get_bound_student(self, device_id: str) -> Optional[str]:
        return self._device_bindings.get(device_id)

    def queue_offline_event(self, event: SyncEvent) -> bool:
        """Add event to local queue if device is authorized and event is not a duplicate."""
        if self.get_bound_student(event.device_id) != event.student_id:
            raise PermissionError("Device is not bound to the specified student.")
        if event.event_id in self._processed_event_ids or any(e.event_id == event.event_id for e in self._local_queue):
            # Still track event in local queue to report as duplicate during sync
            self._local_queue.append(event)
            return False
        self._local_queue.append(event)
        return True

    def process_sync(self) -> dict[str, int]:
        """Process queued offline events idempotently."""
        synced_count = 0
        duplicate_count = 0
        
        pending = list(self._local_queue)
        self._local_queue.clear()

        for event in pending:
            if event.event_id in self._processed_event_ids:
                duplicate_count += 1
                continue
            # Mark event as processed cleanly
            self._processed_event_ids.add(event.event_id)
            synced_count += 1

        return {"synced": synced_count, "duplicates": duplicate_count}
