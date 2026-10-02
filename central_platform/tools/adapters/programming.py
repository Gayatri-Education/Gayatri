"""Gayatri AI Platform — Programming Sandbox Tool Adapter (Phase 08).

Provides safe code syntax validation, AST analysis, and sandboxed deterministic execution.
"""

from __future__ import annotations

import ast
import io
import sys
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


class ProgrammingSandboxAdapter(ToolAdapter):
    """Adapter exposing sandboxed code execution and static syntax analysis."""

    CODE_EXECUTION_ID = "code_execution"

    BLOCKED_MODULES = {
        "os", "sys", "subprocess", "socket", "requests", "urllib", "shutil",
        "pathlib", "importlib", "ctypes", "posix", "nt", "_thread",
    }

    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                tool_id=self.CODE_EXECUTION_ID,
                name="Programming Sandbox",
                description="Performs syntax verification and sandboxed execution of introductory Python code.",
                category=ToolCategory.CODING,
                allowed_roles=[
                    UserRole.STUDENT,
                    UserRole.TEACHER,
                    UserRole.COURSE_ADMIN,
                    UserRole.ORG_ADMIN,
                    UserRole.SUPER_ADMIN,
                ],
                resource_limits=ResourceLimits(
                    timeout_seconds=3.0,
                    max_input_chars=5000,
                    max_output_chars=10000,
                    max_memory_mb=64,
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code snippet to analyze and execute"},
                        "mode": {"type": "string", "enum": ["syntax_only", "execute"], "default": "execute"},
                    },
                    "required": ["code"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "syntax_valid": {"type": "boolean"},
                        "stdout": {"type": "string"},
                        "result": {"type": "any"},
                    },
                },
            )
        ]

    def validate_arguments(self, tool_id: str, arguments: Dict[str, Any]) -> bool:
        if tool_id == self.CODE_EXECUTION_ID:
            code = arguments.get("code")
            return isinstance(code, str) and len(code.strip()) > 0
        return False

    def _inspect_ast_security(self, tree: ast.AST) -> List[str]:
        """Check AST for forbidden operations (imports, dangerous calls, file access)."""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in getattr(node, "names", []):
                    mod_name = alias.name.split(".")[0]
                    if mod_name in self.BLOCKED_MODULES:
                        violations.append(f"Import of forbidden module '{mod_name}' is blocked.")
                if isinstance(node, ast.ImportFrom) and node.module:
                    mod_name = node.module.split(".")[0]
                    if mod_name in self.BLOCKED_MODULES:
                        violations.append(f"Import from forbidden module '{mod_name}' is blocked.")

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"exec", "eval", "open", "__import__", "compile", "breakpoint"}:
                    violations.append(f"Call to dangerous built-in '{node.func.id}' is blocked.")

        return violations

    def execute(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        start = time.perf_counter()
        if tool_id != self.CODE_EXECUTION_ID:
            return ToolExecutionResult(success=False, error=f"Unknown tool '{tool_id}'")

        code = arguments["code"]
        mode = arguments.get("mode", "execute")

        # 1. Syntax parse
        try:
            tree = ast.parse(code)
        except SyntaxError as syn_err:
            return ToolExecutionResult(
                success=False,
                output={"syntax_valid": False, "error_details": str(syn_err)},
                error=f"Syntax error at line {syn_err.lineno}: {syn_err.msg}",
                execution_time_ms=(time.perf_counter() - start) * 1000,
            )

        # 2. Security inspection
        violations = self._inspect_ast_security(tree)
        if violations:
            return ToolExecutionResult(
                success=False,
                error=f"Security sandbox policy violation: {'; '.join(violations)}",
                execution_time_ms=(time.perf_counter() - start) * 1000,
                resource_usage={"security_check": "FAILED"},
            )

        if mode == "syntax_only":
            return ToolExecutionResult(
                success=True,
                output={"syntax_valid": True, "node_count": len(list(ast.walk(tree)))},
                execution_time_ms=(time.perf_counter() - start) * 1000,
            )

        # 3. Restricted execution
        safe_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "sorted": sorted,
        }

        stdout_capture = io.StringIO()
        orig_stdout = sys.stdout

        safe_globals = {
            "__builtins__": safe_builtins,
            "print": lambda *args, **kwargs: print(*args, file=stdout_capture, **kwargs),
        }
        safe_locals: Dict[str, Any] = {}

        try:
            compiled_code = compile(tree, filename="<sandbox>", mode="exec")
            sys.stdout = stdout_capture
            exec(compiled_code, safe_globals, safe_locals)
            captured = stdout_capture.getvalue()
            duration_ms = (time.perf_counter() - start) * 1000

            # Exclude builtins from result output
            cleaned_locals = {k: str(v) for k, v in safe_locals.items() if not k.startswith("_")}

            return ToolExecutionResult(
                success=True,
                output={
                    "syntax_valid": True,
                    "stdout": captured,
                    "variables": cleaned_locals,
                },
                execution_time_ms=duration_ms,
                resource_usage={"lines_executed": len(code.splitlines())},
            )
        except Exception as exc:
            return ToolExecutionResult(
                success=False,
                error=f"Runtime error in sandbox: {str(exc)}",
                execution_time_ms=(time.perf_counter() - start) * 1000,
            )
        finally:
            sys.stdout = orig_stdout
