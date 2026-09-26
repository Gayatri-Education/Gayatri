"""Unit and backtesting test suite for Adaptive Learning Engine 2.0 (Phase 6)."""

import pytest
from core.tutor.adaptive_2 import AdaptiveAction, AdaptiveEngineV2, MasteryDimensions


def test_multi_dimensional_mastery_calculation():
    m = MasteryDimensions(knowledge=0.8, application=0.7, retention=0.9, confidence=0.8, independence=1.0)
    # 0.3*0.8 + 0.3*0.7 + 0.2*0.9 + 0.1*0.8 + 0.1*1.0 = 0.24 + 0.21 + 0.18 + 0.08 + 0.10 = 0.81
    assert m.composite_score == 0.81


def test_independent_success_triggers_advancement():
    engine = AdaptiveEngineV2()
    initial_m = MasteryDimensions(knowledge=0.80, application=0.80)

    updated_m, action = engine.evaluate_turn(
        current_mastery=initial_m,
        correct=True,
        hints_used=0,
        response_time_ms=5000,
        confidence=0.9,
    )

    assert updated_m.knowledge >= 0.85
    assert action == AdaptiveAction.ADVANCE


def test_failure_triggers_remediation():
    engine = AdaptiveEngineV2()
    initial_m = MasteryDimensions(knowledge=0.35, application=0.30)

    updated_m, action = engine.evaluate_turn(
        current_mastery=initial_m,
        correct=False,
        hints_used=2,
        response_time_ms=18000,
        confidence=0.3,
    )

    assert updated_m.knowledge < 0.35
    assert action == AdaptiveAction.REMEDIATE
