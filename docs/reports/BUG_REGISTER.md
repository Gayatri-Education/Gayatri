# Comprehensive Bug Register

**Document:** `docs/reports/BUG_REGISTER.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Maintained Per:** Section 47 of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## Active Architectural & Defect Findings

### BUG-ARCH-001
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Generic Platform Core, Curriculum, RAG, UI (`core/curriculum/`, `core/runtimes/`, `app/bridge/`)
- **Reproduction:** Inspect concept resolution keywords in `core/curriculum/` or run `rg "chemistry|thermodynamics|hess" core/ central_platform/ app/`.
- **Expected:** Generic platform runtime contains zero subject-specific keywords or hardcoded curriculum paths.
- **Actual:** 115 files in generic layers assume Chemistry as the sole or default subject.
- **Root Cause:** Historical design of Gayatri as a Chemistry tutor without course abstraction.
- **Fix:** Extract all Chemistry-specific logic to `adapters/chemistry/` and make core curriculum and orchestrator data-driven.
- **Test:** Course genericity static guard test + generic course creation test.
- **Verification:** **VERIFIED FIXED** (Phase 10 Generic Tutor Core, Phase 11 Generic Assessment & Evaluation Engine, Phase 12 Online API Boundary, Phase 15 Admin Course Workflows, and Phase 24 End-to-End Journeys verified 100% decoupled with capability routing, zero chemistry coupling across generic routers, and live HTTP probes; `tests/architecture/test_anti_chemistry_leakage.py` passes 100%).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-002
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** AI Inference Pipeline (`core/inference/service.py`, `core/runtimes/chemistry.py`, `core/runtimes/general.py`)
- **Reproduction:** `python -c "import core.inference.service; print(core.inference.service._local_chat_stream)"`
- **Expected:** Tutor core calls AI Gateway / Inference Service without legacy dependencies.
- **Actual:** Production modules imported directly from `legacy.agents.default_agents`.
- **Root Cause:** Incomplete migration to decoupled inference abstraction.
- **Fix:** Decoupled prompt assembly to `core/inference/context.py`, refactored `InferenceService` to route directly through `LocalProvider` / provider registry, and updated `test_anti_legacy_imports.py` to enforce zero legacy imports across `core/`, `central_platform/`, and `app/`.
- **Test:** `tests/test_phase09_model_registry_ai_gateway.py::test_anti_legacy_zero_callers` & `tests/architecture/test_anti_legacy_imports.py::test_zero_legacy_imports_in_active_codebase`.
- **Verification:** **VERIFIED FIXED** (Zero legacy callers in active codebase; all 946 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-003
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Bridge & Server UI State (`app/bridge/facade.py`, `server.py`, `core/session.py`)
- **Reproduction:** Load student portal with clean database; observe fake students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`) injected into roster.
- **Expected:** Empty state rendered honestly when no students or classes are enrolled.
- **Actual:** Mock roster data hardcoded in production bridge methods.
- **Root Cause:** Placeholder bridge methods developed for quick demoing without real service backing.
- **Fix:** Connect bridge methods directly to `central_platform.db` repositories with honest empty states.
- **Test:** Clean database startup test verifying 0 fake students rendered.
- **Verification:** **VERIFIED FIXED** (Phase 13 completely removed hardcoded fake demo roster seeding in `app/bridge/facade.py`; verified via `test_zero_fake_demo_roster_in_bridge_and_portal` and `test_first_offline_launch_clean_environment` in `tests/test_phase13_offline_local_runtime.py`).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-004
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** SQLite Session & RAG Storage (`core/session.py`, `core/rag/store.py`, `core/tutor/state.py`)
- **Reproduction:** Inspect `core/session.py` lines 128-171; note repeated `ALTER TABLE` statements inside `try...except Exception: pass`.
- **Expected:** Schema managed strictly via migration scripts (`migrations/*.sql`) and hardening functions that re-raise unexpected database errors.
- **Actual:** Runtime DDL statements executed on connection instantiation, swallowing errors.
- **Root Cause:** Incremental schema modifications bolted onto runtime initialization without duplicate column discrimination.
- **Fix:** Introduced `add_column_if_missing` in `core/db.py` to discriminate duplicate column OperationalErrors from database corruption/locks, migrated session summary column to versioned migration 4, and hardened `core/rag/store.py`.
- **Test:** `tests/test_phase15_database_hardening.py` & `tests/test_multi_turn_flow.py`.
- **Verification:** **VERIFIED FIXED** (All 981 suite tests green; zero silent swallows of operational errors).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-005
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Database Migrations (`migrations/001_initial_schema.sql`)
- **Reproduction:** Inspect line 351 and line 448 of `migrations/001_initial_schema.sql`.
- **Expected:** Each table defined exactly once in canonical DDL.
- **Actual:** `assignments` table defined twice with differing column definitions.
- **Root Cause:** Merge conflict concatenation in initial migration file.
- **Fix:** Deduplicated and consolidated `assignments` table definition into a single authoritative schema in `migrations/001_initial_schema.sql`.
- **Test:** Migration integrity architecture guard test (`tests/architecture/test_migration_integrity.py`).
- **Verification:** **VERIFIED FIXED** (Migration integrity test passes; zero duplicate tables).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-006
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Model Manifest & Configuration (`model_manifest.json`, `core/config.py`)
- **Reproduction:** Compare `model_manifest.json` default model ID with `core/config.py` search list.
- **Expected:** Single authoritative model registry/manifest declaring active models and capabilities.
- **Actual:** Contradictory model filenames, quantization tags, and prompt template parameters across files.
- **Root Cause:** Divergent configuration updates in documentation vs code.
- **Fix:** Unified `model_manifest.json` schema with canonical Phase 09 fields, synchronized `core/config.py` default model and HuggingFace repo/file constants with Qwen2.5-0.5B, and enhanced `manifest_validator.py`.
- **Test:** `tests/test_phase09_model_registry_ai_gateway.py::test_manifest_consistency_and_canonical_keys` & `tests/architecture/test_model_config_registry.py`.
- **Verification:** **VERIFIED FIXED** (Manifest and config fully synchronized; all 946 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-RAG-007
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `424f343`
- **Subsystem:** Plug-and-Play RAG Retrieval (`central_platform/db.py`)
- **Reproduction:** Insert RAG source with uppercase enum status (`PUBLISHED`); query `get_rag_chunks_by_course(only_published=True)`.
- **Expected:** Chunks are returned regardless of whether the status string is uppercase or lowercase.
- **Actual:** Exact match `rs.status = 'published'` filtered out records stored with uppercase enum value.
- **Root Cause:** Direct literal comparison in SQLite/PostgreSQL SQL condition without `LOWER()`.
- **Fix:** Updated `central_platform/db.py` to use `LOWER(rs.status) = 'published'` and `LOWER(status) = ?`.
- **Test:** `tests/test_phase05_knowledge_assets.py::test_phase_gate_student_visibility_invariant`.
- **Verification:** **VERIFIED FIXED** (All 12 Phase 05 tests pass; all 898 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-RAG-008
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 06 Implementation`
- **Subsystem:** RAG Source Creation Endpoint (`central_platform/api/routes/rag.py`)
- **Reproduction:** Register RAG source with a course belonging to a custom tenant organization via `POST /api/v1/rag/sources`.
- **Expected:** Source registers under the course's owning organization without FK violation.
- **Actual:** Endpoint hardcoded `organization_id="org-default"`, triggering SQLite foreign key violation when `org-default` did not exist.
- **Root Cause:** Hardcoded organization string instead of resolving from `course_id`.
- **Fix:** Dynamically look up `svc.db.get_course(req.course_id)` to resolve `course.organization_id`.
- **Test:** `tests/test_phase06_scoped_rag_authorization.py::test_scoped_rag_api_flow`.
- **Verification:** **VERIFIED FIXED** (All 10 Phase 06 tests pass; all 908 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-INST-009
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 07 Implementation`
- **Subsystem:** Teacher Instruction Hierarchy Cascade (`central_platform/teacher/instruction.py`)
- **Reproduction:** Query student instructions with specific `concept_id` when targeted student instructions specify a different `concept_scope`.
- **Expected:** Concept-specific student instructions targeting a different concept are filtered out.
- **Actual:** Concept filtering was applied only to `COURSE` scope; student-targeted instructions bypassed concept filter.
- **Root Cause:** Concept condition was placed inside `scope == "COURSE"` block instead of globally across scopes.
- **Fix:** Moved concept scope evaluation to apply across all hierarchy levels in `resolve_hierarchical_instructions`.
- **Test:** `tests/test_phase11_teacher_instructions_platform.py::test_instruction_scoping_student_cohort_concept`.
- **Verification:** **VERIFIED FIXED** (All 13 Phase 07 and Phase 11 tests pass; all 921 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-TOOL-010
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 08 Implementation`
- **Subsystem:** Tool Execution Engine RBAC (`central_platform/tools/engine.py`)
- **Reproduction:** Configure a tool capability restricted to teachers/admins and execute with student context.
- **Expected:** Student execution is rejected with `ToolAuthorizationError`.
- **Actual:** Compound boolean check `role not in allowed and super_admin not in allowed` evaluated to false when super_admin was listed in allowed roles, bypassing the restriction.
- **Root Cause:** Incorrect boolean condition checking whether super_admin was in the capability's allowed list rather than checking if caller was super_admin.
- **Fix:** Refactored condition to `if role_val_norm not in allowed_role_vals_norm and role_val_norm != UserRole.SUPER_ADMIN.value.lower():`.
- **Test:** `tests/test_phase08_course_tool_registry.py::test_role_based_access_control_for_tools`.
- **Verification:** **VERIFIED FIXED** (All 11 Phase 08 tests pass; all 932 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-DESK-011
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 07 Implementation`
- **Subsystem:** Desktop Portals (`app/portals/*/controller.py`)
- **Reproduction:** Call `get_dashboard_context()` across portal controllers; inspect returned state.
- **Expected:** Controllers support dynamic database context queries while maintaining baseline schema contract.
- **Actual:** Controllers returned empty stub dictionaries decoupled from platform database state (`BUG-0005`).
- **Root Cause:** Incomplete desktop portal routing stubs.
- **Fix:** Enhanced `StudentPortalController`, `TeacherPortalController`, `ParentPortalController`, and `AdminPortalController` to accept `user_id` and `db` parameters, querying real database entities while preserving baseline schema keys (`portal`, `version`).
- **Test:** `tests/test_phase07_portal_ui.py`.
- **Verification:** **VERIFIED FIXED** (All 4 portal UI tests pass; all 981 suite tests green).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ANL-012
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 20 Implementation`
- **Subsystem:** Analytics & Numerical Evaluation (`central_platform/analytics/`, `central_platform/assessment/evaluators/`)
- **Reproduction:** Compute student health with zero events (`recent_velocity=1.0`) or calculate retention decay with clock skew.
- **Expected:** Velocity is `0.0` when zero learning events exist; retention probability is strictly bounded `[0.0, 1.0]`; numerical floats are NaN/Inf safe.
- **Actual:** Hardcoded velocity baseline `1.0` (`BUG-0010`), unbounded retention probability (`BUG-0012`), and missing NaN/Inf guards.
- **Root Cause:** Missing boundary clamping and baseline normalization.
- **Fix:** Set `recent_velocity=0.0` on zero events, clamped retention with `min(1.0, max(0.0, ...))`, and added `math.isnan` / `math.isinf` checks in `NumericalEvaluator`.
- **Test:** `tests/test_phase35_learning_analytics.py` & `tests/test_phase19_assessment_platform.py`.
- **Verification:** **VERIFIED FIXED** (All analytics and assessment tests green).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-TEST-013
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `Phase 01 Implementation`
- **Subsystem:** Test Suite Architecture Guards (`tests/architecture/test_anti_demo_roster.py`, `test_anti_legacy_imports.py`)
- **Reproduction:** Inspect line 24-26 of `tests/architecture/test_anti_demo_roster.py`.
- **Expected:** Assertions execute outside try/except blocks to prevent `AssertionError` suppression.
- **Actual:** `assert not matches` placed inside `try: ... except Exception: pass`, silently swallowing assertion failures.
- **Root Cause:** Indiscriminate error wrapping in test file reader loop.
- **Fix:** Removed try/except wrapping assertions and file scans, directly enforcing assertions and surfacing any read exceptions.
- **Test:** `tests/architecture/test_anti_demo_roster.py` & `tests/architecture/test_anti_legacy_imports.py`.
- **Verification:** **VERIFIED FIXED** (Negative tests verify synthetic detection; guard suite 100% green).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-REL-014
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 23 Implementation`
- **Subsystem:** Teacher Instruction Temporal Validity & Pruning (`central_platform/teacher/instruction.py`)
- **Reproduction:** Call `resolve_hierarchical_instructions` on an instruction with `expires_at` in the past.
- **Expected:** Expired instruction is pruned (`is_active=False`, `status="EXPIRED"`) and excluded from candidate directives.
- **Actual:** `_is_temporally_valid` accessed `inst.id`, triggering an `AttributeError` on `TeacherInstruction` (which uses `instruction_id`), which was caught by `except Exception: return True`, silently retaining expired instructions indefinitely.
- **Root Cause:** Attribute name mismatch (`inst.id` vs `inst.instruction_id`) inside try/except block returning fallback `True`.
- **Fix:** Used `getattr(inst, "instruction_id", getattr(inst, "id", "unknown"))` to safely extract instruction identifier for logging and recovery.
- **Test:** `tests/test_phase23_reliability_failure_injection_recovery.py::test_inject_expired_instruction`.
- **Verification:** **VERIFIED FIXED** (Expired instructions cleanly pruned and omitted from context hierarchy).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-PLT-015
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 24 Testing`
- **Subsystem:** Teacher Instruction API Route (`central_platform/api/routes/instructions.py`)
- **Reproduction:** Create teacher instruction with `start_at` and `expires_at` via `POST /api/v1/instructions`.
- **Expected:** Timestamps are propagated to the database record.
- **Actual:** Route hardcoded `start_at=None, expires_at=None`, discarding request timestamps.
- **Root Cause:** Incomplete argument forwarding in route handler.
- **Fix:** Forwarded `start_at=req.start_at` and `expires_at=req.expires_at` to `svc.create_instruction`.
- **Test:** `tests/test_phase24_e2e_journeys_real.py::test_negative_journeys_nj1_through_nj11`.
- **Verification:** **VERIFIED FIXED** (Expired instructions cleanly evicted).
- **Status:** VERIFIED.

---

### BUG-PLT-016
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 24 Testing`
- **Subsystem:** Platform Database Instruction Query (`central_platform/db.py`)
- **Reproduction:** Call `get_teacher_instructions(only_active=True)` when instruction `expires_at` has elapsed.
- **Expected:** Expired instructions are omitted from query results.
- **Actual:** Only `is_active` boolean was checked, ignoring `expires_at` timestamp.
- **Root Cause:** SQL query omitted temporal expiration condition.
- **Fix:** Added `AND (expires_at IS NULL OR expires_at > ?)` check in query.
- **Test:** `tests/test_phase24_e2e_journeys_real.py`.
- **Verification:** **VERIFIED FIXED**.
- **Status:** VERIFIED.

---

### BUG-PLT-017
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 24 Testing`
- **Subsystem:** Tutor Turn Orchestrator (`central_platform/tutor/orchestrator.py`)
- **Reproduction:** Invoke `execute_turn` specifying a draft or archived `course_version_id`.
- **Expected:** Turn execution is rejected with error because version is not approved/published.
- **Actual:** Orchestrator accepted arbitrary version IDs without status validation.
- **Root Cause:** Missing course version status guard.
- **Fix:** Added validation ensuring `course_version.status == CourseStatus.PUBLISHED` (raises `CourseNotFoundError` on draft/archived).
- **Test:** `tests/test_phase24_e2e_journeys_real.py::test_negative_journeys_nj1_through_nj11`.
- **Verification:** **VERIFIED FIXED**.
- **Status:** VERIFIED.

---

### BUG-PLT-018
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 25 Testing & CI`
- **Subsystem:** Event Store Ingestion (`central_platform/events/store.py`, `central_platform/db.py`)
- **Reproduction:** Ingest batch of 200 events with duplicates in cloud VM environment.
- **Expected:** High-throughput batch ingestion (> 500 ev/s) with intra-batch duplicate deduplication.
- **Actual:** 200 separate disk commits throttled performance to ~44 ev/s; duplicate events within same batch weren't deduplicated before commit.
- **Root Cause:** Iterative single-record transactions and missing `seen_batch_ids` tracking.
- **Fix:** Implemented `record_learning_events_batch` with `executemany` single transaction and added `seen_batch_ids` set. Throughput increased to > 30,000 ev/s.
- **Test:** `tests/test_phase05_learning_events.py` & `tests/test_phase25_performance_capacity_verification.py`.
- **Verification:** **VERIFIED FIXED** (All tests green).
- **Status:** VERIFIED.

---

### BUG-PLT-019
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 26 Forensic Audit`
- **Subsystem:** Distribution Packaging (`scripts/package_release.py`)
- **Reproduction:** Run `python scripts/package_release.py` and inspect packaged directories.
- **Expected:** Distribution package includes full central backend and migrations.
- **Actual:** `central_platform`, `migrations`, and `scripts` were omitted from `include_dirs`.
- **Root Cause:** Outdated release packager file manifest.
- **Fix:** Added `central_platform`, `migrations`, `scripts`, `model_manifest.json`, and `LICENSE.md` to packaging configuration.
- **Test:** `tests/test_phase26_packaging_clean_install.py::test_packaging_completeness_and_manifest`.
- **Verification:** **VERIFIED FIXED** (566 files packaged and verified).
- **Status:** VERIFIED.

---

### BUG-PLT-020
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 26 Forensic Audit`
- **Subsystem:** Deployment Validator (`central_platform/deployment/validator.py`)
- **Reproduction:** Run deployment validator on missing database.
- **Expected:** Health checks probe real subsystem and report DOWN.
- **Actual:** Validator returned hardcoded `"UP"` strings for all 5 subsystems without probing.
- **Root Cause:** Mocked status dictionary left from initial prototype.
- **Fix:** Implemented live operational probes for SQLite database, AI Gateway manifest, RAG query vector, FeeService, and i18n registry.
- **Test:** `tests/test_phase26_packaging_clean_install.py::test_deployment_validator_real_subsystem_probes`.
- **Verification:** **VERIFIED FIXED** (Reports real failure when subsystem is down).
- **Status:** VERIFIED.

---

### BUG-PLT-021
- **Severity:** P1
- **Date Found:** 2026-10-02
- **Commit Found:** `Phase 26 Forensic Audit`
- **Subsystem:** Deployment Validator Secret Security (`central_platform/deployment/validator.py`)
- **Reproduction:** Run deployment validation in production environment without `SECRET_KEY`.
- **Expected:** Deployment readiness fails.
- **Actual:** Missing secret returned `ValidationStatus.WARN`, allowing insecure release.
- **Root Cause:** Lenient warning-only status on missing secret.
- **Fix:** Enforced `ValidationStatus.FAIL` when `APP_ENV=production` or `STRICT_SECRETS=true`.
- **Test:** `tests/test_phase26_packaging_clean_install.py::test_deployment_validator_secret_enforcement`.
- **Verification:** **VERIFIED FIXED**.
- **Status:** VERIFIED.


