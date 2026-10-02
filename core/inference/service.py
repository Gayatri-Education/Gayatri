"""Gayatri AI — Unified Model Inference Service (Phase 09).

Authoritative model inference service coordinating local and provider-based execution
without legacy dependencies. Adheres strictly to the architectural boundary:
Tutor Runtime -> Inference Service -> Provider -> Model.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config import ExecutionMode
from core.providers.local import LocalModelError, LocalProvider

logger = logging.getLogger("gayatri.inference.service")


@dataclass
class ModelConfig:
    """Configuration for model engine and provider."""
    provider: str = "local"
    family: str = "qwen2.5"
    model_id: str = "gayatri-chem-qwen2.5-0.5b-v4"
    quantization: str = "Q4_K_M"
    context_length: int = 8192
    format: str = "gguf"
    prompt_template: str = "chatml"
    streaming: bool = True
    capabilities: List[str] = field(default_factory=lambda: ["text-generation", "socratic-tutoring"])

    @classmethod
    def from_manifest(cls, manifest: Optional[Dict[str, Any]] = None) -> ModelConfig:
        """Create ModelConfig from validated model_manifest.json."""
        if manifest is None:
            try:
                from core.model_fetch.manifest_validator import get_active_manifest
                manifest = get_active_manifest()
            except Exception as exc:
                logger.warning(f"Could not load active manifest, falling back to default config: {exc}")
                return cls()

        return cls(
            provider=manifest.get("provider", "local"),
            family=manifest.get("architecture", "qwen2.5").lower(),
            model_id=manifest.get("model_id", "gayatri-chem-qwen2.5-0.5b-v4"),
            quantization=manifest.get("quantization", "Q4_K_M"),
            context_length=manifest.get("context_window", manifest.get("context_length", 8192)),
            format=manifest.get("format", "gguf"),
            prompt_template=manifest.get("prompt_template", manifest.get("chat_template", "chatml")),
            streaming=manifest.get("streaming", True),
            capabilities=list(manifest.get("capabilities", ["text-generation", "socratic-tutoring"])),
        )


class InferenceService:
    """Unified model inference service for all runtime modes and course engines."""

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig.from_manifest()
        self._cancel_flag = False
        self._lock = threading.Lock()

    def cancel(self) -> None:
        """Signal cooperative cancellation of ongoing inference."""
        self._cancel_flag = True
        try:
            LocalProvider.cancel()
        except Exception as exc:
            logger.debug("LocalProvider cancel ignored or not active: %s", exc)

    def reset_cancellation(self) -> None:
        """Reset the cancellation flag."""
        self._cancel_flag = False

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 400,
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream chat tokens from the configured model engine without legacy imports.

        Enforces privacy mode boundaries and observable fallbacks.
        """
        target_provider = (provider or self.config.provider).lower()
        target_model = model_id or self.config.model_id
        self._cancel_flag = False

        # Privacy mode check
        try:
            from core.settings import get_settings
            mode_str = get_settings().get("privacy_mode", "local_only")
            exec_mode = ExecutionMode(mode_str)
        except Exception:
            exec_mode = ExecutionMode.LOCAL_ONLY

        if exec_mode == ExecutionMode.LOCAL_ONLY and target_provider != "local":
            raise PermissionError(
                f"Data cannot leave the device: provider '{target_provider}' "
                "is blocked because privacy mode is set to 'local_only'."
            )

        logger.info(
            f"InferenceService streaming chat: provider={target_provider}, "
            f"model={target_model}, max_tokens={max_tokens}, temperature={temperature}"
        )

        extra_params = dict(kwargs)
        if temperature is not None:
            extra_params["temperature"] = temperature

        if target_provider == "local":
            try:
                if LocalProvider.is_available():
                    for chunk in LocalProvider.chat_stream(
                        messages,
                        max_tokens=max_tokens,
                        **extra_params,
                    ):
                        if self._cancel_flag:
                            logger.info("Inference generation cancelled cooperative stop.")
                            break
                        yield chunk
                else:
                    fallback_msg = (
                        "Welcome to Gayatri AI Tutor! Local model is currently operating offline. "
                        "To enable full local LLM responses, ensure the GGUF model file is downloaded in `models/gayatri`."
                    )
                    logger.info("Local model uninstalled; yielding offline guidance fallback.")
                    yield fallback_msg
            except LocalModelError as exc:
                logger.warning(f"LocalProvider unavailable in InferenceService: {exc}")
                yield f"Gayatri AI Tutor: {str(exc)}"
            except Exception as exc:
                logger.error(f"InferenceService stream_chat error: {exc}")
                raise
        else:
            # Multi-provider routing via ProviderRegistry
            try:
                from core.providers.base import ChatMessage, ChatOptions
                from core.providers.registry import get_registry

                registry = get_registry()
                prov = registry.get(target_provider)
                if not prov:
                    raise ValueError(f"Requested provider '{target_provider}' is not registered.")

                prov.check_privacy_policy()
                chat_msgs = [ChatMessage(role=m.get("role", "user"), content=m.get("content", "")) for m in messages]
                opts = ChatOptions(
                    model=target_model,
                    max_tokens=max_tokens,
                    temperature=temperature if temperature is not None else 0.7,
                )
                for chunk in prov.stream(chat_msgs, options=opts):
                    if self._cancel_flag:
                        break
                    yield chunk
            except Exception as exc:
                logger.error(f"InferenceService remote provider stream error: {exc}")
                raise

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 400,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Non-streaming chat generation returning the complete text response."""
        chunks = list(self.stream_chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs))
        return "".join(chunks)


_global_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get the singleton InferenceService instance."""
    global _global_service
    if _global_service is None:
        _global_service = InferenceService()
    return _global_service
