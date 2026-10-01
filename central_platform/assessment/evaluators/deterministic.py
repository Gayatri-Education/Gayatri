"""Deterministic Evaluators for Phase 11.

Provides exact, numerical (with tolerance & unit checks), and boolean item evaluators.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)


class MCQEvaluator(BaseEvaluator):
    """Evaluates multiple-choice and single-choice items."""

    SUPPORTED_TYPES = {"MCQ", "CHOICE", "SINGLE_CHOICE"}

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    @staticmethod
    def _normalize(text: Any) -> str:
        if text is None:
            return ""
        return re.sub(r"\s+", " ", str(text).strip().lower())

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        norm_ans = self._normalize(student_answer)
        correct_answer = getattr(item, "correct_answer", "") or ""
        norm_correct = self._normalize(correct_answer)
        options: List[str] = getattr(item, "options", []) or []

        # Empty / ambiguous answer check
        if not norm_ans:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="No answer provided.",
                evidence=["Empty answer submitted"],
            )

        if norm_ans in {"idk", "dunno", "maybe", "skip"}:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.9,
                error_type="other",
                feedback="Student indicated uncertainty.",
                evidence=[f"Uncertain answer token '{norm_ans}' submitted"],
            )

        # Exact string match
        if norm_ans == norm_correct:
            return EvaluationOutcome(
                outcome=EvaluationStatus.CORRECT,
                score=1.0,
                confidence=1.0,
                error_type="none",
                feedback="Correct.",
                evidence=[f"Student answer '{norm_ans}' matched expected '{norm_correct}'"],
            )

        # Option letter mapping (a -> 0, b -> 1, ...)
        letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}

        # 1. Student entered letter, correct is option text
        if options and norm_ans in letter_map and letter_map[norm_ans] < len(options):
            selected_opt = self._normalize(options[letter_map[norm_ans]])
            if selected_opt == norm_correct:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=1.0,
                    error_type="none",
                    feedback="Correct.",
                    evidence=[f"Option '{norm_ans.upper()}' ({selected_opt}) matches correct answer"],
                )

        # 2. Student entered option text, correct is letter
        if options and norm_correct in letter_map and letter_map[norm_correct] < len(options):
            expected_opt = self._normalize(options[letter_map[norm_correct]])
            if norm_ans == expected_opt:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=1.0,
                    error_type="none",
                    feedback="Correct.",
                    evidence=[f"Answer '{norm_ans}' matches expected option '{norm_correct.upper()}'"],
                )

        # 3. Numeric index matching (1-based or 0-based)
        if options and norm_ans.isdigit():
            idx = int(norm_ans)
            # Try 1-based
            if 1 <= idx <= len(options) and self._normalize(options[idx - 1]) == norm_correct:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=1.0,
                    error_type="none",
                    feedback="Correct.",
                    evidence=[f"Option index {idx} matches correct answer"],
                )
            # Try 0-based
            if 0 <= idx < len(options) and self._normalize(options[idx]) == norm_correct:
                return EvaluationOutcome(
                    outcome=EvaluationStatus.CORRECT,
                    score=1.0,
                    confidence=1.0,
                    error_type="none",
                    feedback="Correct.",
                    evidence=[f"Option index {idx} matches correct answer"],
                )

        # Incorrect
        return EvaluationOutcome(
            outcome=EvaluationStatus.INCORRECT,
            score=0.0,
            confidence=1.0,
            error_type="conceptual",
            feedback=f"Incorrect. Selected '{student_answer}'.",
            evidence=[f"Student selected '{norm_ans}', expected '{norm_correct}'"],
        )


class NumericalEvaluator(BaseEvaluator):
    """Evaluates numerical answers with tolerance and unit verification."""

    SUPPORTED_TYPES = {"NUMERICAL", "CALCULATION", "MATH"}

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        ans_str = str(student_answer or "").strip()
        correct_answer = getattr(item, "correct_answer", "") or ""
        tolerance_pct = float(getattr(item, "tolerance_pct", 2.0) or 2.0)
        expected_unit = getattr(item, "expected_unit", None) or ""

        # Extract context overrides
        if context:
            if "tolerance_pct" in context:
                tolerance_pct = float(context["tolerance_pct"])
            if "expected_unit" in context:
                expected_unit = str(context["expected_unit"])

        # Check for empty response
        if not ans_str:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="No numerical value submitted.",
                evidence=["Empty numerical answer submitted"],
            )

        # Extract number matches (supports integers, decimals, scientific notation)
        s_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", ans_str)
        c_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(correct_answer))

        if not s_match or not c_match:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.0,
                error_type="malformed",
                feedback="Could not parse numerical value from submission.",
                evidence=[f"Could not extract numerical value from '{ans_str}' (expected '{correct_answer}')"],
            )

        try:
            val_student = float(s_match.group(0))
            val_correct = float(c_match.group(0))
        except ValueError as val_err:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.0,
                error_type="malformed",
                feedback=f"Failed to parse numerical float: {val_err}",
                evidence=[str(val_err)],
            )

        if math.isnan(val_student) or math.isinf(val_student) or math.isnan(val_correct) or math.isinf(val_correct):
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.0,
                error_type="malformed",
                feedback="Numerical value is NaN or Infinite.",
                evidence=[f"val_student={val_student}, val_correct={val_correct}"],
            )

        # Calculate numerical closeness
        if val_correct == 0.0:
            is_close = abs(val_student) < 1e-4
        else:
            rel_diff = abs((val_student - val_correct) / val_correct) * 100.0
            is_close = rel_diff <= tolerance_pct or math.isclose(
                val_student, val_correct, rel_tol=tolerance_pct / 100.0
            )

        # Unit verification
        unit_mismatch = False
        detected_unit = ""

        # Attempt to infer expected unit from correct_answer if not explicitly specified
        if not expected_unit and isinstance(correct_answer, str):
            unit_sub = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?\s*([a-zA-Z/°%^0-9-]+)", correct_answer)
            if unit_sub and unit_sub.group(1).strip():
                expected_unit = unit_sub.group(1).strip().lower()

        if expected_unit:
            exp_unit_clean = expected_unit.strip().lower()
            ans_clean = ans_str.lower()
            if exp_unit_clean not in ans_clean:
                unit_mismatch = True
                detected_unit = ans_str.replace(s_match.group(0), "").strip()

        # Outcome synthesis
        if is_close and not unit_mismatch:
            return EvaluationOutcome(
                outcome=EvaluationStatus.CORRECT,
                score=1.0,
                confidence=0.98,
                error_type="none",
                feedback="Numerically correct.",
                evidence=[f"Value {val_student} within {tolerance_pct}% of expected {val_correct}"],
            )
        elif is_close and unit_mismatch:
            return EvaluationOutcome(
                outcome=EvaluationStatus.PARTIALLY_CORRECT,
                score=0.7,
                confidence=0.90,
                error_type="unit",
                feedback=f"Value {val_student} is correct, but unit is missing or incorrect (expected '{expected_unit}').",
                evidence=[
                    f"Numerical value {val_student} matches expected {val_correct}",
                    f"Unit mismatch: expected '{expected_unit}', found '{detected_unit}'",
                ],
                remediation_hint=f"Check your physical or mathematical units. Did you include {expected_unit}?",
            )
        else:
            return EvaluationOutcome(
                outcome=EvaluationStatus.INCORRECT,
                score=0.0,
                confidence=0.95,
                error_type="arithmetic",
                feedback=f"Incorrect calculation. Expected {val_correct} (tolerance ±{tolerance_pct}%).",
                evidence=[f"Value {val_student} exceeds allowed tolerance from expected {val_correct}"],
                remediation_hint="Recheck your arithmetic calculations and intermediate steps.",
            )


class BooleanEvaluator(BaseEvaluator):
    """Evaluates True/False and Boolean items."""

    SUPPORTED_TYPES = {"BOOLEAN", "TRUE_FALSE", "TF"}

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    @staticmethod
    def _parse_bool(val: Any) -> Optional[bool]:
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        s = str(val).strip().lower()
        if s in {"true", "t", "yes", "y", "1", "correct"}:
            return True
        if s in {"false", "f", "no", "n", "0", "incorrect"}:
            return False
        return None

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        parsed_student = self._parse_bool(student_answer)
        parsed_correct = self._parse_bool(getattr(item, "correct_answer", ""))

        if parsed_student is None:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="Could not parse boolean True/False answer.",
                evidence=[f"Non-boolean answer '{student_answer}' provided"],
            )

        if parsed_correct is None:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.0,
                error_type="other",
                feedback="Item lacks authoritative boolean answer.",
                evidence=["Question definition lacks valid boolean expected answer"],
            )

        if parsed_student == parsed_correct:
            return EvaluationOutcome(
                outcome=EvaluationStatus.CORRECT,
                score=1.0,
                confidence=1.0,
                error_type="none",
                feedback="Correct.",
                evidence=[f"Boolean value {parsed_student} matches expected {parsed_correct}"],
            )
        else:
            return EvaluationOutcome(
                outcome=EvaluationStatus.INCORRECT,
                score=0.0,
                confidence=1.0,
                error_type="conceptual",
                feedback=f"Incorrect. Expected {parsed_correct}.",
                evidence=[f"Selected {parsed_student}, expected {parsed_correct}"],
            )
