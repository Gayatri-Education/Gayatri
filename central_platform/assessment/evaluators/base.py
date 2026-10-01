"""Authoritative Base Evaluator Contract for Gayatri AI Platform (Phase 11).

Defines canonical 4-valued evaluation outcome:
- CORRECT
- PARTIALLY_CORRECT
- INCORRECT
- UNCERTAIN

Provides capability-driven evaluation contracts independent of specific academic disciplines.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvaluationStatus(str, Enum):
    CORRECT = "CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class EvaluationOutcome:
    """Canonical, typed evaluation result (Phase 11)."""
    outcome: EvaluationStatus
    score: float  # [0.0, 1.0]
    confidence: float  # [0.0, 1.0]
    error_type: str = "none"  # "none", "arithmetic", "unit", "conceptual", "malformed", "syntax", "timeout", "other"
    misconception_code: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    feedback: str = ""
    remediation_hint: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value if isinstance(self.outcome, EvaluationStatus) else str(self.outcome)
        return d


class BaseEvaluator(ABC):
    """Abstract base evaluator for item capabilities."""

    @abstractmethod
    def supports_type(self, item_type: str) -> bool:
        """Check if evaluator handles given item type."""
        ...

    @abstractmethod
    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        """Evaluate student answer against item criteria and return canonical EvaluationOutcome."""
        ...
