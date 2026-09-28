"""Gayatri AI Platform — AI Model Router (Phase 17).

Intelligently routes requests to optimal providers and models based on task type,
performance tier, cost constraints, and available fallback chains.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from central_platform.ai.schema import (
    AIModelDescriptor,
    ModelTier,
    ProviderConfig,
    RoutingDecision,
    TaskType,
)


class ModelRouter:
    """Selects the best provider and model for a given AI workload."""

    TASK_TIER_MAPPING: Dict[TaskType, ModelTier] = {
        TaskType.TUTORING: ModelTier.TIER_2_STANDARD,
        TaskType.ASSESSMENT_GRADING: ModelTier.TIER_1_HEAVY,
        TaskType.COPILOT_SUMMARY: ModelTier.TIER_2_STANDARD,
        TaskType.INTERVENTION_RECOMMENDATION: ModelTier.TIER_2_STANDARD,
        TaskType.INTENT_CLASSIFICATION: ModelTier.TIER_3_FAST,
        TaskType.GENERAL: ModelTier.TIER_2_STANDARD,
    }

    def __init__(self, providers: Optional[Dict[str, ProviderConfig]] = None):
        self.providers: Dict[str, ProviderConfig] = providers or {}

    def register_provider(self, config: ProviderConfig) -> None:
        self.providers[config.provider_name] = config

    def route(
        self,
        task_type: TaskType,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> RoutingDecision:
        """Determine target provider, model, and fallback chain."""
        # 1. If explicit provider and model requested and available
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.enabled:
                target_model = preferred_model or (provider.models[0].model_name if provider.models else "default-model")
                fallback = [provider.fallback_provider] if provider.fallback_provider else []
                return RoutingDecision(
                    task_type=task_type,
                    target_provider=provider.provider_name,
                    target_model=target_model,
                    target_tier=ModelTier.TIER_2_STANDARD,
                    fallback_chain=[f for f in fallback if f and f in self.providers],
                    rationale=f"Explicitly requested provider '{preferred_provider}'.",
                )

        # 2. Determine target tier based on task
        target_tier = self.TASK_TIER_MAPPING.get(task_type, ModelTier.TIER_2_STANDARD)

        # 3. Search enabled providers sorted by priority
        sorted_providers = sorted(
            [p for p in self.providers.values() if p.enabled],
            key=lambda x: x.priority,
        )

        target_p: Optional[ProviderConfig] = None
        target_m: Optional[AIModelDescriptor] = None

        # Look for matching model in preferred tier
        for p in sorted_providers:
            for m in p.models:
                if m.tier == target_tier:
                    target_p = p
                    target_m = m
                    break
            if target_p:
                break

        # Fallback to any enabled provider if exact tier not found
        if not target_p and sorted_providers:
            target_p = sorted_providers[0]
            target_m = target_p.models[0] if target_p.models else AIModelDescriptor(
                model_id="default",
                model_name="default",
                tier=ModelTier.TIER_2_STANDARD,
            )

        if not target_p:
            # Fallback default provider descriptor
            return RoutingDecision(
                task_type=task_type,
                target_provider="mock_engine",
                target_model="mock-default-model",
                target_tier=target_tier,
                fallback_chain=[],
                rationale="No enabled providers found; defaulting to mock engine.",
            )

        # Build fallback chain from other active providers
        fallback_chain = [
            p.provider_name for p in sorted_providers
            if p.provider_name != target_p.provider_name
        ]

        return RoutingDecision(
            task_type=task_type,
            target_provider=target_p.provider_name,
            target_model=target_m.model_name if target_m else "default",
            target_tier=target_tier,
            fallback_chain=fallback_chain,
            rationale=f"Routed to '{target_p.provider_name}' ({target_m.model_name if target_m else 'default'}) for tier {target_tier.value}.",
        )
