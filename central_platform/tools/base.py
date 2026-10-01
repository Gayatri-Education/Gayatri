"""Gayatri AI Platform — Base Tool Adapter Interface (Phase 08).

Defines the abstract interface that all pedagogical tool adapters must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from central_platform.tools.capabilities import (
    ToolCapability,
    ToolExecutionContext,
    ToolExecutionResult,
)


class ToolAdapter(ABC):
    """Abstract interface for pedagogical tool adapters."""

    @abstractmethod
    def get_capabilities(self) -> List[ToolCapability]:
        """Return all tool capabilities supported by this adapter."""
        pass

    @abstractmethod
    def validate_arguments(self, tool_id: str, arguments: Dict[str, Any]) -> bool:
        """Validate argument dictionary against the tool's input contract."""
        pass

    @abstractmethod
    def execute(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        """Execute the tool deterministically within resource constraints."""
        pass
