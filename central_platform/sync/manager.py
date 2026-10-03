"""Offline event sync queue, device binding, and idempotency manager (Phase 08 Remediation).

Provides durable SQLite persistence across process restarts for:
- Device hardware binding and student authorization
- Processed event idempotency ledger (UNIQUE event_id)
- Local sync queue with sequence ordering and crash recovery
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger("gayatri.sync.manager")


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
    """Manages local event queueing, idempotency checking, and server sync reconciliation.

    Backed by durable SQLite persistence so state survives application restarts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("GAYATRI_SYNC_MANAGER_DB", ":memory:")
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

        # In-memory caches synchronized with durable SQLite storage
        self._processed_event_ids: Set[str] = set()
        self._local_queue: List[SyncEvent] = []
        self._device_bindings: Dict[str, str] = {}
        self._reload_caches()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_device_bindings (
                    device_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    bound_at TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_processed_events (
                    event_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_event_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sequence_num INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    server_acknowledged INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sync_queue_event_id
                ON sync_event_queue (event_id);
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status_seq
                ON sync_event_queue (status, sequence_num, created_at);
                """
            )

    def _reload_caches(self) -> None:
        """Reload in-memory caches from SQLite tables to survive process restarts."""
        cursor = self._conn.cursor()

        # 1. Device bindings
        cursor.execute("SELECT device_id, student_id FROM sync_device_bindings;")
        self._device_bindings = {row["device_id"]: row["student_id"] for row in cursor.fetchall()}

        # 2. Processed event IDs
        cursor.execute("SELECT event_id FROM sync_processed_events;")
        self._processed_event_ids = {row["event_id"] for row in cursor.fetchall()}

        # 3. Local queue (PENDING or PENDING_DUPLICATE events)
        cursor.execute(
            """
            SELECT event_id, student_id, device_id, event_type, payload_json, timestamp, sequence_num
            FROM sync_event_queue
            WHERE status IN ('PENDING', 'PENDING_DUPLICATE')
            ORDER BY sequence_num ASC, id ASC;
            """
        )
        self._local_queue = []
        for r in cursor.fetchall():
            try:
                p = json.loads(r["payload_json"])
            except Exception:
                p = {}
            self._local_queue.append(
                SyncEvent(
                    event_id=r["event_id"],
                    student_id=r["student_id"],
                    device_id=r["device_id"],
                    event_type=r["event_type"],
                    payload=p,
                    timestamp=r["timestamp"],
                    sequence_num=r["sequence_num"],
                )
            )

    def bind_device(self, device_id: str, student_id: str, force: bool = False) -> None:
        """Bind device hardware identifier to student account.

        Raises PermissionError if the device is already bound to a different student,
        unless force=True is explicitly specified.
        """
        current_bound = self.get_bound_student(device_id)
        if current_bound and current_bound != student_id and not force:
            raise PermissionError(
                f"Device '{device_id}' is already bound to another student ('{current_bound}')."
            )

        now_ts = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO sync_device_bindings (device_id, student_id, bound_at)
                VALUES (?, ?, ?);
                """,
                (device_id, student_id, now_ts),
            )
        self._device_bindings[device_id] = student_id

    def get_bound_student(self, device_id: str) -> Optional[str]:
        """Look up student bound to device."""
        if device_id in self._device_bindings:
            return self._device_bindings[device_id]
        cursor = self._conn.execute(
            "SELECT student_id FROM sync_device_bindings WHERE device_id = ?;", (device_id,)
        )
        row = cursor.fetchone()
        if row:
            self._device_bindings[device_id] = row[0]
            return row[0]
        return None

    def record_event(self, event: SyncEvent) -> bool:
        """Record an incoming event on the central platform. Idempotent based on event_id.

        Enforces device ownership security:
        Rejects event if the device is registered to another student.
        """
        bound_student = self.get_bound_student(event.device_id)
        if not bound_student:
            self.bind_device(event.device_id, event.student_id)
        elif bound_student != event.student_id:
            raise PermissionError(
                f"Device '{event.device_id}' is bound to another student ('{bound_student}')."
            )

        if event.event_id in self._processed_event_ids:
            return False

        now_ts = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(event.payload) if isinstance(event.payload, dict) else str(event.payload)

        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO sync_processed_events (event_id, processed_at) VALUES (?, ?);",
                (event.event_id, now_ts),
            )
            self._conn.execute(
                """
                INSERT INTO sync_event_queue (
                    event_id, student_id, device_id, event_type, payload_json,
                    timestamp, sequence_num, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'RECORDED', ?);
                """,
                (
                    event.event_id,
                    event.student_id,
                    event.device_id,
                    event.event_type,
                    payload_str,
                    event.timestamp,
                    event.sequence_num,
                    now_ts,
                ),
            )

        self._processed_event_ids.add(event.event_id)
        self._local_queue.append(event)
        return True

    def queue_offline_event(self, event: SyncEvent) -> bool:
        """Add event to local queue if device is authorized and event is not a duplicate.

        Guarantees:
        - Rejects event if device is not bound to specified student.
        - Persists event to SQLite table so it survives application crash.
        """
        if self.get_bound_student(event.device_id) != event.student_id:
            raise PermissionError("Device is not bound to the specified student.")

        is_duplicate = (
            event.event_id in self._processed_event_ids
            or any(e.event_id == event.event_id for e in self._local_queue)
        )

        now_ts = datetime.now(timezone.utc).isoformat()
        status = "PENDING_DUPLICATE" if is_duplicate else "PENDING"
        payload_str = json.dumps(event.payload) if isinstance(event.payload, dict) else str(event.payload)

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO sync_event_queue (
                    event_id, student_id, device_id, event_type, payload_json,
                    timestamp, sequence_num, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event.event_id,
                    event.student_id,
                    event.device_id,
                    event.event_type,
                    payload_str,
                    event.timestamp,
                    event.sequence_num,
                    status,
                    now_ts,
                ),
            )

        self._local_queue.append(event)
        return not is_duplicate

    def process_sync(self) -> dict[str, int]:
        """Process queued offline events idempotently.

        Marks events as SYNCED in the persistent table and records them in processed_events.
        """
        synced_count = 0
        duplicate_count = 0

        pending = list(self._local_queue)
        self._local_queue.clear()
        now_ts = datetime.now(timezone.utc).isoformat()

        with self._conn:
            for event in pending:
                if event.event_id in self._processed_event_ids:
                    duplicate_count += 1
                    self._conn.execute(
                        """
                        UPDATE sync_event_queue
                        SET status = 'DUPLICATE'
                        WHERE event_id = ? AND status IN ('PENDING', 'PENDING_DUPLICATE');
                        """,
                        (event.event_id,),
                    )
                    continue

                self._processed_event_ids.add(event.event_id)
                self._conn.execute(
                    "INSERT OR IGNORE INTO sync_processed_events (event_id, processed_at) VALUES (?, ?);",
                    (event.event_id, now_ts),
                )
                self._conn.execute(
                    """
                    UPDATE sync_event_queue
                    SET status = 'SYNCED', server_acknowledged = 1
                    WHERE event_id = ? AND status IN ('PENDING', 'PENDING_DUPLICATE');
                    """,
                    (event.event_id,),
                )
                synced_count += 1

        return {"synced": synced_count, "duplicates": duplicate_count}

    def is_event_processed(self, event_id: str) -> bool:
        """Check if an event ID has already been authoritatively processed."""
        if event_id in self._processed_event_ids:
            return True
        cursor = self._conn.execute(
            "SELECT 1 FROM sync_processed_events WHERE event_id = ?;", (event_id,)
        )
        return cursor.fetchone() is not None

    def get_queued_events(self) -> List[SyncEvent]:
        """Return all currently queued pending events."""
        return list(self._local_queue)

    def close(self) -> None:
        """Close SQLite database connection."""
        try:
            self._conn.close()
        except Exception:
            pass
