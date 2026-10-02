"""Migration tests for Phase 02: Verification of schema evolution and idempotency."""

import sqlite3
import pytest
from pathlib import Path
from scripts.migrate_db import (
    MIGRATIONS_DIR,
    run_all_migrations,
    get_applied_migrations,
    rollback_migration_file,
    apply_migration_file,
)
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, CourseVisibility, CourseVersion, CourseStatus


def test_migrations_fresh_db_and_idempotency(tmp_path):
    """Test clean migration application, verification of all tables, and idempotency."""
    db_file = tmp_path / "fresh_migration_test.db"
    conn = sqlite3.connect(str(db_file))

    # 1. First run: Applies all migrations
    applied_first = run_all_migrations(conn)
    assert len(applied_first) >= 4
    assert "001" in applied_first
    assert "002" in applied_first
    assert "003" in applied_first
    assert "004" in applied_first

    # 2. Second run: Idempotent - applies 0
    applied_second = run_all_migrations(conn)
    assert len(applied_second) == 0

    # 3. Verify tables exist
    cursor = conn.cursor()
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    assert "courses" in tables
    assert "course_versions" in tables
    assert "organization_course_offerings" in tables
    assert "fee_structures" in tables
    assert "schema_migrations" in tables

    # 4. Verify columns in courses
    course_cols = [r[1] for r in cursor.execute("PRAGMA table_info(courses);").fetchall()]
    assert "visibility" in course_cols

    # 5. Verify no duplicate assignments table in schema
    assignments_tables = [t for t in tables if t == "assignments"]
    assert len(assignments_tables) == 1

    conn.close()


def test_migrations_rollback_and_reapply(tmp_path):
    """Test rolling back migrations using down scripts and reapplying."""
    db_file = tmp_path / "rollback_test.db"
    conn = sqlite3.connect(str(db_file))

    # Apply all
    run_all_migrations(conn)
    applied = get_applied_migrations(conn)
    assert len(applied) >= 4

    # Rollback 004
    down_004 = MIGRATIONS_DIR / "004_course_domain_model_down.sql"
    assert down_004.exists()
    rolled_back = rollback_migration_file(conn, down_004, "004")
    assert rolled_back is True

    # Verify course_versions is dropped
    cursor = conn.cursor()
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    assert "course_versions" not in tables
    assert "organization_course_offerings" not in tables

    # Re-apply 004
    up_004 = MIGRATIONS_DIR / "004_course_domain_model.sql"
    reapplied = apply_migration_file(conn, up_004, "004", "Course Domain Model")
    assert reapplied is True

    # Verify course_versions is recreated
    tables_reapplied = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    assert "course_versions" in tables_reapplied
    assert "organization_course_offerings" in tables_reapplied

    conn.close()
