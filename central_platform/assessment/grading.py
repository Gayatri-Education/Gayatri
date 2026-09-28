"""Authoritative Deterministic and AI-Assisted Assessment Grading Engine (Phase 19).

Supports deterministic grading (MCQ, True/False, Numerical ranges, Exact matches)
and AI-assisted rubric evaluation for free-form responses, conceptual derivations, and coding items.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from central_platform.assessment.models import ItemGradingResult, QuestionType, Rubric, RubricCriterion
from central_platform.assessment.rubrics import RubricEngine
from central_platform.models.schema import QuestionBankItem


class DeterministicGrader:
    """Exact, numerical, and rule-based deterministic evaluator."""

    @staticmethod
    def _normalize(text: Any) -> str:
        if text is None:
            return ""
        return re.sub(r"\s+", " ", str(text).strip().lower())

    @classmethod
    def grade_mcq(cls, student_answer: Any, correct_answer: str, options: List[str] = None) -> Tuple[bool, float, str]:
        """Grade MCQ matching either option index/letter (e.g. 'A', '1') or option content."""
        norm_ans = cls._normalize(student_answer)
        norm_correct = cls._normalize(correct_answer)

        if not norm_ans:
            return False, 0.0, "No answer provided."

        if norm_ans == norm_correct:
            return True, 1.0, "Correct."

        # Check option letter index if correct_answer is 'A', 'B', etc.
        if options:
            letter_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}
            # If student entered letter and correct is text
            if norm_ans in letter_map and letter_map[norm_ans] < len(options):
                selected_opt = cls._normalize(options[letter_map[norm_ans]])
                if selected_opt == norm_correct:
                    return True, 1.0, "Correct."

            # If student entered text and correct is letter
            if norm_correct in letter_map and letter_map[norm_correct] < len(options):
                expected_opt = cls._normalize(options[letter_map[norm_correct]])
                if norm_ans == expected_opt:
                    return True, 1.0, "Correct."

        return False, 0.0, f"Incorrect. Correct answer was: {correct_answer}"

    @classmethod
    def grade_numerical(
        cls,
        student_answer: Any,
        correct_answer: Any,
        tolerance_pct: float = 2.0,
    ) -> Tuple[bool, float, str]:
        """Grade numerical values with relative tolerance."""
        try:
            # Extract number from student answer string (e.g. " -110.5 kJ " -> -110.5)
            s_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(student_answer))
            c_match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(correct_answer))

            if not s_match or not c_match:
                return False, 0.0, "Could not parse numerical value."

            val_student = float(s_match.group(0))
            val_correct = float(c_match.group(0))

            if val_correct == 0.0:
                is_close = abs(val_student) < 1e-4
            else:
                rel_diff = abs((val_student - val_correct) / val_correct) * 100.0
                is_close = rel_diff <= tolerance_pct or math.isclose(val_student, val_correct, rel_tol=tolerance_pct / 100.0)

            if is_close:
                return True, 1.0, "Numerically correct."
            return False, 0.0, f"Incorrect calculation. Expected approximately {val_correct} (tolerance ±{tolerance_pct}%)."
        except Exception:
            return False, 0.0, "Numerical evaluation failed."

    @classmethod
    def grade_item(
        cls,
        item: QuestionBankItem,
        student_answer: Any,
    ) -> Tuple[bool, float, str]:
        """Route item to appropriate deterministic evaluator."""
        item_type = str(item.item_type).upper()
        if item_type in ("MCQ", "TRUE_FALSE", "CHOICE"):
            return cls.grade_mcq(student_answer, item.correct_answer, item.options)
        elif item_type in ("NUMERICAL", "CALCULATION"):
            return cls.grade_numerical(student_answer, item.correct_answer)
        else:
            # Standard string normalization fallback
            norm_ans = cls._normalize(student_answer)
            norm_corr = cls._normalize(item.correct_answer)
            if norm_ans == norm_corr:
                return True, 1.0, "Correct."
            return False, 0.0, f"Expected: {item.correct_answer}"


class AIAssistedGrader:
    """Intelligent rubric evaluator and misconception detector for open-ended and subjective items."""

    MISCONCEPTION_PATTERNS = {
        "MISCON_THERMO_HEAT_WORK_CONFUSION": {
            "keywords": ["heat is work", "q is always equal to w", "heat equals work", "work cannot be converted"],
            "feedback": "Misconception identified: Heat (q) and Work (w) are path functions representing modes of energy transfer, not identical state quantities.",
        },
        "MISCON_ISOTHERMAL_ADIABATIC": {
            "keywords": ["isothermal means no heat transfer", "adiabatic means constant temperature", "isothermal adiabatic same"],
            "feedback": "Misconception identified: Isothermal means constant temperature (ΔT=0), whereas Adiabatic means no heat exchange with surroundings (q=0).",
        },
        "MISCON_BOND_BREAKING_ENERGY": {
            "keywords": ["bond breaking releases energy", "breaking bonds creates energy", "forming bonds absorbs energy"],
            "feedback": "Misconception identified: Breaking chemical bonds always REQUIRES energy (endothermic), while forming bonds RELEASES energy (exothermic).",
        },
    }

    @classmethod
    def grade_with_rubric(
        cls,
        item: QuestionBankItem,
        student_answer: Any,
        rubric: Optional[Rubric] = None,
    ) -> ItemGradingResult:
        """Perform AI/rule-assisted rubric grading on open-ended responses."""
        ans_str = str(student_answer or "").strip()
        ans_lower = ans_str.lower()
        max_marks = float(item.difficulty * 2.0 if hasattr(item, "difficulty") else 4.0)

        # Check for empty response
        if not ans_str:
            return ItemGradingResult(
                item_id=item.id,
                student_answer=student_answer,
                is_correct=False,
                score=0.0,
                max_marks=max_marks,
                percentage=0.0,
                feedback="No response provided.",
                ai_graded=True,
                ai_confidence=1.0,
                ai_rationale="Blank answer submitted.",
            )

        # 1. Detect known misconceptions
        detected_misconception = None
        misconception_feedback = ""
        for code, data in cls.MISCONCEPTION_PATTERNS.items():
            for kw in data["keywords"]:
                if kw in ans_lower:
                    detected_misconception = code
                    misconception_feedback = data["feedback"]
                    break
            if detected_misconception:
                break

        # 2. Rubric Evaluation
        if not rubric and item.rubric:
            criteria_list = []
            for c_id, c_data in item.rubric.get("criteria", {}).items():
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
                    rubric_id=item.rubric.get("rubric_id", f"rubric_{item.id}"),
                    title=item.rubric.get("title", "Item Rubric"),
                    criteria=criteria_list,
                )

        if not rubric:
            # Default to standard STEM problem solving rubric
            standard_rubrics = RubricEngine.get_standard_rubrics()
            rubric = standard_rubrics.get("stem_problem_solving")

        # 3. Score criteria heuristically based on expected keywords, explanation length, and correct answer match
        criterion_scores: Dict[str, float] = {}
        correct_keywords = [w.strip().lower() for w in re.findall(r"\w+", item.correct_answer) if len(w) >= 1]
        matches = sum(1 for kw in correct_keywords if kw in ans_lower)
        keyword_ratio = (matches / len(correct_keywords)) if correct_keywords else (1.0 if item.correct_answer.lower() in ans_lower else 0.0)

        for crit in rubric.criteria:
            if "concept" in crit.criterion_id or "accuracy" in crit.criterion_id:
                if detected_misconception:
                    crit_score = crit.max_points * 0.25
                elif keyword_ratio >= 0.75:
                    crit_score = crit.max_points * 1.0
                elif keyword_ratio >= 0.4:
                    crit_score = crit.max_points * 0.75
                elif len(ans_str) > 10:
                    crit_score = crit.max_points * 0.5
                else:
                    crit_score = crit.max_points * 0.25
            elif "execution" in crit.criterion_id or "step" in crit.criterion_id or "correctness" in crit.criterion_id:
                if item.correct_answer.lower() in ans_lower:
                    crit_score = crit.max_points * 1.0
                elif keyword_ratio >= 0.5:
                    crit_score = crit.max_points * 0.75
                else:
                    crit_score = crit.max_points * 0.5
            else:
                # Clarity / explanation
                if len(ans_str) >= 40:
                    crit_score = crit.max_points * 1.0
                elif len(ans_str) >= 15:
                    crit_score = crit.max_points * 0.75
                else:
                    crit_score = crit.max_points * 0.5
            criterion_scores[crit.criterion_id] = crit_score

        eval_result = RubricEngine.evaluate_with_rubric(rubric, criterion_scores)
        fraction_earned = eval_result["total_earned"] / max(eval_result["total_possible"], 1e-4)
        scaled_score = round(fraction_earned * max_marks, 2)
        is_correct = fraction_earned >= 0.70

        feedback = "Answer accurately addresses core principles." if is_correct else "Answer requires refinement on key conceptual steps."
        if misconception_feedback:
            feedback = f"{feedback} {misconception_feedback}"

        return ItemGradingResult(
            item_id=item.id,
            student_answer=student_answer,
            is_correct=is_correct,
            score=scaled_score,
            max_marks=max_marks,
            percentage=round(fraction_earned * 100.0, 2),
            criterion_scores=criterion_scores,
            feedback=feedback,
            misconception_code=detected_misconception,
            ai_graded=True,
            ai_confidence=0.92,
            ai_rationale=f"Graded against rubric '{rubric.title}' ({eval_result['percentage']}% criteria met).",
        )


class AssessmentGradingEngine:
    """Unified grading orchestrator executing deterministic and AI-assisted rubric grading."""

    @classmethod
    def grade_submission(
        cls,
        items: List[QuestionBankItem],
        answers: Dict[str, Any],
        assessment_rubric: Optional[Rubric] = None,
        passing_threshold: float = 70.0,
    ) -> Dict[str, Any]:
        """Grade all answers in a submission and compute aggregate outcomes."""
        item_results: Dict[str, ItemGradingResult] = {}
        total_score = 0.0
        total_max_score = 0.0
        concept_scores: Dict[str, List[float]] = {}
        detected_misconceptions: List[str] = []

        item_map = {item.id: item for item in items}

        for item_id, item in item_map.items():
            student_ans = answers.get(item_id)
            item_type = str(item.item_type).upper()

            if item_type in ("MCQ", "NUMERICAL", "TRUE_FALSE", "CHOICE"):
                # Deterministic grading
                is_correct, frac, feedback = DeterministicGrader.grade_item(item, student_ans)
                max_m = float(item.difficulty * 2.0 if hasattr(item, "difficulty") else 4.0)
                item_score = round(frac * max_m, 2)

                res = ItemGradingResult(
                    item_id=item.id,
                    student_answer=student_ans,
                    is_correct=is_correct,
                    score=item_score,
                    max_marks=max_m,
                    percentage=round(frac * 100.0, 2),
                    feedback=feedback,
                    ai_graded=False,
                    ai_confidence=1.0,
                )
            else:
                # AI-assisted rubric grading
                res = AIAssistedGrader.grade_with_rubric(item, student_ans, assessment_rubric)

            item_results[item.id] = res
            total_score += res.score
            total_max_score += res.max_marks

            # Track per-concept mastery
            cid = item.concept_id or "general"
            concept_scores.setdefault(cid, []).append(res.score / max(res.max_marks, 1e-4))

            if res.misconception_code:
                detected_misconceptions.append(res.misconception_code)

        overall_percentage = (total_score / max(total_max_score, 1e-4)) * 100.0
        passed = overall_percentage >= passing_threshold

        # Determine weak concepts (< 70% accuracy)
        weak_concepts = []
        for cid, scores in concept_scores.items():
            avg_c_score = sum(scores) / len(scores)
            if avg_c_score < 0.70:
                weak_concepts.append(cid)

        ai_summary = {
            "graded_at_epoch": int(__import__("time").time()),
            "total_questions": len(items),
            "correct_questions": sum(1 for r in item_results.values() if r.is_correct),
            "ai_evaluated_count": sum(1 for r in item_results.values() if r.ai_graded),
            "misconceptions_flagged": list(set(detected_misconceptions)),
            "weak_concepts": weak_concepts,
            "overall_feedback": "Passed assessment with strong mastery." if passed else "Recommended review on identified weak concepts.",
        }

        return {
            "total_score": round(total_score, 2),
            "max_score": round(total_max_score, 2),
            "percentage": round(overall_percentage, 2),
            "passed": passed,
            "item_results": {k: v.to_dict() for k, v in item_results.items()},
            "ai_grading_summary": ai_summary,
            "reassessment_recommendations": weak_concepts,
        }
