# Append-Only Development Log

**Document:** `docs/reports/DEVELOPMENT_LOG.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Established:** 2026-10-01T11:26:00+05:30  

This log records every development phase and architectural transition in chronological, append-only order as required by **Section 46** of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`.

---

## Entry 001 — Phase 00: Forensic Baseline & Branch Reconciliation

- **Timestamp:** 2026-10-01T11:26:00+05:30
- **Phase:** `PHASE 00 — FORENSIC BASELINE`
- **Active Commit:** `bf47a63273e936b7617937be199e44efb4d9cb5d` (master) / `9ca3c652dc0dbcfa4340af351f6b05594c3cae45` (main)
- **What Changed:**
  - Collected branch comparison and verified git lineage: `origin/master` is 10 commits ahead of `origin/main` with 0 non-merge unique commits on `main`.
  - Created safety backup tags `backup-main-9ca3c65` and `backup-master-bf47a63`.
  - Generated full file inventory of 607 tracked repository files into `docs/reports/PHASE_00_FILE_INVENTORY.csv`.
  - Analyzed and mapped 43 runtime entry points and full subsystem coupling matrix in `docs/reports/PHASE_00_DEPENDENCY_GRAPH.md`.
  - Ran baseline test suite: 856 collected, 856 passed in 80.32s (`pytest -q`).
  - Ran static byte-compilation: 0 errors (`compileall`).
  - Ran static linter: 5,188 diagnostics categorized (`ruff check`).
  - Cataloged 5 primary architectural defect classes into `docs/reports/BUG_REGISTER.md`.
  - Published reports: `docs/reports/BRANCH_RECONCILIATION_REPORT.md`, `docs/reports/PHASE_00_FORENSICS.md`, `docs/reports/PHASE_00_TEST_BASELINE.md`, and `docs/reports/PHASE_00_TEST_RESULTS.json`.
  - Initialized `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `REQUIREMENTS_TRACEABILITY.md`, and `GITHUB_SYNC_QUEUE.md`.
- **Bugs Found:**
  - BUG-ARCH-001 (P0): 115 files in generic core and UI hardcoding Chemistry concepts and assumptions.
  - BUG-ARCH-002 (P0): 3 production files importing directly from `legacy.agents.default_agents`.
  - BUG-ARCH-003 (P0): 13 production files hardcoding fake student rosters and demo users.
  - BUG-ARCH-004 (P1): 5 modules executing dynamic inline `ALTER TABLE` statements inside swallowed `try...except Exception: pass`.
  - BUG-ARCH-005 (P1): Duplicate `CREATE TABLE IF NOT EXISTS assignments` in `migrations/001_initial_schema.sql`.
  - BUG-ARCH-006 (P1): Contradictory model definitions between `model_manifest.json` and `core/config.py`.
- **Bugs Fixed:** None in Phase 00 (Forensic Baseline phase).
- **Tests Run:** 856 tests collected, 856 passed, 0 failed, 0 skipped.
- **Remaining Risks:**
  - Inadvertently breaking passing tests during Chemistry decoupling.
  - Runtime breakage when `legacy/` imports are excised.
  - Schema migration regression when moving inline DDL into versioned SQL.

---

## Entry 002 — Phase 01: Architecture Freeze

- **Timestamp:** 2026-10-01T17:43:30+05:30
- **Phase:** `PHASE 01 — ARCHITECTURE CONTRACT & REPOSITORY GUARDRAILS`
- **Active Commit:** `f9854f8`
- **What Changed:**
  - Locked all 4 target specifications: `docs/ARCHITECTURE_TARGET.md`, `docs/DATA_MODEL_TARGET.md`, `docs/SECURITY_MODEL_TARGET.md`, `docs/TESTING_STRATEGY_TARGET.md`.
  - Created `docs/AGENT_DEVELOPMENT_RULES.md` formalizing agent discipline and non-negotiable coding invariants.
  - Implemented automated architecture guard suite in `tests/architecture/` (12 tests):
    - `test_anti_chemistry_coupling.py`: Asserts 0 chemistry keywords in `central_platform/courses/`.
    - `test_anti_demo_roster.py`: Asserts 0 hardcoded demo users in courses & models.
    - `test_anti_legacy_imports.py`: Asserts 0 legacy imports in `central_platform/` and bounds legacy to known decommission list.
    - `test_migration_integrity.py`: Asserts all migrations have matching down scripts and no duplicate `CREATE TABLE` statements.
    - `test_model_config_registry.py`: Asserts model manifest and configuration integrity.
  - Updated `.github/workflows/ci.yml` to trigger on both `main` and `master`, verifying compile hygiene and architecture guards.
  - Generated `docs/reports/PHASE_01_TEST_REPORT.md` and `docs/reports/PHASE_01_TEST_RESULTS.json`.
- **Bugs Found:** 0 new bugs.
- **Bugs Fixed:** BUG-ARCH-005 (resolved duplicate `assignments` table in `migrations/001_initial_schema.sql`).
- **Tests Run:** 12 architecture guard tests collected, 12 passed in 4.35s (`pytest tests/architecture -v`). Bytecode compilation passed with 0 errors across 600+ files.
- **Remaining Risks:**
---

## Entry 003 — Phase 02: Canonical Course, Version & Offering Domain

- **Timestamp:** 2026-10-01T17:50:00+05:30
- **Phase:** `PHASE 02 — CANONICAL COURSE, VERSION & OFFERING DOMAIN`
- **Active Commit:** `48e5e5f`
- **What Changed:**
  - Implemented core domain models in `central_platform/models/schema.py`:
    - `CourseVisibility` (`PUBLIC`, `PRIVATE`)
    - `CourseStatus` (`DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `PUBLISHED`, `ARCHIVED`, `FAILED`)
    - `CourseToolPolicy` and `CoursePolicy` dataclasses with serialization and server-side feature validation.
    - `CourseVersion` dataclass with status lifecycle, content hash, and timestamp auditing.
    - `OrganizationCourseOffering` (and alias `CourseOffering`) managing institutional adoption and pinned versioning.
  - Implemented versioned relational database migration:
    - `migrations/004_course_domain_model.sql`: Added columns `visibility` to courses, `course_offering_id` to sessions, and tables `course_versions` and `organization_course_offerings`.
    - `migrations/004_course_domain_model_down.sql`: Implemented complete rollback script with SQLite 3.35+ column drop support.
  - Extended `central_platform/db.py` (`PlatformDatabase`): Added CRUD operations for `course_versions` and `organization_course_offerings`.
  - Implemented `central_platform/courses/service.py` (`CourseService`):
    - Course creation, retrieval with visibility-aware isolation (public vs private cross-tenant separation).
    - Version draft creation, publishing state transitions with tool policy validation.
    - Organization course offering enrollment, version pinning, and active listing.
    - Runtime tool access verification (`validate_tool_access`).
  - Implemented unit and integration test suites:
    - `tests/test_phase02_course_domain_model.py`: 4 tests verifying CourseService, visibility security denial, version lifecycles, and tool enforcement.
    - `tests/test_phase02_migrations.py`: 2 tests verifying migration 004 execution, clean rollback, and re-application idempotency.
  - Generated reports: `docs/reports/PHASE_02_MIGRATION_REPORT.md`, `docs/reports/PHASE_02_TEST_REPORT.md`, `docs/reports/PHASE_02_TEST_RESULTS.json`.
- **Bugs Found:**
  - Rollback bug in SQLite where dropping a table left altered columns in `courses` and `sessions`, causing rerun failures. Fixed in `004_course_domain_model_down.sql`.
- **Bugs Fixed:** 1 SQLite rollback edge-case.
- **Tests Run:** 874 tests collected (856 regression + 12 guards + 6 Phase 2 tests), 874 passed in 91.27s.
- **Remaining Risks:** None for Phase 02.

---

## Entry 004 — Phase 03: Generic Curriculum & Versioned Learning Graph

- **Timestamp:** 2026-10-01T19:07:00+05:30
- **Phase:** `PHASE 03 — GENERIC CURRICULUM & VERSIONED LEARNING GRAPH`
- **Active Commit:** `db870df`
- **What Changed:**
  - Implemented canonical generic curriculum domain models in `core/curriculum/models.py`:
    - `GenericConcept`, `GenericTopic`, `GenericModule`, and `GenericCurriculum`.
    - Canonical namespacing helpers `format_concept_id(course_id, version_id, concept_key)` producing collision-free keys (`course:<cid>:version:<vid>:concept:<key>`).
    - Bidirectional parsing helper `parse_concept_id()` handling both modern namespaced formats and legacy keys (`chem_*`, `thermo.*`).
  - Decoupled Chemistry concept knowledge into dedicated `core/curriculum/chemistry_adapter.py`:
    - Isolated `CHEMISTRY_CONCEPT_KEYWORD_MAP` from generic core.
    - Added `ChemistryCurriculumAdapter` with toggleable runtime enablement (`is_enabled`).
  - Generalized `ConceptResolver` in `core/curriculum/resolver.py`:
    - Added course-scoped registry (`register_curriculum`, `get_curriculum`, `clear_curricula`).
    - Multi-stage resolution: Course curriculum keywords/aliases/names → Chemistry adapter fallback (for backwards compatibility) → student learning history → neutral undetermined fallback (`general_undetermined`).
  - Extensible `CurriculumValidator` in `core/curriculum/validator.py`:
    - Updated `STABLE_ID_PATTERN` to support colon (`:`) characters in canonical namespaced concept IDs.
    - Replaced hardcoded `ALLOWED_DOMAINS` restriction with data-driven configuration.
  - Extensible Generic Ingestion Engine in `core/curriculum/loader.py`:
    - Added `load_generic_curriculum()` supporting nested modules/topics as well as flat concept catalogs.
  - Implemented Canonical Four-Course Curriculum Fixtures:
    - Chemistry: `data/curriculum/chemistry/ncert_class11_12.json`
    - Physics: `data/curriculum/physics/mechanics_grade11.json`
    - History: `data/curriculum/history/world_history.json`
    - Programming: `data/curriculum/programming/intro_cs.json`
  - Scoped DAG and Cycle Detection in `central_platform/learning/graph.py`:
    - Added `validate_curriculum_dag()` supporting DFS cycle detection, missing prerequisite detection, and orphan node detection.
  - Created Comprehensive Test Suite `tests/test_phase03_generic_curriculum.py`:
    - Four-course ingestion test.
    - Cross-course resolution test (Physics, History, Programming, Chemistry).
    - Phase gate test: verified complete platform functionality with Chemistry adapter disabled.
    - Namespaced collision resistance test.
    - DAG cycle and missing prerequisite injection test.
    - Multi-hop prerequisite dependency traversal test.
  - Generated reports: `docs/reports/PHASE_03_PLAN.md`, `docs/reports/PHASE_03_TEST_REPORT.md`, `docs/reports/PHASE_03_TEST_RESULTS.json`.
- **Bugs Found:**
  - `STABLE_ID_PATTERN` previously lacked `:` support, which would reject namespaced IDs. Resolved.
- **Bugs Fixed:** 1 validation regex edge-case.
- **Tests Run:** 880 tests collected, 880 passed in 105.67s.
- **Remaining Risks:**
  - Multi-course student learning record isolation (scheduled for Phase 04).




