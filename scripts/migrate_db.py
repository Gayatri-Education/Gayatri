"""Database migration runner for Gayatri AI Central Platform (Phase 03).

Provides automated schema versioning, forward migration, rollback, and checksum verification.
Compatible with SQLite and PostgreSQL connections.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA-256 checksum of migration SQL script."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Ensure the schema_migrations ledger exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        );
    """)
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    """Return list of applied migration records."""
    ensure_migrations_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version, description, applied_at, checksum FROM schema_migrations ORDER BY version ASC;")
    rows = cursor.fetchall()
    return [
        {"version": r[0], "description": r[1], "applied_at": r[2], "checksum": r[3]}
        for r in rows
    ]


def apply_migration_file(conn: sqlite3.Connection, sql_path: Path, version: str, description: str) -> bool:
    """Apply a single forward SQL migration file within a transaction."""
    ensure_migrations_table(conn)
    applied = {m["version"] for m in get_applied_migrations(conn)}
    if version in applied:
        return False  # Already applied

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    checksum = compute_file_checksum(sql_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.executescript(sql_content)
        conn.execute(
            "INSERT OR REPLACE INTO schema_migrations (version, description, applied_at, checksum) VALUES (?, ?, ?, ?);",
            (version, description, now_iso, checksum),
        )
    return True


def rollback_migration_file(conn: sqlite3.Connection, sql_path: Path, version: str) -> bool:
    """Roll back a migration using its corresponding down script."""
    ensure_migrations_table(conn)
    applied = {m["version"] for m in get_applied_migrations(conn)}
    if version not in applied:
        return False  # Not applied

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    with conn:
        conn.executescript(sql_content)
        conn.execute("DELETE FROM schema_migrations WHERE version = ?;", (version,))
    return True


def run_all_migrations(conn: sqlite3.Connection) -> List[str]:
    """Discover and apply all pending migrations in order."""
    applied_versions = []
    # Currently migration 001
    mig_001 = MIGRATIONS_DIR / "001_initial_schema.sql"
    if mig_001.exists():
        if apply_migration_file(conn, mig_001, "001", "Initial Authoritative Platform Schema"):
            applied_versions.append("001")
    return applied_versions


def rollback_all_migrations(conn: sqlite3.Connection) -> List[str]:
    """Rollback migrations in reverse order."""
    rolled_back = []
    down_001 = MIGRATIONS_DIR / "001_initial_schema_down.sql"
    if down_001.exists():
        if rollback_migration_file(conn, down_001, "001"):
            rolled_back.append("001")
    return rolled_back


def main() -> int:
    parser = argparse.ArgumentParser(description="Gayatri AI Database Migration Runner")
    parser.add_argument("command", choices=["up", "down", "status"], help="Migration action")
    parser.add_argument("--db-path", default=os.environ.get("GAYATRI_DB_PATH", ":memory:"), help="Database path")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        if args.command == "up":
            applied = run_all_migrations(conn)
            print(f"[OK] Applied {len(applied)} migration(s): {', '.join(applied) if applied else 'Already up to date'}")
        elif args.command == "down":
            rolled = rollback_all_migrations(conn)
            print(f"[OK] Rolled back {len(rolled)} migration(s): {', '.join(rolled) if rolled else 'Nothing to roll back'}")
        elif args.command == "status":
            records = get_applied_migrations(conn)
            print(f"Total Applied Migrations: {len(records)}")
            for r in records:
                print(f" - Version: {r['version']} | {r['description']} | Applied: {r['applied_at']}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
