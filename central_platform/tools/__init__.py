"""Gayatri AI Platform — Tools Package (Phase 08)."""
from __future__ import annotations

from typing import Optional

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


def get_configured_tool_registry(include_chemistry: Optional[bool] = None) -> ToolRegistry:
    """Return a ToolRegistry initialized with all platform standard adapters."""
    from central_platform.adapters.chemistry.adapter import is_chemistry_adapter_enabled
    
    should_include_chem = include_chemistry if include_chemistry is not None else is_chemistry_adapter_enabled()
    registry = get_default_registry()
    if not registry.list_capabilities():
        if should_include_chem:
            registry.register_adapter(ChemistryToolAdapter())
        registry.register_adapter(MathToolAdapter())
        registry.register_adapter(ProgrammingSandboxAdapter())
    elif not should_include_chem:
        # If registry was previously initialized with chemistry, unregister it
        registry.unregister_adapter("ChemistryToolAdapter")
    elif should_include_chem and not registry.is_adapter_registered("ChemistryToolAdapter"):
        registry.register_adapter(ChemistryToolAdapter())
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
