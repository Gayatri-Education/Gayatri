"""Code Execution Evaluator for Phase 11.

Evaluates student programming submissions safely via syntax verification and sandboxing.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional

from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)
from central_platform.models.schema import UserRole
from central_platform.tools.adapters.programming import ProgrammingSandboxAdapter
from central_platform.tools.capabilities import ToolExecutionContext


class CodeExecutionEvaluator(BaseEvaluator):
    """Evaluates student programming submissions against syntax, test cases, or expected output."""

    SUPPORTED_TYPES = {"CODE", "PROGRAMMING", "PYTHON", "CODING"}

    def __init__(self, sandbox_adapter: Optional[ProgrammingSandboxAdapter] = None):
        self.sandbox = sandbox_adapter or ProgrammingSandboxAdapter()

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        code_str = str(student_answer or "").strip()
        expected_output = str(getattr(item, "correct_answer", "") or "").strip()

        if context and "expected_output" in context:
            expected_output = str(context["expected_output"]).strip()

        # Check for empty response
        if not code_str:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="No code provided.",
                evidence=["Empty code snippet submitted"],
            )

        # 1. AST Syntax Verification
        try:
            ast.parse(code_str)
        except SyntaxError as syn_err:
            return EvaluationOutcome(
                outcome=EvaluationStatus.INCORRECT,
                score=0.0,
                confidence=1.0,
                error_type="syntax",
                feedback=f"Syntax Error on line {syn_err.lineno}: {syn_err.msg}",
                evidence=[f"Python SyntaxError: {syn_err}"],
                remediation_hint="Fix the syntax error highlighted above before submitting.",
            )

        # 2. Execute via Programming Sandbox Adapter
        tool_ctx = ToolExecutionContext(
            course_id=getattr(item, "course_id", "default_course"),
            user_role=UserRole.STUDENT,
        )
        exec_res = self.sandbox.execute("code_execution", {"code": code_str}, context=tool_ctx)

        if not exec_res.success:
            err_msg = exec_res.error or "Execution failed"
            err_type = "security" if "Forbidden" in err_msg or "Security" in err_msg else "other"
            return EvaluationOutcome(
                outcome=EvaluationStatus.INCORRECT,
                score=0.0,
                confidence=1.0,
                error_type=err_type,
                feedback=f"Execution error: {err_msg}",
                evidence=[err_msg],
            )

        out_data = exec_res.output if isinstance(exec_res.output, dict) else {}
        actual_stdout = str(out_data.get("stdout", "")).strip()

        # 3. Output comparison if expected_output is provided
        if expected_output:
            if actual_stdout == expected_output:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=1.0,
                    error_type="none",
                    feedback="Code executed successfully with correct output.",
                    evidence=[f"Standard output '{actual_stdout}' matches expected '{expected_output}'"],
                    details={"stdout": actual_stdout},
                )
            elif expected_output in actual_stdout:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=0.9,
                    error_type="none",
                    feedback="Expected output found in program output.",
                    evidence=[f"Expected '{expected_output}' found within output"],
                    details={"stdout": actual_stdout},
                )
            else:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.INCORRECT,
                    score=0.0,
                    confidence=0.95,
                    error_type="conceptual",
                    feedback=f"Output mismatch. Expected: '{expected_output}', got: '{actual_stdout}'",
                    evidence=[f"Output mismatch: got '{actual_stdout}', expected '{expected_output}'"],
                    details={"stdout": actual_stdout},
                    remediation_hint="Review your logic. The output does not match the test case.",
                )

        # If no expected output, clean syntax & execution is considered successful
        return EvaluationOutcome(
            outcome=EvaluationStatus.CORRECT,
            score=1.0,
            confidence=0.85,
            error_type="none",
            feedback="Code parsed and executed cleanly.",
            evidence=["Code compiled without syntax error and completed execution in sandbox"],
            details={"stdout": actual_stdout},
        )
