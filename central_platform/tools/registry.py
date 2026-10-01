"""Gayatri AI Platform — Tool Registry (Phase 08).

Provides dynamic, course-agnostic registration, discovery, and capability tracking
for all platform computational tools.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from central_platform.models.schema import CourseToolPolicy
from central_platform.tools.base import ToolAdapter
from central_platform.tools.capabilities import ToolCapability

logger = logging.getLogger("gayatri.central_platform.tools.registry")


class ToolRegistry:
    """Central registry for pedagogical tool adapters and capabilities."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, ToolCapability] = {}
        self._tool_to_adapter: Dict[str, ToolAdapter] = {}
        self._adapters: List[ToolAdapter] = []

    def register_adapter(self, adapter: ToolAdapter) -> None:
        """Register a tool adapter and index its advertised capabilities."""
        if adapter not in self._adapters:
            self._adapters.append(adapter)

        for cap in adapter.get_capabilities():
            self._capabilities[cap.tool_id] = cap
            self._tool_to_adapter[cap.tool_id] = adapter
            logger.info("Registered tool capability: %s (%s)", cap.tool_id, cap.name)

    def get_adapter(self, tool_id: str) -> Optional[ToolAdapter]:
        """Retrieve the adapter registered for a specific tool ID."""
        return self._tool_to_adapter.get(tool_id)

    def get_capability(self, tool_id: str) -> Optional[ToolCapability]:
        """Retrieve capability metadata for a tool ID."""
        return self._capabilities.get(tool_id)

    def list_capabilities(self) -> List[ToolCapability]:
        """List all registered tool capabilities."""
        return list(self._capabilities.values())

    def list_tools_for_policy(self, policy: Optional[CourseToolPolicy]) -> List[ToolCapability]:
        """List tool capabilities enabled under a given CourseToolPolicy."""
        if not policy:
            return []
        return [
            cap for cap in self._capabilities.values()
            if policy.is_tool_enabled(cap.tool_id)
        ]

    def clear(self) -> None:
        """Clear all registered adapters and capabilities (useful for test isolation)."""
        self._capabilities.clear()
        self._tool_to_adapter.clear()
        self._adapters.clear()


# Global default registry instance
_default_registry: Optional[ToolRegistry] = None


def get_default_registry() -> ToolRegistry:
    """Retrieve or initialize the global singleton ToolRegistry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry
