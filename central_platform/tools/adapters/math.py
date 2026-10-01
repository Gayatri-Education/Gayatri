"""Gayatri AI Platform — Math Calculator Tool Adapter (Phase 08).

Provides safe mathematical calculation using Python's AST parser.
Zero use of unsafe eval() or exec().
"""

from __future__ import annotations

import ast
import math
import operator
import time
from typing import Any, Callable, Dict, List

from central_platform.models.schema import UserRole
from central_platform.tools.base import ToolAdapter
from central_platform.tools.capabilities import (
    ResourceLimits,
    ToolCapability,
    ToolCategory,
    ToolExecutionContext,
    ToolExecutionResult,
)


class SafeMathEvaluator(ast.NodeVisitor):
    """Safely evaluates mathematical expressions by walking the abstract syntax tree."""

    _BIN_OPS: Dict[type, Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    _UNARY_OPS: Dict[type, Callable[[Any], Any]] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    _SAFE_FUNCTIONS: Dict[str, Callable[..., Any]] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    _SAFE_CONSTANTS: Dict[str, float] = {
        "pi": math.pi,
        "e": math.e,
    }

    def evaluate(self, expr_str: str) -> float | int:
        expr_str = expr_str.strip()
        tree = ast.parse(expr_str, mode="eval")
        return self.visit(tree.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node: ast.Num) -> Any:  # for Python < 3.8 compatibility
        return node.n

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_type = type(node.op)
        if op_type not in self._BIN_OPS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        # Prevent huge exponents causing resource exhaustion
        if op_type is ast.Pow and abs(right) > 1000:
            raise ValueError("Exponent too large (max 1000).")
        return self._BIN_OPS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_type = type(node.op)
        if op_type not in self._UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = self.visit(node.operand)
        return self._UNARY_OPS[op_type](operand)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self._SAFE_CONSTANTS:
            return self._SAFE_CONSTANTS[node.id]
        raise ValueError(f"Variable '{node.id}' is not defined in safe math context.")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Unsupported function call target.")
        fn_name = node.func.id
        if fn_name not in self._SAFE_FUNCTIONS:
            raise ValueError(f"Function '{fn_name}' is not permitted.")
        args = [self.visit(arg) for arg in node.args]
        return self._SAFE_FUNCTIONS[fn_name](*args)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Disallowed syntax node in math expression: {type(node).__name__}")


class MathToolAdapter(ToolAdapter):
    """Adapter exposing safe mathematical calculation."""

    CALCULATOR_ID = "calculator"

    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                tool_id=self.CALCULATOR_ID,
                name="Scientific Math Calculator",
                description="Performs exact arithmetic, algebraic power, logarithmic, and trigonometric calculations safely.",
                category=ToolCategory.CALCULATION,
                allowed_roles=[
                    UserRole.STUDENT,
                    UserRole.TEACHER,
                    UserRole.COURSE_ADMIN,
                    UserRole.ORG_ADMIN,
                    UserRole.SUPER_ADMIN,
                ],
                resource_limits=ResourceLimits(timeout_seconds=2.0, max_input_chars=1000),
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical expression, e.g. 'sqrt(16) + 2^3'"}
                    },
                    "required": ["expression"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                        "result": {"type": "number"},
                    },
                },
            )
        ]

    def validate_arguments(self, tool_id: str, arguments: Dict[str, Any]) -> bool:
        if tool_id == self.CALCULATOR_ID:
            expr = arguments.get("expression")
            return isinstance(expr, str) and len(expr.strip()) > 0
        return False

    def execute(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        start = time.perf_counter()
        if tool_id != self.CALCULATOR_ID:
            return ToolExecutionResult(success=False, error=f"Unknown tool '{tool_id}'")

        expr = arguments["expression"]
        # Allow '^' as alias for exponentiation
        cleaned_expr = expr.replace("^", "**")

        evaluator = SafeMathEvaluator()
        try:
            val = evaluator.evaluate(cleaned_expr)
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolExecutionResult(
                success=True,
                output={"expression": expr, "result": val},
                execution_time_ms=duration_ms,
                resource_usage={"evaluator": "ast_safe_visitor"},
            )
        except ZeroDivisionError:
            return ToolExecutionResult(
                success=False,
                error="Division by zero",
                execution_time_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as exc:
            return ToolExecutionResult(
                success=False,
                error=f"Calculation error: {str(exc)}",
                execution_time_ms=(time.perf_counter() - start) * 1000,
            )
