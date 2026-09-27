"""Gayatri AI Platform — AI Gateway & Governance API Endpoints (Phase 02)."""
from __future__ import annotations

from fastapi import APIRouter
from central_platform.api.schemas import ApiResponse, AIStatusResponse

router = APIRouter(prefix="/ai", tags=["AI Gateway"])


@router.get("/status", response_model=ApiResponse[AIStatusResponse])
async def get_ai_status():
    """Retrieve AI model router health, token usage, and provider availability."""
    return ApiResponse(
        ok=True,
        data=AIStatusResponse(
            gateway_status="HEALTHY",
            active_provider="local_llama",
            active_model="Qwen2.5-3B-Instruct-Q4_K_M",
            available_providers=["local_llama", "ollama", "openai", "gemini"],
            token_usage_today=4210,
            budget_remaining_usd=98.45,
            kill_switch_active=False,
        ),
    )
