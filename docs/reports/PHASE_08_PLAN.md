# Phase 08 Execution Plan — Course Tool Capability & Adapter Registry

**Document:** `docs/reports/PHASE_08_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.8)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Allow courses to enable pedagogical computational tools (e.g. chemical equation balancers, symbolic math calculators, code sandboxes, graphing engines) without coupling the generic tutor core to subject-specific implementations.

### Core Architectural Invariants for Phase 08:
1. **Decoupled Tool Registry & Adapter Architecture:**
   - Tools are registered dynamically via a modular `ToolRegistry` and exposed through standard `ToolAdapter` interfaces.
   - Subject-specific tools live entirely within isolated adapter modules (`central_platform/tools/adapters/`).
2. **Six-Point Tool Execution Guardrails:**
   Tool execution must strictly require and verify:
   - **Course Policy:** The course's active `CourseToolPolicy` explicitly enables the tool (`is_tool_enabled(tool_id) == True`). Courses with tools disabled cannot execute them.
   - **User Role:** User role permits tool invocation (`user.role in capability.allowed_roles`).
   - **Scope Containment:** Execution bounded to valid course, student, and session contexts.
   - **Input Validation:** Input arguments strictly validated against typed schemas before execution.
   - **Typed Output:** Results formatted into standardized `ToolExecutionResult` dataclasses with execution metadata.
   - **Resource Limits:** Hard execution timeouts (e.g., 5.0s max), maximum input payload size limits, and memory safety.
3. **Phase Gate Requirement:**
   The generic tutor core (`core/tutor/`, `central_platform/learning/`, `central_platform/ai/`) MUST NOT import subject-specific tool implementations directly. All access must flow through `ToolRegistry` and `ToolExecutionEngine`.

---

## 2. Forensic Findings & Implementation Strategy

1. **Current State:**
   - `core/tutor/chemistry_tools.py` provides deterministic `FormulaParser` and `ChemicalEquationBalancer`.
   - `core/runtimes/chemistry.py` line 435 directly imports `ChemicalEquationBalancer`, coupling runtime code to specific tool implementations.
   - `central_platform/models/schema.py` defines `CourseToolPolicy` (supporting `calculator`, `graphing`, `code_execution`, `equation_balancer`, `periodic_table`, and `custom_tools`), but lacks execution-level capability metadata and an execution engine.
   - No generic math calculator or programming sandbox adapter exists.
2. **Strategy:**
   - **Tool Models (`central_platform/tools/capabilities.py`):**
     - `ToolCategory` enum (`CALCULATION`, `SCIENCE`, `CODING`, `GRAPHING`, `REFERENCE`).
     - `ResourceLimits` dataclass (`timeout_seconds`, `max_input_chars`, `max_output_chars`, `max_memory_mb`).
     - `ToolCapability` dataclass (`tool_id`, `name`, `description`, `category`, `allowed_roles`, `resource_limits`, `input_schema`, `output_schema`).
     - `ToolExecutionContext` dataclass (`course_id`, `student_id`, `session_id`, `user_role`, `course_policy`).
     - `ToolExecutionResult` dataclass (`success`, `output`, `error`, `execution_time_ms`, `resource_usage`).
   - **Adapter Contract (`central_platform/tools/base.py`):**
     - Abstract `ToolAdapter` interface with `get_capabilities()`, `validate_arguments()`, and `execute()`.
   - **Registry & Execution Engine (`central_platform/tools/registry.py`, `central_platform/tools/engine.py`):**
     - `ToolRegistry`: Discovers, registers, and tracks adapters.
     - `ToolExecutionEngine`: Enforces course policy, user role, input validation, execution timeouts, and error isolation.
   - **Adapters (`central_platform/tools/adapters/`):**
     - `ChemistryToolAdapter`: Exposes `equation_balancer` and `formula_parser`.
     - `MathToolAdapter`: Exposes `calculator` with safe AST-parsed symbolic/arithmetic evaluation (zero unsafe `eval`).
     - `ProgrammingSandboxAdapter`: Exposes `code_execution` with AST syntax analysis and safe execution controls.
   - **Runtime Decoupling:**
     - Update `core/runtimes/chemistry.py` to route equation balancing queries through the tool registry rather than direct file import.
   - **REST API Routes (`central_platform/api/routes/tools.py`):**
     - `GET /api/v1/tools`: List registered tools and capabilities.
     - `GET /api/v1/tools/{course_id}`: List tools enabled for a specific course policy.
     - `POST /api/v1/tools/execute`: Execute a tool with role authorization and course policy enforcement.

---

## 3. Planned Implementation Steps

1. **Step 1: Domain Entities & Capability Models**
   - Create `central_platform/tools/capabilities.py` defining `ToolCategory`, `ResourceLimits`, `ToolCapability`, `ToolExecutionContext`, `ToolExecutionResult`.
   - Export models in `central_platform/tools/__init__.py`.
2. **Step 2: Base Tool Adapter Interface**
   - Create `central_platform/tools/base.py` with `ToolAdapter` abstract base class.
3. **Step 3: Tool Registry & Execution Engine**
   - Create `central_platform/tools/registry.py` (`ToolRegistry`).
   - Create `central_platform/tools/engine.py` (`ToolExecutionEngine`).
4. **Step 4: Tool Adapters**
   - Create `central_platform/tools/adapters/chemistry.py` (`ChemistryToolAdapter`).
   - Create `central_platform/tools/adapters/math.py` (`MathToolAdapter`).
   - Create `central_platform/tools/adapters/programming.py` (`ProgrammingSandboxAdapter`).
5. **Step 5: Runtime Decoupling**
   - Update `core/runtimes/chemistry.py` to invoke tools via `ToolRegistry` and `ToolExecutionEngine`.
6. **Step 6: Central REST API Endpoints & Schemas**
   - Add tool request/response schemas in `central_platform/api/schemas.py`.
   - Create `central_platform/api/routes/tools.py` and register on FastAPI app.
7. **Step 7: Comprehensive Test Suite & Verification**
   - Create `tests/test_phase08_course_tool_registry.py` covering:
     1. Registry discovery and capability listing.
     2. Course tool policy enablement check (enabled vs disabled).
     3. Role-based access gatekeeping.
     4. Resource limits (execution timeout).
     5. Input argument validation.
     6. Chemistry equation balancer through registry.
     7. Safe math calculator without `eval`.
     8. Programming sandbox controls.
     9. Zero-tools course policy enforcement.
     10. Phase gate architectural import isolation check.
     11. Central REST API endpoints.
8. **Step 8: Regression Testing & Evidence Reporting**
   - Run full regression suite (must achieve 921+ passing tests, 100% green).
   - Generate `docs/reports/PHASE_08_TEST_REPORT.md` and `docs/reports/PHASE_08_TEST_RESULTS.json`.
   - Update `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`.
   - Commit and push to `origin/master`.
