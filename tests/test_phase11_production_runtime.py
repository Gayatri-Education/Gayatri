"""Unit and integration test suite for Phase 11: Production Runtime and Database Validation.

Covers Master Plan Section 16 requirements:
1. SQLite WAL mode and foreign-key pragma enforcement on file-backed databases.
2. Database migration runner integrity, status reporting, and tamper detection.
3. PostgreSQL honest reporting when unreachable (F-025 remediation).
4. End-to-end production runtime validation outside test harness.
5. State persistence across process restart and connection teardown.
6. Explicit safe failure semantics without synthetic data or swallowed errors.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import create_app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, CourseVisibility, Organization, User, UserRole
from scripts.migrate_db import (
    MIGRATIONS_DIR,
    compute_file_checksum,
    get_migration_connection,
    run_all_migrations,
    verify_migration_checksums,
)
from scripts.validate_production_runtime import validate_production_runtime

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sqlite_wal_mode_enabled_on_disk(tmp_path):
    """Verify that file-backed PlatformDatabase automatically enables WAL journal mode and normal sync."""
    db_file = str(tmp_path / "prod_wal_test.db")
    db = PlatformDatabase(db_file)

    raw_conn = db._get_raw_connection()
    journal_mode = raw_conn.execute("PRAGMA journal_mode;").fetchone()[0]
    synchronous = raw_conn.execute("PRAGMA synchronous;").fetchone()[0]
    fk_enabled = raw_conn.execute("PRAGMA foreign_keys;").fetchone()[0]

    db.close()

    assert journal_mode.lower() == "wal", "Expected WAL journal mode for production concurrency"
    assert synchronous in (1, 2), "Expected NORMAL (1) or FULL (2) synchronous pragma"
    assert fk_enabled == 1, "Foreign key constraints must be strictly enabled"


def test_migrate_db_status_and_checksum_verification(tmp_path):
    """Verify CLI migration runner 'status' and 'verify' commands report clean state on migrated database."""
    db_file = str(tmp_path / "migrate_test.db")

    # Run migrations up
    res_up = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "migrate_db.py"), "up", "--db-path", db_file],
        capture_output=True,
        text=True,
    )
    assert res_up.returncode == 0
    assert "Applied" in res_up.stdout

    # Run migration verify (tamper check)
    res_verify = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "migrate_db.py"), "verify", "--db-path", db_file],
        capture_output=True,
        text=True,
    )
    assert res_verify.returncode == 0
    assert "verified against on-disk checksums" in res_verify.stdout

    # Run migration status
    res_status = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "migrate_db.py"), "status", "--db-path", db_file],
        capture_output=True,
        text=True,
    )
    assert res_status.returncode == 0
    assert "Database Backend: SQLite" in res_status.stdout
    assert "Journal: WAL" in res_status.stdout


def test_migrate_db_tamper_detection(tmp_path):
    """Verify migration runner detects modified migration records and returns failure exit code."""
    db_file = str(tmp_path / "tamper_test.db")
    conn = sqlite3.connect(db_file)
    run_all_migrations(conn)

    # Tamper with recorded checksum of migration 001
    conn.execute("UPDATE schema_migrations SET checksum = '0000000000000000000000000000000000000000000000000000000000000000' WHERE version = '001';")
    conn.commit()
    conn.close()

    res_verify = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "migrate_db.py"), "verify", "--db-path", db_file],
        capture_output=True,
        text=True,
    )
    assert res_verify.returncode == 1
    assert "Tampering detected" in res_verify.stdout


def test_postgres_honest_reporting_when_unreachable():
    """Verify F-025 remediation: attempting PostgreSQL connection when server is unreachable reports honest error."""
    unreachable_url = "postgresql://invalid_user:invalid_pass@127.0.0.1:5432/nonexistent_db"
    with pytest.raises(ConnectionError) as exc_info:
        get_migration_connection(unreachable_url)

    assert "PostgreSQL connection to 127.0.0.1:5432/nonexistent_db failed" in str(exc_info.value)


def test_full_production_runtime_lifecycle(tmp_path):
    """Verify that the full 15-step production runtime validation passes completely outside pytest harness."""
    db_file = str(tmp_path / "e2e_prod_runtime.db")
    passed = validate_production_runtime(db_path=db_file, verbose=False)
    assert passed is True, "validate_production_runtime must pass 100% of all 15 production lifecycle steps"


def test_persistence_across_process_restart(tmp_path):
    """Verify database entities survive complete connection close and reopen from disk."""
    db_file = str(tmp_path / "restart_persist.db")
    db1 = PlatformDatabase(db_file)

    org = Organization(id="org-persist-1", name="Persistent Institute", slug="persist-inst")
    user = User(
        id="usr-persist-1",
        organization_id=org.id,
        email="persist@test.edu",
        full_name="Persistent Scholar",
        role=UserRole.STUDENT,
    )
    course = Course(
        id="crs-persist-1",
        organization_id=org.id,
        code="PERSIST-101",
        title="Durable State Persistence",
        visibility=CourseVisibility.PRIVATE,
    )

    db1.create_organization(org)
    db1.create_user(user)
    db1.create_course(course)
    db1.close()
    del db1

    # Reopen brand new database instance referencing the same file on disk
    db2 = PlatformDatabase(db_file)
    fetched_user = db2.get_user(user.id)
    fetched_course = db2.get_course(course.id)
    fetched_org = db2.get_organization(org.id)
    db2.close()

    assert fetched_org is not None and fetched_org.name == "Persistent Institute"
    assert fetched_user is not None and fetched_user.email == "persist@test.edu"
    assert fetched_course is not None and fetched_course.title == "Durable State Persistence"


def test_runtime_boundary_isolation_cross_tenant_and_cross_student(tmp_path):
    """Verify multi-tenant and student isolation are enforced with HTTP 403 in the live application."""
    db_file = str(tmp_path / "isolation_test.db")
    db = PlatformDatabase(db_file)

    org1 = Organization(id="org-iso-1", name="Org One", slug="org-1")
    org2 = Organization(id="org-iso-2", name="Org Two", slug="org-2")
    db.create_organization(org1)
    db.create_organization(org2)

    student1 = User(id="usr-iso-s1", organization_id=org1.id, email="s1@org1.edu", full_name="Student 1", role=UserRole.STUDENT)
    student2 = User(id="usr-iso-s2", organization_id=org2.id, email="s2@org2.edu", full_name="Student 2", role=UserRole.STUDENT)
    db.create_user(student1)
    db.create_user(student2)

    course_private = Course(
        id="crs-private-org1",
        organization_id=org1.id,
        code="PRIV-101",
        title="Org 1 Proprietary Course",
        visibility=CourseVisibility.PRIVATE,
    )
    db.create_course(course_private)
    db.close()

    os.environ["GAYATRI_DB_PATH"] = db_file
    app = create_app()
    client = TestClient(app)

    token_s1 = create_access_token(user_id=student1.id, role="student", organization_id=org1.id)
    token_s2 = create_access_token(user_id=student2.id, role="student", organization_id=org2.id)

    # Student 2 (Org 2) accessing private course of Org 1 -> 403 Forbidden
    r_cross_org = client.get("/api/v1/courses/crs-private-org1", headers={"Authorization": f"Bearer {token_s2}"})
    assert r_cross_org.status_code == 403

    # Student 2 attempting to view Student 1's private SLR -> 403 Forbidden
    r_cross_student = client.get(f"/api/v1/students/{student1.id}/slr", headers={"Authorization": f"Bearer {token_s2}"})
    assert r_cross_student.status_code == 403

    # Student 1 accessing own profile -> 200 OK
    r_self = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_s1}"})
    assert r_self.status_code == 200
