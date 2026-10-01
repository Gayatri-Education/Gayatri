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
- **Verification:** PARTIAL (Phase 10 Generic Tutor Core, Phase 11 Generic Assessment & Evaluation Engine, and Phase 12 Real Online API Boundary verified 100% decoupled with capability routing, zero chemistry coupling across generic routers, and live HTTP probes; full legacy runtime migration continues through Phase 15).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** IN_PROGRESS.

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
- **Verification:** PARTIAL (Phase 12 eliminated mock in-memory `_COURSES` and `_ENROLLMENTS` in API layer; UI bridge decoupling scheduled Phase 22).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** IN_PROGRESS.

---

### BUG-ARCH-004
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** SQLite Session & RAG Storage (`core/session.py`, `core/rag/store.py`, `core/tutor/state.py`)
- **Reproduction:** Inspect `core/session.py` lines 128-171; note repeated `ALTER TABLE` statements inside `try...except Exception: pass`.
- **Expected:** Schema managed strictly via migration scripts (`migrations/*.sql`).
- **Actual:** Runtime DDL statements executed on connection instantiation, swallowing errors.
- **Root Cause:** Incremental schema modifications bolted onto runtime initialization.
- **Fix:** Consolidate all table columns into deterministic migration scripts and enforce startup schema checks.
- **Test:** Dynamic DDL scan assertion ensuring 0 `ALTER TABLE` in runtime execution.
- **Verification:** Pending (Scheduled for Phase 2).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

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
