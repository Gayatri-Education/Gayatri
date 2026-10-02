# Phase 19 Implementation Plan: Chemistry Adapter Extraction & Disablement Test

**Document:** `docs/reports/PHASE_19_PLAN.md`  
**Phase:** 19  
**Status:** IN_PROGRESS  
**Target:** Chemistry Adapter Extraction, First-Class Domain Adapter Interface, Runtime Disablement Test, Zero Platform Coupling Invariant, and Multi-Course Isolation  

---

## 1. Architectural Scope & Objectives

Section 12.19 of the Master Plan mandates:
- **Convert Existing Chemistry Behavior into a First-Class Adapter**:
  - Encapsulate equation balancing, formula parsing, chemistry evaluators, concept keywords, misconceptions, and entities into a cohesive, decoupled domain adapter package (`central_platform/adapters/chemistry/`).
- **Zero Generic Platform Coupling**:
  - Generic core platform (tutor orchestrator, context builder, database layer, REST routers) must NOT depend on or unconditionally import Chemistry adapter implementations.
- **Dynamic Adapter Selection & Disablement**:
  - Provide a toggle mechanism (`ChemistryDomainAdapter.is_enabled`, `GAYATRI_ENABLE_CHEMISTRY_ADAPTER` env var, and course capability selection) to disable Chemistry behavior entirely.
- **Phase Gate Invariant**:
  - All generic platform operations MUST run cleanly with the Chemistry adapter disabled.
  - Zero `ImportError`, `AttributeError`, or `KeyError` when Chemistry is disabled.
  - Non-Chemistry courses (Math, Python, History, General Science) must never load or trigger Chemistry tools or evaluators.

---

## 2. Component Architecture

### 2.1 Unified Chemistry Domain Adapter (`central_platform/adapters/chemistry/`)
Create `central_platform/adapters/chemistry/`:
- `adapter.py`:
  - `ChemistryDomainAdapter`:
    - `is_enabled: bool`
    - `get_tool_adapter() -> Optional[ChemistryToolAdapter]`
    - `get_evaluators() -> List[BaseEvaluator]`
    - `get_curriculum_adapter() -> Optional[ChemistryCurriculumAdapter]`
    - `get_entity_normalizer() -> Optional[ChemistryEntityNormalizer]`
    - `get_misconceptions() -> List[Dict[str, Any]]`
    - `can_handle_course(course_id_or_subject: str) -> bool`
    - `enable() / disable()`
- `__init__.py`:
  - Expose `ChemistryDomainAdapter`, `get_chemistry_domain_adapter()`, `is_chemistry_adapter_enabled()`.

### 2.2 Tool Registry Decoupling (`central_platform/tools/registry.py` & `__init__.py`)
- Support unregistering or disabling adapters dynamically: `unregister_adapter(adapter_name)`.
- `get_configured_tool_registry()` respects domain adapter enable/disable state.
- When disabled, `equation_balancer` and `formula_parser` are omitted from capabilities.

### 2.3 Evaluator Registry Decoupling (`central_platform/assessment/evaluators/registry.py`)
- Support disabling domain evaluators dynamically: `set_domain_evaluator_enabled(domain, enabled)`.
- When Chemistry evaluator is disabled, chemical equation items fall back gracefully to `RubricEvaluator` or deterministic evaluation without crashing.

### 2.4 Curriculum & Context Decoupling
- Concept resolution and query understanding respect domain boundaries; non-Chemistry courses route to generic concept matchers.

---

## 3. Test Strategy & Verification (`tests/test_phase19_chemistry_adapter_extraction_disablement.py`)

12 comprehensive tests:
1. `test_chemistry_domain_adapter_contract`: Verify adapter implements domain adapter interface and advertises capabilities.
2. `test_platform_startup_with_chemistry_disabled`: Verify tool registry and evaluator registry initialize without errors when Chemistry is disabled.
3. `test_tool_registry_omits_chemistry_when_disabled`: Verify `equation_balancer` and `formula_parser` are not advertised when disabled.
4. `test_tool_execution_rejection_when_chemistry_disabled`: Verify executing chemistry tools when disabled raises `ToolNotFoundError`.
5. `test_evaluator_registry_graceful_fallback_when_disabled`: Verify chemical equation items fall back to rubric/generic evaluator when chemistry evaluator is disabled.
6. `test_chemistry_enabled_tools_execute`: Verify `equation_balancer` and `formula_parser` execute accurately when enabled.
7. `test_chemistry_enabled_evaluator_scores_accurately`: Verify `ChemistryEquationEvaluator` scores balanced equations correctly when enabled.
8. `test_math_and_coding_unaffected_by_chemistry_disablement`: Verify Math and Coding tools/evaluators function with 100% accuracy when Chemistry is disabled.
9. `test_non_chemistry_course_isolation`: Verify non-chemistry courses (Math, Python, History) never load or expose Chemistry capabilities.
10. `test_concept_keyword_matcher_disabled_for_generic_courses`: Verify generic queries do not trigger Chemistry concept keyword matching.
11. `test_runtime_dynamic_toggle`: Verify dynamic enable/disable updates registries and capabilities immediately without restart.
12. `test_env_var_configuration_disablement`: Verify `GAYATRI_ENABLE_CHEMISTRY_ADAPTER=0` env flag disables the adapter cleanly during startup.
