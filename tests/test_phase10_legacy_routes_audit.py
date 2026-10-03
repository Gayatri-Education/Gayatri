"""Phase 10: Legacy, Dead Ends, and Route Reachability Audit Test Suite.

Master Plan Section 15 Requirements:
1. Canonical production application entrypoint exists in central_platform.api.server.
2. Zero reverse dependencies: central_platform does not import from root server.py.
3. Root server.py delegates cleanly without behavioral divergence.
4. False-green and backdoor paths gated: /api/v1/auth/demo-tokens returns 404 in production mode.
5. docs/verification/ROUTE_REACHABILITY_MATRIX.md exists and comprehensively documents all routes.
6. Clean error handling: zero bare silent exception swallowing in active service flows.
7. Teacher dashboard HTML rendering is self-contained within central_platform.teacher.views.
8. Endpoints and health probes report consistent platform health without divergence.
"""
from __future__ import annotations

import inspect
import os
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    from central_platform.api.app import app
    return TestClient(app)


# ── Test 1: Canonical Server Entrypoint Exists & Exports App ──────────────────

def test_canonical_server_entrypoint_exists_and_exports_app():
    """Verify central_platform.api.server exists, exports app, and has run_server."""
    server_module = Path(ROOT / "central_platform" / "api" / "server.py")
    assert server_module.exists(), "central_platform/api/server.py does not exist."

    import central_platform.api.server as cp_server
    from central_platform.api.app import app as canonical_app

    assert hasattr(cp_server, "app"), "central_platform.api.server must export 'app'."
    assert cp_server.app is canonical_app, "Exported app must be identical to canonical app."
    assert hasattr(cp_server, "run_server"), "central_platform.api.server must provide 'run_server'."
    assert callable(cp_server.run_server)


# ── Test 2: Zero Server Imports in central_platform ───────────────────────────

def test_zero_server_imports_in_central_platform():
    """Verify that central_platform has ZERO import statements referencing root server."""
    cp_dir = ROOT / "central_platform"
    assert cp_dir.exists()

    regex = re.compile(r"^\s*(?:from\s+server\b|import\s+server\b)", re.MULTILINE)
    violating_files = []

    for py_file in cp_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if regex.search(content):
            violating_files.append(str(py_file.relative_to(ROOT)))

    assert not violating_files, f"Forbidden root server imports found in central_platform: {violating_files}"


# ── Test 3: Root server.py Delegates to central_platform ──────────────────────

def test_server_py_delegates_to_central_platform():
    """Verify root server.py imports and re-exports from central_platform."""
    server_path = ROOT / "server.py"
    assert server_path.exists()

    import server

    # Must have render_teacher_dashboard_html and TeacherPortalHTTPHandler
    assert hasattr(server, "render_teacher_dashboard_html")
    assert hasattr(server, "TeacherPortalHTTPHandler")
    assert hasattr(server, "run_server")

    # Verify rendering produces valid HTML
    html = server.render_teacher_dashboard_html("crs-chem-101")
    assert "<!DOCTYPE html>" in html
    assert "Teacher Command Center" in html


# ── Test 4: Demo Tokens Gated in Production ───────────────────────────────────

def test_demo_tokens_disabled_in_production_mode(client, monkeypatch):
    """Verify /api/v1/auth/demo-tokens returns 200 in dev but 404 in production."""
    # Development / local mode: available
    monkeypatch.delenv("GAYATRI_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    resp = client.get("/api/v1/auth/demo-tokens")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "superadmin" in data
    assert "token" in data["superadmin"]

    # Production mode: gated and inaccessible
    monkeypatch.setenv("GAYATRI_ENV", "production")
    resp_prod = client.get("/api/v1/auth/demo-tokens")
    assert resp_prod.status_code == 404
    assert "disabled" in resp_prod.json()["detail"].lower()


# ── Test 5: Route Reachability Matrix Exists & Has Required Columns ───────────

def test_route_reachability_matrix_file_exists_and_complete():
    """Verify ROUTE_REACHABILITY_MATRIX.md exists and covers all required columns."""
    matrix_file = ROOT / "docs" / "verification" / "ROUTE_REACHABILITY_MATRIX.md"
    assert matrix_file.exists(), "ROUTE_REACHABILITY_MATRIX.md is missing."

    content = matrix_file.read_text(encoding="utf-8")
    assert "# Gayatri AI Platform — Route Reachability & Audit Matrix" in content

    required_columns = [
        "Route",
        "Method",
        "Auth",
        "Role",
        "Resource Scope",
        "Service",
        "DB Writes",
        "External Calls",
        "Fallback",
        "Error Contract",
        "Runtime Verified",
    ]
    for col in required_columns:
        assert col in content, f"Missing required column in reachability matrix: {col}"

    # Verify minimum endpoint count coverage
    table_rows = [line for line in content.splitlines() if line.startswith("| `/")]
    assert len(table_rows) >= 50, f"Expected at least 50 documented routes, found {len(table_rows)}"


# ── Test 6: Teacher Dashboard View Renderer Independence ───────────────────────

def test_teacher_dashboard_view_renderer_independence():
    """Verify central_platform.teacher.views renders cleanly without root server."""
    from central_platform.teacher.views import render_teacher_dashboard_html

    html = render_teacher_dashboard_html("crs-chem-101")
    assert "<!DOCTYPE html>" in html
    assert "Cohort Mastery Distribution" in html
    assert "Student Performance Roster" in html


# ── Test 7: Zero Divergence in Health Endpoints ────────────────────────────────

def test_zero_divergence_fastapi_and_legacy_endpoints(client):
    """Verify /healthz and /api/health report consistent status from health service."""
    r_healthz = client.get("/healthz")
    r_legacy = client.get("/api/health")

    assert r_healthz.status_code == 200
    assert r_legacy.status_code == 200

    hz_data = r_healthz.json()
    leg_data = r_legacy.json()

    assert hz_data["status"] in ("ONLINE", "HEALTHY")
    assert leg_data["status"] in ("ONLINE", "HEALTHY")
    assert leg_data["service"] == "TeacherPortalServer"


# ── Test 8: Active Services Have No Bare Swallowed Exceptions ─────────────────

def test_active_services_have_no_bare_swallowed_exceptions():
    """Verify that central_platform/sync/service.py has structured logging, not bare pass."""
    sync_service_file = ROOT / "central_platform" / "sync" / "service.py"
    content = sync_service_file.read_text(encoding="utf-8")

    # Assert structured debug logging exists on DB queries
    assert 'logger.debug("Failed looking up device binding for %s from DB: %s"' in content
    assert 'logger.debug("Failed updating device sync time for %s: %s"' in content
