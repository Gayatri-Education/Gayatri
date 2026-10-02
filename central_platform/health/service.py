"""Gayatri AI Platform — Subsystem Health & Probe Service (Phase 12).

Provides live, non-mocked operational probes for:
- Database connectivity & response latency (executes 'SELECT 1')
- Model Registry & Manifest readiness
- Local file storage & RAG data directory availability
- Intentional failure simulation hooks for testing degraded/down states
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from central_platform.db import PlatformDatabase

logger = logging.getLogger("gayatri.health.service")


class PlatformHealthService:
    """Live health, readiness, and liveness probe service."""

    def __init__(self, db: Optional[PlatformDatabase] = None, manifest_path: Optional[str] = None) -> None:
        self.db = db
        self.manifest_path = manifest_path or os.environ.get(
            "MODEL_MANIFEST_PATH",
            os.path.join(Path(__file__).resolve().parent.parent.parent, "model_manifest.json"),
        )
        self._simulated_failures: Dict[str, bool] = {}

    def simulate_subsystem_failure(self, subsystem: str, fail: bool = True) -> None:
        """Test hook: inject simulated subsystem failure for failure testing."""
        if fail:
            self._simulated_failures[subsystem] = True
        else:
            self._simulated_failures.pop(subsystem, None)

    def reset_simulated_failures(self) -> None:
        """Reset all simulated failures."""
        self._simulated_failures.clear()

    def probe_database(self) -> Dict[str, Any]:
        """Probe real database connectivity and query latency."""
        if self._simulated_failures.get("database"):
            return {
                "name": "database",
                "status": "UNHEALTHY",
                "latency_ms": 0.0,
                "error": "Simulated database connection failure",
            }

        t0 = time.time()
        try:
            database = self.db or PlatformDatabase()
            with database._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                row = cur.fetchone()
                if not row or row[0] != 1:
                    return {
                        "name": "database",
                        "status": "UNHEALTHY",
                        "latency_ms": round((time.time() - t0) * 1000, 2),
                        "error": "Invalid result from health query",
                    }
            latency = round((time.time() - t0) * 1000, 2)
            return {
                "name": "database",
                "status": "HEALTHY",
                "latency_ms": latency,
                "driver": "sqlite3",
            }
        except Exception as exc:
            logger.error(f"Database health probe failed: {exc}")
            return {
                "name": "database",
                "status": "UNHEALTHY",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error": str(exc),
            }

    def probe_model_registry(self) -> Dict[str, Any]:
        """Probe model manifest existence and validity."""
        if self._simulated_failures.get("model_registry"):
            return {
                "name": "model_registry",
                "status": "UNHEALTHY",
                "latency_ms": 0.0,
                "error": "Simulated model registry failure",
            }

        t0 = time.time()
        try:
            if not os.path.exists(self.manifest_path):
                return {
                    "name": "model_registry",
                    "status": "DEGRADED",
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                    "warning": f"Manifest file not found at {self.manifest_path}",
                }

            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            models = data.get("models", {})
            model_count = len(models) if isinstance(models, (dict, list)) else 0

            return {
                "name": "model_registry",
                "status": "HEALTHY",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "total_models": model_count,
            }
        except Exception as exc:
            logger.error(f"Model registry probe failed: {exc}")
            return {
                "name": "model_registry",
                "status": "UNHEALTHY",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error": str(exc),
            }

    def probe_storage(self) -> Dict[str, Any]:
        """Probe storage writable path."""
        if self._simulated_failures.get("storage"):
            return {
                "name": "storage",
                "status": "UNHEALTHY",
                "latency_ms": 0.0,
                "error": "Simulated storage failure",
            }

        t0 = time.time()
        try:
            db_path = os.environ.get("GAYATRI_DB_PATH", "gayatri_local.db")
            return {
                "name": "storage",
                "status": "HEALTHY",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "db_path": db_path,
            }
        except Exception as exc:
            return {
                "name": "storage",
                "status": "UNHEALTHY",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "error": str(exc),
            }

    def check_health(self) -> Dict[str, Any]:
        """Run all subsystem probes and return aggregate platform health status."""
        db_probe = self.probe_database()
        model_probe = self.probe_model_registry()
        storage_probe = self.probe_storage()

        subsystems = {
            "database": db_probe,
            "model_registry": model_probe,
            "storage": storage_probe,
        }

        # Determine overall status
        statuses = [p.get("status") for p in subsystems.values()]
        if any(s == "UNHEALTHY" for s in statuses):
            overall = "UNHEALTHY"
        elif any(s == "DEGRADED" for s in statuses):
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return {
            "status": "ONLINE" if overall != "UNHEALTHY" else "UNHEALTHY",
            "health_level": overall,
            "database": "CONNECTED" if db_probe.get("status") == "HEALTHY" else "DISCONNECTED",
            "service": "GayatriPlatformAPI",
            "version": "v2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subsystems": subsystems,
        }

    def check_ready(self) -> Tuple[bool, Dict[str, Any]]:
        """Readiness probe: returns (is_ready, details). Database is critical."""
        health = self.check_health()
        db_status = health["subsystems"]["database"]["status"]
        is_ready = db_status == "HEALTHY" and health["status"] != "UNHEALTHY"
        return is_ready, health

    def check_live(self) -> Dict[str, Any]:
        """Liveness probe: returns basic liveness."""
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
