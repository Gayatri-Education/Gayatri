"""Gayatri AI Platform — Tutor UI Backend Manager (Phase 26).

Provides descriptors, response action contracts, learning context panel contracts,
and truthful AI status tracking for the conversation-first Tutor UI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TutorActionType(str, Enum):
    COPY = "copy"
    EXPLAIN_SIMPLER = "explain_simpler"
    GIVE_HINT = "give_hint"
    PRACTICE = "practice"
    ASK_QUESTION = "ask_question"
    SHOW_SOURCES = "show_sources"


@dataclass
class TruthfulAIStatusData:
    """Truthful AI execution status descriptor."""
    provider_name: str = "local_gguf"
    model_name: str = "Qwen2.5-3B-Instruct"
    latency_ms: float = 120.0
    zero_leakage_enforced: bool = True
    grounding_score: float = 0.95
    status_label: str = "Online • Socratic Mode"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningContextPanelData:
    """Learning context panel data contract."""
    topic_id: str = "topic-thermo"
    topic_name: str = "Chemical Thermodynamics"
    concept_id: str = "concept-hess-law"
    concept_name: str = "Hess's Law of Constant Heat Summation"
    mastery_score: float = 0.72
    active_misconceptions: List[str] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TutorUIState:
    """Overall state for Tutor UI."""
    student_id: str
    course_id: str
    context_panel_collapsed: bool = False
    status: TruthfulAIStatusData = field(default_factory=TruthfulAIStatusData)
    context_data: LearningContextPanelData = field(default_factory=LearningContextPanelData)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "context_panel_collapsed": self.context_panel_collapsed,
            "status": self.status.to_dict(),
            "context_data": self.context_data.to_dict(),
        }


class TutorUIController:
    """Authoritative Tutor UI Backend Manager."""

    @classmethod
    def get_supported_actions(cls) -> List[Dict[str, str]]:
        return [
            {"type": TutorActionType.COPY.value, "label": "Copy"},
            {"type": TutorActionType.EXPLAIN_SIMPLER.value, "label": "Explain Simpler"},
            {"type": TutorActionType.GIVE_HINT.value, "label": "Give Hint"},
            {"type": TutorActionType.PRACTICE.value, "label": "Practice Problem"},
            {"type": TutorActionType.ASK_QUESTION.value, "label": "Ask Related Question"},
            {"type": TutorActionType.SHOW_SOURCES.value, "label": "Show Sources"},
        ]
