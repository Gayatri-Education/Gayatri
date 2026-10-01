"""Gayatri AI Platform — Phase 08: Course Tool Capability & Adapter Registry Test Suite.

Verifies:
1. Tool registry dynamic registration and capability discovery.
2. Course tool policy enablement check (enabled vs disabled).
3. Zero-tools course policy enforcement.
4. Role-based access control for tool execution.
5. Resource limits enforcement (timeout aborts execution).
6. Input argument validation and schema rejection.
7. Chemistry tool adapter (equation balancer & formula parser) through registry.
8. Safe math calculator tool adapter (AST evaluation, zero unsafe eval, blocked code injection).
9. Programming sandbox tool adapter (syntax validation, stdout capture, blocked imports).
10. Phase gate architecture invariant: generic tutor core does not import subject-specific tool modules.
11. Central REST API endpoints: GET /tools, GET /tools/{course_id}, POST /tools/execute.
"""

from __future__ import annotations

import ast
import os
import time
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.models.schema import CourseToolPolicy, UserRole
from central_platform.tools import (
    ChemistryToolAdapter,
    CourseToolPolicyViolation,
    MathToolAdapter,
    ProgrammingSandboxAdapter,
    ResourceLimits,
    ToolAuthorizationError,
    ToolCapability,
    ToolCategory,
    ToolExecutionContext,
    ToolExecutionEngine,
    ToolExecutionResult,
    ToolNotFoundError,
    ToolRegistry,
    ToolTimeoutError,
    ToolValidationError,
    get_configured_tool_registry,
)
from central_platform.tools.base import ToolAdapter


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def student_auth_headers():
    token = create_access_token(
        user_id="stu-dev-01",
        role="STUDENT",
        organization_id="org-default",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_auth_headers():
    token = create_access_token(
        user_id="tchr-science-01",
        role="TEACHER",
        organization_id="org-default",
    )
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registry & Policy Enforcement
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_registry_registration_and_discovery():
    """Verify tool adapters register and publish capabilities correctly."""
    registry = ToolRegistry()
    chem_adapter = ChemistryToolAdapter()
    math_adapter = MathToolAdapter()

    registry.register_adapter(chem_adapter)
    registry.register_adapter(math_adapter)

    caps = registry.list_capabilities()
    cap_ids = [c.tool_id for c in caps]
    assert "equation_balancer" in cap_ids
    assert "formula_parser" in cap_ids
    assert "calculator" in cap_ids

    # Lookup by tool ID
    assert registry.get_adapter("equation_balancer") is chem_adapter
    assert registry.get_adapter("calculator") is math_adapter
    assert registry.get_adapter("unknown_tool") is None


def test_course_tool_policy_enablement_and_filtering():
    """Verify CourseToolPolicy filters available tools and engine blocks disabled tools."""
    registry = ToolRegistry()
    registry.register_adapter(ChemistryToolAdapter())
    registry.register_adapter(MathToolAdapter())
    engine = ToolExecutionEngine(registry)

    # Policy enables equation_balancer, disables calculator
    policy = CourseToolPolicy(equation_balancer=True, calculator=False)
    enabled_tools = registry.list_tools_for_policy(policy)
    enabled_ids = [t.tool_id for t in enabled_tools]
    assert "equation_balancer" in enabled_ids
    assert "calculator" not in enabled_ids

    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # Enabled tool succeeds
    res_enabled = engine.execute_tool(
        "equation_balancer",
        {"equation": "H2 + O2 -> H2O"},
        ctx,
    )
    assert res_enabled.success is True
    assert res_enabled.output["balanced_equation"] == "2H2 + O2 -> 2H2O"

    # Disabled tool fails policy check
    res_disabled = engine.execute_tool(
        "calculator",
        {"expression": "2 + 2"},
        ctx,
    )
    assert res_disabled.success is False
    assert "disabled by course policy" in res_disabled.error

    # Strict exception mode
    with pytest.raises(CourseToolPolicyViolation):
        engine.execute_tool(
            "calculator",
            {"expression": "2 + 2"},
            ctx,
            strict_exceptions=True,
        )


def test_zero_tools_course_policy():
    """Verify a course with all tools disabled cannot execute any tool."""
    registry = get_configured_tool_registry()
    engine = ToolExecutionEngine(registry)

    zero_policy = CourseToolPolicy(
        calculator=False,
        graphing=False,
        code_execution=False,
        equation_balancer=False,
        periodic_table=False,
    )
    ctx = ToolExecutionContext(
        course_id="crs-humanities-101",
        user_role=UserRole.STUDENT,
        course_policy=zero_policy,
    )

    assert registry.list_tools_for_policy(zero_policy) == []

    res = engine.execute_tool("calculator", {"expression": "100 * 5"}, ctx)
    assert res.success is False
    assert "disabled by course policy" in res.error


def test_role_based_access_control_for_tools():
    """Verify tools with role restrictions gate student vs teacher invocation."""
    registry = ToolRegistry()

    # Create mock teacher-only tool
    class TeacherOnlyAdapter(ToolAdapter):
        def get_capabilities(self):
            return [
                ToolCapability(
                    tool_id="rubric_grader",
                    name="Teacher Rubric Grader",
                    description="Automated assignment rubric grading.",
                    category=ToolCategory.REFERENCE,
                    allowed_roles=[UserRole.TEACHER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN],
                )
            ]

        def validate_arguments(self, tool_id, arguments):
            return True

        def execute(self, tool_id, arguments, context):
            return ToolExecutionResult(success=True, output="Graded successfully")

    registry.register_adapter(TeacherOnlyAdapter())
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(custom_tools={"rubric_grader": True})

    # Student context
    student_ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )
    res_student = engine.execute_tool("rubric_grader", {}, student_ctx)
    assert res_student.success is False
    assert "is not authorized" in res_student.error

    with pytest.raises(ToolAuthorizationError):
        engine.execute_tool("rubric_grader", {}, student_ctx, strict_exceptions=True)

    # Teacher context
    teacher_ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.TEACHER,
        course_policy=policy,
    )
    res_teacher = engine.execute_tool("rubric_grader", {}, teacher_ctx)
    assert res_teacher.success is True
    assert res_teacher.output == "Graded successfully"


def test_resource_limits_timeout_enforcement():
    """Verify tool execution exceeding declared timeout aborts."""
    registry = ToolRegistry()

    class SleepyToolAdapter(ToolAdapter):
        def get_capabilities(self):
            return [
                ToolCapability(
                    tool_id="sleepy_tool",
                    name="Slow Simulator",
                    description="Simulates long running computation.",
                    category=ToolCategory.CALCULATION,
                    resource_limits=ResourceLimits(timeout_seconds=0.1),
                )
            ]

        def validate_arguments(self, tool_id, arguments):
            return True

        def execute(self, tool_id, arguments, context):
            time.sleep(0.5)
            return ToolExecutionResult(success=True, output="Completed")

    registry.register_adapter(SleepyToolAdapter())
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(custom_tools={"sleepy_tool": True})
    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    res = engine.execute_tool("sleepy_tool", {}, ctx)
    assert res.success is False
    assert "timed out" in res.error

    with pytest.raises(ToolTimeoutError):
        engine.execute_tool("sleepy_tool", {}, ctx, strict_exceptions=True)


def test_input_schema_validation_and_rejection():
    """Verify malformed or missing arguments are rejected before tool execution."""
    registry = get_configured_tool_registry()
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(equation_balancer=True, calculator=True)
    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # Missing required argument for equation balancer
    res = engine.execute_tool("equation_balancer", {}, ctx)
    assert res.success is False
    assert "failed input validation" in res.error

    # Missing expression for calculator
    res_calc = engine.execute_tool("calculator", {"wrong_key": 123}, ctx)
    assert res_calc.success is False
    assert "failed input validation" in res_calc.error


# ─────────────────────────────────────────────────────────────────────────────
# 2. Specific Domain Tool Adapters
# ─────────────────────────────────────────────────────────────────────────────

def test_chemistry_equation_balancer_via_registry():
    """Verify stoichiometric equation balancer and formula parser via registry."""
    registry = get_configured_tool_registry()
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(equation_balancer=True, custom_tools={"formula_parser": True})
    ctx = ToolExecutionContext(
        course_id="crs-chem-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # 1. Complex reaction balancing: Fe + O2 -> Fe2O3
    res_fe = engine.execute_tool("equation_balancer", {"equation": "Fe + O2 -> Fe2O3"}, ctx)
    assert res_fe.success is True
    assert res_fe.output["balanced_equation"] == "4Fe + 3O2 -> 2Fe2O3"
    assert res_fe.resource_usage["algorithm"] == "matrix_nullspace"

    # 2. Acid-base neutralization: HCl + Ca(OH)2 -> CaCl2 + H2O
    res_ab = engine.execute_tool("equation_balancer", {"equation": "HCl + Ca(OH)2 -> CaCl2 + H2O"}, ctx)
    assert res_ab.success is True
    assert res_ab.output["balanced_equation"] == "2HCl + Ca(OH)2 -> CaCl2 + 2H2O"

    # 3. Formula parser
    res_form = engine.execute_tool("formula_parser", {"formula": "Fe2(SO4)3"}, ctx)
    assert res_form.success is True
    assert res_form.output["elements"] == {"Fe": 2, "S": 3, "O": 12}
    assert res_form.resource_usage["atom_count"] == 17


def test_math_calculator_via_registry_safe_ast():
    """Verify math calculator evaluates mathematical expressions and blocks code injection."""
    registry = get_configured_tool_registry()
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(calculator=True)
    ctx = ToolExecutionContext(
        course_id="crs-math-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # 1. Valid arithmetic & order of operations
    res_arith = engine.execute_tool("calculator", {"expression": "2 + 3 * 4"}, ctx)
    assert res_arith.success is True
    assert res_arith.output["result"] == 14

    # 2. Exponentiation
    res_pow = engine.execute_tool("calculator", {"expression": "2^10"}, ctx)
    assert res_pow.success is True
    assert res_pow.output["result"] == 1024

    # 3. Safe functions and constants
    res_fn = engine.execute_tool("calculator", {"expression": "sqrt(144) + sin(pi / 2)"}, ctx)
    assert res_fn.success is True
    assert pytest.approx(res_fn.output["result"], 0.0001) == 13.0

    # 4. Zero division handling
    res_div0 = engine.execute_tool("calculator", {"expression": "10 / 0"}, ctx)
    assert res_div0.success is False
    assert "Division by zero" in res_div0.error

    # 5. Security injection attempts blocked
    injections = [
        "__import__('os').system('ls')",
        "eval('1+1')",
        "open('some_file.txt')",
        "lambda x: x",
    ]
    for attack in injections:
        res_attack = engine.execute_tool("calculator", {"expression": attack}, ctx)
        assert res_attack.success is False
        assert any(
            phrase in res_attack.error
            for phrase in [
                "Disallowed syntax",
                "not permitted",
                "not defined",
                "Unsupported function",
                "Calculation error",
            ]
        )


def test_programming_sandbox_syntax_and_execution():
    """Verify programming sandbox validates syntax, runs safe code, and blocks dangerous calls."""
    registry = get_configured_tool_registry()
    engine = ToolExecutionEngine(registry)
    policy = CourseToolPolicy(code_execution=True)
    ctx = ToolExecutionContext(
        course_id="crs-cs-101",
        user_role=UserRole.STUDENT,
        course_policy=policy,
    )

    # 1. Syntax validation only
    valid_code = "total = sum([x * 2 for x in range(5)])"
    res_syn = engine.execute_tool("code_execution", {"code": valid_code, "mode": "syntax_only"}, ctx)
    assert res_syn.success is True
    assert res_syn.output["syntax_valid"] is True

    # 2. Syntax error detection
    bad_code = "def broken(:\n    pass"
    res_bad = engine.execute_tool("code_execution", {"code": bad_code}, ctx)
    assert res_bad.success is False
    assert "Syntax error" in res_bad.error

    # 3. Safe execution with stdout and variable capture
    exec_code = "print('Hello from Gayatri sandbox!')\nx = 10\ny = 20\nz = x + y"
    res_exec = engine.execute_tool("code_execution", {"code": exec_code}, ctx)
    assert res_exec.success is True
    assert "Hello from Gayatri sandbox!" in res_exec.output["stdout"]
    assert res_exec.output["variables"]["z"] == "30"

    # 4. Blocked forbidden imports
    forbidden_code = "import os\nos.system('dir')"
    res_forb = engine.execute_tool("code_execution", {"code": forbidden_code}, ctx)
    assert res_forb.success is False
    assert "forbidden module 'os'" in res_forb.error


# ─────────────────────────────────────────────────────────────────────────────
# 3. Phase Gate Architecture Invariant Test
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_gate_architecture_zero_subject_tool_import_in_core():
    """Phase Gate: Generic tutor core and AI layers must NOT directly import chemistry_tools."""
    forbidden_target = "chemistry_tools"
    core_dirs = [
        os.path.join("core", "session.py"),
        os.path.join("core", "runtimes", "general.py"),
        os.path.join("central_platform", "courses", "service.py"),
        os.path.join("central_platform", "learning", "state.py"),
    ]

    for file_path in core_dirs:
        if not os.path.exists(file_path):
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert forbidden_target not in alias.name, (
                        f"Direct coupling violation in {file_path}: 'import {alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert forbidden_target not in node.module, (
                        f"Direct coupling violation in {file_path}: 'from {node.module} import ...'"
                    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. REST API Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_api_tools_endpoints_and_execution(api_client, student_auth_headers, teacher_auth_headers):
    """Verify REST API exposes tools and executes them under policy controls."""
    # 1. List all tools
    resp_list = api_client.get("/api/v1/tools", headers=student_auth_headers)
    assert resp_list.status_code == 200
    caps = resp_list.json()["data"]
    tool_ids = [c["tool_id"] for c in caps]
    assert "equation_balancer" in tool_ids
    assert "calculator" in tool_ids
    assert "code_execution" in tool_ids

    # 2. List tools for specific course
    resp_crs = api_client.get("/api/v1/tools/crs-chem-101", headers=student_auth_headers)
    assert resp_crs.status_code == 200
    assert len(resp_crs.json()["data"]) >= 1

    # 3. Execute math calculator via API
    resp_exec = api_client.post(
        "/api/v1/tools/execute",
        json={
            "tool_id": "calculator",
            "arguments": {"expression": "25 * 4 + 10"},
            "course_id": "crs-chem-101",
        },
        headers=student_auth_headers,
    )
    assert resp_exec.status_code == 200
    data = resp_exec.json()["data"]
    assert data["success"] is True
    assert data["output"]["result"] == 110

    # 4. Execute equation balancer via API
    resp_eq = api_client.post(
        "/api/v1/tools/execute",
        json={
            "tool_id": "equation_balancer",
            "arguments": {"equation": "CH4 + O2 -> CO2 + H2O"},
            "course_id": "crs-chem-101",
        },
        headers=student_auth_headers,
    )
    assert resp_eq.status_code == 200
    assert resp_eq.json()["data"]["success"] is True
    assert resp_eq.json()["data"]["output"]["balanced_equation"] == "CH4 + 2O2 -> CO2 + 2H2O"

    # 5. Invalid arguments return 422
    resp_bad = api_client.post(
        "/api/v1/tools/execute",
        json={
            "tool_id": "equation_balancer",
            "arguments": {},
            "course_id": "crs-chem-101",
        },
        headers=student_auth_headers,
    )
    assert resp_bad.status_code == 422
