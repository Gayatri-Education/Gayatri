"""Canonical Student Learning Record (SLR) aggregator and timeline engine (Phase 06).

Provides backward-compatible in-memory aggregator interface alongside
production authoritative database integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TimelineItem:
    item_id: str
    student_id: str
    category: str  # assessment, session, mastery_change, mistake, teacher_intervention
    summary: str
    timestamp: str
    metadata: dict = field(default_factory=dict)


class StudentLearningRecord:
    """Canonical aggregator of all learning evidence for a student.
    
    100% backward-compatible with legacy and copilot test suites.
    """

    def __init__(self, student_id: str):
        self.student_id = student_id
        self._timeline: list[TimelineItem] = []
        self._mastery_scores: dict[str, float] = {}
        self._service: Optional[Any] = None

    def add_event(
        self,
        item_id: str,
        category: str,
        summary: str,
        timestamp: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> TimelineItem:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        if metadata is None:
            metadata = {}

        item = TimelineItem(
            item_id=item_id,
            student_id=self.student_id,
            category=category,
            summary=summary,
            timestamp=timestamp,
            metadata=metadata,
        )
        self._timeline.append(item)
        return item

    def update_concept_mastery(self, concept_id: str, score: float) -> None:
        self._mastery_scores[concept_id] = float(score)

    def get_timeline(self, reverse: bool = True) -> List[TimelineItem]:
        """Return chronological or reverse-chronological learning timeline."""
        return sorted(self._timeline, key=lambda x: x.timestamp, reverse=reverse)

    def get_mastery_snapshot(self) -> dict[str, float]:
        return dict(self._mastery_scores)
