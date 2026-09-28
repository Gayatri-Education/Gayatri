"""Phase 17 — Real AI Gateway + Model Router Platform Tests.

Verifies:
1. Provider-neutral execution layer across multi-provider adapters (OpenAI, Anthropic, Gemini, Local GGUF, Mock).
2. Task-based intelligent model routing (Tutoring, Assessment Grading, Copilot, Intent Classification).
3. Context builder (system prompt, teacher directives, RAG context).
4. Policy engine:
   - Global AI kill switch
   - Per-provider kill switch
   - Daily budget limit enforcement
   - Rate limiting (RPM)
   - Circuit breaker tripping and state recovery
5. Automated fallback chain execution when primary provider fails or is disabled.
6. REST API endpoints on /api/v1/ai.
"""
from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from central_platform.ai.context_builder import ContextBuilder
from central_platform.ai.gateway import AIGatewayService
from central_platform.ai.model_router import ModelRouter
from central_platform.ai.policy_engine import CircuitState, PolicyEngine
from central_platform.ai.schema import (
    AIExecutionRequest,
    AIModelDescriptor,
    ModelTier,
    ProviderConfig,
    ProviderType,
    TaskType,
)
from central_platform.api.app import app
from central_platform.auth.dependencies import get_db
from central_platform.db import PlatformDatabase


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_gateway():
    db = PlatformDatabase(":memory:")
    return AIGatewayService(db=db)


# ── 1. Provider Adapter Execution ──────────────────────────────────────────

def test_mock_and_local_adapter_execution(test_gateway):
    # Test Tutoring prompt
    req = AIExecutionRequest(
        prompt="Explain the first law of thermodynamics with mathematical formula",
        task_type=TaskType.TUTORING,
    )
    res = test_gateway.execute(req)
    assert res.success is True
    assert "Delta U = q + w" in res.content
    assert res.prompt_tokens > 0
    assert res.completion_tokens > 0
    assert res.latency_ms > 0.0


def test_chemistry_enthalpy_generation(test_gateway):
    req = AIExecutionRequest(
        prompt="Define enthalpy change in exothermic reactions",
        task_type=TaskType.TUTORING,
    )
    res = test_gateway.execute(req)
    assert res.success is True
    assert "Delta H < 0" in res.content or "exothermic" in res.content.lower()


# ── 2. Context Builder ────────────────────────────────────────────────────

def test_context_builder_combines_directives_and_rag():
    directives = ["Enforce Socratic questioning only", "Do not give final answer on first turn"]
    rag_data = '<rag_evidence_data chunk_id="chk-01">Delta U = q + w</rag_evidence_data>'

    sys_prompt = ContextBuilder.build_system_prompt(
        teacher_directives=directives,
        subject="Chemistry",
    )
    assert "SUBJECT SCOPE: Chemistry" in sys_prompt
    assert "ACTIVE TEACHER DIRECTIVES" in sys_prompt
    assert "Enforce Socratic questioning" in sys_prompt

    user_prompt = ContextBuilder.build_user_prompt(
        user_query="How to calculate work?",
        rag_context=rag_data,
    )
    assert '<rag_evidence_data chunk_id="chk-01">' in user_prompt
    assert "Student Query: How to calculate work?" in user_prompt


# ── 3. Model Router & Tier Routing ────────────────────────────────────────

def test_model_router_task_tier_mapping(test_gateway):
    router = test_gateway.router

    # Tutoring should map to Tier 2 Standard or Tier 3 Fast
    d_tutor = router.route(TaskType.TUTORING)
    assert d_tutor.target_tier in [ModelTier.TIER_2_STANDARD, ModelTier.TIER_3_FAST]

    # Assessment grading should map to Tier 1 Heavy
    d_grade = router.route(TaskType.ASSESSMENT_GRADING)
    assert d_grade.target_tier in [ModelTier.TIER_1_HEAVY, ModelTier.TIER_2_STANDARD]

    # Intent classification should map to Tier 3 Fast
    d_intent = router.route(TaskType.INTENT_CLASSIFICATION)
    assert d_intent.target_tier == ModelTier.TIER_3_FAST


# ── 4. Policy Engine & Guardrails ─────────────────────────────────────────

def test_global_kill_switch(test_gateway):
    test_gateway.policy_engine.global_kill_switch = True

    req = AIExecutionRequest(prompt="Hello tutor", task_type=TaskType.GENERAL)
    res = test_gateway.execute(req)

    assert res.success is False
    assert "GLOBAL_KILL_SWITCH_ACTIVE" in res.error_message


def test_provider_kill_switch_triggers_fallback(test_gateway):
    # Disable local_llama provider
    test_gateway.policy_engine.provider_kill_switches["local_llama"] = True

    req = AIExecutionRequest(
        prompt="Explain calculus derivative of x^2",
        task_type=TaskType.TUTORING,
    )
    res = test_gateway.execute(req)

    # Should succeed via fallback provider (e.g. openai/gemini/mock_engine)
    assert res.success is True
    assert res.fallback_used is True or res.provider != "local_llama"
    assert "2x" in res.content


def test_daily_budget_limit_enforcement():
    engine = PolicyEngine()
    engine.daily_budget_usd = 1.00
    engine.daily_spend_usd = 0.95

    # Request requiring 0.10 USD should fail
    allowed, reason = engine.validate_execution("openai", "gpt-4o", estimated_cost=0.10)
    assert allowed is False
    assert "BUDGET_EXCEEDED" in reason


def test_rate_limiter_rpm():
    engine = PolicyEngine()
    engine.default_rate_limit_rpm = 3
    caller = "student-test-101"

    # Execute 3 calls
    for _ in range(3):
        allowed, _ = engine.validate_execution("mock", "model", caller_id=caller)
        assert allowed is True

    # 4th call should exceed rate limit
    allowed, reason = engine.validate_execution("mock", "model", caller_id=caller)
    assert allowed is False
    assert "RATE_LIMIT_EXCEEDED" in reason


def test_circuit_breaker_tripping_and_recovery():
    engine = PolicyEngine()
    cb = engine.get_circuit_breaker("openai")
    cb.failure_threshold = 3
    cb.recovery_timeout_seconds = 0.1

    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    # 3rd failure trips breaker
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # After recovery timeout
    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success closes breaker
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


# ── 5. REST API Endpoints Verification ───────────────────────────────────

def test_ai_status_endpoint(client):
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["gateway_status"] in ["HEALTHY", "DEGRADED"]
    assert len(data["available_providers"]) >= 1


def test_ai_execution_endpoint(client):
    resp = client.post(
        "/api/v1/ai/execute",
        json={
            "prompt": "What is the formula for internal energy change Delta U?",
            "task_type": "tutoring",
            "temperature": 0.5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert data["total_tokens"] > 0
    assert "Delta U" in data["content"] or "thermodynamics" in data["content"].lower()


def test_ai_provider_management_and_toggle(client):
    # 1. List Providers
    resp = client.get("/api/v1/ai/providers")
    assert resp.status_code == 200
    providers = resp.json()["data"]
    assert len(providers) >= 1

    # 2. Toggle Provider Off
    resp = client.post("/api/v1/ai/providers/local_llama/toggle?enabled=false")
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False

    # 3. Toggle Provider On
    resp = client.post("/api/v1/ai/providers/local_llama/toggle?enabled=true")
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is True


def test_ai_killswitch_endpoint(client):
    # Toggle Kill Switch ON
    resp = client.post("/api/v1/ai/killswitch", json={"enabled": True, "reason": "Emergency maintenance"})
    assert resp.status_code == 200
    assert resp.json()["data"]["global_kill_switch_active"] is True

    # Execution should fail when kill switch active
    exec_resp = client.post("/api/v1/ai/execute", json={"prompt": "Test prompt"})
    assert exec_resp.json()["ok"] is False

    # Toggle Kill Switch OFF
    resp = client.post("/api/v1/ai/killswitch", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["global_kill_switch_active"] is False


def test_ai_route_preview_endpoint(client):
    resp = client.post(
        "/api/v1/ai/route",
        json={"task_type": "assessment_grading"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["task_type"] == "assessment_grading"
    assert "target_provider" in data
    assert "target_model" in data
