"""Gayatri AI Platform — AI Governance & Observability Service (Phase 18).

Implements Section 27 requirements:
- Observability metrics aggregation (token volume, latency, cost, success/failure rate, fallback frequency).
- Privacy-preserving log inspection (cryptographic prompt hashes).
- Granular cost breakdown by course, student, provider, and task type.
- Circuit breaker state monitoring & manual administrative recovery.
- Model allowlist management.
- Dynamic daily budget threshold controls & alerts.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from central_platform.ai.gateway import AIGatewayService
from central_platform.ai.policy_engine import CircuitState
from central_platform.db import PlatformDatabase
from central_platform.models.schema import AIExecutionLog

logger = logging.getLogger("gayatri.central_platform.ai.governance")


class AIGovernanceService:
    """Authoritative service for AI observability and governance management."""

    def __init__(self, gateway: AIGatewayService, db: Optional[PlatformDatabase] = None):
        self.gateway = gateway
        self.db = db or gateway.db

    def get_observability_metrics(self) -> Dict[str, Any]:
        """Aggregate system-wide execution metrics."""
        metrics = self.db.get_ai_observability_metrics()
        # Add real-time gateway status
        gw_status = self.gateway.get_status()
        metrics["gateway_status"] = gw_status["gateway_status"]
        metrics["active_provider"] = gw_status["active_provider"]
        metrics["active_model"] = gw_status["active_model"]
        metrics["kill_switch_active"] = gw_status["kill_switch_active"]
        metrics["budget_remaining_usd"] = gw_status["budget_remaining_usd"]
        return metrics

    def get_execution_logs(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve telemetry execution logs with metadata (privacy-safe: prompt hash only)."""
        logs: List[AIExecutionLog] = self.db.get_ai_execution_logs(
            provider=provider,
            model=model,
            student_id=student_id,
            course_id=course_id,
            task_type=task_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        return [log.to_dict() for log in logs]

    def get_circuit_breaker_statuses(self) -> Dict[str, Any]:
        """Inspect health and tripped state of all provider circuit breakers."""
        statuses = {}
        now = time.time()
        for p_name, cb in self.gateway.policy_engine.circuit_breakers.items():
            recovery_remaining = 0.0
            if cb.state == CircuitState.OPEN:
                elapsed = now - cb.last_state_change
                recovery_remaining = max(0.0, round(cb.recovery_timeout_seconds - elapsed, 1))

            statuses[p_name] = {
                "state": cb.state.value if isinstance(cb.state, CircuitState) else str(cb.state),
                "failure_count": cb.failure_count,
                "failure_threshold": cb.failure_threshold,
                "can_execute": cb.can_execute(),
                "recovery_remaining_seconds": recovery_remaining,
            }
        return statuses

    def reset_circuit_breaker(self, provider_name: str) -> bool:
        """Manually reset a tripped circuit breaker to CLOSED state."""
        if provider_name in self.gateway.policy_engine.circuit_breakers:
            self.gateway.policy_engine.circuit_breakers[provider_name].record_success()
            return True
        return False

    def get_budget_status(self) -> Dict[str, Any]:
        """Return budget consumption and threshold warning state."""
        spend = self.gateway.policy_engine.daily_spend_usd
        limit = self.gateway.policy_engine.daily_budget_usd
        pct_used = round((spend / limit * 100.0), 1) if limit > 0 else 0.0

        return {
            "daily_budget_usd": limit,
            "daily_spend_usd": round(spend, 4),
            "remaining_budget_usd": max(0.0, round(limit - spend, 4)),
            "percentage_used": pct_used,
            "budget_alert": pct_used >= 80.0,
            "budget_exceeded": spend >= limit,
        }

    def set_budget(self, daily_budget_usd: float) -> Dict[str, Any]:
        """Configure daily budget cap in USD."""
        if daily_budget_usd <= 0.0:
            raise ValueError("Daily budget must be greater than 0.")
        self.gateway.policy_engine.daily_budget_usd = float(daily_budget_usd)
        return self.get_budget_status()

    def get_model_allowlist(self) -> List[str]:
        """List active allowed models (empty = all allowed)."""
        return list(sorted(self.gateway.policy_engine.model_allowlist))

    def set_model_allowlist(self, models: List[str]) -> List[str]:
        """Set or overwrite model allowlist."""
        self.gateway.policy_engine.model_allowlist = set(models)
        return self.get_model_allowlist()

    def add_model_to_allowlist(self, model_name: str) -> List[str]:
        """Add model to allowlist."""
        self.gateway.policy_engine.model_allowlist.add(model_name)
        return self.get_model_allowlist()

    def remove_model_from_allowlist(self, model_name: str) -> List[str]:
        """Remove model from allowlist."""
        self.gateway.policy_engine.model_allowlist.discard(model_name)
        return self.get_model_allowlist()

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Generate authoritative cost allocation report."""
        metrics = self.db.get_ai_observability_metrics()
        return {
            "total_cost_usd": metrics["total_cost_usd"],
            "providers": metrics["providers_breakdown"],
            "tasks": metrics["tasks_breakdown"],
        }
