"""Phase 19: Chemistry Adapter Extraction & Disablement Test Suite.

Master Plan Section 12.19 Requirements:
1. Convert existing Chemistry behavior into a first-class adapter.
2. Generic core cannot import Chemistry adapter implementation directly.
3. Course configuration selects adapter capabilities.
4. Run platform with adapter disabled; all generic platform operations succeed.
5. Chemistry course with adapter enabled; specialized tools and evaluators function.
6. Cross-course isolation: non-Chemistry courses do not load Chemistry modules.
"""

import os
import pytest
from typing import Any, Dict

from central_platform.adapters.chemistry.adapter import (
    ChemistryDomainAdapter,
    DEFAULT_CHEMISTRY_MISCONCEPTIONS,
    get_chemistry_domain_adapter,
    is_chemistry_adapter_enabled,
)
from central_platform.assessment.evaluators.base import EvaluationStatus
from central_platform.assessment.evaluators.registry import EvaluatorRegistry
from central_platform.models.schema import CourseToolPolicy, UserRole
from central_platform.tools import (
    ToolExecutionContext,
    ToolExecutionEngine,
    ToolNotFoundError,
    get_configured_tool_registry,
    get_default_registry,
)


@pytest.fixture(autouse=True)
def reset_chemistry_adapter_state():
    """Ensure chemistry adapter state is cleanly restored after each test."""
    adapter = get_chemistry_domain_adapter()
    adapter.enable()
    reg = get_default_registry()
    reg.clear()
    get_configured_tool_registry(include_chemistry=True)
    yield
    adapter.enable()
    reg.clear()
    get_configured_tool_registry(include_chemistry=True)


# ── Test 1: Chemistry Domain Adapter Interface Contract ───────────────────────

def test_chemistry_domain_adapter_contract():
    """Verify ChemistryDomainAdapter implements standard domain adapter contract."""
    adapter = get_chemistry_domain_adapter()
    assert adapter.DOMAIN_NAME == "chemistry"
    assert adapter.is_enabled is True

    # 1. Tool adapter
    tool_ad = adapter.get_tool_adapter()
    assert tool_ad is not None
    caps = tool_ad.get_capabilities()
    cap_ids = [c.tool_id for c in caps]
    assert "equation_balancer" in cap_ids
    assert "formula_parser" in cap_ids

    # 2. Evaluators
    evaluators = adapter.get_evaluators()
    assert len(evaluators) >= 1
    assert any(ev.supports_type("EQUATION_BALANCING") for ev in evaluators)

    # 3. Curriculum adapter
    curr_ad = adapter.get_curriculum_adapter()
    assert curr_ad is not None
    assert curr_ad.course_id == "chemistry"

    # 4. Entity normalizer
    norm = adapter.get_entity_normalizer()
    assert norm is not None
    assert hasattr(norm, "normalize_latex")

    # 5. Misconceptions catalog
    miscs = adapter.get_misconceptions()
    assert len(miscs) >= 4
    misc_codes = [m["code"] for m in miscs]
    assert "MISC-BOND-BREAK" in misc_codes
    assert "MISC-EQUIL-STATIC" in misc_codes

    # 6. Capabilities summary
    summary = adapter.get_capabilities_summary()
    assert summary["domain"] == "chemistry"
    assert summary["is_enabled"] is True
    assert "equation_balancer" in summary["tool_capabilities"]


# ── Test 2: Platform Startup with Chemistry Disabled ─────────────────────────

def test_platform_startup_with_chemistry_disabled():
    """Verify tool and evaluator registries initialize without errors when Chemistry is disabled."""
    adapter = get_chemistry_domain_adapter()
    adapter.disable()
    assert is_chemistry_adapter_enabled() is False

    reg = get_default_registry()
    reg.clear()
    configured_reg = get_configured_tool_registry(include_chemistry=False)

    # Registry has tools, but zero chemistry tools
    caps = configured_reg.list_capabilities()
    cap_ids = [c.tool_id for c in caps]
    assert "equation_balancer" not in cap_ids
    assert "formula_parser" not in cap_ids
    assert "calculator" in cap_ids
    assert "code_execution" in cap_ids

    # Evaluator registry initializes cleanly
    eval_reg = EvaluatorRegistry()
    eval_reg.set_domain_evaluator_enabled("chemistry", False)
    assert not any("chemistry" in ev.__class__.__name__.lower() for ev in eval_reg._evaluators)


# ── Test 3: Tool Registry Omits Chemistry When Disabled ──────────────────────

def test_tool_registry_omits_chemistry_when_disabled():
    """Verify ToolRegistry omits chemistry tools when disabled even under an all-enabled policy."""
    configured_reg = get_configured_tool_registry(include_chemistry=False)
    assert configured_reg.get_capability("equation_balancer") is None
    assert configured_reg.get_capability("formula_parser") is None

    # Even if CourseToolPolicy enables all tools, chemistry tools are not returned
    all_enabled_policy = CourseToolPolicy(
        calculator=True,
        equation_balancer=True,
        code_execution=True,
    )
    tools = configured_reg.list_tools_for_policy(all_enabled_policy)
    tool_ids = [t.tool_id for t in tools]
    assert "equation_balancer" not in tool_ids
    assert "calculator" in tool_ids
    assert "code_execution" in tool_ids


# ── Test 4: Tool Execution Rejection When Chemistry Disabled ─────────────────

def test_tool_execution_rejection_when_chemistry_disabled():
    """Verify ToolExecutionEngine rejects chemistry tools with ToolNotFoundError when disabled."""
    reg = get_configured_tool_registry(include_chemistry=False)
    engine = ToolExecutionEngine(reg)

    policy = CourseToolPolicy(equation_balancer=True)
    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    with pytest.raises(ToolNotFoundError) as exc_info:
        engine.execute_tool(
            tool_id="equation_balancer",
            arguments={"equation": "H2 + O2 -> H2O"},
            context=ctx,
            strict_exceptions=True,
        )
    assert "equation_balancer" in str(exc_info.value)


# ── Test 5: Evaluator Registry Graceful Fallback When Disabled ────────────────

def test_evaluator_registry_graceful_fallback_when_disabled():
    """Verify EvaluatorRegistry falls back to RubricEvaluator for chemical items without crashing."""
    eval_reg = EvaluatorRegistry()
    eval_reg.set_domain_evaluator_enabled("chemistry", False)

    # Item with item_type="EQUATION_BALANCING"
    class DummyItem:
        id = "item-chem-01"
        item_type = "EQUATION_BALANCING"
        rubric = None
        correct_answer = "2H2 + O2 -> 2H2O"

    outcome = eval_reg.evaluate(
        item=DummyItem(),
        student_answer="2H2 + O2 -> 2H2O",
        context={"course_id": "crs-general-science"},
    )
    # Falls back gracefully to default rubric evaluator instead of raising an unhandled exception
    assert outcome is not None
    assert outcome.score is not None


# ── Test 6: Chemistry Enabled Tools Execute Accurately ────────────────────────

def test_chemistry_enabled_tools_execute():
    """Verify equation_balancer and formula_parser execute accurately when enabled."""
    reg = get_configured_tool_registry(include_chemistry=True)
    engine = ToolExecutionEngine(reg)

    policy = CourseToolPolicy(
        equation_balancer=True,
        custom_tools={"formula_parser": True},
    )
    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # 1. Equation Balancer
    res_bal = engine.execute_tool(
        "equation_balancer",
        {"equation": "H2 + O2 -> H2O"},
        ctx,
    )
    assert res_bal.success is True
    assert "2H2 + O2 -> 2H2O" in res_bal.output.get("balanced_equation", "")

    # 2. Formula Parser
    res_parse = engine.execute_tool(
        "formula_parser",
        {"formula": "H2SO4"},
        ctx,
    )
    assert res_parse.success is True
    assert res_parse.output.get("elements") == {"H": 2, "S": 1, "O": 4}


# ── Test 7: Chemistry Enabled Evaluator Scores Accurately ────────────────────

def test_chemistry_enabled_evaluator_scores_accurately():
    """Verify ChemistryEquationEvaluator accurately evaluates balanced chemical equations."""
    eval_reg = EvaluatorRegistry()
    eval_reg.set_domain_evaluator_enabled("chemistry", True)

    class DummyChemicalItem:
        id = "item-eq-01"
        item_type = "EQUATION_BALANCING"
        correct_answer = "2H2 + O2 -> 2H2O"

    # Correct submission
    outcome_correct = eval_reg.evaluate(
        item=DummyChemicalItem(),
        student_answer="2H2 + O2 -> 2H2O",
    )
    assert outcome_correct.outcome == EvaluationStatus.CORRECT
    assert outcome_correct.score == 1.0

    # Incorrect/unbalanced submission
    outcome_incorrect = eval_reg.evaluate(
        item=DummyChemicalItem(),
        student_answer="H2 + O2 -> H2O",
    )
    assert outcome_incorrect.outcome == EvaluationStatus.INCORRECT
    assert outcome_incorrect.score == 0.0


# ── Test 8: Math and Coding Unaffected by Chemistry Disablement ──────────────

def test_math_and_coding_unaffected_by_chemistry_disablement():
    """Verify Math and Programming tools/evaluators function with 100% fidelity when Chemistry is disabled."""
    reg = get_configured_tool_registry(include_chemistry=False)
    engine = ToolExecutionEngine(reg)

    policy = CourseToolPolicy(calculator=True, code_execution=True)
    ctx = ToolExecutionContext(
        course_id="crs-math-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # 1. Math Calculator
    res_calc = engine.execute_tool(
        "calculator",
        {"expression": "15 * 4 + 10"},
        ctx,
    )
    assert res_calc.success is True
    assert res_calc.output.get("result") == 70.0

    # 2. Python Code Execution
    res_code = engine.execute_tool(
        "code_execution",
        {"code": "x = [i**2 for i in range(5)]; print(sum(x))"},
        ctx,
    )
    assert res_code.success is True
    assert "30" in res_code.output.get("stdout", "")


# ── Test 9: Non-Chemistry Course Isolation ────────────────────────────────────

def test_non_chemistry_course_isolation():
    """Verify non-Chemistry courses return False for can_handle_course."""
    adapter = get_chemistry_domain_adapter()
    assert adapter.can_handle_course("crs-chem-101") is True
    assert adapter.can_handle_course("Organic Chemistry") is True
    assert adapter.can_handle_course("crs-math-101") is False
    assert adapter.can_handle_course("crs-python-101") is False
    assert adapter.can_handle_course("crs-history-9") is False

    # When disabled, returns False for all
    adapter.disable()
    assert adapter.can_handle_course("crs-chem-101") is False


# ── Test 10: Concept Keyword Matcher Disabled for Generic Courses ─────────────

def test_concept_keyword_matcher_disabled_for_generic_courses():
    """Verify generic queries do not trigger Chemistry concept keyword matcher when disabled."""
    adapter = get_chemistry_domain_adapter()
    curr_ad = adapter.get_curriculum_adapter()

    # Enabled: matches chemistry keywords
    res = curr_ad.match_concept("What is the vsepr molecular geometry of ammonia?")
    assert res is not None
    assert res["concept_id"] == "chem_inorg_vsepr"

    # Disabled: returns None
    curr_ad.is_enabled = False
    res_disabled = curr_ad.match_concept("What is the vsepr molecular geometry of ammonia?")
    assert res_disabled is None


# ── Test 11: Runtime Dynamic Toggle ──────────────────────────────────────────

def test_runtime_dynamic_toggle():
    """Verify dynamic toggle updates ToolRegistry capabilities immediately without restart."""
    reg = get_default_registry()
    reg.clear()

    # Start enabled
    get_configured_tool_registry(include_chemistry=True)
    assert reg.get_capability("equation_balancer") is not None

    # Toggle disable
    get_configured_tool_registry(include_chemistry=False)
    assert reg.get_capability("equation_balancer") is None
    assert reg.get_capability("calculator") is not None

    # Toggle re-enable
    get_configured_tool_registry(include_chemistry=True)
    assert reg.get_capability("equation_balancer") is not None


# ── Test 12: Environment Variable Configuration Disablement ──────────────────

def test_env_var_configuration_disablement(monkeypatch):
    """Verify GAYATRI_ENABLE_CHEMISTRY_ADAPTER=0 disables adapter during instantiation."""
    monkeypatch.setenv("GAYATRI_ENABLE_CHEMISTRY_ADAPTER", "0")
    adapter = ChemistryDomainAdapter()
    assert adapter.is_enabled is False
    assert adapter.get_tool_adapter() is None
    assert adapter.get_evaluators() == []
    assert adapter.get_curriculum_adapter() is None
    assert adapter.get_misconceptions() == []
