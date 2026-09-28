"""Authoritative Rubrics Engine for Gayatri AI Platform (Phase 19).

Supports multi-criterion rubric modeling, weighted evaluation, level criteria matching,
and standard rubrics for analytical reasoning, chemistry/physics problem solving, and essay evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from central_platform.assessment.models import Rubric, RubricCriterion


class RubricEngine:
    """Evaluates student answers against structured rubrics."""

    @staticmethod
    def get_standard_rubrics() -> Dict[str, Rubric]:
        """Provides default academic rubrics for standard STEM and reasoning assessments."""
        return {
            "stem_problem_solving": Rubric(
                rubric_id="rubric_stem_problem_solving",
                title="STEM Analytical Problem Solving Rubric",
                description="Evaluates conceptual understanding, mathematical execution, and explanatory reasoning.",
                criteria=[
                    RubricCriterion(
                        criterion_id="concept_understanding",
                        name="Conceptual Accuracy",
                        description="Identifies and applies relevant laws, formulas, and concepts correctly.",
                        max_points=4.0,
                        weight=0.4,
                        levels={
                            "4": "Flawless identification of principles with no misconceptions.",
                            "3": "Accurate conceptual grasp with minor extraneous points.",
                            "2": "Partial conceptual understanding; one or more misconceptions evident.",
                            "1": "Minimal relevant conceptual identification.",
                            "0": "Completely inaccurate or missing concept identification.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="mathematical_execution",
                        name="Calculation & Algebraic Steps",
                        description="Correct algebraic manipulation, substitution, units, and numerical computation.",
                        max_points=4.0,
                        weight=0.4,
                        levels={
                            "4": "All steps shown, units correct, calculation perfectly accurate.",
                            "3": "Steps clear, correct units, minor rounding or arithmetic slip.",
                            "2": "Some intermediate steps missing or significant algebra error.",
                            "1": "Incorrect formulas applied; calculation flawed.",
                            "0": "No mathematical work or entirely incorrect.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="scientific_communication",
                        name="Explanation & Justification",
                        description="Coherent rationale, physical interpretation of the result, and logical flow.",
                        max_points=4.0,
                        weight=0.2,
                        levels={
                            "4": "Clear, concise, scientifically rigorous justification.",
                            "3": "Good explanation with minor ambiguities.",
                            "2": "Vague or incomplete reasoning.",
                            "1": "Fragmented thoughts without logical structure.",
                            "0": "No explanatory justification provided.",
                        },
                    ),
                ],
            ),
            "coding_algorithmic": Rubric(
                rubric_id="rubric_coding_algorithmic",
                title="Coding & Algorithmic Problem Solving Rubric",
                description="Evaluates code correctness, edge cases, time/space efficiency, and code quality.",
                criteria=[
                    RubricCriterion(
                        criterion_id="functional_correctness",
                        name="Functional Correctness",
                        description="Passes all standard and sample test cases.",
                        max_points=4.0,
                        weight=0.5,
                        levels={
                            "4": "All primary and test specifications satisfied perfectly.",
                            "3": "Passes majority of test cases with minor edge case fail.",
                            "2": "Partial logic works but major failures on common inputs.",
                            "1": "Syntax or runtime error preventing core execution.",
                            "0": "No working code provided.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="edge_case_handling",
                        name="Edge Case & Robustness",
                        description="Handles empty inputs, boundaries, negative numbers, and null values.",
                        max_points=4.0,
                        weight=0.3,
                        levels={
                            "4": "Exhaustively handles all boundary conditions.",
                            "3": "Handles typical boundaries; misses extreme cases.",
                            "2": "Vulnerable to common boundary conditions.",
                            "1": "Crashes on basic edge cases.",
                            "0": "No boundary handling.",
                        },
                    ),
                    RubricCriterion(
                        criterion_id="code_quality_style",
                        name="Code Quality & Structure",
                        description="Clean variable naming, modular structure, readability, and idiomatic practices.",
                        max_points=4.0,
                        weight=0.2,
                        levels={
                            "4": "Exemplary readability and modular structure.",
                            "3": "Clean code with minor stylistic deviations.",
                            "2": "Messy structure or poor naming.",
                            "1": "Extremely difficult to read.",
                            "0": "Unreadable code.",
                        },
                    ),
                ],
            ),
        }

    @classmethod
    def evaluate_with_rubric(
        cls,
        rubric: Rubric,
        criterion_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Calculates normalized score and weighted performance from criterion points."""
        total_earned = 0.0
        total_possible = 0.0
        breakdown = {}

        for crit in rubric.criteria:
            crit_max = crit.max_points * crit.weight
            raw_score = float(criterion_scores.get(crit.criterion_id, 0.0))
            clamped_raw = max(0.0, min(raw_score, crit.max_points))
            weighted_earned = clamped_raw * crit.weight

            total_earned += weighted_earned
            total_possible += crit_max

            breakdown[crit.criterion_id] = {
                "name": crit.name,
                "raw_score": clamped_raw,
                "max_raw_points": crit.max_points,
                "weight": crit.weight,
                "weighted_score": round(weighted_earned, 3),
                "max_weighted_points": round(crit_max, 3),
            }

        percentage = (total_earned / total_possible * 100.0) if total_possible > 0 else 0.0
        return {
            "rubric_id": rubric.rubric_id,
            "total_earned": round(total_earned, 3),
            "total_possible": round(total_possible, 3),
            "percentage": round(percentage, 2),
            "breakdown": breakdown,
        }
