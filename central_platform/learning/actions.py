"""Next Action Engine for Phase 15.

Implements deterministic Next Action selection supporting 9 canonical actions:
1. CONTINUE
2. EXPLAIN
3. HINT
4. REMEDIATE
5. PRACTICE
6. REVIEW
7. ASSESS
8. CHALLENGE
9. ADVANCE

Includes structured explainability details for every decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.learning.graph import ConceptNodeState, LearningGraph
from central_platform.learning.mastery import MasteryEvidenceEngine


class NextActionType(str, Enum):
    CONTINUE = "CONTINUE"
    EXPLAIN = "EXPLAIN"
    HINT = "HINT"
    REMEDIATE = "REMEDIATE"
    PRACTICE = "PRACTICE"
    REVIEW = "REVIEW"
    ASSESS = "ASSESS"
    CHALLENGE = "CHALLENGE"
    ADVANCE = "ADVANCE"


@dataclass
class NextActionDecision:
    """Canonical next action decision with explainability."""
    action: NextActionType
    target_concept_id: str
    target_concept_name: str
    recommended_mode: str  # "EXPLAIN", "QUESTION", "REMEDIATE", "SUMMARY", "ASSESS", "CHALLENGE"
    reason: str
    explainability_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value if isinstance(self.action, NextActionType) else str(self.action)
        return d


class NextActionEngine:
    """Authoritative Next Action decision engine with full explainability."""

    def __init__(self, db: Optional[PlatformDatabase] = None):
        self.db = db
        self.graph = LearningGraph(db) if db else None
        self.mastery_engine = MasteryEvidenceEngine(db) if db else None

    def decide_next_action(
        self,
        student_id: str,
        course_id: str,
        current_concept_id: str,
        node_state: Optional[ConceptNodeState] = None,
        last_action_payload: Optional[Dict[str, Any]] = None,
    ) -> NextActionDecision:
        """Select next pedagogical action based on multi-factor student node state and history."""
        # 1. Fetch node state if not provided
        if not node_state and self.graph:
            node_state = self.graph.get_concept_node_state(student_id, course_id, current_concept_id)

        # Fallback default node_state if still None
        if not node_state:
            node_state = ConceptNodeState(
                concept_id=current_concept_id,
                concept_name=current_concept_id,
                topic_id="",
            )

        payload = last_action_payload or {}
        correctness = payload.get("correctness")
        action_type = payload.get("action_type")
        misconception_code = payload.get("misconception_code")
        hint_requested = action_type == "hint_requested" or payload.get("hint_requested") is True

        # Decision factors for explainability
        factors: Dict[str, Any] = {
            "mastery_score": node_state.mastery_score,
            "confidence": node_state.confidence,
            "prerequisites_satisfied": node_state.prerequisites_satisfied,
            "prerequisite_ids": node_state.prerequisite_ids,
            "total_attempts": node_state.total_attempts,
            "correct_attempts": node_state.correct_attempts,
            "incorrect_attempts": node_state.incorrect_attempts,
            "active_misconceptions": node_state.active_misconceptions,
            "review_due": node_state.review_due,
            "correctness": correctness,
            "action_type": action_type,
            "misconception_code": misconception_code,
        }

        # Rule 1: Hint Request -> HINT action
        if hint_requested:
            return NextActionDecision(
                action=NextActionType.HINT,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="QUESTION",
                reason=f"Student requested a progressive hint for {node_state.concept_name}.",
                explainability_details={**factors, "trigger": "user_hint_request"},
            )

        # Rule 2: Active Misconception / Prerequisite Unsatisfied -> REMEDIATE
        if not node_state.prerequisites_satisfied and node_state.prerequisite_ids:
            unmet_prereq = node_state.prerequisite_ids[0]
            return NextActionDecision(
                action=NextActionType.REMEDIATE,
                target_concept_id=unmet_prereq,
                target_concept_name=unmet_prereq,
                recommended_mode="REMEDIATE",
                reason=f"Prerequisite {unmet_prereq} is not sufficiently mastered (< 0.60). Directing to prerequisite remediation.",
                explainability_details={**factors, "trigger": "unsatisfied_prerequisite", "unmet_prerequisite_id": unmet_prereq},
            )

        if misconception_code or (correctness == "incorrect" and node_state.incorrect_attempts >= 2):
            misc = misconception_code or (node_state.active_misconceptions[0] if node_state.active_misconceptions else "CONCEPTUAL_ERROR")
            return NextActionDecision(
                action=NextActionType.REMEDIATE,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="REMEDIATE",
                reason=f"Detected conceptual misconception ({misc}). Switching to targeted remediation.",
                explainability_details={**factors, "trigger": "misconception_detected", "misconception_code": misc},
            )

        # Rule 3: Spaced Review Due -> REVIEW
        if node_state.review_due or node_state.mastery_status == "review_due":
            return NextActionDecision(
                action=NextActionType.REVIEW,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="SUMMARY",
                reason=f"Spaced review schedule indicates {node_state.concept_name} is due for review to prevent memory decay.",
                explainability_details={**factors, "trigger": "spaced_review_due"},
            )

        # Rule 4: High Mastery (>= 0.90) with high confidence -> CHALLENGE or ADVANCE
        if node_state.mastery_score >= 0.90 and node_state.confidence >= 0.85:
            # Advance if student has performed multiple successful assessments/practice rounds
            if node_state.correct_attempts >= 3:
                return NextActionDecision(
                    action=NextActionType.ADVANCE,
                    target_concept_id=current_concept_id,
                    target_concept_name=node_state.concept_name,
                    recommended_mode="SUMMARY",
                    reason=f"Student achieved high mastery ({node_state.mastery_score:.2f}) and sustained accuracy. Ready to advance in curriculum.",
                    explainability_details={**factors, "trigger": "high_mastery_advance"},
                )
            else:
                return NextActionDecision(
                    action=NextActionType.CHALLENGE,
                    target_concept_id=current_concept_id,
                    target_concept_name=node_state.concept_name,
                    recommended_mode="CHALLENGE",
                    reason=f"High mastery ({node_state.mastery_score:.2f}). Presenting advanced multi-step challenge question.",
                    explainability_details={**factors, "trigger": "high_mastery_challenge"},
                )

        # Rule 5: Mastery >= 0.80 -> ASSESS
        if node_state.mastery_score >= 0.80:
            return NextActionDecision(
                action=NextActionType.ASSESS,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="ASSESS",
                reason=f"Concept mastery ({node_state.mastery_score:.2f}) approaching threshold. Triggering formal assessment.",
                explainability_details={**factors, "trigger": "mastery_assessment_threshold"},
            )

        # Rule 6: New Concept / Attempts == 0 -> EXPLAIN
        if node_state.total_attempts == 0 or node_state.mastery_status == "new":
            return NextActionDecision(
                action=NextActionType.EXPLAIN,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="EXPLAIN",
                reason=f"First exposure to {node_state.concept_name}. Providing foundational concept explanation.",
                explainability_details={**factors, "trigger": "first_exposure"},
            )

        # Rule 7: Moderate Mastery (0.40 - 0.79) -> PRACTICE or CONTINUE
        if node_state.total_attempts >= 1 and correctness == "correct":
            return NextActionDecision(
                action=NextActionType.CONTINUE,
                target_concept_id=current_concept_id,
                target_concept_name=node_state.concept_name,
                recommended_mode="QUESTION",
                reason=f"Recent correct attempt. Continuing active practice sequence on {node_state.concept_name}.",
                explainability_details={**factors, "trigger": "successful_attempt_continue"},
            )

        return NextActionDecision(
            action=NextActionType.PRACTICE,
            target_concept_id=current_concept_id,
            target_concept_name=node_state.concept_name,
            recommended_mode="QUESTION",
            reason=f"Building concept foundation for {node_state.concept_name} (mastery={node_state.mastery_score:.2f}). Presenting practice problem.",
            explainability_details={**factors, "trigger": "default_practice"},
        )
