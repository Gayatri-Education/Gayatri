"""Architecture Guard: Ensure migration scripts are idempotent, complete, and free of duplicate DDL."""

import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent
MIGRATIONS_DIR = ROOT / "migrations"


def extract_created_tables(sql_content: str) -> list[str]:
    """Extract list of table names created in a SQL script."""
    pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.IGNORECASE)
    return pattern.findall(sql_content)


def test_migrations_have_corresponding_down_scripts():
    """Verify that every forward migration script has a matching down script."""
    assert MIGRATIONS_DIR.exists()
    forward_scripts = [f for f in MIGRATIONS_DIR.glob("*.sql") if not f.name.endswith("_down.sql")]
    assert len(forward_scripts) >= 3

    missing_down = []
    for f in forward_scripts:
        down_script = MIGRATIONS_DIR / f"{f.stem}_down.sql"
        if not down_script.exists():
            missing_down.append(f.name)

    assert not missing_down, f"Migrations missing corresponding down scripts: {missing_down}"


def test_migrations_no_duplicate_create_table_statements():
    """Verify that no migration script declares duplicate CREATE TABLE statements."""
    for sql_file in MIGRATIONS_DIR.glob("*.sql"):
        content = sql_file.read_text(encoding="utf-8")
        tables = extract_created_tables(content)
        counts = Counter(tables)
        duplicates = {table: count for table, count in counts.items() if count > 1}
        assert not duplicates, f"Migration {sql_file.name} defines duplicate tables: {duplicates}"


def test_migration_integrity_guard_negative_synthetic_detection():
    """Negative test: verify that synthetic duplicate DDL is detected."""
    synthetic_ddl = """
    CREATE TABLE IF NOT EXISTS sample_table (id TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS sample_table (id TEXT PRIMARY KEY, extra TEXT);
    """
    tables = extract_created_tables(synthetic_ddl)
    counts = Counter(tables)
    duplicates = {table: count for table, count in counts.items() if count > 1}
    assert "sample_table" in duplicates
