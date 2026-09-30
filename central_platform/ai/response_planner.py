"""Response Planner Engine for Phase 18.

Implements structured pedagogical response planning and Pydantic schema validation.
Converts query interpretation, next action decision, and assembled context into an
authoritative execution plan for response generation.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from central_platform.learning.actions import NextActionDecision, NextActionType
from central_platform.ai.context_builder import AssembledContext
from central_platform.ai.query_understanding import StructuredQueryInterpretation

logger = logging.getLogger("gayatri.response_planner")


class PedagogicalResponsePlan(BaseModel):
    """Authoritative Pydantic contract for structured response planning (Phase 18)."""
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    pedagogical_action: str = Field(default="EXPLAIN")
    recommended_mode: str = Field(default="EXPLAIN")
    learning_objective: str = Field(default="Explain concept foundations clearly.")
    scaffolding_steps: List[str] = Field(
        default_factory=lambda: [
            "Acknowledge student query",
            "Present foundational core concept",
            "Provide illustrative real-world or chemistry example",
            "Ask guiding Socratic check question"
        ]
    )
    tone_guidance: str = Field(default="Socratic and encouraging")
    anti_answer_leakage_guard: bool = Field(default=True)
    rag_sources_to_cite: List[str] = Field(default_factory=list)
    target_concept: str = Field(default="")
    validation_passed: bool = Field(default=True)

    @field_validator("pedagogical_action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = {a.value for a in NextActionType}
        v_upper = str(v).upper().strip()
        if v_upper in valid_actions:
            return v_upper
        return "EXPLAIN"


class ResponsePlannerEngine:
    """Authoritative Response Planner with SLM planning and deterministic fallback."""

    def __init__(self, slm_client: Optional[Any] = None):
        self.slm_client = slm_client

    def create_deterministic_plan(
        self,
        interpretation: StructuredQueryInterpretation,
        action_decision: NextActionDecision,
        assembled_context: Optional[AssembledContext] = None,
    ) -> PedagogicalResponsePlan:
        """Create structured pedagogical response plan using deterministic rules (infallible)."""
        action_str = action_decision.action.value if isinstance(action_decision.action, NextActionType) else str(action_decision.action)
        concept = action_decision.target_concept_name or (assembled_context.concept_id if assembled_context else "Concept")

        # 1. Determine scaffolding steps based on action
        if action_str == "EXPLAIN":
            scaffolding = [
                f"Define {concept} clearly in plain language",
                "Explain underlying physical/chemical mechanism",
                "Provide relatable chemical example or equation",
                "Ask guiding Socratic question to verify understanding"
            ]
            objective = f"Build intuitive understanding of {concept}."
            anti_leak = False
        elif action_str == "HINT":
            scaffolding = [
                "Acknowledge student attempt",
                "Highlight key principle without giving final formula/answer",
                "Provide progressive hint guiding next step"
            ]
            objective = f"Guide student through obstacle in {concept}."
            anti_leak = True
        elif action_str in ("PRACTICE", "CONTINUE"):
            scaffolding = [
                f"Pose a targeted problem on {concept}",
                "Specify required units or format",
                "Prompt student for step 1 of solution"
            ]
            objective = f"Reinforce mastery of {concept} through active problem solving."
            anti_leak = True
        elif action_str == "REMEDIATE":
            scaffolding = [
                f"Identify misconception in {concept}",
                "Explain correct conceptual model and contrast with error",
                "Check for understanding before proceeding"
            ]
            objective = f"Remediate misconception in {concept}."
            anti_leak = False
        elif action_str == "REVIEW":
            scaffolding = [
                f"Summarize key principles of {concept}",
                "Highlight common pitfalls",
                "Ask review question to refresh memory"
            ]
            objective = f"Review and consolidate {concept}."
            anti_leak = False
        elif action_str == "CHALLENGE":
            scaffolding = [
                f"Present advanced multi-step challenge on {concept}",
                "Encourage rigorous multi-concept application"
            ]
            objective = f"Challenge high-mastery student on {concept}."
            anti_leak = True
        elif action_str == "ADVANCE":
            scaffolding = [
                f"Congratulate student on mastering {concept}",
                "Introduce next concept in curriculum sequence"
            ]
            objective = f"Advance to next curriculum node."
            anti_leak = False
        else:
            scaffolding = [
                f"Respond to query regarding {concept}",
                "Ensure clarity and pedagogical alignment"
            ]
            objective = f"Address student query regarding {concept}."
            anti_leak = True

        # Extract RAG sources
        rag_sources = []
        if assembled_context and assembled_context.rag_context:
            for item in assembled_context.rag_context:
                title = item.get("source_title")
                if title and title not in rag_sources:
                    rag_sources.append(title)

        return PedagogicalResponsePlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            pedagogical_action=action_str,
            recommended_mode=action_decision.recommended_mode,
            learning_objective=objective,
            scaffolding_steps=scaffolding,
            tone_guidance="Socratic, encouraging, and clear",
            anti_answer_leakage_guard=anti_leak,
            rag_sources_to_cite=rag_sources,
            target_concept=concept,
            validation_passed=True,
        )

    def plan_response(
        self,
        interpretation: StructuredQueryInterpretation,
        action_decision: NextActionDecision,
        assembled_context: Optional[AssembledContext] = None,
        use_slm: bool = False,
    ) -> PedagogicalResponsePlan:
        """Generate structured response plan using SLM or deterministic fallback."""
        if use_slm and self.slm_client:
            try:
                slm_prompt = (
                    f"Create pedagogical response plan JSON:\n"
                    f"Action: {action_decision.action}\n"
                    f"Concept: {action_decision.target_concept_name}\n"
                    f"Output JSON with keys: pedagogical_action, recommended_mode, "
                    f"learning_objective, scaffolding_steps, tone_guidance, anti_answer_leakage_guard"
                )
                raw_response = self.slm_client.generate(slm_prompt)
                
                if isinstance(raw_response, dict):
                    data = raw_response
                else:
                    match = re.search(r"\{.*\}", str(raw_response), re.DOTALL)
                    if not match:
                        raise ValueError("No valid JSON found in SLM response")
                    data = json.loads(match.group(0))

                plan = PedagogicalResponsePlan(**data)
                return plan
            except Exception as exc:
                logger.warning(f"SLM planning failed or validation error ({exc}); using fallback planner.")

        return self.create_deterministic_plan(interpretation, action_decision, assembled_context)
