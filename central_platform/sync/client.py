"""Persistent Desktop Local Event Queue & Sync Client (Phase 08).

Master Plan Section 17:
- Disk-backed persistent SQLite queue for offline/online event buffering
- Guarantees zero data loss across application restarts or power failures
- Automatic retry with exponential backoff on network failures
- Automatic JWT token expiry detection and token refresh recovery
- Strictly ensures: No learning event may silently disappear.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from central_platform.sync.manager import SyncEvent

logger = logging.getLogger("gayatri.sync.client")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueueItem:
    event_id: str
    student_id: str
    device_id: str
    event_type: str
    concept_id: str
    payload: Dict[str, Any]
    sequence_num: int
    status: str  # PENDING, SYNCING, ACKNOWLEDGED, FAILED
    created_at: str
    retry_count: int = 0
    last_error: str = ""

    def to_sync_event(self) -> SyncEvent:
        return SyncEvent(
            event_id=self.event_id,
            student_id=self.student_id,
            device_id=self.device_id,
            event_type=self.event_type,
            payload={**self.payload, "concept_id": self.concept_id},
            timestamp=self.created_at,
            sequence_num=self.sequence_num,
        )


class PersistentSyncQueue:
    """Disk-persisted SQLite event queue on the student desktop client."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS local_sync_queue (
                    event_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    concept_id TEXT DEFAULT '',
                    payload TEXT NOT NULL,
                    sequence_num INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT DEFAULT ''
                );
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status_seq
                ON local_sync_queue (status, sequence_num, created_at);
            """)

    def enqueue(
        self,
        event_id: str,
        student_id: str,
        device_id: str,
        event_type: str,
        payload: Dict[str, Any],
        concept_id: str = "",
        sequence_num: Optional[int] = None,
    ) -> bool:
        """Enqueue a learning event atomically to persistent storage."""
        if sequence_num is None:
            cursor = self.conn.execute(
                "SELECT COALESCE(MAX(sequence_num), 0) + 1 AS next_seq FROM local_sync_queue WHERE student_id = ?",
                (student_id,),
            )
            row = cursor.fetchone()
            sequence_num = row["next_seq"] if row else 1

        payload_json = json.dumps(payload)
        now = _now_iso()

        with self.conn:
            # Idempotent insert: ignore if event_id already in local queue
            cursor = self.conn.execute(
                """
                INSERT OR IGNORE INTO local_sync_queue (
                    event_id, student_id, device_id, event_type, concept_id,
                    payload, sequence_num, status, created_at, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, 0)
                """,
                (event_id, student_id, device_id, event_type, concept_id, payload_json, sequence_num, now),
            )
            return cursor.rowcount > 0

    def enqueue_event(self, event: SyncEvent, concept_id: str = "") -> bool:
        """Convenience method to enqueue a SyncEvent dataclass."""
        c_id = concept_id or event.payload.get("concept_id", "")
        return self.enqueue(
            event_id=event.event_id,
            student_id=event.student_id,
            device_id=event.device_id,
            event_type=event.event_type,
            payload=event.payload,
            concept_id=c_id,
            sequence_num=event.sequence_num,
        )

    def get_pending_batch(self, limit: int = 50) -> List[QueueItem]:
        """Fetch pending items ordered by sequence_num and creation timestamp."""
        cursor = self.conn.execute(
            """
            SELECT * FROM local_sync_queue
            WHERE status IN ('PENDING', 'FAILED')
            ORDER BY sequence_num ASC, created_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        items = []
        for row in cursor.fetchall():
            items.append(
                QueueItem(
                    event_id=row["event_id"],
                    student_id=row["student_id"],
                    device_id=row["device_id"],
                    event_type=row["event_type"],
                    concept_id=row["concept_id"],
                    payload=json.loads(row["payload"]),
                    sequence_num=row["sequence_num"],
                    status=row["status"],
                    created_at=row["created_at"],
                    retry_count=row["retry_count"],
                    last_error=row["last_error"],
                )
            )
        return items

    def mark_acknowledged(self, event_ids: List[str]) -> int:
        """Mark events acknowledged by platform server, removing them safely."""
        if not event_ids:
            return 0
        placeholders = ",".join("?" for _ in event_ids)
        with self.conn:
            cursor = self.conn.execute(
                f"DELETE FROM local_sync_queue WHERE event_id IN ({placeholders})",
                event_ids,
            )
            return cursor.rowcount

    def mark_failed(self, event_ids: List[str], error_message: str) -> None:
        """Increment retry count and record error on transmission failure."""
        if not event_ids:
            return
        placeholders = ",".join("?" for _ in event_ids)
        with self.conn:
            self.conn.execute(
                f"""
                UPDATE local_sync_queue
                SET status = 'FAILED',
                    retry_count = retry_count + 1,
                    last_error = ?
                WHERE event_id IN ({placeholders})
                """,
                [error_message, *event_ids],
            )

    def count_pending(self) -> int:
        """Return total un-synced events currently buffered."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM local_sync_queue WHERE status IN ('PENDING', 'FAILED')"
        )
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def count_all(self) -> int:
        """Return total events in table."""
        cursor = self.conn.execute("SELECT COUNT(*) AS cnt FROM local_sync_queue")
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


@dataclass
class SyncResult:
    success: bool
    synced_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    remaining_pending: int = 0
    error: Optional[str] = None
    retried_token_refresh: bool = False


class DesktopSyncClient:
    """Desktop sync agent that coordinates network uploads with the persistent queue."""

    def __init__(
        self,
        queue: PersistentSyncQueue,
        student_id: str,
        device_id: str,
        http_client: Any = None,  # requests, httpx, or TestClient
        api_base_url: str = "/api/v1",
        auth_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_refresher: Optional[Callable[[str], Optional[Tuple[str, str]]]] = None,
    ):
        self.queue = queue
        self.student_id = student_id
        self.device_id = device_id
        self.http_client = http_client
        self.api_base_url = api_base_url.rstrip("/")
        self.auth_token = auth_token
        self.refresh_token = refresh_token
        self.token_refresher = token_refresher

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def sync_batch(self, limit: int = 50, max_retries: int = 3) -> SyncResult:
        """Transmit oldest pending events to platform API.
        
        Handles:
        - 0 network / connection errors -> records failure, keeps events in queue
        - 401 Unauthorized -> refreshes token and retries
        - 200 OK -> marks acknowledged events in persistent queue
        """
        pending_items = self.queue.get_pending_batch(limit=limit)
        if not pending_items:
            return SyncResult(success=True, remaining_pending=0)

        event_dicts = [
            {
                "event_id": item.event_id,
                "student_id": item.student_id,
                "device_id": item.device_id,
                "event_type": item.event_type,
                "concept_id": item.concept_id,
                "payload": item.payload,
                "sequence_num": item.sequence_num,
                "timestamp": item.created_at,
            }
            for item in pending_items
        ]
        event_ids = [item.event_id for item in pending_items]

        req_body = {
            "student_id": self.student_id,
            "events": event_dicts,
        }

        retried_refresh = False
        last_error_str = ""

        for attempt in range(max_retries):
            try:
                if self.http_client is None:
                    # Simulation mode or client missing
                    return SyncResult(
                        success=False,
                        error="No HTTP client provided",
                        remaining_pending=self.queue.count_pending(),
                    )

                sync_url = f"{self.api_base_url}/sync/events"
                headers = self._get_headers()

                # Dispatch POST request
                resp = self.http_client.post(sync_url, json=req_body, headers=headers)

                # Check 401 Unauthorized -> Token Refresh Recovery
                if resp.status_code == 401:
                    if self.token_refresher and self.refresh_token and not retried_refresh:
                        tokens = self.token_refresher(self.refresh_token)
                        if tokens:
                            self.auth_token, self.refresh_token = tokens
                            retried_refresh = True
                            continue  # Retry with refreshed token
                    self.queue.mark_failed(event_ids, "401 Unauthorized: token expired or invalid")
                    return SyncResult(
                        success=False,
                        error="401 Unauthorized: token refresh failed or unavailable",
                        remaining_pending=self.queue.count_pending(),
                        retried_token_refresh=retried_refresh,
                    )

                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    synced = data.get("synced_count", len(event_ids))
                    duplicates = data.get("duplicate_count", 0)
                    failed = data.get("failed_count", 0)

                    # Authoritatively acknowledged by platform -> remove from local disk
                    ack_ids = data.get("acknowledged_ids", event_ids)
                    self.queue.mark_acknowledged(ack_ids)

                    return SyncResult(
                        success=True,
                        synced_count=synced,
                        duplicate_count=duplicates,
                        failed_count=failed,
                        remaining_pending=self.queue.count_pending(),
                        retried_token_refresh=retried_refresh,
                    )
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    last_error_str = err_msg
                    self.queue.mark_failed(event_ids, err_msg)
                    return SyncResult(
                        success=False,
                        error=err_msg,
                        remaining_pending=self.queue.count_pending(),
                    )

            except Exception as exc:
                # Connection refused, network timeout, DNS error
                last_error_str = str(exc)
                logger.warning(f"Sync attempt {attempt+1} failed with network error: {exc}")
                if attempt < max_retries - 1:
                    time.sleep(0.05 * (2**attempt))  # Exponential backoff

        # All retries exhausted -> keep in queue safely
        self.queue.mark_failed(event_ids, f"Network error after {max_retries} attempts: {last_error_str}")
        return SyncResult(
            success=False,
            error=last_error_str,
            remaining_pending=self.queue.count_pending(),
            retried_token_refresh=retried_refresh,
        )

    def sync_all(self, batch_size: int = 50) -> SyncResult:
        """Drain the entire persistent queue in batches."""
        total_synced = 0
        total_duplicates = 0
        total_failed = 0

        while self.queue.count_pending() > 0:
            res = self.sync_batch(limit=batch_size)
            if not res.success:
                return SyncResult(
                    success=False,
                    synced_count=total_synced,
                    duplicate_count=total_duplicates,
                    failed_count=total_failed,
                    remaining_pending=self.queue.count_pending(),
                    error=res.error,
                    retried_token_refresh=res.retried_token_refresh,
                )
            total_synced += res.synced_count
            total_duplicates += res.duplicate_count
            total_failed += res.failed_count

        return SyncResult(
            success=True,
            synced_count=total_synced,
            duplicate_count=total_duplicates,
            failed_count=total_failed,
            remaining_pending=0,
        )
