"""Gayatri AI — Unified Context & Message Builder (Phase 09).

Decoupled message and context formatting for model inference.
Provides pure, course-agnostic prompt assembly without legacy dependencies.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.inference.context")


def build_chat_messages(
    system_prompt: str,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    dynamic_context: Optional[str] = None,
    **kwargs: Any,
) -> List[Dict[str, str]]:
    """Build a list of normalized message dicts for model chat inference.

    Args:
        system_prompt: Base system prompt / instructions.
        user_message: Current user / student query.
        history: Prior conversation turns as list of {"role": str, "content": str}.
        dynamic_context: Injected dynamic pedagogical or RAG context string.
        **kwargs: Extra parameters preserved for forward compatibility.

    Returns:
        List of message dicts with role and content keys.
    """
    messages: List[Dict[str, str]] = []

    full_system = system_prompt or ""
    if dynamic_context:
        full_system = f"{full_system}\n\n[Active Tutor Context]\n{dynamic_context}".strip()

    if full_system:
        messages.append({"role": "system", "content": full_system})

    if history:
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": str(msg["role"]), "content": str(msg["content"])})

    messages.append({"role": "user", "content": user_message})
    return messages


def get_tutor_context(context: Any = None, **kwargs: Any) -> str:
    """Extract and format pedagogical context into a prompt string.

    Supports dicts, strings, and domain context objects.

    Args:
        context: Context object, dict, or string.
        **kwargs: Extra parameters.

    Returns:
        Formatted context string.
    """
    if context is None:
        return ""
    if isinstance(context, str):
        return context
    if isinstance(context, dict):
        topic = context.get("topic", "")
        domain = context.get("domain", "")
        concept = context.get("active_concept_id", "")
        mastery = context.get("mastery", "")
        parts = []
        if domain:
            parts.append(f"Domain: {domain}")
        if topic:
            parts.append(f"Topic: {topic}")
        if concept:
            parts.append(f"Active Concept: {concept}")
        if mastery:
            parts.append(f"Mastery: {mastery}")
        return "\n".join(parts)

    # Handle objects with domain-model attributes
    parts = []
    for attr in ("domain", "topic", "active_concept_id", "mastery"):
        val = getattr(context, attr, None)
        if val:
            parts.append(f"{attr.capitalize()}: {val}")
    if parts:
        return "\n".join(parts)

    return str(context)


# Backwards compatibility aliases
_build_messages = build_chat_messages
_get_tutor_context = get_tutor_context
