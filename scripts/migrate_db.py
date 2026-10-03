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


class MigrationChecksumMismatchError(RuntimeError):
    """Raised when on-disk migration script checksum differs from ledger record."""
    pass


def apply_migration_file(conn: sqlite3.Connection, sql_path: Path, version: str, description: str) -> bool:
    """Apply a single forward SQL migration file within a transaction."""
    ensure_migrations_table(conn)
    applied_records = get_applied_migrations(conn)
    applied_map = {m["version"]: m["checksum"] for m in applied_records}

    current_checksum = compute_file_checksum(sql_path)

    if version in applied_map:
        if current_checksum != applied_map[version]:
            raise MigrationChecksumMismatchError(
                f"Migration {version} ({sql_path.name}) has been tampered with after application! "
                f"Recorded checksum: {applied_map[version]}, Current: {current_checksum}"
            )
        return False  # Already applied and checksum matches

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    now_iso = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.executescript(sql_content)
        conn.execute(
            "INSERT OR REPLACE INTO schema_migrations (version, description, applied_at, checksum) VALUES (?, ?, ?, ?);",
            (version, description, now_iso, current_checksum),
        )
    return True


def verify_migration_checksums(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    """Verify that all applied migrations match their on-disk file checksums."""
    applied = get_applied_migrations(conn)
    mismatches = []
    for record in applied:
        version = record["version"]
        matching = list(MIGRATIONS_DIR.glob(f"{version}_*.sql"))
        forward = [f for f in matching if not f.name.endswith("_down.sql")]
        if not forward:
            continue
        actual_checksum = compute_file_checksum(forward[0])
        if actual_checksum != record["checksum"]:
            mismatches.append({
                "version": version,
                "recorded_checksum": record["checksum"],
                "actual_checksum": actual_checksum,
                "file": forward[0].name,
            })
    return mismatches


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
    if not MIGRATIONS_DIR.exists():
        return applied_versions

    forward_scripts = sorted([
        f for f in MIGRATIONS_DIR.glob("*.sql")
        if not f.name.endswith("_down.sql")
    ])

    for script in forward_scripts:
        parts = script.name.split("_", 1)
        version = parts[0]
        if version == "001":
            desc = "Initial Authoritative Platform Schema"
        else:
            desc = parts[1].replace(".sql", "").replace("_", " ").title() if len(parts) > 1 else f"Migration {version}"
        if apply_migration_file(conn, script, version, desc):
            applied_versions.append(version)

    return applied_versions


def rollback_all_migrations(conn: sqlite3.Connection) -> List[str]:
    """Rollback migrations in reverse order."""
    rolled_back = []
    if not MIGRATIONS_DIR.exists():
        return rolled_back

    down_scripts = sorted([
        f for f in MIGRATIONS_DIR.glob("*_down.sql")
    ], reverse=True)

    for script in down_scripts:
        parts = script.name.split("_", 1)
        version = parts[0]
        if rollback_migration_file(conn, script, version):
            rolled_back.append(version)

    return rolled_back


def get_migration_connection(db_target: Optional[str] = None) -> Any:
    """Resolve database connection, handling PostgreSQL URLs or SQLite paths."""
    target = db_target or os.environ.get("DATABASE_URL") or os.environ.get("GAYATRI_DB_PATH", ":memory:")
    if target.startswith("postgres://") or target.startswith("postgresql://"):
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError("PostgreSQL driver psycopg2 is not installed.")
        try:
            conn = psycopg2.connect(target, connect_timeout=3)
            return conn
        except Exception as exc:
            raise ConnectionError(f"PostgreSQL connection to {target.split('@')[-1]} failed: {exc}")

    conn = sqlite3.connect(target)
    conn.execute("PRAGMA foreign_keys = ON;")
    if target != ":memory:":
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
        except Exception:
            pass
    return conn


def main() -> int:
    parser = argparse.ArgumentParser(description="Gayatri AI Database Migration Runner")
    parser.add_argument("command", choices=["up", "down", "status", "verify"], help="Migration action")
    parser.add_argument("--db-path", default=None, help="Database path or connection string")
    args = parser.parse_args()

    db_target = args.db_path or os.environ.get("DATABASE_URL") or os.environ.get("GAYATRI_DB_PATH", ":memory:")

    try:
        conn = get_migration_connection(db_target)
    except ConnectionError as err:
        print(f"[ERROR] Database connection failed: {err}")
        return 1
    except Exception as err:
        print(f"[ERROR] Could not initialize database: {err}")
        return 1

    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)
        backend = "SQLite" if is_sqlite else "PostgreSQL"

        if args.command == "up":
            applied = run_all_migrations(conn)
            print(f"[OK] Applied {len(applied)} migration(s) on {backend}: {', '.join(applied) if applied else 'Already up to date'}")
        elif args.command == "down":
            rolled = rollback_all_migrations(conn)
            print(f"[OK] Rolled back {len(rolled)} migration(s) on {backend}: {', '.join(rolled) if rolled else 'Nothing to roll back'}")
        elif args.command == "verify":
            mismatches = verify_migration_checksums(conn)
            if mismatches:
                print(f"[FAILED] Tampering detected in {len(mismatches)} migration(s):")
                for m in mismatches:
                    print(f" - Version {m['version']} ({m['file']}): recorded {m['recorded_checksum'][:12]}... != actual {m['actual_checksum'][:12]}...")
                return 1
            print(f"[OK] All applied migrations on {backend} verified against on-disk checksums (Zero tampering).")
        elif args.command == "status":
            records = get_applied_migrations(conn)
            journal = "N/A"
            if is_sqlite and db_target != ":memory:":
                try:
                    journal = conn.execute("PRAGMA journal_mode;").fetchone()[0].upper()
                except Exception:
                    pass
            print(f"Database Backend: {backend} (Target: {db_target}, Journal: {journal})")
            print(f"Total Applied Migrations: {len(records)}")
            for r in records:
                print(f" - Version: {r['version']} | {r['description']} | Applied: {r['applied_at']}")
            mismatches = verify_migration_checksums(conn)
            if mismatches:
                print(f"[WARNING] {len(mismatches)} migration checksum mismatch(es) detected!")
            else:
                print("[OK] Migration checksum integrity: VERIFIED")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
