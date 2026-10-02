"""Gayatri AI Platform — Chemistry Tool Adapter (Phase 08).

Wraps deterministic chemistry computational tools (equation balancer, formula parser)
as a modular, decoupled ToolAdapter.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from central_platform.models.schema import UserRole
from central_platform.tools.base import ToolAdapter
from central_platform.tools.capabilities import (
    ResourceLimits,
    ToolCapability,
    ToolCategory,
    ToolExecutionContext,
    ToolExecutionResult,
)
from core.tutor.chemistry_tools import ChemicalEquationBalancer, FormulaParser


class ChemistryToolAdapter(ToolAdapter):
    """Adapter exposing chemical equation balancing and formula atom counting."""

    EQUATION_BALANCER_ID = "equation_balancer"
    FORMULA_PARSER_ID = "formula_parser"

    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                tool_id=self.EQUATION_BALANCER_ID,
                name="Chemical Equation Balancer",
                description="Mathematically balances stoichiometric chemical reactions using nullspace matrix reduction.",
                category=ToolCategory.SCIENCE,
                allowed_roles=[
                    UserRole.STUDENT,
                    UserRole.TEACHER,
                    UserRole.COURSE_ADMIN,
                    UserRole.ORG_ADMIN,
                    UserRole.SUPER_ADMIN,
                ],
                resource_limits=ResourceLimits(timeout_seconds=3.0, max_input_chars=1000),
                input_schema={
                    "type": "object",
                    "properties": {
                        "equation": {"type": "string", "description": "Unbalanced chemical equation, e.g., 'H2 + O2 -> H2O'"}
                    },
                    "required": ["equation"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "balanced_equation": {"type": "string"},
                        "coefficients": {"type": "object"},
                    },
                },
            ),
            ToolCapability(
                tool_id=self.FORMULA_PARSER_ID,
                name="Chemical Formula Parser",
                description="Parses chemical formulas with parenthesis and multiplier counts into atom constituent counts.",
                category=ToolCategory.SCIENCE,
                allowed_roles=[
                    UserRole.STUDENT,
                    UserRole.TEACHER,
                    UserRole.COURSE_ADMIN,
                    UserRole.ORG_ADMIN,
                    UserRole.SUPER_ADMIN,
                ],
                resource_limits=ResourceLimits(timeout_seconds=2.0, max_input_chars=500),
                input_schema={
                    "type": "object",
                    "properties": {
                        "formula": {"type": "string", "description": "Chemical formula, e.g., 'Ca(OH)2'"}
                    },
                    "required": ["formula"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "elements": {"type": "object"},
                    },
                },
            ),
        ]

    def validate_arguments(self, tool_id: str, arguments: Dict[str, Any]) -> bool:
        if tool_id == self.EQUATION_BALANCER_ID:
            eq = arguments.get("equation")
            return isinstance(eq, str) and len(eq.strip()) > 0
        elif tool_id == self.FORMULA_PARSER_ID:
            form = arguments.get("formula")
            return isinstance(form, str) and len(form.strip()) > 0
        return False

    def execute(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        start = time.perf_counter()
        if tool_id == self.EQUATION_BALANCER_ID:
            equation = arguments["equation"]
            res = ChemicalEquationBalancer.balance(equation)
            duration_ms = (time.perf_counter() - start) * 1000
            if res.get("success"):
                return ToolExecutionResult(
                    success=True,
                    output=res,
                    execution_time_ms=duration_ms,
                    resource_usage={"algorithm": "matrix_nullspace"},
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    error=res.get("error", "Failed to balance equation"),
                    execution_time_ms=duration_ms,
                )

        elif tool_id == self.FORMULA_PARSER_ID:
            formula = arguments["formula"]
            try:
                elements = FormulaParser.parse_formula(formula)
                duration_ms = (time.perf_counter() - start) * 1000
                return ToolExecutionResult(
                    success=True,
                    output={"formula": formula, "elements": elements},
                    execution_time_ms=duration_ms,
                    resource_usage={"atom_count": sum(elements.values())},
                )
            except Exception as exc:
                return ToolExecutionResult(
                    success=False,
                    error=f"Error parsing formula '{formula}': {str(exc)}",
                    execution_time_ms=(time.perf_counter() - start) * 1000,
                )

        return ToolExecutionResult(
            success=False,
            error=f"Unknown chemistry tool '{tool_id}'",
            execution_time_ms=(time.perf_counter() - start) * 1000,
        )
