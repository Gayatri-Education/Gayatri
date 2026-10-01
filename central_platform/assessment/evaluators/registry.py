"""Central Evaluator Registry for Gayatri AI Platform (Phase 11).

Provides capability-driven routing across deterministic, rubric, code, and adapter evaluators.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from central_platform.assessment.evaluators.adapter_hooks import ChemistryEquationEvaluator
from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)
from central_platform.assessment.evaluators.code import CodeExecutionEvaluator
from central_platform.assessment.evaluators.deterministic import (
    BooleanEvaluator,
    MCQEvaluator,
    NumericalEvaluator,
)
from central_platform.assessment.evaluators.rubric import RubricEvaluator

logger = logging.getLogger("gayatri.assessment.evaluators")


class EvaluatorRegistry:
    """Authoritative Evaluator Registry mapping item capabilities to specialized evaluators."""

    def __init__(self):
        self._evaluators: List[BaseEvaluator] = []
        self._default_evaluator = RubricEvaluator()
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(MCQEvaluator())
        self.register(NumericalEvaluator())
        self.register(BooleanEvaluator())
        self.register(CodeExecutionEvaluator())
        self.register(ChemistryEquationEvaluator())
        self.register(self._default_evaluator)

    def register(self, evaluator: BaseEvaluator) -> None:
        """Register a new evaluator."""
        self._evaluators.insert(0, evaluator)  # Higher precedence for newly registered

    def get_evaluator(self, item_type: str) -> BaseEvaluator:
        """Find the evaluator that supports the specified item type."""
        for ev in self._evaluators:
            if ev.supports_type(item_type):
                return ev
        return self._default_evaluator

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        """Route item to appropriate evaluator and return canonical EvaluationOutcome."""
        item_type = getattr(item, "item_type", None) or getattr(item, "type", "CONCEPTUAL")
        evaluator = self.get_evaluator(str(item_type))
        try:
            return evaluator.evaluate(item, student_answer, context=context)
        except Exception as exc:
            logger.error(f"Evaluator error on item type {item_type}: {exc}", exc_info=True)
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.0,
                error_type="other",
                feedback=f"Evaluation pipeline encountered error: {exc}",
                evidence=[str(exc)],
            )


# Global default instance
DEFAULT_EVALUATOR_REGISTRY = EvaluatorRegistry()
