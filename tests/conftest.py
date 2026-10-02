"""Pytest root configuration and fixtures for Gayatri AI platform test suite."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from scripts.migrate_db import run_all_migrations


@pytest.fixture(scope="session", autouse=True)
def ensure_local_database():
    """Ensure that gayatri_local.db exists and has all migrations applied for tests."""
    root = Path(__file__).resolve().parent.parent
    db_path = root / "gayatri_local.db"

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        run_all_migrations(conn)
    finally:
        conn.close()
