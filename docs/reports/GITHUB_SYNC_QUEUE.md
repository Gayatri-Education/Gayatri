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
- **Push Status:** `COMPLETED (commit 082ceab pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 009: Phase 08 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 08 Course Tool Capability & Adapter Registry Complete`
- **Intended Labels:** `tools`, `capabilities`, `adapters`, `security`, `P0`
- **Intended Comment:**
  ```text
  Phase 08 Course Tool Capability & Adapter Registry completed.

  Deliverables:
  - central_platform/tools/capabilities.py: ToolCategory enum, ResourceLimits dataclass, ToolCapability, ToolExecutionContext, ToolExecutionResult models.
  - central_platform/tools/base.py: ToolAdapter abstract base class defining get_capabilities, validate_arguments, execute.
  - central_platform/tools/registry.py: ToolRegistry supporting modular registration, discovery, and policy-filtered tool enumeration.
  - central_platform/tools/engine.py: ToolExecutionEngine enforcing the 6-point execution contract (course tool policy, user role RBAC, scope containment, schema validation, resource timeout limits, and typed results).
  - central_platform/tools/adapters/: Domain adapters for Chemistry (nullspace equation balancer & formula parser), Math (safe AST mathematical calculator without eval), and Programming (sandboxed syntax verification & execution).
  - central_platform/api/schemas.py & routes/tools.py: REST endpoints for GET /api/v1/tools, GET /api/v1/tools/{course_id}, and POST /api/v1/tools/execute.
  - tests/test_phase08_course_tool_registry.py: 11 comprehensive tests verifying registry discovery, course policy enablement, zero-tools course policies, role-based access control, resource limit timeouts, input validation, chemistry equation balancing, safe math AST evaluation, programming sandbox execution, phase gate architectural decoupling, and REST API endpoints.
  - Regression results: 932/932 passed in 121.92s (100% green).
  ```
- **Push Status:** `COMPLETED (commit 9abc261 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 010: Phase 09 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 09 Model Registry & AI Gateway Unification Complete`
- **Intended Labels:** `models`, `gateway`, `manifest`, `inference`, `legacy-cleanup`, `P0`
- **Intended Comment:**
  ```text
  Phase 09 Model Registry & AI Gateway Unification completed.

  Deliverables:
  - model_manifest.json: Extended schema with canonical Phase 09 fields (artifact_path, format="gguf", prompt_template="chatml", context_window=8192, streaming=true, capabilities, resource_profile, checksum).
  - core/model_fetch/manifest_validator.py: Hardened validator with canonical alias field normalization, get_active_manifest(), and verify_model_checksum().
  - core/config.py: Synchronized default fallback model, HuggingFace repository, and filename with Qwen2.5-0.5B (eliminating BUG-ARCH-006).
  - core/inference/context.py: Decoupled prompt message construction (build_chat_messages) and tutor context formatting (get_tutor_context) from legacy.
  - core/inference/service.py: Replaced legacy _local_chat_stream import with direct routing via LocalProvider.chat_stream and ProviderRegistry. Added privacy mode enforcement (local_only fail-closed with PermissionError), cooperative streaming cancellation, and non-silent error propagation (Rule 3).
  - core/runtimes/chemistry.py & core/runtimes/general.py: Decoupled from legacy to core.inference.context.
  - legacy/agents/default_agents.py: Marked deprecated with DeprecationWarning; re-exports from core.inference.context.
  - tests/architecture/test_anti_legacy_imports.py: Whitelist reduced to 0 callers. Verified zero legacy callers across core/, central_platform/, and app/ (eliminating BUG-ARCH-002).
  - tests/test_phase09_model_registry_ai_gateway.py: 14 comprehensive tests covering manifest consistency, model config parsing, missing model offline guidance, wrong provider rejection, corrupt checksum rejection, timeout propagation, invalid response handling, privacy mode blocking, observable fallback chain, streaming and cancellation, ChatML template consistency, context builder, and zero legacy imports.
  - Regression results: 946/946 passed in 135.53s (100% green).
  ```
- **Push Status:** `COMPLETED (commit 92b9db8 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 011: Phase 10 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 10 Generic Tutor Orchestrator with 16-Step Course Lifecycle Complete`
- **Intended Labels:** `tutor`, `orchestration`, `course-lifecycle`, `anti-leakage`, `P0`
- **Intended Comment:**
  ```text
  Phase 10 Generic Tutor Orchestrator with 16-Step Course Lifecycle completed.

  Deliverables:
  - central_platform/tutor/orchestrator.py: GenericTutorOrchestrator enforcing the 16-step turn lifecycle (identity validation, enrollment validation, course/version resolution, class/cohort resolution, canonical learning state isolation, hierarchical teacher instruction resolution, course policy enforcement, course tool policy check, scoped RAG retrieval, 7-layer context assembly, pedagogy response planning, AI gateway execution, 7-invariant response validation, learning evidence staging, 2-phase transactional commit/rollback, and telemetry).
  - central_platform/api/routes/tutor.py & central_platform/api/app.py: REST turn endpoint POST /api/v1/tutor/turn with typed error mapping and client execution.
  - core/orchestrator.py: Updated TurnOptions with optional course_id.
  - central_platform/ai/context_builder.py: Enhanced build_system_prompt with grade_level and neutral academic base prompt; enhanced build_user_prompt with misconception_alerts.
  - central_platform/learning/commit_pipeline.py: Enhanced validate_and_commit to accept response_plan and pass it to ResponseValidatorEngine.
  - tests/test_phase10_generic_tutor_orchestrator.py: 11 comprehensive tests verifying multi-subject execution, auto-enrollment, Rule 4 identity validation, unauthorized access denial, RAG empty resilience, answer-leakage rejection and state rollback, duplicate turn idempotency, zero Chemistry coupling invariant, and REST API integration.
  - Regression results: 957/957 passed in 143.59s (100% green).
  ```
- **Push Status:** `COMPLETED (commit bc8d773 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 012: Phase 11 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 11 Generic Assessment & Evaluation Engine Complete`
- **Intended Labels:** `assessment`, `evaluation`, `anti-leakage`, `rubric`, `P0`
- **Intended Comment:**
  ```text
  Phase 11 Generic Assessment & Evaluation Engine completed.

  Deliverables:
  - central_platform/assessment/evaluators/base.py: Canonical 4-valued EvaluationStatus (CORRECT, PARTIALLY_CORRECT, INCORRECT, UNCERTAIN), typed EvaluationOutcome, and BaseEvaluator protocol.
  - central_platform/assessment/evaluators/deterministic.py: MCQEvaluator, NumericalEvaluator (relative tolerance & unit mismatch detection), BooleanEvaluator.
  - central_platform/assessment/evaluators/code.py: CodeExecutionEvaluator with AST syntax check and ProgrammingSandboxAdapter isolation.
  - central_platform/assessment/evaluators/rubric.py: RubricEvaluator with dynamic misconception catalog extraction from curriculum metadata and multi-criterion scoring.
  - central_platform/assessment/evaluators/adapter_hooks.py: ChemistryEquationEvaluator domain adapter hook using ChemistryToolAdapter.
  - central_platform/assessment/evaluators/registry.py: EvaluatorRegistry with capability-driven routing and fallback mechanism.
  - central_platform/assessment/sanitizer.py: AssessmentSanitizer stripping answer keys, correct answers, rubrics, and notes before question delivery to students.
  - central_platform/assessment/service.py: Decoupled service removing hardcoded chemistry default, added get_sanitized_assessment(), and review_attempt() wrapper for teacher overrides.
  - tests/test_phase11_generic_assessment_evaluation.py: 12 comprehensive unit, integration, and security tests covering all evaluator types, unit errors, code execution, dynamic misconceptions, uncertain inputs, anti-leakage sanitization, course/version isolation, teacher overrides, and zero chemistry coupling in generic evaluators.
  - Regression results: 969/969 passed in 142.14s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 70fb229 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 013: Phase 12 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 12 Real Online API Boundary Complete with Live Probes and 16 Subsystems`
- **Intended Labels:** `api`, `health`, `routes`, `real-runtime`, `P0`
- **Intended Comment:**
  ```text
  Phase 12 Real Online API Boundary completed.

  Deliverables:
  - central_platform/health/service.py: PlatformHealthService probing live SQLite connectivity (SELECT 1), AI model manifest, and storage readiness, with failure simulation hooks.
  - central_platform/api/app.py: Wired /healthz, /livez, /readyz, and /api/v1/health directly to live PlatformHealthService; mounted all 16 subsystem routers.
  - central_platform/api/routes/courses.py: Replaced hardcoded _COURSES with dynamic CourseService queries; enforced public/private scoping; added course version drafting, submission, and publication endpoints.
  - central_platform/api/routes/classes.py: Added class groups and academic cohorts REST endpoints.
  - central_platform/api/routes/enrollments.py: Replaced in-memory _ENROLLMENTS with persistent PlatformDatabase operations and auto-provisioning.
  - central_platform/api/routes/instructions.py: Added 5-tier hierarchical instruction resolution REST endpoints.
  - central_platform/api/routes/assessments.py: Added sanitized assessment delivery with anti-answer-leakage guarantee and teacher attempt review / score adjustment endpoints.
  - central_platform/api/routes/tutor.py: Exposed generic 16-step tutoring lifecycle over POST /api/v1/tutor/turn.
  - central_platform/api/schemas.py: Added typed Pydantic models for all new endpoints.
  - docs/reports/OPENAPI_SNAPSHOT_V2.json: Exported canonical OpenAPI 3.1.0 snapshot containing 167 endpoints.
  - docs/reports/API_CONTRACT_V2.md: Published canonical HTTP API contract.
  - tests/test_phase12_real_online_api_boundary.py: 12 tests against live Uvicorn socket covering health probes, broken subsystem failure, auth, account suspension, RBAC, courses, cohorts, instructions, assessments, tutor turn, error envelopes, and zero-chemistry router decoupling.
  - Regression results: 981/981 passed in 129.56s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 7f5489f pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 014: Phase 13 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 13 Offline Local Runtime Package & Sync Readiness Complete`
- **Intended Labels:** `offline`, `local-runtime`, `rag`, `persistence`, `anti-demo-roster`, `P0`
- **Intended Comment:**
  ```text
  Phase 13 Offline Local Runtime Package & Sync Readiness completed.

  Deliverables:
  - local_runtime/errors.py: Typed offline errors (OfflineRuntimeError, OfflineCourseNotCachedError, ModelUnavailableError, CorruptedCacheError, ReadOnlyDatabaseError).
  - local_runtime/course_cache.py: LocalCourseCache managing .gpk zip/JSON distribution, deterministic SHA-256 package checksum validation, and automated quarantine isolation of corrupted packages into data/cache/quarantine/.
  - local_runtime/rag_cache.py: LocalRAGCache offline BM25 knowledge search strictly enforcing course and version scoping (zero cross-course leakage).
  - local_runtime/session.py: LocalSessionPersistence providing transactional SQLite turn lifecycle (begin_turn, commit_turn, rollback_turn), crash recovery rolling back PENDING_COMMIT turns on startup, and graceful read-only degraded execution.
  - local_runtime/detector.py: OfflineCapabilityDetector providing OfflineCapabilitiesReport and honest DegradedStateInfo.
  - local_runtime/engine.py: LocalRuntimeEngine gluing cache, RAG, and session persistence to execute offline tutoring turns without internet connection.
  - app/bridge/facade.py: Remediated BUG-ARCH-003 by eliminating fake demo student roster (Rahul Kumar, Priya Sharma, Amit Patel), fake instructions, and fake alerts; wired to PlatformDatabase with honest empty states.
  - tests/test_phase13_offline_local_runtime.py: 12 comprehensive unit and integration tests covering clean launch, capability detection, package caching, quarantine, uncached courses, tutor turns, state persistence across restarts, crash rollback, read-only mode, missing models, bridge zero-demo-roster guard, and zero-chemistry invariant.
  - Regression results: 993/993 passed in 131.81s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit b88b616 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 015: Phase 14 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 14 Sync & Conflict Resolution Complete`
- **Intended Labels:** `sync`, `conflict-resolution`, `outbox`, `idempotency`, `P0`
- **Intended Comment:**
  ```text
  Phase 14 Sync & Conflict Resolution completed.

  Deliverables:
  - migrations/008_sync_operations.sql & 008_sync_operations_down.sql: Schema for sync_operations audit and tracking table with composite indexes.
  - central_platform/models/schema.py & central_platform/db.py: SyncOperationRecord model and DB methods record_sync_operation, get_sync_operation, get_sync_operations_for_student.
  - local_runtime/sync_outbox.py: LocalSyncOutbox with microsecond-resolution next_retry_ts backoff, batch staging/commit, crash/restart durability, and exponential retry.
  - central_platform/sync/service.py: Authoritative SyncService with operation-level idempotency replay caching, LearningEventStore deduplication, partial sync acknowledgement, multi-device SLR mastery convergence, out-of-order event reconciliation, course version mismatch handling, and device quarantine enforcement.
  - central_platform/api/schemas.py & central_platform/api/routes/sync.py: Extended POST /api/v1/sync and added GET /api/v1/sync/status.
  - tests/test_phase14_sync_conflict_resolution.py: 12 comprehensive unit and integration tests covering normal lifecycle, duplicate event idempotency, operation replay idempotency, partial acknowledgement, network timeout/retry, device quarantine, client crash recovery, server restart persistence, multi-device convergence, version mismatch resolution, out-of-order reconciliation, and sync audit API.
  - Regression results: 1,005/1,005 passed in 153.13s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 33df924 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 016: Phase 15 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 15 Admin Course & Content Workflow UI Complete`
- **Intended Labels:** `ui`, `admin-portal`, `course-workflow`, `review-queue`, `P0`
- **Intended Comment:**
  ```text
  Phase 15 Admin Course & Content Workflow UI completed.

  Deliverables:
  - central_platform/db.py: archive_course, archive_course_version, get_course_versions_by_status.
  - central_platform/courses/service.py: Audit logging for course/version transitions, archive_course, archive_course_version, get_review_queue with tenant scoping.
  - central_platform/api/schemas.py & central_platform/api/routes/courses.py: CourseArchiveResponse, CourseReviewQueueItemResponse, GET /api/v1/courses/review-queue, POST /api/v1/courses/{id}/archive, POST /api/v1/courses/{id}/versions/{version_id}/archive.
  - central_platform/api/routes/curricula.py: Dynamic DB binding for CurriculumService eliminating test fixture stale singletons.
  - app/portals/admin/controller.py: Real DB and CourseService integration with stats, courses, review queue, and audit trail.
  - app/ui/admin_portal.html: Course catalog with visibility filters, modals (course, offering, new version, upload content), live review queue with approve & publish / archive actions.
  - tests/test_phase15_admin_course_content_workflow.py: 12 comprehensive unit and integration tests covering private/public isolation, offering selection, versioning, RAG ingestion, review queue scoping, approve/publish, unauthorized role rejection, archiving, and controller audit trail.
  - Regression results: 1,017/1,017 passed in 154.32s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 3fb9d8e pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 017: Phase 16 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 16 Teacher Workflow UI & Class Management Complete`
- **Intended Labels:** `ui`, `teacher-portal`, `class-management`, `remedial-content`, `instructions`, `P0`
- **Intended Comment:**
  ```text
  Phase 16 Teacher Workflow UI & Class Management completed.

  Deliverables:
  - central_platform/db.py: get_class_group, list_class_groups_by_organization, list_class_groups_by_course, get_students_for_class_group, get_cohort, get_cohorts_for_class_group, get_offerings_by_course, scoped teacher student assignments, class group assignment filtering.
  - central_platform/rag/service.py: Updated publish_knowledge_asset to allow teachers to publish teacher-authored class notes and targeted remedial materials.
  - central_platform/api/schemas.py & central_platform/api/routes/teachers.py: Added endpoints for GET/POST classes, GET class students, POST class notes, POST remedial content, POST assignments, GET assignments, and upgraded POST instructions with hierarchical scoping and strict cross-tenant 403 Forbidden enforcement. Added intervention_alerts to TeacherDashboardResponse.
  - app/portals/teacher/controller.py: Real DB and CourseService/RAGService/SLRService integration for courses, classes, class notes, remedial content, assignments, and SLR progress review.
  - app/bridge/facade.py: Added slots get_teacher_classes, get_class_students, upload_class_note, upload_remedial_content, create_assignment with JSON parsing and error sanitization.
  - app/ui/teacher_portal.html: Added Classes navigation tab, dynamic course and class headers, view-classes UI, and modals (modalCreateClass, modalUploadClassNote, modalUploadRemedialContent, modalCreateAssignment).
  - tests/test_phase16_teacher_workflow_ui.py: 12 comprehensive unit and integration tests covering course/class scoping, class creation, honest empty rosters, unauthorized student selection rejection (403), class note RAG scoping, cross-class isolation, remedial content RAG scoping, cross-student isolation, hierarchical instructions, real assignments, controller workflows, and desktop bridge facade durability.
  - Regression results: 1,029/1,029 passed in 165.76s (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 1210a25 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 018: Phase 17 Completion Update
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 17 Student Multi-Course Workflow UI Complete`
- **Intended Labels:** `ui`, `student-portal`, `multi-course`, `course-selector`, `concurrency`, `P0`
- **Intended Comment:**
  ```text
  Phase 17 Student Multi-Course Workflow UI completed.

  Deliverables:
  - central_platform/db.py: get_assignments_for_student (scoped to course and student's class group), get_knowledge_sources_for_student (authorized published course, class, and student-targeted remedial sources), get_mastery_states convenience accessor.
  - central_platform/api/schemas.py & central_platform/api/routes/students.py: Endpoints for GET /api/v1/students/{id}/courses, GET /api/v1/students/{id}/courses/{course_id}/curriculum (with live student concept mastery overlay), GET /api/v1/students/{id}/courses/{course_id}/assignments, GET /api/v1/students/{id}/courses/{course_id}/knowledge, POST /api/v1/students/{id}/courses/switch (enforcing HTTP 409 Conflict safe turn cancellation invariant), GET /api/v1/students/{id}/courses/{course_id}/offline-status.
  - app/portals/student/controller.py: Real DB and CourseService/CurriculumService/RAGService/SLRService integration for enrolled courses listing, safe course switching, scoped curriculum navigation, scoped assignments, scoped knowledge sources, and offline indicators.
  - app/bridge/facade.py: Added PySide6 slots get_student_courses, switch_student_course (with active generation check), get_student_course_curriculum, get_student_course_assignments, get_student_course_knowledge, get_student_course_offline_status.
  - app/ui/student_dashboard.html: Dynamic course switcher dropdown (#courseSelector), live sync/cache status badge (#courseOfflineBadge), active course context metadata binding, and JavaScript handlers with active turn generation protection.
  - tests/test_phase17_student_multi_course_workflow_ui.py: 12 comprehensive unit and integration tests covering enrolled courses listing, context resolution, active context switching, concurrency guard (409 Conflict), unauthorized course rejection (403 Forbidden), scoped curriculum DAG navigation, scoped assignments isolation, class group boundaries, scoped knowledge notes, offline indicators, PySide6 bridge slots, and HTML controls.
  - Regression results: 1,041/1,041 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 8f65325 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 019: Phase 18 Completion & System-Wide Bug/Deadend Fixes
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 18 Teacher Instruction + RAG Integration & System-Wide Audit Complete`
- **Intended Labels:** `teacher-instructions`, `rag`, `provenance`, `audit`, `P0`
- **Intended Comment:**
  ```text
  Phase 18 Teacher Instruction + RAG Integration & System-Wide Audit completed.

  Deliverables:
  - central_platform/ai/context_builder.py: Implemented ProvenanceRecord dataclass, enhanced AssembledContext with applied_instruction_ids, contributed_source_ids, contributed_chunk_ids, provenance_records; integrated TeacherInstructionEngine with 5-tier precedence hierarchy (SESSION > STUDENT > CLASS > COURSE > ORGANIZATION), numerical priority tie-breaking, and timestamp recency resolution; integrated RAGService across textbook, class, and remedial scopes; strictly partitioned prompt blocks between behavioral directives and factual reference evidence.
  - central_platform/tutor/orchestrator.py: Replaced non-existent search_chunks() call with rag_service.query(); updated TutorTurnResult with complete provenance and applied instruction IDs.
  - central_platform/api/routes/tutor.py: Updated TutorTurnApiResponse to return applied instruction IDs, contributed chunk IDs, and provenance records.
  - central_platform/db.py: Updated get_rag_chunks_by_course() with fallback concept matching and dual version ID checking; added list_courses(), list_course_versions(), get_users_by_role(), and get_teacher_instructions_for_course().
  - central_platform/rag/service.py: Added concept and topic prefix-cleaning (cpt-, cpt_) for robust query matching.
  - Codebase-Wide Bug & Silent Fail Remediation:
    - Fixed silent tool policy fallback in central_platform/api/routes/tools.py due to missing list_course_versions.
    - Replaced silent except-pass blocks with structured warning and debug logging across users.py, sync.py, teachers.py, curricula.py, students.py, courses/service.py, curriculum/service.py, notifications/queue.py, sync/client.py, local_runtime (course_cache, rag_cache, session, engine), and UI controllers (student, parent, admin).
  - tests/test_phase18_teacher_instruction_rag_integration.py: 12 comprehensive unit and integration tests covering merged multi-tier context, provenance tracking, directives vs evidence separation, precedence cascade, priority tie-breaking, expiration, unauthorized note exclusion, graceful empty fallbacks, mixed scopes, version pinning, and REST API turn propagation.
  - Regression results: 1,053/1,053 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit a3885ec pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 020: Phase 19 Chemistry Adapter Extraction & Disablement Test
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 19 Chemistry Adapter Extraction & Disablement Test Complete`
- **Intended Labels:** `adapters`, `chemistry`, `modularity`, `architecture`, `P0`
- **Intended Comment:**
  ```text
  Phase 19 Chemistry Adapter Extraction & Disablement Test completed.

  Deliverables:
  - central_platform/adapters/chemistry/: Standalone package containing ChemistryDomainAdapter, integrating ChemistryToolAdapter (equation_balancer, formula_parser), ChemistryEquationEvaluator, ChemistryCurriculumAdapter, entity normalizer, and misconceptions catalog (MISC-BOND-BREAK, MISC-EQUIL-STATIC, etc.).
  - central_platform/tools/registry.py: Added unregister_adapter() and is_adapter_registered() methods for dynamic hot-swapping and clean capability index invalidation.
  - central_platform/tools/__init__.py: Updated get_configured_tool_registry() with include_chemistry toggle and dynamic adapter enablement checks.
  - central_platform/assessment/evaluators/registry.py: Added set_domain_evaluator_enabled() for dynamic domain evaluator registration/unregistration with graceful fallback to RubricEvaluator.
  - Platform Independence Proof: Verified generic tutor core, courses services, and AI layers have zero direct imports of the Chemistry adapter implementation. Math (calculator) and coding sandboxes execute with 100% fidelity when chemistry is disabled. Non-chemistry courses return False for can_handle_course.
  - tests/test_phase19_chemistry_adapter_extraction_disablement.py: 12 comprehensive unit and integration tests covering domain adapter contract, startup with chemistry disabled, tool registry omission, tool execution rejection, evaluator fallback, chemistry tool execution, equation evaluation, math/coding sandbox independence, cross-course isolation, concept keyword matcher isolation, dynamic runtime toggle, and env var configuration.
  - Regression results: 1,065/1,065 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 7e2c6dc pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 021: Phase 20 Legacy Removal & Dead-Code Cleanup
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 20 Legacy Removal & Dead-Code Cleanup Complete`
- **Intended Labels:** `cleanup`, `refactoring`, `dead-code`, `architecture`, `P0`
- **Intended Comment:**
  ```text
  Phase 20 Legacy Removal & Dead-Code Cleanup completed.

  Deliverables:
  - Physical Deletion of legacy/ Directory: Deleted legacy/agents/default_agents.py, legacy/agents/__init__.py, and legacy/__init__.py after reachability proofs demonstrated zero production or test references.
  - Core Configuration Cleanup: Removed dead enable_legacy_agents feature flag from core/config.py.
  - Scratch Directory Sanitization: Removed obsolete forensic analysis scripts, JSON dumps, and test SQLite databases from scratch/.
  - Architecture Guard Upgrade (tests/architecture/test_anti_legacy_imports.py): Added test_legacy_directory_eliminated() ensuring permanent absence of the legacy directory on disk.
  - Clean Module Imports & Startup: Verified core, central_platform, app, and local_runtime modules import cleanly without deprecation warnings or missing module errors. Full platform boot and /healthz, /readyz, /livez probes verified.
  - End-to-End Orchestrator Turn: Verified GenericTutorOrchestrator completes real tutoring turns with 100% fidelity without legacy code paths.
  - tests/test_phase20_legacy_removal_dead_code_cleanup.py: 12 comprehensive unit and integration tests covering legacy directory deletion, zero codebase-wide imports, dead config removal, scratch sanitization, clean imports across all layers, inference service decoupling, context builder independence, health probes, packaging hygiene, and end-to-end tutor orchestration.
  - Regression results: 1,078/1,078 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit fcb9720 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 022: Phase 21 Database & Migration Hardening
- **Target Branch:** `master`
- **Intended Issue Title:** `[Architecture] Phase 21 Database & Migration Hardening Complete`
- **Intended Labels:** `database`, `migrations`, `sqlite`, `postgresql`, `integrity`, `P0`
- **Intended Comment:**
  ```text
  Phase 21 Database & Migration Hardening completed.

  Deliverables:
  - Authoritative Table Manifest (docs/reports/DATABASE_SCHEMA_MANIFEST.md): Exhaustive catalog of all 50 tables across migrations 001-008. Verified 0 duplicate table definitions across all migration files.
  - Checksum Ledger & Tamper Detection: Upgraded scripts/migrate_db.py to record SHA-256 hashes in schema_migrations. Added verify_migration_checksums() and MigrationChecksumMismatchError rejecting modified migration scripts.
  - Migration Lifecycle & Idempotency: Verified clean migration on empty database, idempotent reruns (returning empty list), incremental step-by-step application, and symmetric reverse rollback (008 down to 001) with clean re-application.
  - Relational Integrity & Concurrency: Enforced foreign key constraints with PRAGMA foreign_keys = ON; verified rejection of orphan rows and uniqueness collisions; verified data preservation across migrations 001 through 008; verified thread-safe concurrent reads/writes without deadlocks.
  - Dual-Engine Compatibility: Documented SQLite as authoritative verified local engine and psycopg2 driver present with honest environment reporting (live PostgreSQL daemon marked unverified).
  - tests/test_phase21_database_migration_hardening.py: 12 comprehensive unit and integration tests covering all migration operations and database constraints.
  - Regression results: 1,090/1,090 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 6b86258 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 023: Phase 22 Security, Privacy & Isolation Audit
- **Target Branch:** `master`
- **Intended Issue Title:** `[Security] Phase 22 Security, Privacy & Isolation Audit Complete`
- **Intended Labels:** `security`, `rbac`, `isolation`, `privacy`, `audit`, `P0`
- **Intended Comment:**
  ```text
  Phase 22 Security, Privacy & Isolation Audit completed.

  Deliverables:
  - Privilege Escalation & Auth Fixes: Closed RBAC gaps across list_courses, course review-queue, and all RAG write endpoints.
  - Prompt Injection Guard: Added SecurityAuditor prompt screening in /tutor/turn.
  - Role Enum Resolution: Normalized UserRole enum comparisons between string and enum types.
  - tests/test_phase22_security_privacy_isolation_audit.py: 12 attack-style tests covering cross-tenant access, IDOR, privilege escalation, prompt injection, XSS/script injection, cross-tenant instructions, path traversal uploads, executable uploads, credential protection, PII masking, RAG boundary isolation, and sync replay idempotency.
  - Regression results: 1,102/1,102 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commit 585c6a3 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 024: Phase 23 Reliability, Failure Injection & Recovery
- **Target Branch:** `master`
- **Intended Issue Title:** `[Resilience] Phase 23 Reliability, Failure Injection & Recovery Complete`
- **Intended Labels:** `reliability`, `recovery`, `failure-injection`, `resilience`, `P0`
- **Intended Comment:**
  ```text
  Phase 23 Reliability, Failure Injection & Recovery completed.

  Deliverables:
  - Standardized Recovery Contracts (central_platform/recovery/manager.py): Classification, observable status, safe user message, technical diagnostic, retryability, and commit/rollback decisions across all failure categories.
  - Dedicated Failure Handlers: Missing model, corrupt model, provider timeout, provider malformed response, RAG unavailable, DB unavailable, broken migration, broken upload, interrupted publish, expired instruction, duplicate sync, and app crash mid-turn.
  - Resilient Orchestrator Turn Execution: Unhandled exceptions trigger clean state rollback (0 orphaned events) and safe pedagogical redirection without crashing sessions.
  - Silent-Fail Bug Fix (BUG-23A): Fixed AttributeError on inst.id in _is_temporally_valid, ensuring expired instructions are cleanly pruned from prompt hierarchy.
  - tests/test_phase23_reliability_failure_injection_recovery.py: 12 failure injection tests verifying all 6 resilience properties across 12 failure domains.
  - Regression results: 1,114/1,114 passed (100% green, 0 regressions).
  ```
- **Push Status:** `COMPLETED (commits 1a8bfd4, 4578abf pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`

### Item 025: Platform Documentation & Architectural Synchronization for Phase 23
- **Target Branch:** `master`
- **Intended Issue Title:** `[Docs] Comprehensive Update to System Architecture, Data Model, and Project State for Phase 23`
- **Intended Labels:** `documentation`, `architecture`, `data-model`, `state`
- **Intended Comment:**
  ```text
  Platform Documentation & Architectural Synchronization completed.

  Deliverables:
  - Root README.md overhaul: 1,114 passing tests badge, executive overview for incoming developers, complete system architecture diagram, technical invariants of the 16-step orchestrator, quickstart instructions, and phase-by-phase verification matrix.
  - docs/ARCHITECTURE.md: Updated to document the course-independent architecture, 16-step turn lifecycle, 12 failure handlers, 50-table schema, and local-first SLM router.
  - docs/DATA_MODEL.md: Comprehensive documentation of all 50 tables across migrations 001-008, schema versioning with SHA-256 validation, and canonical dataclasses.
  - docs/SECURITY_MODEL.md: Cleaned formatting, 6-role RBAC matrix, Phase 22 security audit hardening, and local device quarantine.
  - docs/PROJECT_STATE.md: Complete snapshot of verified invariant metrics, bug defect register, and Phase 24 roadmap.
  ```
- **Push Status:** `COMPLETED (commit f22c474 pushed to origin/master)`
- **Issue Operations Status:** `QUEUED`


