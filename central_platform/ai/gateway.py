"""Gayatri AI Platform — Unified AI Gateway Service (Phase 17).

Coordinates context building, policy enforcement, model routing, adapter dispatching,
circuit breaking, automated failover, and telemetry logging.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.ai.adapters import (
    AnthropicAdapter,
    BaseAIProviderAdapter,
    GeminiAdapter,
    LocalGGUFAdapter,
    MockAIAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)
from central_platform.ai.context_builder import ContextBuilder
from central_platform.ai.model_router import ModelRouter
from central_platform.ai.policy_engine import PolicyEngine
from central_platform.ai.schema import (
    AIExecutionRequest,
    AIExecutionResult,
    AIModelDescriptor,
    ModelTier,
    ProviderConfig,
    ProviderType,
    RoutingDecision,
    TaskType,
)
from central_platform.db import PlatformDatabase
from central_platform.models.schema import AIExecutionLog

logger = logging.getLogger("gayatri.central_platform.ai.gateway")


class AIGatewayService:
    """Authoritative singleton service managing provider-neutral AI execution."""

    def __init__(self, db: Optional[PlatformDatabase] = None):
        self.db = db or PlatformDatabase()
        self.policy_engine = PolicyEngine()
        self.router = ModelRouter()
        self.adapters: Dict[str, BaseAIProviderAdapter] = {}
        self._init_default_providers()

    def _init_default_providers(self) -> None:
        """Register default provider configurations and adapters."""
        # 1. Local GGUF / SLM
        local_cfg = ProviderConfig(
            provider_name="local_llama",
            provider_type=ProviderType.LOCAL_GGUF,
            priority=1,
            rate_limit_rpm=600,
            daily_budget_usd=100.0,
            models=[
                AIModelDescriptor(
                    model_id="qwen-2.5-3b",
                    model_name="Qwen2.5-3B-Instruct-Q4_K_M",
                    tier=ModelTier.TIER_3_FAST,
                    context_window=8192,
                    latency_p50_ms=45.0,
                ),
                AIModelDescriptor(
                    model_id="llama-3.2-3b",
                    model_name="Llama-3.2-3B-Instruct-Q4_K_M",
                    tier=ModelTier.TIER_3_FAST,
                    context_window=8192,
                    latency_p50_ms=50.0,
                ),
            ],
        )

        # 2. OpenAI
        openai_cfg = ProviderConfig(
            provider_name="openai",
            provider_type=ProviderType.OPENAI,
            api_key_ref="OPENAI_API_KEY",
            priority=2,
            rate_limit_rpm=300,
            daily_budget_usd=50.0,
            fallback_provider="local_llama",
            models=[
                AIModelDescriptor(
                    model_id="gpt-4o",
                    model_name="gpt-4o",
                    tier=ModelTier.TIER_1_HEAVY,
                    cost_per_1k_input_usd=0.005,
                    cost_per_1k_output_usd=0.015,
                ),
                AIModelDescriptor(
                    model_id="gpt-4o-mini",
                    model_name="gpt-4o-mini",
                    tier=ModelTier.TIER_2_STANDARD,
                    cost_per_1k_input_usd=0.00015,
                    cost_per_1k_output_usd=0.0006,
                ),
            ],
        )

        # 3. Google Gemini
        gemini_cfg = ProviderConfig(
            provider_name="gemini",
            provider_type=ProviderType.GEMINI,
            api_key_ref="GEMINI_API_KEY",
            priority=3,
            rate_limit_rpm=300,
            daily_budget_usd=50.0,
            fallback_provider="local_llama",
            models=[
                AIModelDescriptor(
                    model_id="gemini-2.0-flash",
                    model_name="gemini-2.0-flash",
                    tier=ModelTier.TIER_2_STANDARD,
                    cost_per_1k_input_usd=0.0001,
                    cost_per_1k_output_usd=0.0004,
                ),
            ],
        )

        # 4. Mock Engine (Fallback safety net)
        mock_cfg = ProviderConfig(
            provider_name="mock_engine",
            provider_type=ProviderType.MOCK,
            priority=99,
            rate_limit_rpm=10000,
            daily_budget_usd=1000.0,
            models=[
                AIModelDescriptor(
                    model_id="mock-standard",
                    model_name="Mock-Pedagogical-Engine",
                    tier=ModelTier.TIER_2_STANDARD,
                ),
            ],
        )

        for cfg in [local_cfg, openai_cfg, gemini_cfg, mock_cfg]:
            self.register_provider(cfg)

    def register_provider(self, config: ProviderConfig) -> None:
        """Register provider config and instantiate matching adapter."""
        self.router.register_provider(config)
        if config.provider_type == ProviderType.OPENAI:
            self.adapters[config.provider_name] = OpenAIAdapter(config)
        elif config.provider_type == ProviderType.ANTHROPIC:
            self.adapters[config.provider_name] = AnthropicAdapter(config)
        elif config.provider_type == ProviderType.GEMINI:
            self.adapters[config.provider_name] = GeminiAdapter(config)
        elif config.provider_type == ProviderType.OPENROUTER:
            self.adapters[config.provider_name] = OpenRouterAdapter(config)
        elif config.provider_type == ProviderType.LOCAL_GGUF:
            self.adapters[config.provider_name] = LocalGGUFAdapter(config)
        else:
            self.adapters[config.provider_name] = MockAIAdapter(config)

    def execute(self, request: AIExecutionRequest) -> AIExecutionResult:
        """Execute AI request through the complete Gateway pipeline."""
        req_id = request.request_id or f"req-agy-{hashlib.sha256(f'{time.time()}:{request.prompt}'.encode()).hexdigest()[:12]}"
        request.request_id = req_id

        # 1. Build Context
        enriched_system_prompt = ContextBuilder.build_system_prompt(
            base_prompt=request.system_prompt,
            teacher_directives=request.teacher_directives,
        )
        enriched_user_prompt = ContextBuilder.build_user_prompt(
            user_query=request.prompt,
            rag_context=request.rag_context,
        )
        exec_req = AIExecutionRequest(
            prompt=enriched_user_prompt,
            system_prompt=enriched_system_prompt,
            task_type=request.task_type,
            student_id=request.student_id,
            session_id=request.session_id,
            course_id=request.course_id,
            preferred_model=request.preferred_model,
            preferred_provider=request.preferred_provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stop_sequences=request.stop_sequences,
            timeout_seconds=request.timeout_seconds,
            request_id=req_id,
        )

        # 2. Model Routing Decision
        routing: RoutingDecision = self.router.route(
            task_type=request.task_type,
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
        )

        # 3. Execution with Fallback Chain
        providers_to_try = [routing.target_provider] + routing.fallback_chain
        if "mock_engine" not in providers_to_try and "mock_engine" in self.adapters:
            providers_to_try.append("mock_engine")

        last_error = None
        for idx, p_name in enumerate(providers_to_try):
            p_config = self.router.providers.get(p_name)
            if not p_config or not p_config.enabled:
                continue

            adapter = self.adapters.get(p_name)
            if not adapter:
                continue

            # Select model descriptor
            model_desc = self._resolve_model_descriptor(p_config, routing.target_model)

            # 4. Policy Engine Check
            allowed, reason = self.policy_engine.validate_execution(
                provider_name=p_name,
                model_name=model_desc.model_name,
                caller_id=request.student_id or "anonymous",
            )

            if not allowed:
                # If kill switch is global, do not try other providers
                if self.policy_engine.global_kill_switch:
                    return AIExecutionResult(
                        request_id=req_id,
                        content="",
                        provider=p_name,
                        model=model_desc.model_name,
                        success=False,
                        error_class="PolicyViolation",
                        error_message=reason,
                    )
                last_error = reason
                continue

            # 5. Dispatch to Adapter
            cb = self.policy_engine.get_circuit_breaker(p_name)
            try:
                result = adapter.execute(exec_req, model_desc)
                if result.success:
                    cb.record_success()
                    self.policy_engine.record_spend(result.estimated_cost_usd)
                    if idx > 0:
                        result.fallback_used = True
                        result.original_provider = routing.target_provider

                    self._log_execution(result)
                    return result
                else:
                    cb.record_failure()
                    last_error = result.error_message or "Execution failed"
            except Exception as err:
                cb.record_failure()
                last_error = str(err)
                logger.warning(f"Provider {p_name} execution error: {err}")

        # All providers failed
        return AIExecutionResult(
            request_id=req_id,
            content="",
            provider=routing.target_provider,
            model=routing.target_model,
            success=False,
            error_class="AllProvidersFailed",
            error_message=f"All configured providers failed. Last error: {last_error}",
        )

    def _resolve_model_descriptor(self, p_config: ProviderConfig, target_model: str) -> AIModelDescriptor:
        for m in p_config.models:
            if m.model_name == target_model or m.model_id == target_model:
                return m
        if p_config.models:
            return p_config.models[0]
        return AIModelDescriptor(model_id="default", model_name=target_model)

    def _log_execution(self, result: AIExecutionResult) -> None:
        """Record execution metrics to the database."""
        try:
            log_entry = AIExecutionLog(
                id=f"log-{result.request_id}",
                model_id=f"{result.provider}:{result.model}",
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                latency_ms=result.latency_ms,
                status="SUCCESS" if result.success else "FAILED",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self.db.record_ai_execution_log(log_entry)
        except Exception as exc:
            logger.debug(f"Failed to record AI execution log: {exc}")

    def get_status(self) -> Dict[str, Any]:
        """Return real-time AI Gateway status and metrics."""
        enabled_providers = [p.provider_name for p in self.router.providers.values() if p.enabled]
        active_provider = enabled_providers[0] if enabled_providers else "none"
        active_model = (
            self.router.providers[active_provider].models[0].model_name
            if active_provider in self.router.providers and self.router.providers[active_provider].models
            else "none"
        )
        remaining_budget = max(0.0, round(self.policy_engine.daily_budget_usd - self.policy_engine.daily_spend_usd, 2))

        return {
            "gateway_status": "DEGRADED" if self.policy_engine.global_kill_switch else "HEALTHY",
            "active_provider": active_provider,
            "active_model": active_model,
            "available_providers": enabled_providers,
            "token_usage_today": int(self.policy_engine.daily_spend_usd * 10000),  # Representative count
            "budget_remaining_usd": remaining_budget,
            "kill_switch_active": self.policy_engine.global_kill_switch,
        }
