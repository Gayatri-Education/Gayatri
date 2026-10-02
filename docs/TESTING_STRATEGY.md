# Testing Strategy & Backtesting Framework — Gayatri AI Platform

## 1. Testing Philosophy & Guiding Principles

1. **Zero Regression Guarantee**: Every new phase must execute the full regression suite (`pytest`) with 100% passing tests before advancing.
2. **Empirical Runtime Verification**: Code changes are not complete until verified by executing the unit/integration test suite.
3. **No Masking or Fallback Swallowing**: Failure cases must be handled explicitly; tests are never deleted, muted, or wrapped in silent dummy returns.

---

## 2. Test Suite Breakdown (845 Tests)

```text
                                 TEST SUITE MAP
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
  Unit Tests                      Integration Tests               Full Regression Master
  (Core logic, algorithms,        (Multi-subsystem integration,   (End-to-end multi-tenant,
   data models, parsers)           DB + AI Gateway + RAG + UI)     analytics, payments, security)
```

### Key Test File Groups
- **Core Platform & DB (`test_phase07_tenant_isolation.py`, `test_phase14_database.py`, `test_phase30_fee_data_layer.py`)**: Relational tables, CRUD operations, migration scripts, tenant isolation.
- **Learning & Mastery Engine (`test_phase11_canonical_state.py`, `test_phase13_learning_graph.py`, `test_phase14_mastery_engine.py`, `test_phase15_next_action_engine.py`)**: Concept DAGs, Ebbinghaus decay, prerequisite propagation, action triggers.
- **AI & RAG Gateway (`test_phase16_query_understanding.py`, `test_phase17_context_builder.py`, `test_phase18_response_planner.py`, `test_phase19_response_validator.py`, `test_phase21_local_first_router.py`, `test_phase23_rag_reliability.py`)**: Intent classification, context trimming, scaffolding plans, response validation, local/cloud router.
- **UI Design System & Portals (`test_phase24_shared_ui_design_system.py`, `test_phase25_application_shell.py`, `test_phase26_tutor_ui_redesign.py`, `test_phase27_student_portal_ui.py`, `test_phase28_teacher_portal_ui.py`, `test_phase29_parent_portal_ui.py`, `test_phase31_fee_admin_ui.py`)**: CSS/JS tokens, app shell, 4 persona portals, theme switching.
- **Payments, Privacy & Resilience (`test_phase32_payment_provider_abstraction.py`, `test_phase33_i18n.py`, `test_phase34_parent_privacy.py`, `test_phase35_learning_analytics.py`, `test_phase36_explainability.py`, `test_phase37_security_audit.py`, `test_phase38_failure_recovery.py`, `test_phase40_performance.py`, `test_phase41_deployment_validation.py`)**: Financial ledgers, parent policies, PII sanitization, profiler, deployment validator.

---

## 3. Backtesting & Educational Scenario Verification

The platform executes deterministic backtesting scenarios (`test_phase23_e2e_journeys_master.py`, `test_phase39_full_regression_master.py`):

```text
Student starts concept
 → asks question
 → receives structured explanation
 → answers incorrectly
 → misconception code flagged
 → remediation action triggered
 → answers correctly
 → mastery score recalculated
 → spaced review item scheduled
 → review completed
 → concept DAG advances
```

Expected state transitions are verified at each step in the backtest trajectory.
