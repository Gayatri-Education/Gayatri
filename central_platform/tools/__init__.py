"""Gayatri AI Platform — Tools Package (Phase 08)."""

from central_platform.tools.capabilities import (
    ResourceLimits,
    ToolCapability,
    ToolCategory,
    ToolExecutionContext,
    ToolExecutionResult,
)
from central_platform.tools.base import ToolAdapter
from central_platform.tools.registry import ToolRegistry, get_default_registry
from central_platform.tools.engine import (
    CourseToolPolicyViolation,
    ToolAuthorizationError,
    ToolExecutionEngine,
    ToolNotFoundError,
    ToolTimeoutError,
    ToolValidationError,
)
from central_platform.tools.adapters.chemistry import ChemistryToolAdapter
from central_platform.tools.adapters.math import MathToolAdapter
from central_platform.tools.adapters.programming import ProgrammingSandboxAdapter


def get_configured_tool_registry() -> ToolRegistry:
    """Return a ToolRegistry initialized with all platform standard adapters."""
    registry = get_default_registry()
    if not registry.list_capabilities():
        registry.register_adapter(ChemistryToolAdapter())
        registry.register_adapter(MathToolAdapter())
        registry.register_adapter(ProgrammingSandboxAdapter())
    return registry


__all__ = [
    "ResourceLimits",
    "ToolCapability",
    "ToolCategory",
    "ToolExecutionContext",
    "ToolExecutionResult",
    "ToolAdapter",
    "ToolRegistry",
    "get_default_registry",
    "get_configured_tool_registry",
    "ToolExecutionEngine",
    "ToolNotFoundError",
    "CourseToolPolicyViolation",
    "ToolAuthorizationError",
    "ToolValidationError",
    "ToolTimeoutError",
    "ChemistryToolAdapter",
    "MathToolAdapter",
    "ProgrammingSandboxAdapter",
]
