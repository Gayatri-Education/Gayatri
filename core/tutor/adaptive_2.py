"""Adaptive Learning Engine 2.0 with multi-dimensional mastery and evidence weighting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class AdaptiveAction(str, Enum):
    ADVANCE = "advance"
    MAINTAIN = "maintain"
    REMEDIATE = "remediate"
    REASSESS = "reassess"


@dataclass
class MasteryDimensions:
    knowledge: float = 0.5
    application: float = 0.5
    retention: float = 0.5
    confidence: float = 0.5
    independence: float = 0.5

    @property
    def composite_score(self) -> float:
        return round(
            0.3 * self.knowledge
            + 0.3 * self.application
            + 0.2 * self.retention
            + 0.1 * self.confidence
            + 0.1 * self.independence,
            3,
        )


class AdaptiveEngineV2:
    """Adaptive learning decision engine analyzing multi-dimensional evidence."""

    def evaluate_turn(
        self,
        current_mastery: MasteryDimensions,
        correct: bool,
        hints_used: int,
        response_time_ms: int,
        confidence: float = 0.5,
    ) -> tuple[MasteryDimensions, AdaptiveAction]:
        new_knowledge = current_mastery.knowledge
        new_application = current_mastery.application
        new_independence = current_mastery.independence

        if correct:
            if hints_used == 0:
                new_knowledge = min(1.0, new_knowledge + 0.15)
                new_application = min(1.0, new_application + 0.15)
                new_independence = min(1.0, new_independence + 0.10)
                action = AdaptiveAction.ADVANCE if new_knowledge >= 0.85 else AdaptiveAction.MAINTAIN
            else:
                new_knowledge = min(1.0, new_knowledge + 0.05)
                new_application = min(1.0, new_application + 0.05)
                new_independence = max(0.0, new_independence - 0.05)
                action = AdaptiveAction.MAINTAIN
        else:
            new_knowledge = max(0.0, new_knowledge - 0.10)
            new_application = max(0.0, new_application - 0.15)
            new_independence = max(0.0, new_independence - 0.10)
            action = AdaptiveAction.REMEDIATE if new_knowledge < 0.4 else AdaptiveAction.MAINTAIN

        updated_dimensions = MasteryDimensions(
            knowledge=round(new_knowledge, 3),
            application=round(new_application, 3),
            retention=current_mastery.retention,
            confidence=round(confidence, 3),
            independence=round(new_independence, 3),
        )

        return updated_dimensions, action
