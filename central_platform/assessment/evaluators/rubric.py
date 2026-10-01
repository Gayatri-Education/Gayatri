"""Rubric and Open-Ended Response Evaluator for Phase 11.

Evaluates conceptual derivations, short answers, and essays against multi-criteria rubrics.
Decoupled from hardcoded subject misconceptions; pulls misconceptions dynamically from course context.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from central_platform.assessment.evaluators.base import (
    BaseEvaluator,
    EvaluationOutcome,
    EvaluationStatus,
)
from central_platform.assessment.models import Rubric, RubricCriterion
from central_platform.assessment.rubrics import RubricEngine


class RubricEvaluator(BaseEvaluator):
    """Evaluates open-ended, conceptual, and essay responses against structured rubrics."""

    SUPPORTED_TYPES = {"RUBRIC", "ESSAY", "SHORT_ANSWER", "CONCEPTUAL", "OPEN_ENDED"}

    def supports_type(self, item_type: str) -> bool:
        return str(item_type).upper() in self.SUPPORTED_TYPES

    def evaluate(
        self,
        item: Any,
        student_answer: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationOutcome:
        ans_str = str(student_answer or "").strip()
        ans_lower = ans_str.lower()
        correct_answer = str(getattr(item, "correct_answer", "") or "").strip()
        item_rubric = getattr(item, "rubric", None)

        # 1. Empty or Ambiguous Input Checks
        if not ans_str:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=1.0,
                error_type="malformed",
                feedback="No response provided.",
                evidence=["Empty submission for open-ended item"],
            )

        if ans_lower in {"idk", "dunno", "maybe", "skip", "pass", "no idea"}:
            return EvaluationOutcome(
                outcome=EvaluationStatus.UNCERTAIN,
                score=0.0,
                confidence=0.9,
                error_type="other",
                feedback="Student indicated uncertainty.",
                evidence=[f"Uncertain token '{ans_str}' submitted"],
            )

        # 2. Dynamic Misconception Detection
        # Misconceptions can be passed in context or on the item
        active_misconceptions: Dict[str, Dict[str, Any]] = {}
        if context and "misconceptions" in context:
            active_misconceptions = context["misconceptions"]
        elif hasattr(item, "common_misconceptions") and isinstance(item.common_misconceptions, dict):
            active_misconceptions = item.common_misconceptions

        detected_misconception_code: Optional[str] = None
        misconception_feedback: str = ""
        for code, m_data in active_misconceptions.items():
            keywords = m_data.get("keywords", [])
            for kw in keywords:
                if kw.lower() in ans_lower:
                    detected_misconception_code = code
                    misconception_feedback = m_data.get("feedback", f"Misconception identified: {code}")
                    break
            if detected_misconception_code:
                break

        # 3. Rubric Resolution
        rubric: Optional[Rubric] = None
        if isinstance(item_rubric, Rubric):
            rubric = item_rubric
        elif isinstance(item_rubric, dict):
            criteria_list = []
            for c_id, c_data in item_rubric.get("criteria", {}).items():
                criteria_list.append(
                    RubricCriterion(
                        criterion_id=c_id,
                        name=c_data.get("name", c_id),
                        description=c_data.get("description", ""),
                        max_points=float(c_data.get("max_points", 4.0)),
                        weight=float(c_data.get("weight", 1.0)),
                        levels=c_data.get("levels", {}),
                    )
                )
            if criteria_list:
                rubric = Rubric(
                    rubric_id=item_rubric.get("rubric_id", f"rubric_{getattr(item, 'id', 'item')}"),
                    title=item_rubric.get("title", "Item Rubric"),
                    criteria=criteria_list,
                )

        if not rubric:
            # Fall back to standard academic problem solving rubric
            standard_rubrics = RubricEngine.get_standard_rubrics()
            rubric = standard_rubrics.get("stem_problem_solving")

        # 4. Evaluation Scoring
        # Match keywords from correct_answer or rubric
        key_terms = [w.lower() for w in re.findall(r"\w{3,}", correct_answer) if len(w) >= 3]
        matches = [w for w in key_terms if w in ans_lower]
        keyword_ratio = (len(matches) / len(key_terms)) if key_terms else (1.0 if correct_answer.lower() in ans_lower else 0.5)

        total_earned = 0.0
        total_possible = 0.0
        criterion_feedback: List[str] = []

        if rubric and rubric.criteria:
            for crit in rubric.criteria:
                crit_max = crit.max_points * crit.weight
                total_possible += crit_max

                if "concept" in crit.criterion_id.lower() or "accuracy" in crit.criterion_id.lower():
                    if detected_misconception_code:
                        earned = crit_max * 0.25
                        criterion_feedback.append(f"{crit.name}: Misconception detected ({detected_misconception_code}).")
                    else:
                        earned = crit_max * min(1.0, max(0.2, keyword_ratio))
                        criterion_feedback.append(f"{crit.name}: Evaluated with keyword alignment ({keyword_ratio:.0%}).")
                elif "method" in crit.criterion_id.lower() or "reasoning" in crit.criterion_id.lower():
                    has_reasoning = any(tok in ans_lower for tok in ["because", "therefore", "thus", "since", "due to", "steps"])
                    earned = crit_max * (0.85 if has_reasoning else 0.45)
                    criterion_feedback.append(f"{crit.name}: Reasoning structure {'present' if has_reasoning else 'minimal'}.")
                else:
                    earned = crit_max * 0.70
                total_earned += earned
        else:
            total_possible = 100.0
            total_earned = 100.0 * keyword_ratio

        normalized_score = min(1.0, max(0.0, total_earned / max(total_possible, 1.0)))

        # 5. Outcome Mapping
        evidence = [f"Content keyword match: {len(matches)}/{len(key_terms)} key terms"]
        if detected_misconception_code:
            evidence.append(f"Misconception detected: {detected_misconception_code}")

        if normalized_score >= 0.70:
            outcome = EvaluationStatus.CORRECT
            err_type = "none"
            feedback = "Strong conceptual explanation."
        elif normalized_score >= 0.35:
            outcome = EvaluationStatus.PARTIALLY_CORRECT
            err_type = "conceptual"
            feedback = misconception_feedback or "Partially correct explanation. Review key principles."
        else:
            outcome = EvaluationStatus.INCORRECT
            err_type = "conceptual"
            feedback = misconception_feedback or "Incorrect or incomplete explanation."

        return EvaluationOutcome(
            outcome=outcome,
            score=round(normalized_score, 2),
            confidence=0.88,
            error_type=err_type,
            misconception_code=detected_misconception_code,
            evidence=evidence,
            feedback=feedback,
            remediation_hint=misconception_feedback or "Review the foundational definitions and concepts.",
            details={
                "criterion_feedback": criterion_feedback,
                "keyword_ratio": keyword_ratio,
            },
        )
