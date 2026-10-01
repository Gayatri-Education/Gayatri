# Phase 01 Execution Plan — Architecture Contract & Repository Guardrails

**Document:** `docs/reports/PHASE_01_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.1)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Establish the authoritative target architecture specifications and implement automated static architecture guardrail tests in `tests/architecture/`. These guards will prevent reintroduction of Chemistry coupling into generic core, legacy imports in production paths, fake demo user rosters in runtime code, duplicate DDL tables, or contradictory model configurations.

---

## 2. Planned Deliverables & Changes

1. **Target Architecture Specifications:**
   - `docs/ARCHITECTURE_TARGET.md`: Core layers, generic tutor boundary, online/offline dual-mode execution, AI Gateway.
   - `docs/DATA_MODEL_TARGET.md`: Relational DDL, composite keys (`student_id`, `course_id`, `course_version_id`, `concept_id`), content authorization.
   - `docs/SECURITY_MODEL_TARGET.md`: Multi-tenant authorization matrix, pre-retrieval RAG filtering, server-side tool policies.
   - `docs/TESTING_STRATEGY_TARGET.md`: 5-level testing pyramid, mandatory Acceptance Journeys A through G, anti-false-green rules.
   - `docs/AGENT_DEVELOPMENT_RULES.md`: Non-negotiable code rules, style invariants, and architectural constraints for development agents.

2. **Automated Architecture Guard Tests (`tests/architecture/`):**
   - `test_anti_chemistry_coupling.py`: Scans generic modules (`core/`, `central_platform/`) to verify zero direct coupling to chemistry keywords.
   - `test_anti_legacy_imports.py`: Verifies zero active production files import from `legacy.*`.
   - `test_anti_demo_roster.py`: Scans production runtime for hardcoded fake student names (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`, `local_user_1`).
   - `test_model_config_registry.py`: Validates model manifest and config integrity.
   - `test_migration_integrity.py`: Asserts zero duplicate `CREATE TABLE` definitions across all migration files.

3. **CI & Automated Checks:**
   - Update `.github/workflows/ci.yml` (or repository test configuration) to execute `tests/architecture/` as a required gate.

4. **Phase Reporting & Tracking:**
   - Run compilation and tests across `tests/architecture/` and the regression suite.
   - Generate `docs/reports/PHASE_01_TEST_REPORT.md` and `docs/reports/PHASE_01_TEST_RESULTS.json`.
   - Update `PROJECT_STATE.yaml`, `docs/reports/DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, and `GITHUB_SYNC_QUEUE.md`.

---

## 3. Phase 01 Acceptance Gate

Phase 01 is considered `VERIFIED` and ready to transition to Phase 02 when:
1. Target architecture specifications are mutually consistent and locked.
2. `docs/AGENT_DEVELOPMENT_RULES.md` is published.
3. All architecture guard tests in `tests/architecture/` are executed and passing.
4. Negative tests demonstrate that guardrails accurately catch synthetic violations.
5. All Phase 01 reports are generated and Git commits pushed to remote.
