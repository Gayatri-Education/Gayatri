"""Legacy agent compatibility module — DEPRECATED (Phase 09).

This module is maintained exclusively for temporary backwards compatibility.
All active code must import from core.inference.context, core.inference.service,
or core.providers.local.
"""
from __future__ import annotations

import logging
import warnings
from typing import Iterator

from core.inference.context import _build_messages, _get_tutor_context
from core.providers.local import LocalModelError, LocalProvider

logger = logging.getLogger("gayatri.legacy")
warnings.warn(
    "legacy.agents.default_agents is deprecated and scheduled for removal in Phase 28. "
    "Use core.inference.context and core.inference.service instead.",
    DeprecationWarning,
    stacklevel=2,
)


def _local_chat_stream(
    messages: list[dict[str, str]],
    max_tokens: int = 400,
    **kwargs,
) -> Iterator[str]:
    """Stream chat responses via LocalProvider or yield fallback message."""
    try:
        if LocalProvider.is_available():
            yield from LocalProvider.chat_stream(messages, max_tokens=max_tokens, **kwargs)
        else:
            fallback = (
                "Welcome to Gayatri AI Tutor! Local model is currently operating offline. "
                "To enable full local LLM responses, ensure the GGUF model file is downloaded in `GayatriAI\\models\\gayatri`."
            )
            yield fallback
    except LocalModelError as exc:
        logger.warning(f"LocalProvider unavailable in _local_chat_stream: {exc}")
        yield f"Gayatri AI Tutor: {str(exc)}"
    except Exception as exc:
        logger.error(f"Unexpected error in _local_chat_stream: {exc}")
        yield "Gayatri AI Tutor: An error occurred while generating the response."
