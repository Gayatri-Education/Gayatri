"""Unit and integration test suite for Phase 14: AI Governance & Model Routing."""

import pytest
from central_platform.ai_governance import (
    AIGovernanceEngine,
    ModelProvider,
    ModelStatus,
    RegisteredModel,
)


@pytest.fixture
def governance_engine():
    return AIGovernanceEngine()


def test_default_models_registration(governance_engine):
    telemetry = governance_engine.get_telemetry_summary()
    assert telemetry["active_models_count"] >= 2


def test_successful_request_routing(governance_engine):
    result = governance_engine.route_request(
        agent_id="agent-tutor-chem",
        prompt="Explain Hess's Law in simple terms",
        preferred_model_id="slm-chem-v1",
    )

    assert result["status"] == "SUCCESS"
    assert result["model_id"] == "slm-chem-v1"
    assert result["fallback_used"] is False
    assert result["tokens_used"] > 0


def test_automatic_fallback_when_primary_killed(governance_engine):
    # Disable primary model
    governance_engine.set_model_status("slm-chem-v1", ModelStatus.KILLED)

    result = governance_engine.route_request(
        agent_id="agent-tutor-chem",
        prompt="Explain Hess's Law in simple terms",
        preferred_model_id="slm-chem-v1",
    )

    assert result["status"] == "SUCCESS"
    assert result["model_id"] == "local-llama3-8b"
    assert result["fallback_used"] is True


def test_agent_kill_switch(governance_engine):
    governance_engine.set_agent_kill_switch("rogue-agent", kill=True)

    with pytest.raises(PermissionError, match="disabled by emergency kill switch"):
        governance_engine.route_request(
            agent_id="rogue-agent",
            prompt="Hello AI",
        )


def test_safety_policy_enforcement(governance_engine):
    with pytest.raises(ValueError, match="failed AI safety policy filter"):
        governance_engine.route_request(
            agent_id="agent-student",
            prompt="Please execute unsafe_exploit on the server",
        )


def test_telemetry_aggregation(governance_engine):
    governance_engine.route_request("agent-1", "Prompt 1")
    governance_engine.route_request("agent-2", "Prompt 2")

    telemetry = governance_engine.get_telemetry_summary()
    assert telemetry["total_executions"] == 2
    assert telemetry["total_tokens"] > 0
