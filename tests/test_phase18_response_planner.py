"""Tests for Phase 18: Response Planner.

Tests structured pedagogical planning and Pydantic schema validation.
"""

import pytest
from central_platform.learning.actions import NextActionDecision, NextActionType
from central_platform.ai.context_builder import AssembledContext
from central_platform.ai.query_understanding import StructuredQueryInterpretation
from central_platform.ai.response_planner import PedagogicalResponsePlan, ResponsePlannerEngine

class MockSLMPlanner:
    def __init__(self, response_dict=None, should_fail=False):
        self.response_dict = response_dict or {
            "pedagogical_action": "EXPLAIN",
            "recommended_mode": "EXPLAIN",
            "learning_objective": "Explain thermodynamics",
            "scaffolding_steps": ["Step 1", "Step 2"],
            "tone_guidance": "Encouraging",
            "anti_answer_leakage_guard": False
        }
        self.should_fail = should_fail

    def generate(self, prompt: str):
        if self.should_fail:
            return "Non-JSON response"
        return self.response_dict

def test_pedagogical_response_plan_schema():
    plan = PedagogicalResponsePlan(
        pedagogical_action="EXPLAIN",
        target_concept="Entropy",
        learning_objective="Understand entropy"
    )
    assert plan.plan_id.startswith("plan_")
    assert plan.pedagogical_action == "EXPLAIN"
    assert plan.target_concept == "Entropy"
    assert plan.validation_passed is True

def test_deterministic_plan_explain():
    engine = ResponsePlannerEngine()
    interp = StructuredQueryInterpretation(intent="concept_explanation")
    action = NextActionDecision(
        action=NextActionType.EXPLAIN,
        target_concept_id="cpt_1",
        target_concept_name="Thermodynamics",
        recommended_mode="EXPLAIN",
        reason="First exposure"
    )
    
    plan = engine.create_deterministic_plan(interp, action)
    assert plan.pedagogical_action == "EXPLAIN"
    assert "Thermodynamics" in plan.learning_objective
    assert len(plan.scaffolding_steps) >= 3
    assert plan.anti_answer_leakage_guard is False

def test_deterministic_plan_hint():
    engine = ResponsePlannerEngine()
    interp = StructuredQueryInterpretation(intent="hint")
    action = NextActionDecision(
        action=NextActionType.HINT,
        target_concept_id="cpt_1",
        target_concept_name="Work Calculation",
        recommended_mode="QUESTION",
        reason="Hint requested"
    )
    
    plan = engine.create_deterministic_plan(interp, action)
    assert plan.pedagogical_action == "HINT"
    assert plan.anti_answer_leakage_guard is True

def test_deterministic_plan_remediate():
    engine = ResponsePlannerEngine()
    interp = StructuredQueryInterpretation(intent="remediation")
    action = NextActionDecision(
        action=NextActionType.REMEDIATE,
        target_concept_id="cpt_1",
        target_concept_name="Heat Capacity",
        recommended_mode="REMEDIATE",
        reason="Misconception detected"
    )
    
    plan = engine.create_deterministic_plan(interp, action)
    assert plan.pedagogical_action == "REMEDIATE"
    assert "misconception" in plan.learning_objective.lower()

def test_slm_plan_response_success():
    slm = MockSLMPlanner()
    engine = ResponsePlannerEngine(slm_client=slm)
    interp = StructuredQueryInterpretation()
    action = NextActionDecision(action=NextActionType.EXPLAIN, target_concept_id="cpt1", target_concept_name="Thermo", recommended_mode="EXPLAIN", reason="Explain")
    
    plan = engine.plan_response(interp, action, use_slm=True)
    assert plan.learning_objective == "Explain thermodynamics"
    assert plan.scaffolding_steps == ["Step 1", "Step 2"]

def test_slm_plan_response_fallback_on_error():
    slm = MockSLMPlanner(should_fail=True)
    engine = ResponsePlannerEngine(slm_client=slm)
    interp = StructuredQueryInterpretation()
    action = NextActionDecision(action=NextActionType.PRACTICE, target_concept_id="cpt1", target_concept_name="Thermo", recommended_mode="QUESTION", reason="Practice")
    
    plan = engine.plan_response(interp, action, use_slm=True)
    assert plan.pedagogical_action == "PRACTICE"
    assert plan.anti_answer_leakage_guard is True
