"""Authoritative Computerized Adaptive Testing (CAT) Engine for Gayatri AI Platform (Phase 19).

Dynamically selects questions based on student ability estimation, difficulty progression,
and balanced concept coverage across the curriculum.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from central_platform.assessment.models import AdaptiveState
from central_platform.models.schema import QuestionBankItem


class AdaptiveTestingEngine:
    """Orchestrates Computerized Adaptive Testing (CAT) progression."""

    @staticmethod
    def initialize_state(
        target_concepts: List[str],
        initial_difficulty: int = 2,
    ) -> AdaptiveState:
        """Initialize a new adaptive testing session state."""
        return AdaptiveState(
            current_difficulty=max(1, min(5, initial_difficulty)),
            consecutive_correct=0,
            consecutive_incorrect=0,
            tested_concepts=[],
            remaining_concepts=list(target_concepts),
            items_administered=[],
            history=[],
        )

    @classmethod
    def select_next_item(
        cls,
        available_items: List[QuestionBankItem],
        state: AdaptiveState,
    ) -> Optional[QuestionBankItem]:
        """Select the next optimal question item matching adaptive difficulty and concept coverage."""
        unadministered = [q for q in available_items if q.id not in state.items_administered]
        if not unadministered:
            return None

        # 1. Prioritize remaining untested concepts
        candidate_items = unadministered
        if state.remaining_concepts:
            concept_priority = [q for q in unadministered if q.concept_id in state.remaining_concepts]
            if concept_priority:
                candidate_items = concept_priority

        # 2. Match exact target difficulty
        exact_match = [q for q in candidate_items if q.difficulty == state.current_difficulty]
        if exact_match:
            return exact_match[0]

        # 3. Find closest difficulty
        candidate_items.sort(key=lambda q: abs(q.difficulty - state.current_difficulty))
        return candidate_items[0] if candidate_items else None

    @classmethod
    def update_state_on_response(
        cls,
        state: AdaptiveState,
        item: QuestionBankItem,
        is_correct: bool,
    ) -> AdaptiveState:
        """Update adaptive state following a student response."""
        state.items_administered.append(item.id)
        if item.concept_id:
            state.tested_concepts.append(item.concept_id)
            if item.concept_id in state.remaining_concepts:
                state.remaining_concepts.remove(item.concept_id)

        state.history.append({
            "item_id": item.id,
            "concept_id": item.concept_id,
            "difficulty": item.difficulty,
            "is_correct": is_correct,
        })

        # Difficulty ladder step
        if is_correct:
            state.consecutive_correct += 1
            state.consecutive_incorrect = 0
            if state.current_difficulty < 5:
                state.current_difficulty += 1
        else:
            state.consecutive_incorrect += 1
            state.consecutive_correct = 0
            if state.current_difficulty > 1:
                state.current_difficulty -= 1

        return state
