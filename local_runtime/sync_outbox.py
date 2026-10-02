"""Local Sync Outbox subsystem.

Provides durable, crash-resilient disk-backed queueing of learning events
with operation-level batching, exponential backoff retries, and receipt tracking.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("gayatri.local_runtime.sync_outbox")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class OutboxItem:
    event_id: str
    student_id: str
    course_id: str
    device_id: str
    event_type: str
    concept_id: str
    payload: Dict[str, Any]
    sequence_num: int
    status: str  # PENDING, IN_FLIGHT, ACKNOWLEDGED, FAILED
    operation_id: Optional[str]
    retry_count: int
    last_error: str
    next_retry_at: Optional[str]
    created_at: str
    updated_at: str

    def to_event_payload(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "concept_id": self.concept_id,
            "sequence_num": self.sequence_num,
            "payload": self.payload,
            "timestamp": self.created_at,
        }


class LocalSyncOutbox:
    """Manages transactional disk-buffered outbound synchronization events."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.recover_in_flight()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS local_sync_outbox (
                    event_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    concept_id TEXT DEFAULT '',
                    payload_json TEXT NOT NULL,
                    sequence_num INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    operation_id TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT DEFAULT '',
                    next_retry_at TEXT,
                    next_retry_ts REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_outbox_status_seq
                ON local_sync_outbox (status, sequence_num, created_at);
                """
            )
            conn.commit()

    def recover_in_flight(self) -> int:
        """Reset any in-flight items to PENDING on application startup."""
        now = _now_iso()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE local_sync_outbox
                SET status = 'PENDING', operation_id = NULL, updated_at = ?
                WHERE status = 'IN_FLIGHT';
                """,
                (now,)
            )
            count = cursor.rowcount
            conn.commit()
            if count > 0:
                logger.info("Recovered %d in-flight outbox items on startup.", count)
            return count

    def enqueue(
        self,
        student_id: str,
        course_id: str,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        concept_id: str = "",
        sequence_num: Optional[int] = None,
        device_id: Optional[str] = None,
    ) -> bool:
        """Add an event to the local sync outbox idempotently."""
        now = _now_iso()
        dev_id = device_id or f"dev_{student_id}"

        with self._get_connection() as conn:
            if sequence_num is None:
                row = conn.execute(
                    "SELECT COALESCE(MAX(sequence_num), 0) + 1 AS next_seq FROM local_sync_outbox WHERE student_id = ?",
                    (student_id,)
                ).fetchone()
                sequence_num = row["next_seq"] if row else 1

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO local_sync_outbox (
                    event_id, student_id, course_id, device_id, event_type,
                    concept_id, payload_json, sequence_num, status,
                    retry_count, last_error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, '', ?, ?)
                """,
                (
                    event_id, student_id, course_id, dev_id, event_type,
                    concept_id, json.dumps(payload), sequence_num, now, now
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_pending_batch(
        self,
        limit: int = 50,
        operation_id: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Fetch pending outbox items and transition them to IN_FLIGHT under an operation_id."""
        op_id = operation_id or f"op_{uuid.uuid4().hex[:12]}"
        now = _now_iso()
        now_ts = time.time()

        with self._get_connection() as conn:
            # Query eligible items
            rows = conn.execute(
                """
                SELECT * FROM local_sync_outbox
                WHERE status IN ('PENDING', 'FAILED')
                  AND (next_retry_ts IS NULL OR next_retry_ts <= ?)
                ORDER BY sequence_num ASC, created_at ASC
                LIMIT ?
                """,
                (now_ts, limit)
            ).fetchall()

            if not rows:
                return op_id, []

            event_ids = [r["event_id"] for r in rows]
            placeholders = ",".join("?" for _ in event_ids)

            conn.execute(
                f"""
                UPDATE local_sync_outbox
                SET status = 'IN_FLIGHT', operation_id = ?, updated_at = ?
                WHERE event_id IN ({placeholders})
                """,
                (op_id, now, *event_ids)
            )
            conn.commit()

            events = []
            for r in rows:
                try:
                    payload = json.loads(r["payload_json"])
                except Exception:
                    payload = {}
                events.append({
                    "event_id": r["event_id"],
                    "student_id": r["student_id"],
                    "course_id": r["course_id"],
                    "device_id": r["device_id"],
                    "event_type": r["event_type"],
                    "concept_id": r["concept_id"],
                    "sequence_num": r["sequence_num"],
                    "payload": payload,
                    "timestamp": r["created_at"],
                })

            return op_id, events

    def mark_acknowledged(self, operation_id: str, acknowledged_ids: List[str]) -> int:
        """Safely remove confirmed events from the outbox."""
        if not acknowledged_ids:
            return 0
        placeholders = ",".join("?" for _ in acknowledged_ids)
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM local_sync_outbox WHERE event_id IN ({placeholders})",
                acknowledged_ids
            )
            count = cursor.rowcount
            conn.commit()
            return count

    def mark_failed(
        self,
        operation_id: str,
        error_message: str,
        backoff_base_sec: float = 1.0,
    ) -> None:
        """Mark items failed and set exponential backoff retry timestamp."""
        now_ts = time.time()
        now_str = _now_iso()

        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT event_id, retry_count FROM local_sync_outbox WHERE operation_id = ?",
                (operation_id,)
            ).fetchall()

            for r in rows:
                retries = r["retry_count"] + 1
                delay = backoff_base_sec * (2 ** min(retries, 6))
                next_ts = now_ts + delay
                next_retry_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(next_ts))

                conn.execute(
                    """
                    UPDATE local_sync_outbox
                    SET status = 'FAILED', retry_count = ?, last_error = ?,
                        next_retry_at = ?, next_retry_ts = ?, updated_at = ?
                    WHERE event_id = ?
                    """,
                    (retries, error_message, next_retry_str, next_ts, now_str, r["event_id"])
                )
            conn.commit()

    def count_pending(self) -> int:
        """Return total unacknowledged events in outbox."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM local_sync_outbox WHERE status IN ('PENDING', 'FAILED', 'IN_FLIGHT')"
            ).fetchone()
            return row["cnt"] if row else 0

    def get_outbox_status(self) -> Dict[str, int]:
        """Return breakdown of outbox states."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS cnt FROM local_sync_outbox GROUP BY status").fetchall()
            counts = {r["status"]: r["cnt"] for r in rows}
            return {
                "pending": counts.get("PENDING", 0),
                "in_flight": counts.get("IN_FLIGHT", 0),
                "failed": counts.get("FAILED", 0),
                "total": sum(counts.values()),
            }
