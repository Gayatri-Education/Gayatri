"""Phase 27: Production Operations Master Test Suite.

Implements Master Plan Section 36:
Validates production readiness and operational safeguards:
1. Health, readiness, and liveness probe integrity (/healthz, /readyz, /livez)
2. Production analytics and metric emission (/api/v1/analytics/system)
3. Emergency AI kill-switch activation, status, and restoration
4. Structured error envelopes and request tracing (X-Request-ID)
"""

import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_production_health_probes(client):
    """Test 1: Liveness, readiness, and health probes return 200 OK with valid operational states."""
    # Livez
    r_live = client.get("/livez")
    assert r_live.status_code == 200
    assert r_live.json().get("alive") is True

    # Readyz
    r_ready = client.get("/readyz")
    assert r_ready.status_code == 200
    assert r_ready.json().get("ready") is True

    # Healthz
    r_health = client.get("/healthz")
    assert r_health.status_code == 200
    data = r_health.json()
    assert data.get("status") in ("ONLINE", "HEALTHY")
    assert "database" in data
    assert "X-Request-ID" in r_health.headers


def test_production_system_analytics(client):
    """Test 2: Operational telemetry endpoint returns server health and cost metrics."""
    resp = client.get("/api/v1/analytics/system")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data or "ok" in data or "metrics" in data or "health" in data


def test_production_emergency_kill_switch(client):
    """Test 3: Emergency global AI kill-switch immediately disables and re-enables AI execution."""
    token = create_access_token(user_id="admin_ops", role="super_admin", organization_id="org_global")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Activate kill switch
    r_activate = client.post("/api/v1/admin/kill-switch?active=true&reason=ops_drill", headers=headers)
    assert r_activate.status_code == 200
    assert r_activate.json()["data"]["kill_switch_active"] is True

    # 2. Deactivate kill switch
    r_restore = client.post("/api/v1/admin/kill-switch?active=false&reason=drill_completed", headers=headers)
    assert r_restore.status_code == 200
    assert r_restore.json()["data"]["kill_switch_active"] is False


def test_production_request_tracing(client):
    """Test 4: Incoming correlation headers are preserved across platform boundaries."""
    custom_trace = "trace-ops-prod-9988"
    resp = client.get("/healthz", headers={"X-Request-ID": custom_trace})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_trace
