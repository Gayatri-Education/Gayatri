"""Local Transactional Session Persistence subsystem.

Provides atomic turn commits, restart survivability, interrupted turn
recovery, and graceful read-only degraded mode for offline execution.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from local_runtime.errors import ReadOnlyDatabaseError

logger = logging.getLogger("gayatri.local_runtime.session")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class LocalSessionPersistence:
    """Manages transactional offline student sessions, mastery, and learning events."""

    def __init__(
        self,
        db_path: Path | str = ":memory:",
        read_only: bool = False,
    ) -> None:
        self.db_path = str(db_path)
        self.is_read_only = read_only

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        if not self.is_read_only:
            self.recover_interrupted_turns()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with row factory enabled."""
        if self.is_read_only and self.db_path != ":memory:":
            # Connect via URI in read-only mode if file exists
            uri = f"file:{Path(self.db_path).as_posix()}?mode=ro"
            try:
                conn = sqlite3.connect(uri, uri=True, timeout=10.0)
                conn.row_factory = sqlite3.Row
                return conn
            except Exception as exc:
                logger.debug("Failed opening read-only URI connection to %s: %s", uri, exc)

        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize schema if database is writable."""
        if self.is_read_only:
            return

        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_session_turns (
                        turn_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        turn_index INTEGER NOT NULL,
                        state_status TEXT NOT NULL, -- PENDING_COMMIT, COMMITTED, ROLLED_BACK
                        user_input TEXT,
                        tutor_output TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_student_mastery (
                        student_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        concept_id TEXT NOT NULL,
                        score REAL NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY(student_id, course_id, concept_id)
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_learning_events (
                        event_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower():
                logger.warning("Local database is read-only. Enabling read-only degraded mode.")
                self.is_read_only = True
            else:
                raise

    def set_read_only(self, mode: bool) -> None:
        """Programmatically switch read-only mode (e.g. on disk permission error)."""
        self.is_read_only = mode

    def recover_interrupted_turns(self) -> int:
        """Roll back any turns left in PENDING_COMMIT status from prior crashes."""
        if self.is_read_only:
            return 0

        now = _now_iso()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    UPDATE local_session_turns
                    SET state_status = 'ROLLED_BACK', updated_at = ?
                    WHERE state_status = 'PENDING_COMMIT'
                    """,
                    (now,)
                )
                count = cursor.rowcount
                conn.commit()
                if count > 0:
                    logger.info("Recovered %d interrupted turn(s) on startup.", count)
                return count
        except Exception as exc:
            logger.error("Failed to recover interrupted turns: %s", exc)
            return 0

    def begin_turn(
        self,
        session_id: str,
        student_id: str,
        course_id: str,
        user_input: str,
        turn_index: Optional[int] = None,
    ) -> str:
        """Initiate an atomic turn. Returns unique turn_id in PENDING_COMMIT status."""
        if self.is_read_only:
            raise ReadOnlyDatabaseError(db_path=self.db_path)

        now = _now_iso()
        turn_id = f"trn_{uuid.uuid4().hex[:12]}"

        try:
            with self._get_connection() as conn:
                if turn_index is None:
                    row = conn.execute(
                        "SELECT MAX(turn_index) AS max_idx FROM local_session_turns WHERE session_id = ?",
                        (session_id,)
                    ).fetchone()
                    turn_index = (row["max_idx"] + 1) if (row and row["max_idx"] is not None) else 0

                conn.execute(
                    """
                    INSERT INTO local_session_turns
                    (turn_id, session_id, student_id, course_id, turn_index, state_status, user_input, tutor_output, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'PENDING_COMMIT', ?, '', ?, ?)
                    """,
                    (turn_id, session_id, student_id, course_id, turn_index, user_input, now, now)
                )
                conn.commit()
            return turn_id
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower():
                self.is_read_only = True
                raise ReadOnlyDatabaseError(db_path=self.db_path)
            raise

    def commit_turn(
        self,
        turn_id: str,
        tutor_output: str,
        mastery_updates: Optional[Dict[str, float]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Atomically commit a turn along with its mastery delta and telemetry events."""
        if self.is_read_only:
            raise ReadOnlyDatabaseError(db_path=self.db_path)

        now = _now_iso()

        try:
            conn = self._get_connection()
            try:
                with conn:
                    # 1. Fetch student_id and course_id
                    row = conn.execute(
                        "SELECT student_id, course_id FROM local_session_turns WHERE turn_id = ?",
                        (turn_id,)
                    ).fetchone()
                    if not row:
                        raise ValueError(f"Turn '{turn_id}' does not exist.")

                    student_id = row["student_id"]
                    course_id = row["course_id"]

                    # 2. Update turn to COMMITTED
                    conn.execute(
                        """
                        UPDATE local_session_turns
                        SET state_status = 'COMMITTED', tutor_output = ?, updated_at = ?
                        WHERE turn_id = ?
                        """,
                        (tutor_output, now, turn_id)
                    )

                    # 3. Apply mastery updates
                    if mastery_updates:
                        for concept_id, score in mastery_updates.items():
                            conn.execute(
                                """
                                INSERT INTO local_student_mastery (student_id, course_id, concept_id, score, updated_at)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(student_id, course_id, concept_id)
                                DO UPDATE SET score = excluded.score, updated_at = excluded.updated_at
                                """,
                                (student_id, course_id, concept_id, float(score), now)
                            )

                    # 4. Record learning events
                    if events:
                        for evt in events:
                            eid = evt.get("event_id") or f"evt_{uuid.uuid4().hex[:12]}"
                            etype = evt.get("event_type", "turn_completed")
                            payload_str = json.dumps(evt.get("payload", evt))
                            conn.execute(
                                """
                                INSERT INTO local_learning_events (event_id, student_id, course_id, event_type, payload_json, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (eid, student_id, course_id, etype, payload_str, now)
                            )
            finally:
                conn.close()
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower():
                self.is_read_only = True
                raise ReadOnlyDatabaseError(db_path=self.db_path)
            raise

    def rollback_turn(self, turn_id: str) -> None:
        """Mark turn as ROLLED_BACK in case of failure."""
        if self.is_read_only:
            raise ReadOnlyDatabaseError(db_path=self.db_path)

        now = _now_iso()
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE local_session_turns
                    SET state_status = 'ROLLED_BACK', updated_at = ?
                    WHERE turn_id = ?
                    """,
                    (now, turn_id)
                )
                conn.commit()
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower():
                self.is_read_only = True
                raise ReadOnlyDatabaseError(db_path=self.db_path)
            raise

    def get_session_turns(
        self,
        session_id: str,
        include_uncommitted: bool = False,
    ) -> List[Dict[str, Any]]:
        """Retrieve turns for a session (read-only safe)."""
        query = """
            SELECT turn_id, session_id, student_id, course_id, turn_index,
                   state_status, user_input, tutor_output, created_at, updated_at
            FROM local_session_turns
            WHERE session_id = ?
        """
        params: List[Any] = [session_id]
        if not include_uncommitted:
            query += " AND state_status = 'COMMITTED'"
        query += " ORDER BY turn_index ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_student_mastery(self, student_id: str, course_id: str) -> Dict[str, float]:
        """Retrieve concept mastery dictionary for a student in a course (read-only safe)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT concept_id, score
                FROM local_student_mastery
                WHERE student_id = ? AND course_id = ?
                """,
                (student_id, course_id)
            ).fetchall()
            return {r["concept_id"]: float(r["score"]) for r in rows}

    def get_learning_events(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve learning events for a student (read-only safe)."""
        query = "SELECT event_id, student_id, course_id, event_type, payload_json, created_at FROM local_learning_events WHERE student_id = ?"
        params: List[Any] = [student_id]
        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)
        query += " ORDER BY created_at ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["payload"] = json.loads(item.pop("payload_json"))
                except Exception:
                    item["payload"] = {}
                result.append(item)
            return result
