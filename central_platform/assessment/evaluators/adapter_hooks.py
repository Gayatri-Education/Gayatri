"""Domain Adapter Evaluator Hooks for Phase 11.

Allows domain-specific tools (Chemistry, Physics, Math) to provide specialized deterministic evaluation
without hardcoding domain logic into generic platform evaluators.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)
from central_platform.models.schema import UserRole
from central_platform.tools.adapters.chemistry import ChemistryToolAdapter
from central_platform.tools.capabilities import ToolExecutionContext


class ChemistryEquationEvaluator(BaseEvaluator):
    """Specialized domain evaluator for chemical equation balancing items."""

    SUPPORTED_TYPES = {"EQUATION_BALANCING", "CHEMICAL_EQUATION"}

    def __init__(self, chem_adapter: Optional[ChemistryToolAdapter] = None):
        self.chem_adapter = chem_adapter or ChemistryToolAdapter()

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    @staticmethod
    def _clean_equation(eq_str: str) -> str:
        # Standardize spaces and arrow symbols
        s = re.sub(r"\s+", " ", eq_str).strip()
        s = s.replace("->", "->").replace("-->", "->").replace("=", "->")
        return s

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        ans_str = self._clean_equation(str(student_answer or ""))
        correct_answer = self._clean_equation(str(getattr(item, "correct_answer", "") or ""))

        if not ans_str:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="No chemical equation submitted.",
                evidence=["Empty equation submitted"],
            )

        # 1. Exact canonical string match
        if ans_str == correct_answer:
            return EvaluationOutcome(
                outcome=EvaluationStatus.CORRECT,
                score=1.0,
                confidence=1.0,
                error_type="none",
                feedback="Chemical equation is balanced correctly.",
                evidence=[f"Equation '{ans_str}' matches expected '{correct_answer}'"],
            )

        # 2. Check balancing validity using ChemistryToolAdapter
        tool_ctx = ToolExecutionContext(
            course_id=getattr(item, "course_id", "default_course"),
            user_role=UserRole.STUDENT,
        )
        tool_res = self.chem_adapter.execute("equation_balancer", {"equation": ans_str}, context=tool_ctx)
        out_dict = tool_res.output if isinstance(tool_res.output, dict) else {}
        if tool_res.success and out_dict.get("is_balanced", False):
            return EvaluationOutcome(
                outcome=EvaluationStatus.CORRECT,
                score=1.0,
                confidence=0.98,
                error_type="none",
                feedback="Stoichiometrically balanced equation.",
                evidence=["Stoichiometric matrix verification passed"],
                details=out_dict,
            )

        return EvaluationOutcome(
            outcome=EvaluationStatus.INCORRECT,
            score=0.0,
            confidence=0.95,
            error_type="reaction",
            feedback="Equation is not properly balanced.",
            evidence=[f"Submitted '{ans_str}', expected balanced '{correct_answer}'"],
            remediation_hint="Ensure the number of atoms of each element is equal on both sides of the arrow.",
        )
