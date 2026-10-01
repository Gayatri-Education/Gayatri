"""Anti-Answer-Leakage Sanitizer Service for Phase 11.

Ensures active assessment payloads delivered to students never leak unearned answers,
rubrics, or teacher explanations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class AssessmentSanitizer:
    """Authoritative sanitizer for assessment content delivery to students."""

    RESTRICTED_FIELDS = {
        "correct_answer",
        "answer",
        "expected_answer",
        "expected_value",
        "correct_index",
        "explanation",
        "solution",
        "rubric",
        "internal_notes",
        "common_misconceptions",
    }

    @classmethod
    def sanitize_item_for_student(cls, item: Any, allow_hints: bool = False) -> Dict[str, Any]:
        """Strip answer keys, solutions, rubrics, and explanations from assessment items."""
        if hasattr(item, "to_dict") and callable(item.to_dict):
            raw = item.to_dict()
        elif isinstance(item, dict):
            raw = dict(item)
        else:
            raw = {
                "id": getattr(item, "id", ""),
                "question_text": getattr(item, "question_text", getattr(item, "question", "")),
                "item_type": getattr(item, "item_type", getattr(item, "type", "MCQ")),
                "options": getattr(item, "options", []),
                "difficulty": getattr(item, "difficulty", 1),
                "concept_id": getattr(item, "concept_id", ""),
                "max_marks": getattr(item, "max_marks", 4.0),
            }

        sanitized: Dict[str, Any] = {}
        for k, v in raw.items():
            if k in cls.RESTRICTED_FIELDS:
                continue
            if k == "hints" and not allow_hints:
                continue
            sanitized[k] = v

        return sanitized

    @classmethod
    def sanitize_assessment_for_student(
        cls,
        assessment: Any,
        items: List[Any],
        allow_hints: bool = False,
    ) -> Dict[str, Any]:
        """Produce clean, leak-free assessment payload for student examination."""
        if hasattr(assessment, "to_dict") and callable(assessment.to_dict):
            raw_assess = assessment.to_dict()
        elif isinstance(assessment, dict):
            raw_assess = dict(assessment)
        else:
            raw_assess = {
                "id": getattr(assessment, "id", ""),
                "course_id": getattr(assessment, "course_id", ""),
                "title": getattr(assessment, "title", ""),
                "assessment_type": getattr(assessment, "assessment_type", "FORMATIVE"),
                "duration_minutes": getattr(assessment, "duration_minutes", 0),
                "total_marks": getattr(assessment, "total_marks", 100.0),
            }

        # Remove rubrics or answer configs from assessment metadata
        raw_assess.pop("rubric", None)
        if "config" in raw_assess and isinstance(raw_assess["config"], dict):
            raw_assess["config"] = {
                k: v for k, v in raw_assess["config"].items()
                if k not in cls.RESTRICTED_FIELDS
            }

        sanitized_items = [
            cls.sanitize_item_for_student(item, allow_hints=allow_hints)
            for item in items
        ]

        raw_assess["items"] = sanitized_items
        return raw_assess

    @classmethod
    def verify_no_leakage(cls, payload: Dict[str, Any]) -> bool:
        """Verify that a given payload contains zero restricted answer leakage fields."""
        def _check(obj: Any) -> bool:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in cls.RESTRICTED_FIELDS:
                        return False
                    if not _check(v):
                        return False
            elif isinstance(obj, list):
                for elem in obj:
                    if not _check(elem):
                        return False
            return True

        return _check(payload)
