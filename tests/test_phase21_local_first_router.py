"""Tests for Phase 21: Local-First Router.

Tests routing strategies:
- LOCAL_ONLY
- LOCAL_FIRST
- CLOUD_PREFERRED

Tests capability matching.
"""

import pytest
from central_platform.ai.model_router import ModelRouter
from central_platform.ai.schema import (
    AIModelDescriptor,
    ModelTier,
    ProviderConfig,
    ProviderType,
    RoutingStrategy,
    TaskType,
)

@pytest.fixture
def configured_router():
    router = ModelRouter()
    
    # 1. Local GGUF Provider
    local_p = ProviderConfig(
        provider_name="local_llama",
        provider_type=ProviderType.LOCAL_GGUF,
        priority=1,
        models=[
            AIModelDescriptor(
                model_id="llama-3.2-3b",
                model_name="Llama-3.2-3B-Instruct",
                tier=ModelTier.TIER_3_FAST,
                capabilities=["fast", "local", "reasoning"]
            )
        ]
    )
    
    # 2. Cloud OpenAI Provider
    cloud_p = ProviderConfig(
        provider_name="openai_cloud",
        provider_type=ProviderType.OPENAI,
        priority=2,
        models=[
            AIModelDescriptor(
                model_id="gpt-4o",
                model_name="GPT-4o",
                tier=ModelTier.TIER_1_HEAVY,
                capabilities=["math", "reasoning", "code", "multimodal"]
            )
        ]
    )
    
    router.register_provider(local_p)
    router.register_provider(cloud_p)
    return router

def test_routing_strategy_local_only(configured_router):
    """Test LOCAL_ONLY strategy forces routing to local provider."""
    decision = configured_router.route(
        task_type=TaskType.TUTORING,
        strategy=RoutingStrategy.LOCAL_ONLY
    )
    
    assert decision.target_provider == "local_llama"
    assert decision.target_model == "Llama-3.2-3B-Instruct"
    assert "openai_cloud" not in decision.fallback_chain

def test_routing_strategy_local_first(configured_router):
    """Test LOCAL_FIRST strategy prefers local provider first."""
    decision = configured_router.route(
        task_type=TaskType.TUTORING,
        strategy=RoutingStrategy.LOCAL_FIRST
    )
    
    assert decision.target_provider == "local_llama"
    assert "openai_cloud" in decision.fallback_chain

def test_routing_strategy_local_first_fallback_when_local_disabled(configured_router):
    """Test LOCAL_FIRST falls back to cloud provider when local provider is disabled."""
    configured_router.providers["local_llama"].enabled = False
    
    decision = configured_router.route(
        task_type=TaskType.TUTORING,
        strategy=RoutingStrategy.LOCAL_FIRST
    )
    
    assert decision.target_provider == "openai_cloud"

def test_routing_strategy_cloud_preferred(configured_router):
    """Test CLOUD_PREFERRED strategy prefers cloud provider over local."""
    decision = configured_router.route(
        task_type=TaskType.TUTORING,
        strategy=RoutingStrategy.CLOUD_PREFERRED
    )
    
    assert decision.target_provider == "openai_cloud"
    assert "local_llama" in decision.fallback_chain

def test_capability_matching(configured_router):
    """Test capability matching filters models that satisfy required capabilities."""
    # Model with required capability "math" (only GPT-4o has math)
    decision = configured_router.route(
        task_type=TaskType.TUTORING,
        strategy=RoutingStrategy.LOCAL_FIRST,
        required_capabilities=["math"]
    )
    
    assert decision.target_provider == "openai_cloud"
    assert decision.target_model == "GPT-4o"
