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


