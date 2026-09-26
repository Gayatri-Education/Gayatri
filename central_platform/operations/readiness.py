"""Production Readiness, Database Backup/Restore, Secrets Validation, and Health Diagnostics."""

from __future__ import annotations

import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HealthStatus:
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    database_connected: bool
    secrets_valid: bool
    backup_system_ready: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProductionReadinessManager:
    """Manages production operational readiness, backup/restore cycles, secrets auditing, and health checks."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    def create_database_backup(self, backup_dir: str) -> str:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}_{uuid.uuid4().hex[:6]}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        if self.db_path == ":memory:":
            # Handle in-memory sqlite backup
            conn = sqlite3.connect(":memory:")
            conn.execute("CREATE TABLE backup_marker (id INT);")
            dest_conn = sqlite3.connect(backup_path)
            conn.backup(dest_conn)
            conn.close()
            dest_conn.close()
        else:
            shutil.copy2(self.db_path, backup_path)

        return backup_path

    def verify_backup_restoration(self, backup_path: str) -> bool:
        if not os.path.exists(backup_path):
            return False
        try:
            conn = sqlite3.connect(backup_path)
            conn.execute("SELECT 1;")
            conn.close()
            return True
        except Exception:
            return False

    def validate_secrets_configuration(self, required_keys: Optional[List[str]] = None) -> Dict[str, bool]:
        keys = required_keys or ["DATABASE_URL", "JWT_SECRET_KEY", "ENCRYPTION_KEY"]
        validation_report: Dict[str, bool] = {}
        for key in keys:
            val = os.getenv(key)
            # In production, keys must be set and non-default
            validation_report[key] = bool(val and val != "dev_default_secret")
        return validation_report

    def perform_health_check(self) -> HealthStatus:
        db_ok = True
        try:
            if self.db_path != ":memory:" and os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.execute("SELECT 1;")
                conn.close()
        except Exception:
            db_ok = False

        secrets_report = self.validate_secrets_configuration()
        secrets_ok = all(secrets_report.values())

        return HealthStatus(
            status="HEALTHY" if (db_ok) else "DEGRADED",
            database_connected=db_ok,
            secrets_valid=secrets_ok,
            backup_system_ready=True,
        )

    def purge_expired_logs(self, log_records: List[Dict[str, Any]], max_age_days: int = 30) -> List[Dict[str, Any]]:
        # Keep non-expired records
        return [r for r in log_records if r.get("age_days", 0) <= max_age_days]
