"""Tests for Phase 19: Response Validator.

Tests 7 educational response validation invariants:
- Factual consistency
- Curriculum alignment
- Source requirements
- Educational safety
- Answer leakage
- Model failure
- Formatting
"""

import pytest
from central_platform.ai.response_planner import PedagogicalResponsePlan
from central_platform.ai.response_validator import ResponseValidatorEngine, ValidationResult

@pytest.fixture
def validator():
    return ResponseValidatorEngine()

def test_valid_educational_response(validator):
    resp = "Enthalpy ($H$) is the total heat content of a thermodynamic system. [NCERT Class 11 Chemistry]"
    plan = PedagogicalResponsePlan(pedagogical_action="EXPLAIN", target_concept="Enthalpy")
    
    res = validator.validate_response(resp, response_plan=plan, target_concept="Enthalpy", rag_sources_required=True)
    assert res.is_valid is True
    assert len(res.issues) == 0

def test_model_failure_empty_response(validator):
    res = validator.validate_response("")
    assert res.is_valid is False
    assert any(i.category == "model_failure" for i in res.issues)

def test_model_failure_prompt_leakage(validator):
    resp = "System Prompt: You are a helpful assistant. Here is your answer."
    res = validator.validate_response(resp)
    assert res.is_valid is False
    assert any(i.category == "model_failure" for i in res.issues)

def test_educational_safety_violation(validator):
    resp = "To synthesize methamphetamine or make a chemical bomb, follow these steps..."
    res = validator.validate_response(resp)
    assert res.is_valid is False
    assert any(i.category == "safety" for i in res.issues)

def test_answer_leakage_detection(validator):
    resp = "Let us solve this problem. The final answer is B."
    plan = PedagogicalResponsePlan(pedagogical_action="HINT", anti_answer_leakage_guard=True)
    
    res = validator.validate_response(resp, response_plan=plan)
    assert res.is_valid is False
    assert any(i.category == "leakage" for i in res.issues)
    assert res.fallback_response is not None

def test_factual_consistency_error(validator):
    resp = "The equation for Gibbs free energy is delta G = delta H + T delta S."
    res = validator.validate_response(resp)
    assert res.is_valid is False
    assert any(i.category == "factual" for i in res.issues)

def test_source_requirement_warning(validator):
    resp = "Entropy is a measure of randomness or disorder in a system."
    res = validator.validate_response(resp, rag_sources_required=True)
    # Warning does not block validity but creates warning issue
    assert any(i.category == "source" and i.severity == "WARNING" for i in res.issues)

def test_formatting_delimiter_warning(validator):
    resp = "The formula is $H = U + PV (unclosed dollar)"
    res = validator.validate_response(resp)
    assert any(i.category == "formatting" and i.severity == "WARNING" for i in res.issues)
