# GitHub Remote Sync Queue

**Document:** `docs/reports/GITHUB_SYNC_QUEUE.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** `REMOTE_SYNC = QUEUED_FOR_ISSUE_OPERATIONS`  
**Maintained Per:** Section 44 of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## 1. Remote Git Capabilities Status
- **Git Push Access:** ACTIVE (`git push --dry-run origin master` succeeded via system git credential manager).
- **GitHub CLI / API (`gh`):** UNAUTHENTICATED (`gh auth status` reports not logged in).
- **Policy:** Commits and branches can be pushed to `origin`. Any issue creation, issue commentary, or pull request operations must be recorded here with exact contents and executed when credentials are provided or via web UI.

---

## 2. Queued Remote Actions

### Item 001: Phase 00 Completion Update
- **Target Branch:** `master` / `platform/course-independent-core`
- **Commit SHA:** `bf47a63273e936b7617937be199e44efb4d9cb5d`
- **Intended Issue Title:** `[Architecture] Phase 00 Forensic Baseline & Branch Reconciliation Complete`
- **Intended Labels:** `architecture`, `testing`, `P0`
- **Intended Comment:**
  ```text
  Phase 00 Forensic Baseline and Branch Reconciliation completed.
  
  Baseline Metrics:
  - Branch Reconciliation: master is 10 commits ahead of main; 0 unique non-merge commits on main. Backup tags created: backup-main-9ca3c65, backup-master-bf47a63.
  - Test Suite: 856 tests collected, 856 passed in 80.32s (pytest).
  - Compilation: 0 bytecode syntax errors across 607 files.
  - Linting: 5,188 diagnostics categorized (ruff).
  - Tracked Defects:
    - BUG-ARCH-001 (P0): 115 files coupled to Chemistry outside adapters.
    - BUG-ARCH-002 (P0): 3 production files importing legacy.agents.default_agents.
    - BUG-ARCH-003 (P0): 13 production files hardcoding fake student rosters.
    - BUG-ARCH-004 (P1): 5 modules executing dynamic inline ALTER TABLE.
    - BUG-ARCH-005 (P1): Duplicate CREATE TABLE assignments in migrations/001_initial_schema.sql.
    - BUG-ARCH-006 (P1): Model manifest vs config contradictions.
  
  Reports Generated:
  - docs/reports/BRANCH_RECONCILIATION_REPORT.md
  - docs/reports/PHASE_00_FORENSICS.md
  - docs/reports/PHASE_00_FILE_INVENTORY.csv
  - docs/reports/PHASE_00_DEPENDENCY_GRAPH.md
  - docs/reports/PHASE_00_TEST_BASELINE.md
  - docs/reports/PHASE_00_TEST_RESULTS.json
  - PROJECT_STATE.yaml
  ```
- **Push Status:** `COMPLETED (commit f9854f8 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED (awaiting gh CLI login)`

### Item 002: Phase 01 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 01 Architecture Contract & Repository Guardrails Complete`
- **Intended Labels:** `architecture`, `testing`, `P0`
- **Intended Comment:**
  ```text
  Phase 01 Architecture Contract & Repository Guardrails completed.
  
  Deliverables:
  - docs/ARCHITECTURE_TARGET.md: System specifications and layer contracts.
  - docs/DATA_MODEL_TARGET.md: Relational DDL, composite keys, and dataclasses.
  - docs/SECURITY_MODEL_TARGET.md: Pre-retrieval RAG security and authorization matrix.
  - docs/TESTING_STRATEGY_TARGET.md: 5-level testing pyramid and acceptance journeys A-G.
  - docs/AGENT_DEVELOPMENT_RULES.md: Strict engineering invariants for AI development agents.
  - tests/architecture/: 12 automated guard tests passing (anti-chemistry, anti-legacy, anti-demo roster, migration integrity, model config).
  - .github/workflows/ci.yml: Updated to execute architecture guards on PR/push for main and master.
  - Fixed BUG-ARCH-005: Deduplicated assignments table in migration 001.
  ```
- **Push Status:** `COMPLETED (commit 48e5e5f pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 003: Phase 02 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 02 Canonical Course, Version & Offering Domain Complete`
- **Intended Labels:** `domain-model`, `migrations`, `courses`, `P0`
- **Intended Comment:**
  ```text
  Phase 02 Canonical Course, Version & Offering Domain completed.
  
  Deliverables:
  - central_platform/models/schema.py: CourseVisibility, CourseStatus, CourseToolPolicy, CoursePolicy, CourseVersion, OrganizationCourseOffering models.
  - migrations/004_course_domain_model.sql: Added visibility, course_offering_id, course_versions, organization_course_offerings tables/indexes.
  - migrations/004_course_domain_model_down.sql: Reversible schema rollback.
  - central_platform/courses/service.py: CourseService implementing isolated tenant access, version state machines, and tool permission guards.
  - tests/test_phase02_course_domain_model.py: Service lifecycle & authorization unit/integration tests.
  - tests/test_phase02_migrations.py: Migration up, down, and idempotent reapply tests.
  - docs/reports/PHASE_02_MIGRATION_REPORT.md, PHASE_02_TEST_REPORT.md, PHASE_02_TEST_RESULTS.json.
  - Regression results: 874/874 passed in 91.27s.
  ```
- **Push Status:** `COMPLETED (commit 6edbf5e pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 004: Phase 03 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 03 Generic Curriculum & Versioned Learning Graph Complete`
- **Intended Labels:** `curriculum`, `learning-graph`, `architecture`, `P0`
- **Intended Comment:**
  ```text
  Phase 03 Generic Curriculum & Versioned Learning Graph completed.
  
  Deliverables:
  - core/curriculum/models.py: GenericConcept, GenericTopic, GenericModule, GenericCurriculum, format_concept_id, parse_concept_id.
  - core/curriculum/chemistry_adapter.py: Decoupled Chemistry concept knowledge and keyword maps into isolated adapter with runtime toggle.
  - core/curriculum/resolver.py: Generalized ConceptResolver supporting course curriculum registry, multi-course keyword/alias resolution, and neutral undetermined fallback.
  - core/curriculum/validator.py: Colon (:) enabled in STABLE_ID_PATTERN for namespaced concept IDs, and data-driven domain validation.
  - core/curriculum/loader.py: load_generic_curriculum() supporting diverse subject manifests.
  - Fixtures added: data/curriculum/physics/mechanics_grade11.json, data/curriculum/history/world_history.json, data/curriculum/programming/intro_cs.json.
  - central_platform/learning/graph.py: validate_curriculum_dag() with DFS cycle detection, missing prerequisite checks, and orphan detection.
  - tests/test_phase03_generic_curriculum.py: Ingestion, resolution, namespacing, and DAG tests across 4 disciplines.
  - Phase Gate: Passed verification with Chemistry adapter disabled.
  - Regression results: 880/880 passed in 105.67s.
  ```
- **Push Status:** `COMPLETED (commit 2345def pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 005: Phase 04 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 04 Course-Scoped Student Learning State & Sessions Complete`
- **Intended Labels:** `learning-state`, `sessions`, `multi-course`, `P0`
- **Intended Comment:**
  ```text
  Phase 04 Course-Scoped Student Learning State & Sessions completed.
  
  Deliverables:
  - central_platform/models/schema.py: CourseLearningContext, Session with course_version_id and class_id, LearningEvent with course_version_id.
  - central_platform/db.py: create_session, get_session, and get_sessions_for_student updated with course_version_id and course_id filtering.
  - central_platform/learning/state.py: LearningStateManager enforcing strict (student_id, course_id) partitioning for SLRs and masteries, course context validation gates, and idempotent telemetry.
  - core/tutor/state.py: Added backward-compatible course_id scoping to StudentConceptMastery and LearningEvent.
  - tests/test_phase04_course_learning_state.py: Cross-course isolation (same concept name, distinct courses), session/event scoping, idempotent telemetry, and exact recovery tested.
  - Regression results: 886/886 passed in 85.51s.
  ```
- **Push Status:** `COMPLETED (commit 0f8e178 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 006: Phase 05 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 05 Knowledge Asset Ingestion & Publication Pipeline Complete`
- **Intended Labels:** `rag`, `knowledge-assets`, `publication-pipeline`, `P0`
- **Intended Comment:**
  ```text
  Phase 05 Knowledge Asset Ingestion & Publication Pipeline completed.

  Deliverables:
  - central_platform/models/schema.py: KnowledgeContentType enum, expanded RAGSourceStatus/KnowledgeAssetStatus enum, extended RAGSource with publication and lifecycle attributes.
  - migrations/005_knowledge_assets.sql & _down.sql: Reversible schema migration adding publication metadata and indexing to rag_sources.
  - central_platform/db.py: Updated create_rag_source, get_rag_source, list_rag_sources (content_type filter), and get_rag_chunks_by_course with case-insensitive status matching.
  - central_platform/rag/service.py: Full pipeline implementation including upload_knowledge_asset(), approve_knowledge_asset(), publish_knowledge_asset(), archive_knowledge_asset(), and strict student visibility invariant in query().
  - central_platform/api/schemas.py & routes/rag.py: Updated REST schemas and endpoints to support content classifications and publication lifecycle.
  - tests/test_phase05_knowledge_assets.py: 12 tests verifying multi-format ingestion (Markdown, JSON, Text), full lifecycle state transitions, malformed failure isolation, role-based authorization gates, and the Phase Gate student visibility invariant.
  - Regression results: 898/898 passed in 106.60s.
  ```
- **Push Status:** `COMPLETED (commit 4f7e9f6 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 007: Phase 06 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 06 Scoped RAG & Knowledge Authorization Complete`
- **Intended Labels:** `rag`, `authorization`, `multi-tenant`, `scoping`, `P0`
- **Intended Comment:**
  ```text
  Phase 06 Scoped RAG & Knowledge Authorization completed.

  Deliverables:
  - central_platform/models/schema.py: KnowledgeVisibilityScope enum (COURSE, CLASS, STUDENT_TARGETED), extended RAGSource and RAGChunk with course_version_id, visibility_scope, class_id, target_student_ids.
  - migrations/006_scoped_rag_authorization.sql & _down.sql: Reversible schema migration with composite performance indexes (idx_rag_sources_scoped, idx_rag_chunks_scoped). Tested up/down rollback on SQLite.
  - central_platform/db.py: Updated RAG persistence and get_rag_chunks_by_course with version pinning, class-level filtering, and student targeted remedial filtering.
  - central_platform/rag/service.py: SmartChunker scoping propagation; RAGService.query() with multi-tenant org isolation check (RAG_DENIED on unauthorized access) and zero-leakage invariant (RAG_EMPTY without global fallback).
  - central_platform/api/schemas.py & routes/rag.py: REST endpoints supporting scoped source registration, filtering, chunk listing, and query execution.
  - tests/test_phase06_scoped_rag_authorization.py: 10 comprehensive tests covering course scope, multi-tenant isolation, partner offerings, class notes, student targeted remedial, version isolation, CourseLearningContext binding, no fallback, diagnostic transparency, and REST API flow.
  - Regression results: 908/908 passed in 97.71s (100% green).
  ```
- **Push Status:** `COMPLETED (commit 888d936 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 008: Phase 07 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 07 Teacher Instruction Hierarchy & Scoping Complete`
- **Intended Labels:** `instructions`, `pedagogy`, `rbac`, `hierarchy`, `P0`
- **Intended Comment:**
  ```text
  Phase 07 Teacher Instruction Hierarchy & Scoping completed.

  Deliverables:
  - central_platform/models/schema.py: InstructionScope enum (ORGANIZATION, COURSE, CLASS, STUDENT, SESSION), extended TeacherInstructionRecord with 21 columns including organization_id, course_version_id, class_id, session_id, scope_type, status, safety_status, start_at, expires_at, version, audit_trail, updated_at.
  - migrations/007_teacher_instruction_hierarchy.sql & _down.sql: Reversible schema migration with composite indexes (idx_teacher_inst_scope, idx_teacher_inst_class, idx_teacher_inst_org, idx_teacher_inst_session, idx_teacher_inst_hierarchy).
  - central_platform/db.py: Updated create_teacher_instruction, _row_to_teacher_instruction, get_hierarchical_teacher_instructions with status and scope filtering.
  - central_platform/teacher/instruction.py: ScopeType, TeacherInstructionEngine with resolve_hierarchical_instructions enforcing SESSION > STUDENT > CLASS > COURSE > ORGANIZATION precedence, student write blocking, cross-org teacher denial, format_prompt_directive with strict data framing and system invariant guards.
  - central_platform/api/schemas.py & routes/teachers.py: Hierarchical request/response schemas, create_instruction with org and RBAC checks, get_instructions with hierarchical resolution query parameter.
  - tests/test_phase07_teacher_instruction_hierarchy.py: 13 comprehensive tests covering hierarchy scopes, cross-org denial, student write blocking, temporal filtering, class/student scoping containment, precedence cascade, priority tie-breaking, prompt injection rejection, anti-answer leakage rejection, prompt framing, SQLite persistence, and REST API endpoints.
  - Regression results: 921/921 passed in 111.10s (100% green).
  ```
- **Push Status:** `QUEUED (ready for commit & push)`
- **Issue Operations Status:** `QUEUED`





