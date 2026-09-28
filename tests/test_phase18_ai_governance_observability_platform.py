"""Phase 18 — AI Governance & Observability Platform Tests.

Verifies:
1. Granular telemetry logging (request_id, student/course scope, task type, token counts, latency, cost, status, fallback).
2. Privacy invariant (cryptographic prompt hash stored, no raw prompt text stored in logs).
3. Aggregated observability metrics and cost attribution.
4. Budget management and threshold alert triggers.
5. Circuit breaker state monitoring and administrative reset.
6. Model allowlist lifecycle and enforcement.
7. REST API endpoints on /api/v1/ai/observability and /api/v1/ai/governance.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from central_platform.ai.gateway import AIGatewayService
from central_platform.ai.governance import AIGovernanceService
from central_platform.ai.policy_engine import CircuitState
from central_platform.ai.schema import (
    AIExecutionRequest,
    ModelTier,
    ProviderConfig,
    ProviderType,
    TaskType,
)
from central_platform.api.app import app
from central_platform.db import PlatformDatabase


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_setup():
    db = PlatformDatabase(":memory:")
    gateway = AIGatewayService(db=db)
    governance = AIGovernanceService(gateway=gateway, db=db)
    return gateway, governance, db


# ── 1. Telemetry Logging & Privacy Invariant ──────────────────────────────

def test_telemetry_logging_and_privacy_invariant(test_setup):
    gateway, governance, db = test_setup

    req = AIExecutionRequest(
        prompt="Explain Gibbs free energy Delta G = Delta H - T * Delta S in detail",
        task_type=TaskType.TUTORING,
        student_id="std-chem-99",
        course_id="crs-chem-101",
        session_id="ses-1001",
    )

    res = gateway.execute(req)
    assert res.success is True

    # Retrieve logged execution
    logs = governance.get_execution_logs(student_id="std-chem-99")
    assert len(logs) == 1
    log = logs[0]

    # Verify telemetry attributes
    assert log["student_id"] == "std-chem-99"
    assert log["course_id"] == "crs-chem-101"
    assert log["session_id"] == "ses-1001"
    assert log["task_type"] == "tutoring"
    assert log["prompt_tokens"] > 0
    assert log["completion_tokens"] > 0
    assert log["status"] == "SUCCESS"
    assert log["latency_ms"] > 0.0

    # Verify Privacy Invariant: prompt_hash exists and raw prompt is NOT stored in DB record
    assert log["prompt_hash"] != ""
    assert len(log["prompt_hash"]) == 16
    assert "Gibbs free energy" not in str(log)


# ── 2. Observability Metrics & Cost Attribution ───────────────────────────

def test_observability_metrics_aggregation(test_setup):
    gateway, governance, db = test_setup

    # Execute multiple workloads across tasks and students
    for i in range(3):
        gateway.execute(
            AIExecutionRequest(
                prompt=f"Chemistry concept prompt {i}",
                task_type=TaskType.TUTORING,
                student_id="student-a",
                course_id="crs-chem-101",
            )
        )

    gateway.execute(
        AIExecutionRequest(
            prompt="Grade student response on thermodynamics",
            task_type=TaskType.ASSESSMENT_GRADING,
            student_id="student-b",
            course_id="crs-chem-101",
        )
    )

    metrics = governance.get_observability_metrics()
    assert metrics["total_requests"] == 4
    assert metrics["successful_requests"] == 4
    assert metrics["success_rate"] == 1.0
    assert metrics["total_tokens"] > 0
    assert "tutoring" in metrics["tasks_breakdown"]
    assert "assessment_grading" in metrics["tasks_breakdown"]
    assert metrics["tasks_breakdown"]["tutoring"]["count"] == 3
    assert metrics["tasks_breakdown"]["assessment_grading"]["count"] == 1


# ── 3. Budget Management & Threshold Alerts ───────────────────────────────

def test_budget_management_and_alerts(test_setup):
    gateway, governance, db = test_setup

    # Initial state
    b_status = governance.get_budget_status()
    assert b_status["daily_budget_usd"] == 100.0
    assert b_status["budget_alert"] is False

    # Update budget limit
    updated = governance.set_budget(10.0)
    assert updated["daily_budget_usd"] == 10.0

    # Simulate spend near threshold (e.g. $8.50 on $10.00 budget)
    gateway.policy_engine.daily_spend_usd = 8.50
    alert_status = governance.get_budget_status()
    assert alert_status["percentage_used"] == 85.0
    assert alert_status["budget_alert"] is True
    assert alert_status["budget_exceeded"] is False

    # Simulate budget exceeded ($10.50 on $10.00 budget)
    gateway.policy_engine.daily_spend_usd = 10.50
    exceeded_status = governance.get_budget_status()
    assert exceeded_status["budget_exceeded"] is True


# ── 4. Circuit Breaker Observability & Reset ──────────────────────────────

def test_circuit_breaker_monitoring_and_manual_reset(test_setup):
    gateway, governance, db = test_setup

    cb = gateway.policy_engine.get_circuit_breaker("openai")
    cb.failure_threshold = 2
    cb.record_failure()
    cb.record_failure()

    # Breaker should be OPEN
    assert cb.state == CircuitState.OPEN
    statuses = governance.get_circuit_breaker_statuses()
    assert "openai" in statuses
    assert statuses["openai"]["state"] == "OPEN"
    assert statuses["openai"]["can_execute"] is False

    # Administrative reset
    reset_ok = governance.reset_circuit_breaker("openai")
    assert reset_ok is True
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


# ── 5. Model Allowlist Management & Enforcement ───────────────────────────

def test_model_allowlist_enforcement(test_setup):
    gateway, governance, db = test_setup

    # Empty allowlist allows any registered model
    assert governance.get_model_allowlist() == []

    # Restrict allowlist to only Qwen2.5-3B-Instruct-Q4_K_M
    governance.set_model_allowlist(["Qwen2.5-3B-Instruct-Q4_K_M"])
    assert "Qwen2.5-3B-Instruct-Q4_K_M" in governance.get_model_allowlist()

    # Request targeting allowed model succeeds
    req_ok = AIExecutionRequest(
        prompt="Explain reaction kinetics",
        preferred_model="Qwen2.5-3B-Instruct-Q4_K_M",
    )
    res_ok = gateway.execute(req_ok)
    assert res_ok.success is True

    # Request targeting non-allowlisted model is rejected by policy
    req_blocked = AIExecutionRequest(
        prompt="Explain quantum mechanics",
        preferred_provider="mock_engine",
        preferred_model="unapproved-experimental-model",
    )
    res_blocked = gateway.execute(req_blocked)
    assert res_blocked.success is False
    assert "MODEL_NOT_ALLOWED" in res_blocked.error_message


# ── 6. REST API Endpoints Verification ───────────────────────────────────

def test_observability_api_endpoints(client):
    # 1. Execute a generation to produce telemetry
    client.post(
        "/api/v1/ai/execute",
        json={"prompt": "Explain chemical equilibrium constant Kc", "task_type": "tutoring"},
    )

    # 2. Get Observability Metrics
    resp = client.get("/api/v1/ai/observability/metrics")
    assert resp.status_code == 200
    metrics = resp.json()["data"]
    assert "total_requests" in metrics
    assert "total_tokens" in metrics
    assert "gateway_status" in metrics

    # 3. Get Telemetry Logs
    resp = client.get("/api/v1/ai/observability/logs?limit=5")
    assert resp.status_code == 200
    logs = resp.json()["data"]
    assert len(logs) >= 1
    assert "prompt_hash" in logs[0]

    # 4. Get Budget Status
    resp = client.get("/api/v1/ai/governance/budgets")
    assert resp.status_code == 200
    assert resp.json()["data"]["daily_budget_usd"] > 0

    # 5. Update Budget
    resp = client.put("/api/v1/ai/governance/budgets", json={"daily_budget_usd": 75.0})
    assert resp.status_code == 200
    assert resp.json()["data"]["daily_budget_usd"] == 75.0

    # 6. Get Circuit Breakers
    resp = client.get("/api/v1/ai/governance/circuit-breakers")
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], dict)

    # 7. Model Allowlist Endpoints
    resp = client.post("/api/v1/ai/governance/allowlist", json={"models": ["model-a", "model-b"]})
    assert resp.status_code == 200
    assert "model-a" in resp.json()["data"]

    resp = client.delete("/api/v1/ai/governance/allowlist/model-a")
    assert resp.status_code == 200
    assert "model-a" not in resp.json()["data"]

    # Clear allowlist
    client.post("/api/v1/ai/governance/allowlist", json={"models": []})

    # 8. Cost Breakdown Endpoint
    resp = client.get("/api/v1/ai/governance/cost-breakdown")
    assert resp.status_code == 200
    assert "providers" in resp.json()["data"]
    assert "tasks" in resp.json()["data"]
