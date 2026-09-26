"""Unit and integration test suite for Phase 20: Production Readiness & Operations."""

import os
import pytest
from central_platform.operations import ProductionReadinessManager


@pytest.fixture
def readiness_manager(tmp_path):
    db_file = str(tmp_path / "prod_test.db")
    import sqlite3
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE dummy (id INT);")
    conn.close()
    return ProductionReadinessManager(db_file)


def test_database_backup_and_restore_verification(readiness_manager, tmp_path):
    backup_dir = str(tmp_path / "backups")
    backup_path = readiness_manager.create_database_backup(backup_dir)

    assert os.path.exists(backup_path)
    assert readiness_manager.verify_backup_restoration(backup_path) is True


def test_health_check_execution(readiness_manager):
    status = readiness_manager.perform_health_check()
    assert status.status in ("HEALTHY", "DEGRADED")
    assert status.database_connected is True
    assert status.backup_system_ready is True


def test_secrets_auditing(readiness_manager, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/gayatri")
    monkeypatch.setenv("JWT_SECRET_KEY", "prod_super_secret_jwt_key_123")
    monkeypatch.setenv("ENCRYPTION_KEY", "prod_aes_256_key_abc")

    report = readiness_manager.validate_secrets_configuration()
    assert report["DATABASE_URL"] is True
    assert report["JWT_SECRET_KEY"] is True
    assert report["ENCRYPTION_KEY"] is True


def test_log_retention_purging(readiness_manager):
    logs = [
        {"id": "l1", "age_days": 10},
        {"id": "l2", "age_days": 45},
    ]
    retained = readiness_manager.purge_expired_logs(logs, max_age_days=30)
    assert len(retained) == 1
    assert retained[0]["id"] == "l1"
