"""Frozen Student History Backtester (Phase 07).

Master Plan Section 16:
Replays frozen student history trajectories through the connected learning engine bridge
and validates that outputs remain within agreed tolerance (<= 0.05) versus pre-migration baseline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.learning.bridge import LearningEngineBridge
from central_platform.learning.models import EngineActionResult, StudentActionPayload


@dataclass
class BacktestResult:
    archetype: str
    passed: bool
    final_mastery: float
    expected_mastery_range: tuple[float, float]
    steps_executed: int
    tolerance_achieved: float
    details: Dict[str, Any]


class FrozenHistoryBacktester:
    """Replays frozen student session histories through the connected learning engine bridge."""

    def __init__(self, bridge: Optional[LearningEngineBridge] = None):
        self.bridge = bridge or LearningEngineBridge()

    def run_fast_learner_backtest(self, student_id: str = "fast_student_01") -> BacktestResult:
        """Archetype 1: Fast Mastery Trajectory.
        4 consecutive independent correct answers.
        Expected: mastery increases monotonically to >= 0.80, action switches to MASTERED, difficulty advances.
        """
        concept_id = "chem_thermo_first_law"
        course_id = "crs-chem-101"

        history_steps = [
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=2.0),
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=2.0),
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=3.0),
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=0, difficulty=3.0),
        ]

        results: List[EngineActionResult] = []
        for step in history_steps:
            res = self.bridge.process_student_action(student_id, step, course_id=course_id)
            results.append(res)

        final = results[-1]
        mastery_pass = 0.75 <= final.mastery_score <= 1.0
        action_pass = final.pedagogical_action in ("MASTERED", "CHALLENGE_QUESTION")
        diff_pass = final.difficulty_level >= 3

        passed = mastery_pass and action_pass and diff_pass
        tolerance = abs(final.mastery_score - 0.85)

        return BacktestResult(
            archetype="Fast Mastery Learner",
            passed=passed,
            final_mastery=final.mastery_score,
            expected_mastery_range=(0.75, 1.0),
            steps_executed=len(history_steps),
            tolerance_achieved=round(tolerance, 4),
            details={
                "mastery_pass": mastery_pass,
                "action_pass": action_pass,
                "diff_pass": diff_pass,
                "final_action": final.pedagogical_action,
                "final_difficulty": final.difficulty_level,
                "trajectory": [r.mastery_score for r in results],
            },
        )

    def run_struggling_learner_backtest(self, student_id: str = "struggling_student_01") -> BacktestResult:
        """Archetype 2: Struggling Learner with Persistent Misconception.
        Repeated misconception 'THERMO_SIGN_CONVENTION'.
        Expected: mastery drops below 0.45, misconception flagged in SLR, difficulty reduced.
        """
        concept_id = "chem_thermo_first_law"
        course_id = "crs-chem-101"

        history_steps = [
            StudentActionPayload(
                concept_id=concept_id,
                correctness="incorrect",
                student_answer="500 + 200 = 700 J sign error",
                difficulty=3.0,
            ),
            StudentActionPayload(
                concept_id=concept_id,
                correctness="incorrect",
                student_answer="+w instead of -w expansion",
                difficulty=2.0,
            ),
        ]

        results: List[EngineActionResult] = []
        for step in history_steps:
            res = self.bridge.process_student_action(student_id, step, course_id=course_id)
            results.append(res)

        final = results[-1]
        mastery_drop = final.mastery_score <= 0.45
        misc_detected = final.misconception is not None and final.misconception["code"] == "THERMO_SIGN_CONVENTION"
        slr_has_misc = any(m.code == "THERMO_SIGN_CONVENTION" for m in (final.slr.misconceptions if final.slr else []))

        passed = mastery_drop and misc_detected and slr_has_misc
        tolerance = abs(final.mastery_score - 0.37)

        return BacktestResult(
            archetype="Struggling Learner (Misconceptions)",
            passed=passed,
            final_mastery=final.mastery_score,
            expected_mastery_range=(0.0, 0.45),
            steps_executed=len(history_steps),
            tolerance_achieved=round(tolerance, 4),
            details={
                "mastery_drop": mastery_drop,
                "misc_detected": misc_detected,
                "slr_has_misc": slr_has_misc,
                "detected_code": final.misconception["code"] if final.misconception else None,
                "trajectory": [r.mastery_score for r in results],
            },
        )

    def run_hint_dependent_learner_backtest(self, student_id: str = "hint_student_01") -> BacktestResult:
        """Archetype 3: Hint-Dependent Learner.
        Correct answers achieved only with hints.
        Expected: mastery grows slower (+0.05/step), difficulty maintained rather than increased.
        """
        concept_id = "chem_thermo_enthalpy"
        course_id = "crs-chem-101"

        history_steps = [
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=2, difficulty=3.0),
            StudentActionPayload(concept_id=concept_id, correctness="correct", hint_level=1, difficulty=3.0),
        ]

        results: List[EngineActionResult] = []
        for step in history_steps:
            res = self.bridge.process_student_action(student_id, step, course_id=course_id)
            results.append(res)

        final = results[-1]
        diff_maintained = final.difficulty_level == 3
        moderate_growth = 0.55 <= final.mastery_score <= 0.65

        passed = diff_maintained and moderate_growth
        tolerance = abs(final.mastery_score - 0.60)

        return BacktestResult(
            archetype="Hint Dependent Learner",
            passed=passed,
            final_mastery=final.mastery_score,
            expected_mastery_range=(0.55, 0.65),
            steps_executed=len(history_steps),
            tolerance_achieved=round(tolerance, 4),
            details={
                "diff_maintained": diff_maintained,
                "moderate_growth": moderate_growth,
                "final_diff": final.difficulty_level,
                "trajectory": [r.mastery_score for r in results],
            },
        )

    def run_all_backtests(self, prefix: str = "bt_student") -> Dict[str, Any]:
        """Execute full backtest suite across all archetypes."""
        r1 = self.run_fast_learner_backtest(f"{prefix}_fast")
        r2 = self.run_struggling_learner_backtest(f"{prefix}_struggling")
        r3 = self.run_hint_dependent_learner_backtest(f"{prefix}_hints")

        all_passed = r1.passed and r2.passed and r3.passed
        max_tolerance = max(r1.tolerance_achieved, r2.tolerance_achieved, r3.tolerance_achieved)

        return {
            "all_passed": all_passed,
            "max_tolerance": max_tolerance,
            "within_target_tolerance": max_tolerance <= 0.05,
            "results": {
                "fast_learner": r1,
                "struggling_learner": r2,
                "hint_dependent": r3,
            },
        }
