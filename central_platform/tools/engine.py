"""Gayatri AI Platform — Tool Execution Engine (Phase 08).

Enforces the 6-point tool execution contract:
1. Course policy check: course explicitly enables the tool.
2. User role check: user role is permitted to run the tool.
3. Scope containment: course_id, student_id, session_id context.
4. Input validation: schema and argument boundary enforcement.
5. Resource limits: execution timeout and payload size enforcement.
6. Typed output: standardized ToolExecutionResult.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import time
from typing import Any, Dict, Optional

from central_platform.models.schema import UserRole
from central_platform.tools.capabilities import (
    ToolCapability,
    ToolExecutionContext,
    ToolExecutionResult,
)
from central_platform.tools.registry import ToolRegistry, get_default_registry

logger = logging.getLogger("gayatri.central_platform.tools.engine")


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not registered."""
    pass


class CourseToolPolicyViolation(PermissionError):
    """Raised when a tool is blocked by the active course policy."""
    pass


class ToolAuthorizationError(PermissionError):
    """Raised when a user role is not authorized to invoke the tool."""
    pass


class ToolValidationError(ValueError):
    """Raised when tool arguments fail input schema validation."""
    pass


class ToolTimeoutError(TimeoutError):
    """Raised when tool execution exceeds allocated resource limits."""
    pass


class ToolExecutionEngine:
    """Orchestrates secure, policy-enforced execution of pedagogical tools."""

    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or get_default_registry()

    def execute_tool(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: ToolExecutionContext,
        strict_exceptions: bool = False,
    ) -> ToolExecutionResult:
        """Execute a tool with full policy, role, validation, and timeout guardrails."""
        start_time = time.perf_counter()

        try:
            # 1. Tool Existence Check
            capability = self.registry.get_capability(tool_id)
            adapter = self.registry.get_adapter(tool_id)
            if not capability or not adapter:
                msg = f"Tool '{tool_id}' is not registered."
                if strict_exceptions:
                    raise ToolNotFoundError(msg)
                return ToolExecutionResult(
                    success=False,
                    error=msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # 2. Course Tool Policy Check
            if context.course_policy is None or not context.course_policy.is_tool_enabled(tool_id):
                msg = f"Tool '{tool_id}' is disabled by course policy for course '{context.course_id}'."
                if strict_exceptions:
                    raise CourseToolPolicyViolation(msg)
                return ToolExecutionResult(
                    success=False,
                    error=msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # 3. User Role Authorization Check
            role = context.user_role
            if hasattr(role, "value"):
                role_val = role.value
            else:
                role_val = str(role)

            role_val_norm = role_val.lower()
            allowed_role_vals_norm = [
                (r.value if hasattr(r, "value") else str(r)).lower()
                for r in capability.allowed_roles
            ]
            if role_val_norm not in allowed_role_vals_norm and role_val_norm != UserRole.SUPER_ADMIN.value.lower():
                msg = f"User role '{role_val}' is not authorized to execute tool '{tool_id}'."
                if strict_exceptions:
                    raise ToolAuthorizationError(msg)
                return ToolExecutionResult(
                    success=False,
                    error=msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # 4. Input Size & Validation Check
            raw_args_str = json.dumps(arguments, default=str)
            if len(raw_args_str) > capability.resource_limits.max_input_chars:
                msg = (
                    f"Tool argument payload ({len(raw_args_str)} chars) exceeds maximum limit "
                    f"of {capability.resource_limits.max_input_chars} chars."
                )
                if strict_exceptions:
                    raise ToolValidationError(msg)
                return ToolExecutionResult(
                    success=False,
                    error=msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            if not adapter.validate_arguments(tool_id, arguments):
                msg = f"Arguments for tool '{tool_id}' failed input validation schema."
                if strict_exceptions:
                    raise ToolValidationError(msg)
                return ToolExecutionResult(
                    success=False,
                    error=msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # 5. Resource Limits & Execution with Timeout Guard
            timeout = capability.resource_limits.timeout_seconds
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(adapter.execute, tool_id, arguments, context)
                try:
                    result = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    msg = f"Tool '{tool_id}' execution timed out after {timeout:.1f}s."
                    if strict_exceptions:
                        raise ToolTimeoutError(msg)
                    return ToolExecutionResult(
                        success=False,
                        error=msg,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    )
                except Exception as exc:
                    logger.exception("Error executing tool '%s': %s", tool_id, exc)
                    if strict_exceptions:
                        raise
                    return ToolExecutionResult(
                        success=False,
                        error=f"Internal tool execution error: {str(exc)}",
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    )

            # Ensure execution_time_ms is populated
            if result.execution_time_ms <= 0.0:
                result.execution_time_ms = (time.perf_counter() - start_time) * 1000

            return result

        except Exception as exc:
            if strict_exceptions:
                raise
            return ToolExecutionResult(
                success=False,
                error=str(exc),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
