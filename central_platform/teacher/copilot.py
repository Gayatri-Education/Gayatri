"""Teacher AI Copilot service operating over authorized student SLR evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from central_platform.slr.record import StudentLearningRecord


@dataclass
class CopilotCitation:
    evidence_id: str
    category: str
    summary: str


@dataclass
class CopilotResponse:
    answer: str
    citations: List[CopilotCitation] = field(default_factory=list)


class TeacherCopilot:
    """Retrieval-backed AI Assistant for Teachers operating over empirical learning evidence."""

    def __init__(self):
        self._records: dict[str, StudentLearningRecord] = {}

    def register_learning_record(self, record: StudentLearningRecord) -> None:
        self._records[record.student_id] = record

    def summarize_student_sessions(self, student_id: str) -> CopilotResponse:
        record = self._records.get(student_id)
        if not record:
            return CopilotResponse(answer="No learning evidence found for student.", citations=[])

        timeline = record.get_timeline(reverse=False)
        citations = [
            CopilotCitation(evidence_id=item.item_id, category=item.category, summary=item.summary)
            for item in timeline
        ]

        summary_lines = [f"- [{item.category.upper()}] {item.summary}" for item in timeline]
        answer = f"Student '{student_id}' has {len(timeline)} recorded learning events:\n" + "\n".join(summary_lines)

        return CopilotResponse(answer=answer, citations=citations)

    def identify_learning_gaps(self, student_id: str) -> CopilotResponse:
        record = self._records.get(student_id)
        if not record:
            return CopilotResponse(answer="No student records found.", citations=[])

        mastery = record.get_mastery_snapshot()
        gaps = [concept for concept, score in mastery.items() if score < 0.6]

        if not gaps:
            return CopilotResponse(answer="No learning gaps identified.", citations=[])

        citations = [
            CopilotCitation(evidence_id=f"mastery_{c}", category="mastery", summary=f"Mastery: {mastery[c]}")
            for c in gaps
        ]
        answer = f"Student '{student_id}' requires attention in concepts: {', '.join(gaps)}."
        return CopilotResponse(answer=answer, citations=citations)
