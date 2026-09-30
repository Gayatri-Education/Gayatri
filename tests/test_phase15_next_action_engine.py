"""Tests for Phase 15: Next Action Engine.

Tests selection of all 9 canonical next actions:
- CONTINUE
- EXPLAIN
- HINT
- REMEDIATE
- PRACTICE
- REVIEW
- ASSESS
- CHALLENGE
- ADVANCE

Verifies explainability details structure for every decision.
"""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.learning.actions import NextActionEngine, NextActionType
from central_platform.learning.graph import ConceptNodeState

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 15 tests."""
    db_file = str(tmp_path / "phase15_actions.db")
    return PlatformDatabase(db_file)

def test_action_hint_requested():
    """Test HINT action when hint is requested."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(concept_id="cpt_1", concept_name="Thermodynamics", topic_id="t1")
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state, {"action_type": "hint_requested"})
    assert decision.action == NextActionType.HINT
    assert decision.recommended_mode == "QUESTION"
    assert "explainability_details" in decision.to_dict()
    assert decision.explainability_details["trigger"] == "user_hint_request"

def test_action_remediate_unsatisfied_prerequisite():
    """Test REMEDIATE action when prerequisite is unsatisfied."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_advanced",
        concept_name="Advanced Thermodynamics",
        topic_id="t1",
        prerequisites_satisfied=False,
        prerequisite_ids=["cpt_basic_heat"]
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_advanced", node_state)
    assert decision.action == NextActionType.REMEDIATE
    assert decision.target_concept_id == "cpt_basic_heat"
    assert decision.recommended_mode == "REMEDIATE"
    assert "prerequisite" in decision.reason.lower()

def test_action_remediate_misconception():
    """Test REMEDIATE action when misconception is present."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Enthalpy",
        topic_id="t1",
        active_misconceptions=["HEAT_VS_ENTHALPY_CONFUSION"]
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state, {"misconception_code": "HEAT_VS_ENTHALPY_CONFUSION"})
    assert decision.action == NextActionType.REMEDIATE
    assert decision.recommended_mode == "REMEDIATE"

def test_action_review():
    """Test REVIEW action when review is due."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Heat Capacity",
        topic_id="t1",
        review_due=True
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state)
    assert decision.action == NextActionType.REVIEW
    assert decision.recommended_mode == "SUMMARY"

def test_action_challenge_high_mastery():
    """Test CHALLENGE action when student has high mastery."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Gibbs Free Energy",
        topic_id="t1",
        mastery_score=0.92,
        confidence=0.90,
        correct_attempts=1
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state)
    assert decision.action == NextActionType.CHALLENGE
    assert decision.recommended_mode == "CHALLENGE"

def test_action_advance_high_mastery_and_sustained():
    """Test ADVANCE action when student has high mastery and sustained success."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Gibbs Free Energy",
        topic_id="t1",
        mastery_score=0.95,
        confidence=0.92,
        correct_attempts=4
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state)
    assert decision.action == NextActionType.ADVANCE

def test_action_assess_threshold():
    """Test ASSESS action when mastery is near assessment threshold."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Entropy",
        topic_id="t1",
        mastery_score=0.82,
        confidence=0.80
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state)
    assert decision.action == NextActionType.ASSESS
    assert decision.recommended_mode == "ASSESS"

def test_action_explain_first_exposure():
    """Test EXPLAIN action on first exposure to new concept."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_new",
        concept_name="Quantum Chemistry",
        topic_id="t1",
        total_attempts=0,
        mastery_status="new"
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_new", node_state)
    assert decision.action == NextActionType.EXPLAIN
    assert decision.recommended_mode == "EXPLAIN"

def test_action_continue():
    """Test CONTINUE action after successful attempt in practice sequence."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Bonding",
        topic_id="t1",
        mastery_score=0.65,
        total_attempts=2
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state, {"correctness": "correct"})
    assert decision.action == NextActionType.CONTINUE
    assert decision.recommended_mode == "QUESTION"

def test_action_practice():
    """Test PRACTICE action for default practicing concept."""
    engine = NextActionEngine()
    node_state = ConceptNodeState(
        concept_id="cpt_1",
        concept_name="Bonding",
        topic_id="t1",
        mastery_score=0.50,
        total_attempts=1
    )
    
    decision = engine.decide_next_action("u1", "crs1", "cpt_1", node_state)
    assert decision.action == NextActionType.PRACTICE
    assert decision.recommended_mode == "QUESTION"
