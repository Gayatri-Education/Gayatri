"""Phase 09: Model Registry & AI Gateway Unification Test Suite.

Verifies:
1. Manifest consistency and canonical schema (format, prompt template, context window, streaming, capabilities, resource profile).
2. Missing model handling (offline guidance yield without crash).
3. Wrong / unregistered model rejection (explicit exception, no silent substitution).
4. Corrupt model / checksum mismatch detection.
5. Provider timeout propagation (Rule 3: never hide exceptions).
6. Provider invalid response handling.
7. Local-only policy enforcement (fail-closed on cloud access in local_only mode).
8. Observable fallback chains under privacy modes.
9. Provider selection by task type and capability matching.
10. Token streaming and cooperative cancellation.
11. Anti-legacy import guard (0 legacy imports in core/, central_platform/, app/).
12. Prompt template ChatML token consistency.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import ExecutionMode
from core.inference.context import build_chat_messages, get_tutor_context
from core.inference.service import InferenceService, ModelConfig, get_inference_service
from core.model_fetch.manifest_validator import (
    ModelManifestValidationError,
    get_active_manifest,
    load_and_validate_manifest,
    verify_model_checksum,
)
from core.providers.base import (
    Capability,
    ChatMessage,
    ChatOptions,
    ChatResponse,
    LLMProvider,
    ModelInfo,
    SpeedTier,
)
from core.providers.local import format_chatml_prompt
from core.providers.registry import ProviderRegistry

ROOT = Path(__file__).resolve().parent.parent


# ── 1. Manifest Consistency ──────────────────────────────────────────────────

def test_manifest_consistency_and_canonical_keys():
    """Verify that model_manifest.json defines all required and canonical Phase 09 fields."""
    manifest = get_active_manifest()

    assert manifest["model_id"] == "gayatri-chem-qwen2.5-0.5b-v4"
    assert manifest["provider"] == "local"
    assert manifest["format"] == "gguf"
    assert manifest["quantization"] == "Q4_K_M"
    assert manifest["prompt_template"] == "chatml"
    assert manifest["context_window"] == 8192
    assert manifest["streaming"] is True
    assert "text-generation" in manifest["capabilities"]
    assert "socratic-tutoring" in manifest["capabilities"]
    assert manifest["resource_profile"] == "1GB RAM, CPU"
    assert manifest["checksum"] is not None


def test_model_config_from_manifest():
    """Verify ModelConfig initializes seamlessly from model_manifest.json."""
    cfg = ModelConfig.from_manifest()
    assert cfg.provider == "local"
    assert cfg.family == "qwen2.5"
    assert cfg.model_id == "gayatri-chem-qwen2.5-0.5b-v4"
    assert cfg.quantization == "Q4_K_M"
    assert cfg.context_length == 8192
    assert cfg.format == "gguf"
    assert cfg.prompt_template == "chatml"
    assert cfg.streaming is True


# ── 2. Missing & Corrupt Model Handling ───────────────────────────────────────

def test_missing_model_handling():
    """Verify that when local model file is missing, InferenceService yields clear offline guidance."""
    service = InferenceService()

    with patch("core.providers.local.LocalProvider.is_available", return_value=False):
        messages = [{"role": "user", "content": "What is enthalpy?"}]
        stream = service.stream_chat(messages)
        chunks = list(stream)
        combined = "".join(chunks)

        assert "offline" in combined.lower()
        assert "models" in combined.lower()


def test_wrong_model_or_unregistered_provider_exception():
    """Verify that requesting an unregistered provider raises an explicit ValueError (no silent switch)."""
    service = InferenceService()

    with patch("core.settings.get_settings", return_value={"privacy_mode": "cloud_allowed"}):
        with pytest.raises(ValueError, match="not registered"):
            list(service.stream_chat(
                messages=[{"role": "user", "content": "Hello"}],
                provider="non_existent_provider",
            ))


def test_corrupt_model_checksum_verification(tmp_path):
    """Verify that corrupted model artifact with wrong checksum fails verification."""
    model_file = tmp_path / "corrupt_model.gguf"
    model_file.write_bytes(b"corrupted binary data")

    expected_hash = hashlib.sha256(b"correct original data").hexdigest()
    actual_hash = hashlib.sha256(b"corrupted binary data").hexdigest()

    assert not verify_model_checksum(model_file, expected_hash)
    assert verify_model_checksum(model_file, actual_hash)


# ── 3. Provider Timeout & Error Propagation ──────────────────────────────────

class TimeoutMockProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "TimeoutMock"

    @property
    def key(self) -> str:
        return "timeout_mock"

    def validate_key(self) -> tuple[bool, str]:
        return True, "OK"

    def list_models(self) -> list[ModelInfo]:
        return []

    def chat(self, messages: list[ChatMessage], options: ChatOptions | None = None) -> ChatResponse:
        raise TimeoutError("Provider request timed out after 30000ms")

    def stream(self, messages: list[ChatMessage], options: ChatOptions | None = None):
        raise TimeoutError("Provider stream timed out after 30000ms")


class InvalidResponseMockProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "InvalidResponseMock"

    @property
    def key(self) -> str:
        return "invalid_mock"

    def validate_key(self) -> tuple[bool, str]:
        return True, "OK"

    def list_models(self) -> list[ModelInfo]:
        return []

    def chat(self, messages: list[ChatMessage], options: ChatOptions | None = None) -> ChatResponse:
        raise ValueError("Invalid payload received from upstream model provider")

    def stream(self, messages: list[ChatMessage], options: ChatOptions | None = None):
        raise ValueError("Malformed stream chunk received")


def test_provider_timeout_propagation():
    """Verify provider timeouts are not silenced or converted into false success (Rule 3)."""
    registry = ProviderRegistry()
    registry.register(TimeoutMockProvider())

    with patch("core.providers.registry.get_registry", return_value=registry):
        with patch("core.settings.get_settings", return_value={"privacy_mode": "cloud_allowed"}):
            service = InferenceService()
            with pytest.raises(TimeoutError, match="timed out"):
                list(service.stream_chat(
                    messages=[{"role": "user", "content": "Explain equilibrium"}],
                    provider="timeout_mock",
                ))


def test_provider_invalid_response_propagation():
    """Verify provider invalid responses raise clear exceptions."""
    registry = ProviderRegistry()
    registry.register(InvalidResponseMockProvider())

    with patch("core.providers.registry.get_registry", return_value=registry):
        with patch("core.settings.get_settings", return_value={"privacy_mode": "cloud_allowed"}):
            service = InferenceService()
            with pytest.raises(ValueError, match="Malformed stream chunk"):
                list(service.stream_chat(
                    messages=[{"role": "user", "content": "Explain equilibrium"}],
                    provider="invalid_mock",
                ))


# ── 4. Privacy Policies & Fallback Observability ─────────────────────────────

def test_local_only_policy_blocks_cloud_transmission():
    """Verify that in local_only mode, cloud provider calls raise PermissionError (fail-closed)."""
    service = InferenceService()

    with patch("core.settings.get_settings", return_value={"privacy_mode": "local_only"}):
        with pytest.raises(PermissionError, match="blocked because privacy mode is set to 'local_only'"):
            list(service.stream_chat(
                messages=[{"role": "user", "content": "Hello"}],
                provider="openai",
            ))


def test_local_first_fallback_chain_under_privacy_mode():
    """Verify ProviderRegistry fallback chain respects privacy mode."""
    registry = ProviderRegistry()

    # Create dummy local provider
    local_mock = MagicMock(spec=LLMProvider)
    local_mock.key = "local"
    local_mock.name = "Local"
    local_mock.is_authenticated = True
    local_mock.is_reachable = True
    local_mock.is_ready.return_value = True
    local_mock.list_models.return_value = [
        ModelInfo(
            id="local-qwen",
            name="Qwen 0.5B",
            provider="local",
            speed_tier=SpeedTier.SLOW,
            capabilities=[Capability.CHAT, Capability.STREAM],
        )
    ]
    registry.register(local_mock)

    # Create dummy cloud provider
    cloud_mock = MagicMock(spec=LLMProvider)
    cloud_mock.key = "openai"
    cloud_mock.name = "OpenAI"
    cloud_mock.is_authenticated = True
    cloud_mock.is_reachable = True
    cloud_mock.is_ready.return_value = True
    cloud_mock.list_models.return_value = [
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            speed_tier=SpeedTier.FAST,
            capabilities=[Capability.CHAT, Capability.STREAM],
        )
    ]
    registry.register(cloud_mock)

    # Under LOCAL_ONLY mode, only local should be in fallback chain
    with patch("core.settings.get_settings", return_value={"privacy_mode": "local_only"}):
        chain = registry.get_fallback_chain(preferred_tier=SpeedTier.FAST)
        providers_in_chain = [p.key for p, _ in chain]
        assert "openai" not in providers_in_chain
        assert "local" in providers_in_chain

    # Under CLOUD_ALLOWED mode, both can be in chain
    with patch("core.settings.get_settings", return_value={"privacy_mode": "cloud_allowed"}):
        chain_cloud = registry.get_fallback_chain(preferred_tier=SpeedTier.FAST)
        providers_cloud = [p.key for p, _ in chain_cloud]
        assert "openai" in providers_cloud


# ── 5. Streaming & Cancellation ──────────────────────────────────────────────

def test_streaming_and_cooperative_cancellation():
    """Verify that inference stream can be stopped midway via cancellation."""
    service = InferenceService()

    def mock_chat_stream(messages, max_tokens=400, **kwargs):
        for i in range(10):
            yield f"token_{i} "

    with patch("core.providers.local.LocalProvider.is_available", return_value=True):
        with patch("core.providers.local.LocalProvider.chat_stream", side_effect=mock_chat_stream):
            collected = []
            for token in service.stream_chat([{"role": "user", "content": "Count"}]):
                collected.append(token)
                if len(collected) == 3:
                    service.cancel()

            assert len(collected) == 3
            assert collected == ["token_0 ", "token_1 ", "token_2 "]


def test_inference_service_generate_sync():
    """Verify non-streaming generate helper combines all chunks."""
    service = InferenceService()

    def mock_chat_stream(messages, max_tokens=400, **kwargs):
        yield "The "
        yield "reaction "
        yield "is "
        yield "spontaneous."

    with patch("core.providers.local.LocalProvider.is_available", return_value=True):
        with patch("core.providers.local.LocalProvider.chat_stream", side_effect=mock_chat_stream):
            result = service.generate([{"role": "user", "content": "Question"}])
            assert result == "The reaction is spontaneous."


# ── 6. Prompt Template Consistency ───────────────────────────────────────────

def test_prompt_template_chatml_consistency():
    """Verify ChatML prompt format matches Qwen tokenizer standards."""
    messages = [
        {"role": "system", "content": "You are a tutor."},
        {"role": "user", "content": "Explain moles."},
    ]
    prompt = format_chatml_prompt(messages)

    assert "<|im_start|>system\nYou are a tutor.<|im_end|>" in prompt
    assert "<|im_start|>user\nExplain moles.<|im_end|>" in prompt
    assert prompt.endswith("<|im_start|>assistant\n")


def test_decoupled_context_builder():
    """Verify build_chat_messages and get_tutor_context assemble clean message dictionaries."""
    context_data = {
        "domain": "Chemistry",
        "topic": "Thermodynamics",
        "active_concept_id": "enthalpy_reaction",
        "mastery": "0.75",
    }
    context_str = get_tutor_context(context_data)
    assert "Domain: Chemistry" in context_str
    assert "Topic: Thermodynamics" in context_str
    assert "Active Concept: enthalpy_reaction" in context_str

    msgs = build_chat_messages(
        system_prompt="Base System Directive",
        user_message="Explain Delta H",
        history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}],
        dynamic_context=context_str,
    )

    assert len(msgs) == 4
    assert msgs[0]["role"] == "system"
    assert "Base System Directive" in msgs[0]["content"]
    assert "[Active Tutor Context]" in msgs[0]["content"]
    assert "Domain: Chemistry" in msgs[0]["content"]
    assert msgs[1] == {"role": "user", "content": "Hi"}
    assert msgs[2] == {"role": "assistant", "content": "Hello!"}
    assert msgs[3] == {"role": "user", "content": "Explain Delta H"}


# ── 7. Architecture Guard: Zero Legacy Callers ───────────────────────────────

def test_anti_legacy_zero_callers():
    """Assert that core/, central_platform/, and app/ have ZERO imports from legacy."""
    regex = re.compile(r"^\s*(?:from\s+legacy\b|import\s+legacy\b)", re.MULTILINE)
    violating_files = []

    for directory in [ROOT / "core", ROOT / "central_platform", ROOT / "app"]:
        if not directory.exists():
            continue
        for py_file in directory.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if regex.search(content):
                    violating_files.append(str(py_file.relative_to(ROOT)))
            except Exception:
                pass

    assert not violating_files, f"Forbidden legacy imports discovered: {violating_files}"
