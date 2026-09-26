"""Unified Assessment Builder, Question Item Bank, and AI Grading Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AssessmentType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    ADAPTIVE = "adaptive"


@dataclass
class QuestionItem:
    item_id: str
    concept_id: str
    prompt: str
    correct_answer: str
    difficulty: int = 1  # 1 to 5


@dataclass
class AssessmentSubmission:
    submission_id: str
    assessment_id: str
    student_id: str
    answers: dict[str, str]  # item_id -> response
    ai_score: float = 0.0
    teacher_approved: bool = False
    is_graded: bool = False


class AssessmentBuilder:
    """Unified assessment platform builder and scoring engine."""

    def __init__(self):
        self._item_bank: dict[str, QuestionItem] = {}
        self._assessments: dict[str, list[str]] = {}  # assessment_id -> list of item_ids
        self._submissions: dict[str, AssessmentSubmission] = {}

    def add_question(self, item: QuestionItem) -> QuestionItem:
        self._item_bank[item.item_id] = item
        return item

    def create_assessment(self, assessment_id: str, item_ids: List[str]) -> None:
        self._assessments[assessment_id] = item_ids

    def submit_assessment(self, submission: AssessmentSubmission) -> AssessmentSubmission:
        item_ids = self._assessments.get(submission.assessment_id, [])
        if not item_ids:
            return submission

        correct_count = 0
        for item_id in item_ids:
            item = self._item_bank.get(item_id)
            if item and submission.answers.get(item_id) == item.correct_answer:
                correct_count += 1

        submission.ai_score = round(correct_count / len(item_ids), 3)
        submission.is_graded = True
        self._submissions[submission.submission_id] = submission
        return submission

    def approve_grading(self, submission_id: str) -> bool:
        if submission_id in self._submissions:
            self._submissions[submission_id].teacher_approved = True
            return True
        return False
