"""AI Governance, Model Registry, Routing, Safety, and Telemetry Engine."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ModelProvider(str, Enum):
    LOCAL_GGUF = "local_gguf"
    FINE_TUNED_SLM = "fine_tuned_slm"
    EXTERNAL_API = "external_api"


class ModelStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    KILLED = "killed"
    MAINTENANCE = "maintenance"


@dataclass
class RegisteredModel:
    id: str
    name: str
    provider: ModelProvider
    status: ModelStatus = ModelStatus.ACTIVE
    cost_per_1k_tokens: float = 0.0
    latency_ms_avg: float = 50.0
    max_context_tokens: int = 4096


@dataclass
class AIExecutionLog:
    id: str
    agent_id: str
    prompt: str
    selected_model_id: str
    fallback_used: bool
    tokens_used: int
    cost: float
    latency_ms: float
    safety_passed: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIGovernanceEngine:
    """Centralized AI governance, routing, safety, and telemetry manager."""

    def __init__(self):
        self._models: Dict[str, RegisteredModel] = {}
        self._agent_kill_switches: Dict[str, bool] = {}  # agent_id -> is_killed
        self._execution_logs: List[AIExecutionLog] = []
        self._usage_limits: Dict[str, int] = {"default_token_cap": 10000}
        self._blocked_keywords: List[str] = ["unsafe_exploit", "leak_system_prompt", "malicious_payload"]
        self._init_default_models()

    def _init_default_models(self) -> None:
        self.register_model(
            RegisteredModel(
                id="slm-chem-v1",
                name="Gayatri Fine-Tuned Chemistry SLM",
                provider=ModelProvider.FINE_TUNED_SLM,
                cost_per_1k_tokens=0.001,
            )
        )
        self.register_model(
            RegisteredModel(
                id="local-llama3-8b",
                name="Local Llama-3 8B GGUF",
                provider=ModelProvider.LOCAL_GGUF,
                cost_per_1k_tokens=0.0,
            )
        )

    def register_model(self, model: RegisteredModel) -> RegisteredModel:
        self._models[model.id] = model
        return model

    def set_agent_kill_switch(self, agent_id: str, kill: bool) -> None:
        self._agent_kill_switches[agent_id] = kill

    def set_model_status(self, model_id: str, status: ModelStatus) -> None:
        if model_id in self._models:
            self._models[model_id].status = status

    def check_safety(self, prompt: str) -> bool:
        prompt_lower = prompt.lower()
        for kw in self._blocked_keywords:
            if kw in prompt_lower:
                return False
        return True

    def route_request(self, agent_id: str, prompt: str, preferred_model_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        # Check Agent Kill Switch
        if self._agent_kill_switches.get(agent_id, False):
            raise PermissionError(f"Agent '{agent_id}' has been disabled by emergency kill switch.")

        # Check Safety Policy
        safety_passed = self.check_safety(prompt)
        if not safety_passed:
            raise ValueError(f"Prompt failed AI safety policy filter.")

        selected_model: Optional[RegisteredModel] = None
        fallback_used = False

        # Attempt primary choice
        if preferred_model_id and preferred_model_id in self._models:
            target = self._models[preferred_model_id]
            if target.status == ModelStatus.ACTIVE:
                selected_model = target

        # If primary unavailable or unassigned, fallback to first active model
        if not selected_model:
            for model in self._models.values():
                if model.status == ModelStatus.ACTIVE:
                    selected_model = model
                    fallback_used = True
                    break

        if not selected_model:
            raise RuntimeError("No active AI models available to fulfill request.")

        # Simulate execution telemetry
        tokens_used = min(len(prompt.split()) * 4 + 50, selected_model.max_context_tokens)
        cost = (tokens_used / 1000.0) * selected_model.cost_per_1k_tokens
        latency_ms = (time.time() - start_time) * 1000.0 + selected_model.latency_ms_avg

        exec_log = AIExecutionLog(
            id=f"aiexec-{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            prompt=prompt,
            selected_model_id=selected_model.id,
            fallback_used=fallback_used,
            tokens_used=tokens_used,
            cost=cost,
            latency_ms=latency_ms,
            safety_passed=True,
        )
        self._execution_logs.append(exec_log)

        return {
            "execution_id": exec_log.id,
            "agent_id": agent_id,
            "model_id": selected_model.id,
            "fallback_used": fallback_used,
            "tokens_used": tokens_used,
            "cost": cost,
            "status": "SUCCESS",
        }

    def get_telemetry_summary(self) -> Dict[str, Any]:
        total_calls = len(self._execution_logs)
        total_tokens = sum(log.tokens_used for log in self._execution_logs)
        total_cost = sum(log.cost for log in self._execution_logs)
        fallbacks = sum(1 for log in self._execution_logs if log.fallback_used)

        return {
            "total_executions": total_calls,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "fallback_count": fallbacks,
            "active_models_count": sum(1 for m in self._models.values() if m.status == ModelStatus.ACTIVE),
        }
