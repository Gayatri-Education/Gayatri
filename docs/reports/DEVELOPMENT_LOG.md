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
- **Remaining Risks:** None for Phase 03.

---

## Entry 005 — Phase 04: Course-Scoped Student Learning State & Sessions

- **Timestamp:** 2026-10-01T20:38:00+05:30
- **Phase:** `PHASE 04 — COURSE-SCOPED STUDENT LEARNING STATE & SESSIONS`
- **Active Commit:** `fc5dd18`
- **What Changed:**
  - Implemented authoritative `CourseLearningContext` in `central_platform/models/schema.py`:
    - Validates presence of non-empty `student_id` and `course_id`.
    - Holds optional `organization_id`, `course_version_id`, `course_offering_id`, `cohort_id`, and `class_id`.
  - Extended domain models in `central_platform/models/schema.py`:
    - `Session`: Added `course_version_id`, `course_offering_id`, `class_id`.
    - `LearningEvent`: Added `course_version_id`.
  - Extended persistence layer in `central_platform/db.py`:
    - Updated `create_session` and `get_session` to persist and retrieve `course_version_id` and `class_id`.
    - Updated `get_sessions_for_student` to accept optional `course_id` parameter.
    - Updated `_row_to_learning_event` to map `course_version_id`.
  - Refactored `LearningStateManager` in `central_platform/learning/state.py`:
    - Updated `SessionRuntimeState` and `CanonicalLearningState` to track `course_version_id`, `course_offering_id`, `class_id`.
    - `get_canonical_state`: Enforced mandatory non-empty `course_id` and `student_id`. Partitioned SLRs and masteries by composite `(student_id, course_id)`.
    - `update_mastery`: Strictly isolated mastery updates to the course-specific SLR.
    - `initialize_session`: Added support for `CourseLearningContext` or explicit kwargs with validation gates.
    - `log_event`: Bound session's `course_id` and `course_version_id` to events, with idempotent deduplication.
    - `get_student_courses`: Added helper returning all distinct enrolled course IDs for a student.
  - Updated `core/tutor/state.py`:
    - Added optional `course_id: str = "chemistry"` to `StudentConceptMastery` and `LearningEvent` for backward compatibility.
  - Implemented Comprehensive Test Suite `tests/test_phase04_course_learning_state.py`:
    - Cross-course contamination test: Verified student practicing identical concept `"thermo"` in Chemistry and Physics achieves completely independent mastery records.
    - Session and event isolation: Verified sessions and events in Course A do not bleed into Course B.
    - Idempotent telemetry: Verified duplicate event IDs are ignored without double-counting.
    - State persistence and exact recovery: Verified complete process restart restores exact multi-course state.
    - Validation gates: Verified empty `course_id` or `student_id` raises `ValueError`.
  - Generated reports: `docs/reports/PHASE_04_PLAN.md`, `docs/reports/PHASE_04_TEST_REPORT.md`, `docs/reports/PHASE_04_TEST_RESULTS.json`.
- **Bugs Found:**
  - `initialize_session` originally named its first argument `student_id_or_context` which broke callers expecting keyword argument `student_id`. Resolved with alias support.
- **Bugs Fixed:** 1 parameter signature edge-case.
- **Tests Run:** 886 tests collected, 886 passed in 85.51s.
- **Remaining Risks:**
  - Course content packaging and manifest publishing gates (scheduled for Phase 05).

---

### [2026-10-01] — Phase 05: Knowledge Asset Ingestion & Publication Pipeline
- **Driver:** Antigravity (Advanced Agentic Coding)
- **Phase Goal:** Establish controlled multi-format academic asset ingestion, chunking, sanitization, role-based approval/publication gates, and guarantee the student visibility invariant.
- **Changes Implemented:**
  - `central_platform/models/schema.py`:
    - Defined `KnowledgeContentType` enum (`TEXTBOOK`, `REFERENCE`, `TEACHER_NOTE`, `WORKSHEET`, `REMEDIAL`, `ASSESSMENT_SOURCE`, `SOLUTION_GUIDE`, `OTHER`).
    - Expanded `RAGSourceStatus` / `KnowledgeAssetStatus` (`DRAFT`, `PROCESSING`, `INGESTED`, `VALIDATED`, `READY_FOR_REVIEW`, `APPROVED`, `PUBLISHED`, `ARCHIVED`, `FAILED`) with case-insensitive normalization.
    - Extended `RAGSource` dataclass with `content_type`, `uploaded_by`, `published_by`, `published_at`, `error_message`.
  - Database Migration 005:
    - Added `migrations/005_knowledge_assets.sql` and `migrations/005_knowledge_assets_down.sql`.
    - Tested forward application, full database rollback, and idempotent reapplication.
  - `central_platform/db.py`:
    - Updated `create_rag_source` and `get_rag_source` to persist and load new attributes.
    - Updated `list_rag_sources` with `content_type` filtering and case-insensitive status matching.
    - Updated `get_rag_chunks_by_course` with `LOWER(rs.status) = 'published'`.
  - `central_platform/rag/service.py`:
    - Implemented `upload_knowledge_asset()`: Teacher/Admin upload permitted, student upload forbidden (403 PermissionError), 10MB bounds check, automatic transition to `READY_FOR_REVIEW` on success or `FAILED` on parser error.
    - Implemented `approve_knowledge_asset()`: Restricted strictly to `ORG_ADMIN` and `SUPER_ADMIN`.
    - Implemented `publish_knowledge_asset()`: Sets `published_at` and `published_by`; failed assets cannot be published.
    - Implemented `archive_knowledge_asset()`: Restricts access to admins or author.
    - Updated `query()`: Enforced student visibility invariant where unpublished content in any state is completely hidden from student retrieval queries.
  - `central_platform/api/schemas.py` and `central_platform/api/routes/rag.py`:
    - Updated schemas and REST routes to expose `content_type` and publication metadata.
  - Test Suite & Invariant Verification (`tests/test_phase05_knowledge_assets.py`):
    - 12 comprehensive unit, integration, and security tests: multi-format ingestion (Markdown, JSON, Text), full lifecycle (`DRAFT/PROCESSING` -> `READY_FOR_REVIEW` -> `APPROVED` -> `PUBLISHED` -> `ARCHIVED`), malformed content failure isolation, student upload denial, non-admin approval denial, and zero-leakage student visibility invariant.
  - Reports Generated: `docs/reports/PHASE_05_PLAN.md`, `docs/reports/PHASE_05_TEST_REPORT.md`, `docs/reports/PHASE_05_TEST_RESULTS.json`.
- **Bugs Found & Fixed:**
  - Case sensitivity in SQL status matching: Fixed with `LOWER(rs.status) = 'published'` to tolerate both uppercase and lowercase enum values.
- **Tests Run:** 898 tests collected, 898 passed in 106.60s (100% green).
- **Remaining Risks:**
  - Cross-course teacher instruction scoping (scheduled for Phase 06/07).

### Entry: Phase 06 — Scoped RAG & Knowledge Authorization (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Models & Schemas (`central_platform/models/schema.py`, `central_platform/models/__init__.py`):
    - Added `KnowledgeVisibilityScope` enum (`COURSE`, `CLASS`, `STUDENT_TARGETED`).
    - Extended `RAGSource` with `course_version_id`, `visibility_scope`, `class_id`, `target_student_ids`.
    - Extended `RAGChunk` with `course_version_id`, `visibility_scope`, `class_id`.
  - Database Migration 006:
    - Added `migrations/006_scoped_rag_authorization.sql` with new scoping columns on `rag_sources` and `rag_chunks` and composite indices `idx_rag_sources_scoped` and `idx_rag_chunks_scoped`.
    - Added reversible `migrations/006_scoped_rag_authorization_down.sql` with table-rebuild rollback. Verified up/down/re-up lifecycle on local SQLite DB.
  - Database Layer (`central_platform/db.py`):
    - Updated `_row_to_rag_source`, `create_rag_source`, `list_rag_sources`, `add_rag_chunks`, and `_row_to_rag_chunk`.
    - Updated `get_rag_chunks_by_course` to enforce version pinning, class-level filtering, and student targeted remedial filtering.
  - Service Layer (`central_platform/rag/service.py`):
    - Updated `SmartChunker.chunk_section` and `_build_chunk` to propagate `course_version_id`, `visibility_scope`, `class_id`.
    - Updated `register_source` and `upload_knowledge_asset` to accept and persist scoping parameters.
    - Updated `RAGService.query()`:
      - Resolved effective query scoping parameters from optional `CourseLearningContext`, `student_id`, `course_version_id`, `class_id`.
      - Implemented multi-tenant org isolation check: returns `RAG_DENIED` with 0 chunks if user/student's org does not match private course org and no active `CourseOffering` is present.
      - Enforced zero-leakage invariant: course queries with 0 matches return `RAG_EMPTY` with 0 chunks and never fall back to legacy/global files.
  - API Routes & Schemas (`central_platform/api/schemas.py`, `central_platform/api/routes/rag.py`):
    - Updated `RAGSourceCreateRequest`, `RAGSourceResponse`, `RAGChunkResponse`, `RAGQueryRequest`, `RAGResultItem`, and `RAGQueryResponse`.
    - Dynamic course organization lookup in `create_rag_source`.
  - Test Suite (`tests/test_phase06_scoped_rag_authorization.py`):
    - 10 comprehensive tests covering course scope, multi-tenant isolation denial, partner offering access, class notes scoping, student targeted remedial, version isolation, learning context binding, no fallback under scoped search, diagnostic transparency, and REST API flow.
- **Bugs Found & Fixed:**
  - SQLite FOREIGN KEY constraint in `create_rag_source` when using `org-default`: Resolved by dynamically looking up the course's owning `organization_id` when registering sources.
  - Missing `Enum` import in `central_platform/rag/service.py`: Resolved with explicit import and attribute check.
- **Tests Run:** 908 tests collected, 908 passed in 97.71s (100% green).
- **Remaining Risks:**
  - Hierarchical teacher instruction inheritance cascade (scheduled for Phase 07).

### Entry: Phase 07 — Teacher Instruction Hierarchy & Scoping (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Models & Schemas (`central_platform/models/schema.py`, `central_platform/models/__init__.py`):
    - Added `InstructionScope` enum (`ORGANIZATION`, `COURSE`, `CLASS`, `STUDENT`, `SESSION`).
    - Extended `TeacherInstructionRecord` dataclass to 21 columns including `organization_id`, `course_version_id`, `class_id`, `session_id`, `scope_type`, `status`, `safety_status`, `start_at`, `expires_at`, `version`, `audit_trail`, `updated_at`.
  - Database Migration 007 (`migrations/007_teacher_instruction_hierarchy.sql`, `migrations/007_teacher_instruction_hierarchy_down.sql`):
    - Added new columns and performance indexes `idx_teacher_inst_scope`, `idx_teacher_inst_class`, `idx_teacher_inst_org`, `idx_teacher_inst_session`, `idx_teacher_inst_hierarchy`.
    - Verified forward migration, rollback down, and idempotent reapplication. Guarded by architecture tests.
  - Database Layer (`central_platform/db.py`):
    - Updated `_row_to_teacher_instruction` and `create_teacher_instruction` to persist and retrieve all 21 columns.
    - Added `get_teacher_instruction`, `delete_teacher_instruction`.
    - Added `get_hierarchical_teacher_instructions` supporting hierarchical filtering and status filtering.
  - Teacher Instruction Engine (`central_platform/teacher/instruction.py`):
    - Updated `ScopeType` with `ORGANIZATION`, `COURSE`, `CLASS`, `STUDENT`, `SESSION` (and legacy aliases `COHORT`, `CONCEPT`).
    - Added RBAC gatekeeping to `add_instruction`: student writes strictly blocked (`PermissionError`), cross-org teacher dispatches strictly blocked (`PermissionError`).
    - Implemented `resolve_hierarchical_instructions` enforcing the deterministic precedence cascade: `SESSION (5) > STUDENT (4) > CLASS (3) > COURSE (2) > ORGANIZATION (1)`, with intra-scope tie-breaking by priority (5->1) then `created_at` (descending).
    - Added concept scope filtering across all scopes.
    - Updated `format_prompt_directive` with strict data framing `[TEACHER PEDAGOGICAL DIRECTIVES - STRICT DATA FRAMING]` and non-negotiable invariant note reminding the LLM that directives never override anti-answer leakage, scientific truths, or Socratic guidance.
    - Enhanced `TeacherInstructionValidator` regexes for prompt injections and anti-answer leakage attempts.
  - API Schemas & Routes (`central_platform/api/schemas.py`, `central_platform/api/routes/teachers.py`):
    - Updated `TeacherInstructionCreateRequest` and `TeacherInstructionResponse` with hierarchical fields.
    - Updated `create_instruction` with multi-tenant org validation, student rejection (HTTP 403), and auto-scope inference.
    - Updated `get_instructions` to support `hierarchical=true` resolution parameter.
  - Test Suite (`tests/test_phase07_teacher_instruction_hierarchy.py`):
    - 13 comprehensive unit, security, precedence, database, and API integration tests: all passed.
  - Regression Suite:
    - 921 tests passing in 111.10s (100% green).
- **Bugs Found & Fixed:**
  - Concept scope filtering missing for STUDENT scope in `resolve_hierarchical_instructions`: Fixed by applying concept filter across all scopes.
  - Prompt directive backward compatibility with Phase 11 assertion: Fixed by prepending `[PRIORITY TEACHER INSTRUCTIONS]:` header.
- **Tests Run:** 921 tests collected, 921 passed in 111.10s (100% green).
- **Remaining Risks:** None for Phase 07. Phase 08 (Course Tool Policy Engine) next.

### Entry: Phase 08 — Course Tool Capability & Adapter Registry (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Domain & Capability Models (`central_platform/tools/capabilities.py`, `central_platform/tools/__init__.py`):
    - Added `ToolCategory` enum (`CALCULATION`, `SCIENCE`, `CODING`, `GRAPHING`, `REFERENCE`).
    - Added `ResourceLimits` dataclass (`timeout_seconds`, `max_input_chars`, `max_output_chars`, `max_memory_mb`).
    - Added `ToolCapability` dataclass (`tool_id`, `name`, `description`, `category`, `allowed_roles`, `resource_limits`, `input_schema`, `output_schema`).
    - Added `ToolExecutionContext` dataclass (`course_id`, `student_id`, `session_id`, `user_role`, `course_policy`).
    - Added `ToolExecutionResult` dataclass (`success`, `output`, `error`, `execution_time_ms`, `resource_usage`).
  - Base Tool Adapter Contract (`central_platform/tools/base.py`):
    - Defined `ToolAdapter` abstract base class requiring `get_capabilities()`, `validate_arguments()`, and `execute()`.
  - Tool Registry & Execution Engine (`central_platform/tools/registry.py`, `central_platform/tools/engine.py`):
    - Implemented `ToolRegistry` with dynamic adapter registration, tool ID indexing, capability lookup, and policy-filtered tool listing.
    - Implemented `ToolExecutionEngine` enforcing the 6-point execution contract:
      1. Course tool policy check (`CourseToolPolicy.is_tool_enabled`)
      2. User role authorization check (`user_role in allowed_roles` with super admin bypass)
      3. Scope containment
      4. Input schema validation
      5. Resource limits enforcement with concurrent thread timeout guards
      6. Typed `ToolExecutionResult` response
  - Decoupled Domain Tool Adapters (`central_platform/tools/adapters/`):
    - `ChemistryToolAdapter`: Exposes `equation_balancer` (stoichiometric matrix nullspace solver) and `formula_parser` (parenthesis and multiplier parser).
    - `MathToolAdapter`: Exposes `calculator` evaluating mathematical expressions safely using an AST NodeVisitor (zero `eval()` or `exec()`), blocking dangerous code injections.
    - `ProgrammingSandboxAdapter`: Exposes `code_execution` supporting syntax validation, stdout capture, and blocking dangerous imports (`os`, `sys`, `subprocess`, etc.).
  - Central REST API Endpoints & Schemas (`central_platform/api/schemas.py`, `central_platform/api/routes/tools.py`, `central_platform/api/app.py`):
    - Added `ToolCapabilityResponse`, `ToolExecuteRequest`, `ToolExecuteResponse`.
    - Implemented `GET /api/v1/tools`, `GET /api/v1/tools/{course_id}`, and `POST /api/v1/tools/execute`. Mounted on FastAPI platform app.
  - Test Suite (`tests/test_phase08_course_tool_registry.py`):
    - 11 comprehensive tests covering registry discovery, course policy enablement, zero-tools course policies, role-based access control, resource limit timeouts, input validation, chemistry equation balancing, safe math AST evaluation, programming sandbox execution, phase gate architectural decoupling, and REST API endpoints.
  - Regression Suite:
    - 932 tests passing in 121.92s (100% green).
- **Bugs Found & Fixed:**
  - Role authorization comparison logic in `ToolExecutionEngine`: Fixed super admin bypass logic so that regular student/teacher role restrictions are correctly evaluated.
  - Deprecated FastAPI status code `HTTP_422_UNPROCESSABLE_ENTITY`: Replaced with status code 422 to maintain clean, warning-free API execution.
- **Tests Run:** 932 tests collected, 932 passed in 121.92s (100% green).
- **Remaining Risks:** None for Phase 08.

---

### Entry: Phase 09 — Model Registry & AI Gateway Unification (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Standardized Model Manifest (`model_manifest.json`):
    - Added canonical Phase 09 fields: `artifact_path`, `format` ("gguf"), `prompt_template` ("chatml"), `context_window` (8192), `streaming` (true), `capabilities`, `supports_tools`, `supports_json`, `resource_profile` ("1GB RAM, CPU").
    - Retained all legacy fields for 100% backward compatibility.
  - Hardened Manifest Validator (`core/model_fetch/manifest_validator.py`):
    - Normalized canonical alias fields automatically upon loading.
    - Added `get_active_manifest()` and `verify_model_checksum()` helper utilities.
  - Reconciled Core Configuration (`core/config.py` — BUG-ARCH-006):
    - Updated `_detect_initial_model_file()` default fallback to `"qwen2.5-0.5b-instruct-q4_k_m.gguf"`.
    - Aligned `MODEL_HUGGINGFACE_REPO` ("Qwen/Qwen2.5-0.5B-Instruct-GGUF") and `MODEL_GGUF_FILENAME` ("qwen2.5-0.5b-instruct-q4_k_m.gguf").
  - Decoupled Prompt & Context Building (`core/inference/context.py`):
    - Created pure domain prompt assembly module with `build_chat_messages` (alias `_build_messages`) and `get_tutor_context` (alias `_get_tutor_context`).
  - Decommissioned Legacy Agent Imports (`BUG-ARCH-002`):
    - Refactored `core/inference/service.py` to route directly via `LocalProvider.chat_stream` and `ProviderRegistry` without importing `_local_chat_stream` from legacy.
    - Updated `core/runtimes/chemistry.py` and `core/runtimes/general.py` to import from `core.inference.context`.
    - Deprecated `legacy/agents/default_agents.py` with `DeprecationWarning` and re-exported context helpers.
    - Updated `tests/architecture/test_anti_legacy_imports.py` whitelist to 0 callers. Verified zero legacy callers in `core/`, `central_platform/`, and `app/`.
  - Privacy & Inference Hardening:
    - Added `ExecutionMode.LOCAL_ONLY` enforcement in `InferenceService`: cloud provider calls fail-closed with `PermissionError`.
    - Implemented cooperative streaming cancellation via `InferenceService.cancel()`.
    - Enforced non-silent error propagation for provider timeouts and invalid responses (Rule 3).
  - Test Suite (`tests/test_phase09_model_registry_ai_gateway.py`):
    - 14 comprehensive tests covering manifest consistency, model config parsing, missing model offline guidance, wrong provider rejection, corrupt checksum rejection, timeout propagation, invalid response handling, privacy mode blocking, observable fallback chain, streaming and cancellation, ChatML template consistency, context builder, and zero legacy imports.
  - Regression Suite:
    - 946 tests passing in 135.53s (100% green).
- **Bugs Resolved:**
  - `BUG-ARCH-002`: Legacy inference imports decommissioned. Status: VERIFIED.
  - `BUG-ARCH-006`: Model manifest and config contradiction resolved. Status: VERIFIED.
- **Tests Run:** 946 tests collected, 946 passed in 135.53s (100% green).
- **Remaining Risks:** None for Phase 09. Phase 10 (Generic Tutor Orchestrator) next.

---

### Entry: Phase 10 — Generic Tutor Orchestrator with 16-Step Course Lifecycle (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Implemented Central Generic Tutor Orchestrator (`central_platform/tutor/orchestrator.py`):
    - Enforces the authoritative 16-step course lifecycle contract:
      1. Identity validation (rejects empty/whitespace `student_id`, `session_id`, `course_id` per Rule 4).
      2. Enrollment validation (enforces private course authorization, auto-enrolls public courses).
      3. Course and version resolution (pins specific version or pulls latest published version; raises `CourseNotFoundError`).
      4. Class / Cohort resolution (resolves class/cohort context from enrollment).
      5. Learning state resolution (canonical state partitioned strictly by `(student_id, course_id)`).
      6. Hierarchical instruction resolution (`SESSION > STUDENT > CLASS > COURSE > ORGANIZATION`).
      7. Course policy enforcement (extracts policy from published course version).
      8. Course tool policy check (inspects enabled tools and custom tools via `CourseToolPolicy`).
      9. Scoped RAG retrieval (version & org pinned RAG search, with graceful fallback on empty chunks).
      10. 7-layer context assembly (assembles pruned prompt context blocks via `ContextBuilder`).
      11. Pedagogy response planning (constructs `NextActionDecision` and `PedagogicalResponsePlan` with anti-answer-leakage guard).
      12. AI Gateway execution (routes request via provider-neutral `AIGatewayService`).
      13. 7-invariant response validation (validates generated response against model failures, prompt injection, educational safety, and answer leakage).
      14. Learning evidence staging (stages proposed mastery state and learning events in an isolated buffer).
      15. Two-phase transactional state commit (commits atomically to database only when validation passes; rolls back state on validation failure).
      16. Audit & telemetry (tracks latency, deduplicates identical turns via fingerprint cache, returns typed `TutorTurnResult`).
  - Implemented REST Turn Endpoint (`central_platform/api/routes/tutor.py`, `central_platform/api/app.py`):
    - Mounted `POST /api/v1/tutor/turn` providing typed HTTP client turn execution, structured error mapping (`404` for missing course, `403` for unauthorized enrollment, `400` for validation errors).
  - Enhanced Subsystems & Invariants:
    - Updated `core/orchestrator.py` `TurnOptions` with optional `course_id: str | None = None`.
    - Enhanced `ContextBuilder.build_system_prompt` to accept `grade_level` and generalized default prompt to "academic and STEM tutor".
    - Enhanced `ContextBuilder.build_user_prompt` with `misconception_alerts`.
    - Enhanced `StateCommitPipeline.validate_and_commit` to accept `response_plan` and pass it to `ResponseValidatorEngine`.
  - Test Suite (`tests/test_phase10_generic_tutor_orchestrator.py`):
    - 11 comprehensive tests covering Physics execution, public CS auto-enrollment, History multi-disciplinary execution, identity validation failures (Rule 4), invalid course rejection, unauthorized private enrollment blocking, RAG empty resilience, response validation failure and atomic rollback, duplicate turn idempotency, zero Chemistry coupling invariant, and FastAPI REST endpoint integration.
  - Regression Suite:
    - 957 tests passing in 143.59s (100% green).
- **Bugs Found & Fixed:**
  - Resolved `CourseToolPolicy` attribute access error by dynamically checking declared tool fields and custom tools.
  - Resolved `ContextBuilder.build_system_prompt` keyword argument mismatch and decoupled default base prompt.
  - Resolved `NextActionDecision` constructor keyword argument alignment.
  - Resolved `MasteryState` keyword argument alignment (`slr_id` instead of `student_id`).
  - Resolved SQLite foreign key failure by guaranteeing user and session records exist before staging `LearningEvent`.
  - Resolved Socratic answer-leakage validation bypass by enforcing `response_plan.anti_answer_leakage_guard = True` and forwarding `response_plan` to `commit_pipeline.validate_and_commit`.
- **Tests Run:** 957 tests collected, 957 passed in 143.59s (100% green).
- **Remaining Risks:** None for Phase 10. Phase 11 (General Evaluation Engine) next.

---

### Entry: Phase 11 — Generic Assessment & Evaluation Engine (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Standardized Evaluation Contract (`central_platform/assessment/evaluators/base.py`):
    - Added 4-valued `EvaluationStatus` (`CORRECT`, `PARTIALLY_CORRECT`, `INCORRECT`, `UNCERTAIN`).
    - Added typed `EvaluationOutcome` containing score, confidence, error type, evidence list, misconception code, feedback, and remediation hint.
    - Added abstract `BaseEvaluator` protocol.
  - Deterministic & Multidisciplinary Evaluators (`central_platform/assessment/evaluators/`):
    - `MCQEvaluator`: Handles letter options (A/B/C/D), string value matching, and 0/1-based indexing.
    - `NumericalEvaluator`: Evaluates arithmetic equations with customizable relative tolerance (default 1%) and unit verification; yields `PARTIALLY_CORRECT` with `error_type="unit"` when the numeric value is correct but unit is missing/mismatched.
    - `BooleanEvaluator`: Evaluates boolean True/False tokens and flags ambiguous/malformed inputs as `UNCERTAIN`.
    - `CodeExecutionEvaluator`: Verifies Python AST syntax, executes code safely in `ProgrammingSandboxAdapter`, and validates stdout and return value against test expectations.
    - `RubricEvaluator`: Multi-criterion rubric scoring decoupled from hardcoded chemistry patterns; matches student answers against criteria thresholds and dynamic misconception catalogs extracted from course curriculum metadata.
    - `ChemistryEquationEvaluator`: Domain adapter hook delegating equation balancing to `ChemistryToolAdapter` without leaking chemistry dependencies into platform core.
    - `EvaluatorRegistry`: Central capability-driven registry mapping question types and capabilities to evaluators with fallback handling.
  - Anti-Answer-Leakage Sanitizer (`central_platform/assessment/sanitizer.py`):
    - `AssessmentSanitizer.sanitize_assessment_for_student()` and `sanitize_question_for_student()`: Deep copies assessment/question payloads and scrubs `answer_key`, `correct_answer`, `rubric`, `evaluation_rubric`, `explanation`, and `teacher_notes` before question delivery.
    - Added `verify_sanitized()` invariant validator.
  - Decoupled Assessment Service (`central_platform/assessment/service.py`):
    - Removed hardcoded `"crs-chem-101"` / `"CHEM101"` default in `_ensure_entities`.
    - Integrated `AssessmentSanitizer` via `get_sanitized_assessment()`.
    - Added `review_attempt()` wrapper enabling teacher score overrides, item-level feedback, and explicit approval.
  - Test Suite (`tests/test_phase11_generic_assessment_evaluation.py`):
    - 12 comprehensive unit, integration, and security tests covering MCQ, numerical tolerance, unit mismatch detection, boolean evaluation, code sandbox execution, dynamic rubric misconception resolution, uncertain/malformed input handling, anti-leakage sanitization, course/version isolation, teacher review overrides, remediation recommendation isolation, and the zero-chemistry generic registry invariant.
  - Regression Suite:
    - 969 tests passing in 142.14s (100% green, zero regressions).
- **Bugs Found & Fixed:**
  - `ProgrammingSandboxAdapter` and `ChemistryToolAdapter` require `ToolExecutionContext(course_id=..., user_role=...)`: supplied valid execution context.
  - `AssessmentService.submit_attempt` returns an `AssessmentAttempt` model object rather than a raw dict: updated assertions to access object attributes.
  - Rubric passing score alignment: mapped rubric normalized score `>= 0.70` to `EvaluationStatus.CORRECT` to align with the standard passing threshold.
  - `QuestionBankItem` requires explicit `course_id`: ensured all test fixtures pass `course_id`.
- **Tests Run:** 969 tests collected, 969 passed in 142.14s (100% green).
- **Remaining Risks:** None for Phase 11. Phase 12 (Real Online API Boundary) next.

---

### Entry: Phase 12 — Real Online API Boundary (2026-10-01)
- **Status:** Complete (Verified)
- **Changes Made:**
  - Live Subsystem Health Probes (`central_platform/health/service.py`, `central_platform/health/__init__.py`):
    - Implemented `PlatformHealthService` probing live SQLite connection (`SELECT 1`), model manifest registry, and storage subsystems.
    - Connected `/healthz`, `/livez`, `/readyz`, and `/api/v1/health` with simulated failure hook returning `503 Service Unavailable`.
  - Multi-Tenant Course Catalog & Version Lifecycle (`central_platform/api/routes/courses.py`):
    - Removed hardcoded static `_COURSES` list; routed directly to `CourseService` and persistent database.
    - Enforced public catalog discovery and private organization course gatekeeping (`403 Forbidden` for cross-org access).
    - Added course version creation, review submission, publication, and organization offering pinning endpoints.
  - Multi-Tenant Classes, Cohorts & Enrollments (`central_platform/api/routes/classes.py`, `enrollments.py`):
    - Added class groups and academic cohorts REST endpoints.
    - Replaced in-memory `_ENROLLMENTS` list with persistent database operations and student auto-provisioning.
  - Hierarchical Teacher Instructions REST Resolution (`central_platform/api/routes/instructions.py`):
    - Added endpoints to issue and dynamically resolve 5-tier instruction cascade (Organization -> Course -> Class -> Cohort -> Student).
  - Assessment Delivery & Teacher Review (`central_platform/api/routes/assessments.py`):
    - Added sanitized assessment delivery (`GET /assessments/{id}/sanitized`) with anti-answer-leakage guarantee.
    - Added teacher attempt review and score adjustment endpoint (`POST /assessments/attempts/{id}/review`).
  - Tutor Turn Over HTTP (`central_platform/api/routes/tutor.py`):
    - Exposed generic 16-step tutoring lifecycle over `POST /api/v1/tutor/turn`.
  - API Schemas & App Mounting (`central_platform/api/schemas.py`, `central_platform/api/app.py`):
    - Added typed request/response models for all new endpoints; mounted all routers.
  - Artifacts Exported:
    - Generated OpenAPI 3.1.0 schema snapshot: `docs/reports/OPENAPI_SNAPSHOT_V2.json` (167 paths).
    - Generated API Contract: `docs/reports/API_CONTRACT_V2.md`.
    - Generated Test Report: `docs/reports/PHASE_12_TEST_REPORT.md` and Results JSON `docs/reports/PHASE_12_TEST_RESULTS.json`.
  - Test Suite (`tests/test_phase12_real_online_api_boundary.py`):
    - 12 comprehensive tests running against a real Uvicorn server on a dynamic TCP loopback socket.
  - Regression Suite:
    - 981 tests passing in 129.56s (100% green, zero regressions).
- **Bugs Found & Fixed:**
  - Added missing `import os` in `central_platform/auth/dependencies.py`.
  - Fixed `asmt` dictionary unpacking in `central_platform/api/routes/assessments.py:get_sanitized_assessment`.
  - Fixed parameter keyword arguments for `CourseService.create_course_version` (`version_number`), `submit_version_for_review`, and `select_course_for_org` (`pinned_version_id`).
  - Added compatibility fields `ok` and `assistant_text` to `TutorTurnApiResponse`.
  - Resolved `CourseOffering` attribute mapping (`pinned_version_id` and `enrolled_at`).
  - Resolved order-dependent assertion in `test_phase12_learning_event_system.py`.
- **Tests Run:** 981 tests collected, 981 passed in 129.56s (100% green).
- **Remaining Risks:** None for Phase 12. Phase 13 (Offline Local Runtime) next.





