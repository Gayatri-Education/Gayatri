# System Architecture Specification — Gayatri AI Platform

## 1. High-Level Architecture Overview

The **Gayatri AI Platform** is an enterprise-grade, course-independent, offline-capable adaptive education system. The platform follows a clean layered, local-first hybrid architecture designed for extreme reliability, zero silent failures, strict multi-tenant data isolation, and dynamic persona-based user interfaces.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PRESENTATION LAYER                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  Student Portal  │  │  Teacher Portal  │  │  Parent Portal   │  │  Fee Admin UI  │  │
│  │ (Learner Hub)    │  │ (Class & Copilot)│  │ (Privacy & Feed) │  │ (Billing/Pay)  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           └─────────────────────┼─────────────────────┴────────────────────┘           │
│                                 ▼                                                      │
│                     Unified Application Shell Controller                               │
└─────────────────────────────────┬──────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼──────────────────────────────────────────────────────┐
│                               API & RUNTIME BOUNDARY                                   │
│  ┌──────────────────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │   Online REST API Server (FastAPI /api/v1)   │  │  Offline Local Runtime Engine  │  │
│  │   (16 Modular Routers + Health Probes)       │  │  (Local Cache, Quarantine)     │  │
│  └──────────────────────┬───────────────────────┘  └───────────────┬────────────────┘  │
│                         └───────────────────────┬──────────────────┘                   │
│                                                 ▼                                      │
│                                  GenericTutorOrchestrator                              │
│                                  (16-Step Turn Lifecycle)                              │
└─────────────────────────────────────────────────┬──────────────────────────────────────┘
                                                  │
┌─────────────────────────────────────────────────▼──────────────────────────────────────┐
│                                  AI & PEDAGOGICAL LAYER                                │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ Local-First AI Router │  │ Course Scoped RAG        │  │ Generic Course Tool      │  │
│  │ (llama.cpp / Cloud)   │  │ (Hybrid Vector + BM25)   │  │ Registry & Adapters      │  │
│  └───────────┬───────────┘  └────────────┬────────────┘  └────────────┬─────────────┘  │
│              │                           │                            │                │
│  ┌───────────▼───────────┐  ┌────────────▼────────────┐  ┌────────────▼─────────────┐  │
│  │ 5-Tier Teacher        │  │ Context Builder &       │  │ Capability Assessment &  │  │
│  │ Instruction Cascade   │  │ Token Budget Engine     │  │ Evaluator Registry       │  │
│  └───────────────────────┘  └─────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────┬──────────────────────────────────────┘
                                                  │
┌─────────────────────────────────────────────────▼──────────────────────────────────────┐
│                              LEARNING ENGINE & STATE LAYER                             │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ Learning Graph (DAG)  │  │ Evidence Mastery Engine │  │ Next Action Engine       │  │
│  └───────────┬───────────┘  └────────────┬────────────┘  └────────────┬─────────────┘  │
│              ▼                           ▼                            ▼                │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ Learning Event Store  │  │ Two-Phase State Staging │  │ Atomic Commit Pipeline   │  │
│  │ (Append-Only Log)     │  │ (Scratchpad Isolation)  │  │ & Rollback Hook          │  │
│  └───────────────────────┘  └─────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────┬──────────────────────────────────────┘
                                                  │
┌─────────────────────────────────────────────────▼──────────────────────────────────────┐
│                            DATA, SYNC & RESILIENCE LAYER                               │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ Platform Database     │  │ Bi-Directional Sync     │  │ Failure Recovery Manager │  │
│  │ (50 Relational Tables)│  │ (Outbox + Idempotency)  │  │ (6-Property Contract)    │  │
│  └───────────┬───────────┘  └────────────┬────────────┘  └────────────┬─────────────┘  │
│              ▼                           ▼                            ▼                │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ Migration Ledger      │  │ Multi-Tenant Isolation  │  │ Parent Privacy Engine    │  │
│  │ (Migrations 001-008)  │  │ & RBAC Enforcement      │  │ (4 Policy Levels)        │  │
│  └───────────────────────┘  └─────────────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Invariants & Principles

1. **Course-Independence**:
   - Zero curriculum, domain, or subject knowledge is hardcoded into the core learning engine, database, API routers, or orchestrator.
   - Any syllabus (e.g. NCERT Science, Grade 10 Math, Organic Chemistry, Python Coding, Corporate Compliance) is ingested as a generic `Course` with versioned DAG nodes (`GenericCurriculum`).
   - Domain-specific tools (calculators, chemical balance checkers, code sandboxes) register dynamically with the `ToolRegistry` and `EvaluatorRegistry`.

2. **16-Step Transactional Turn Lifecycle**:
   - Every student-tutor interaction follows a strict 16-step pipeline in `GenericTutorOrchestrator`.
   - In-memory state mutation is staged in a scratchpad and committed atomically to the persistent database ONLY upon pedagogical validation success.
   - Any crash or unhandled exception mid-turn triggers an immediate rollback hook, guaranteeing zero orphaned state mutations or dangling events.

3. **Local-First & Capability-Based Fallback**:
   - Primary AI inference runs locally using an ultra-lean GGUF quantized model (`Qwen2.5-0.5B-Instruct` via `llama.cpp`).
   - Strategy-driven routing (`LOCAL_ONLY`, `LOCAL_FIRST`, `CLOUD_PREFERRED`) seamlessly falls back to cloud providers (OpenAI, Anthropic, Gemini, OpenRouter) if local resources are unavailable or if cloud-level capabilities are requested.

4. **Deterministic Evidence-Backed Pedagogy**:
   - Neural output is never permitted to directly mutate student mastery state or decide learning steps without validation.
   - All learning state transitions are driven by deterministic algorithms evaluating student interaction events (attempt accuracy, hint penalties, time decay, prerequisite graphs).

5. **Multi-Tenant Isolation & Privacy Fail-Closed**:
   - Data scoping enforces zero cross-tenant data leakage. Cross-organization requests return `403 Forbidden`.
   - Parent visibility is governed by explicit privacy policies (`FULL_TRANSPARENCY`, `SUMMARY_ONLY`, `RESTRICTED`, `BLOCKED`) managed by institution policies and student settings.
   - Student prompts are scanned for prompt injection attacks and blocked before reaching any inference engine.

6. **Observable Resilience (Zero Silent Fails)**:
   - All platform exceptions are captured and standardized through the `FailureRecoveryManager`.
   - Every recovery handler yields a standardized `RecoveryResult` with 6 mandatory fields (`failure_category`, `status`, `user_message`, `technical_diagnostic`, `retryable`, and `commit_decision`), preventing swallowed exceptions from corrupting state.

---

## 3. The 16-Step Generic Turn Execution Lifecycle

When a student submits an interaction (chat turn, quiz response, or exercise) via `/api/v1/tutor/turn` or the desktop UI, the `GenericTutorOrchestrator.execute_turn()` executes the following 16 steps:

| Step | Operation | Component | Technical Detail |
|---|---|---|---|
| **1** | **Enrollment Authorization** | `CourseService` | Validates that `student_id` is actively enrolled in the targeted `course_offering_id` and that the offering is currently active. |
| **2** | **Scoped State Retrieval** | `LearningStateEngine` | Loads `CanonicalLearningState` scoped strictly to `(student_id, course_id)`. Prevents cross-course state pollution. |
| **3** | **Query Understanding** | `QueryUnderstandingEngine` | Extracts student intent (`CONCEPT_EXPLORATION`, `EXERCISE_HELP`, `CONFUSION`, etc.) and identified concepts. |
| **4** | **Prompt Injection Guard** | `SecurityAuditor` | Scans input for prompt injection, jailbreaking, and system prompt override attempts. Returns pedagogical redirection if flagged. |
| **5** | **Instruction Cascade** | `TeacherInstructionEngine` | Resolves active 5-tier teacher instructions (`SESSION` > `STUDENT` > `CLASS` > `COURSE` > `ORGANIZATION`) with temporal expiration checks. |
| **6** | **Scoped RAG Retrieval** | `RAGService` | Executes hybrid retrieval (semantic embeddings + BM25) strictly filtered by `course_id` and pinned `course_version_id`. |
| **7** | **Tool Capability Resolution** | `ToolRegistry` | Queries `CourseToolPolicy` to identify tools authorized for this course offering and current concept node. |
| **8** | **Context Assembly** | `ContextBuilder` | Assembles a token-budgeted 7-layer context (Persona, Learner State, RAG Evidence, Teacher Directives, Misconceptions, Recent Events, Tools). |
| **9** | **Pedagogical Scaffolding** | `NextActionEngine` | Computes the target pedagogical action (`HINT`, `EXPLAIN`, `PRACTICE`, `REMEDIATE`, etc.) to guide model instruction. |
| **10** | **Model Inference** | `AIGateway` | Dispatches the assembled prompt to the model router (`LOCAL_FIRST`, fallback to cloud adapter). |
| **11** | **Tool Execution Engine** | `ToolExecutionEngine` | If model requests a tool call (e.g. calculation, formula validation), executes the tool in a sandboxed environment. |
| **12** | **Pedagogical Validation** | `ResponseValidatorEngine` | Validates candidate response against 7 educational invariants (factual fidelity, curriculum scope, age appropriateness, tone). |
| **13** | **Anti-Answer Leakage** | `AntiLeakageGuard` | Verifies that the tutor response does not reveal direct answers to uncompleted exercises or assessment questions. |
| **14** | **Mastery Calculation** | `MasteryEngine` | Calculates state delta (mastery updates, concept stability, review schedule) using deterministic evidence algorithms. |
| **15** | **Two-Phase State Commit** | `StateCommitPipeline` | Commits staged state delta to `PlatformDatabase` ONLY if step 12 & 13 pass. On failure, triggers atomic rollback. |
| **16** | **Event Store Logging** | `LearningEventStore` | Appends immutable learning event to `learning_events` table with telemetry and performance profile. |

---

## 4. Subsystem Breakdown

### 4.1 Central Course Service & Management (`central_platform/courses/`)
- **`Course`**: Root course entity containing metadata, subject, institution ID, and visibility (`PUBLIC` or `PRIVATE`).
- **`CourseVersion`**: Immutable snapshot of curriculum structure and content. Follows lifecycle `DRAFT` → `IN_REVIEW` → `APPROVED` → `PUBLISHED` → `ARCHIVED`.
- **`CourseOffering`**: Specific delivery instance of a published course version, linked to academic terms, classes, and teachers.
- **`CourseEnrollment`**: Student enrollment record binding a learner to a specific offering.
- **Workflow Controllers**: `CourseService` enforces upload, submission, administrative approval, and version-pinned activation.

### 4.2 Local-First AI Gateway & Model Router (`central_platform/ai/`)
- **Local Model Runner (`llama_cpp_runner.py`)**: Direct binding to `llama.cpp` executing 4-bit quantized GGUF models on CPU with low memory footprint (~500MB RAM for 0.5B model).
- **Cloud Adapters (`adapters/`)**: Fully abstracted, standardized adapters for **OpenAI** (`gpt-4o-mini`), **Anthropic** (`claude-3-haiku`), **Gemini** (`gemini-1.5-flash`), and **OpenRouter**.
- **Model Router (`gateway.py`)**: Routing engine respecting strategy preferences (`LOCAL_ONLY`, `LOCAL_FIRST`, `CLOUD_PREFERRED`), handling automatic fallback on local timeouts or memory constraints.
- **Context Builder (`context_builder.py`)**: Layered context management respecting token budgets, trimming conversation history, and injecting RAG and pedagogical instructions.

### 4.3 Scoped RAG & Knowledge Pipeline (`central_platform/rag/`)
- **Knowledge Ingestion (`service.py`)**: Chunks documents into semantically coherent blocks enriched with `course_id`, `course_version_id`, module, and concept IDs.
- **Hybrid Retrieval**: Integrates dense vector embeddings for semantic search with BM25 lexical ranking for formula, keyword, and symbol precision.
- **Remedial & Class Scoping**: Queries can be scoped to specific class groups or remedial tracks.
- **Plug-and-Play Management**: REST endpoints for adding sources, triggering asynchronous chunking, rebuilding indices, and removing outdated source files.

### 4.4 5-Tier Scoped Teacher Instruction Hierarchy (`central_platform/teacher/instruction.py`)
Provides deterministic steering of AI tutor behavior:
1. **SESSION** (Highest Priority): Ephemeral instructions active only for the current student turn or session.
2. **STUDENT**: Direct individualized pedagogical accommodations (e.g. "Use visual analogies for fractions").
3. **CLASS**: Directives applied to all students in a specific section or class group.
4. **COURSE**: General guidelines applicable across the entire course offering.
5. **ORGANIZATION** (Lowest Priority): Institutional policy rules (e.g. "Do not discuss external politics").

- **Cascade Engine**: Merges active directives with strict precedence. A higher-tier instruction always overrides a lower-tier instruction in case of conflicting keys.
- **Temporal Windowing**: Directives support `valid_from` and `valid_until` timestamps. Expired instructions are pruned automatically.

### 4.5 Generic Course Tool Registry & Adapters (`central_platform/tools/`)
- **Dynamic Tool Registry (`registry.py`)**: Decouples subject tools from the core platform. Tools declare their name, description, JSON argument schema, and required permissions.
- **Tool Execution Engine (`engine.py`)**: Sandboxes tool execution with configurable timeouts and resource limits.
- **Domain Adapters (`adapters/`)**:
  - `ChemistryDomainAdapter`: Molecular mass computation, formula balancing, and reaction validation.
  - `MathDomainAdapter`: Safe AST expression evaluation and LaTeX formula verification.
  - `CodingDomainAdapter`: Isolated Python execution sandbox for coding exercises.
- **Runtime Policy Inspection**: Tools are dynamically enabled or disabled per course offering via `CourseToolPolicy`.

### 4.6 Capability-Driven Assessment & Evaluation Engine (`central_platform/assessment/`)
- **Evaluator Registry (`evaluators.py`)**: Maps assessment item capability tags (`deterministic`, `rubric`, `code`, `math`) to specialized evaluators.
- **Deterministic Evaluator**: Handles exact matches, multiple choice, numerical tolerances, and regex patterns.
- **Rubric Evaluator**: LLM-assisted multi-criteria scoring against defined scoring bands with evidence extraction.
- **Anti-Leakage Guard**: Sanitizes assessment questions before presentation, guaranteeing that answer keys and explanations are never leaked in client-facing payloads.
- **Teacher Review Queue**: Open-ended student submissions are automatically flagged and routed to the teacher portal when rubric confidence is low.

### 4.7 Learning Engine, Canonical State & DAG (`central_platform/learning/`)
- **Canonical Learning State (`state.py`)**: Unified student profile tracking multi-course concept mastery levels, active misconceptions, spaced review schedules, and engagement metrics.
- **Learning Graph DAG (`graph.py`)**: Directed Acyclic Graph modeling concept prerequisites. Detects circular dependencies and calculates unlockable frontier concepts.
- **Evidence Mastery Engine (`mastery.py`)**: Multi-factor Bayesian-inspired mastery computation:
  - Base accuracy from recent attempts.
  - Penalties for hints requested and attempts exhausted.
  - Ebbinghaus forgetting curve time decay.
  - Prerequisite mastery propagation.
- **State Commit Pipeline (`pipeline.py`)**: Staged two-phase state mutations preventing partial or corrupted state saves.

### 4.8 Online API Gateway & Modular Routers (`central_platform/api/`)
- **FastAPI Framework**: High-performance asynchronous API server exposing 16 modular sub-routers:
  - `/api/v1/auth`: JWT authentication, token refresh, and identity management.
  - `/api/v1/courses`: Course creation, versioning, offerings, and enrollments.
  - `/api/v1/tutor`: 16-step orchestrator turn execution (`/turn`) and session management.
  - `/api/v1/rag`: Knowledge ingestion, indexing, and scoped search.
  - `/api/v1/assessment`: Assessment delivery, submission evaluation, and review queue.
  - `/api/v1/teacher`: Instruction cascade authoring and class roster management.
  - `/api/v1/student`: Multi-course learning records, review queues, and mastery.
  - `/api/v1/admin`: Institutional administration and course version approvals.
  - `/api/v1/tools`: Dynamic tool registration and policy inspection.
  - `/api/v1/sync`: Bi-directional outbox sync and conflict resolution.
  - `/api/v1/fees`: Billing structures, invoice generation, and student accounts.
  - `/api/v1/payments`: Payment gateway interactions, webhook processing, receipts.
  - `/api/v1/privacy`: Parent visibility settings and policy management.
  - `/api/v1/analytics`: Class health metrics, mastery distribution, learning trends.
  - `/api/v1/recovery`: Failure recovery diagnostics and health checks.
  - `/api/v1/models`: AI model registry and gateway routing status.
- **Health Probes**: `/healthz` (liveness), `/readyz` (database & model readiness), `/livez` (system uptime & diagnostics).

### 4.9 Offline Local Runtime & Bi-Directional Sync (`central_platform/local_runtime/` & `sync/`)
- **Local Course Cache**: On-device SQLite cache holding published course versions and curriculum DAGs.
- **Integrity Quarantine**: Every cached file is verified against its authoritative SHA-256 hash. Tampered files are immediately quarantined into `.quarantine/`.
- **Local Sync Outbox (`outbox.py`)**: All offline student interactions and learning events are queued locally in `LocalSyncOutbox` with monotonically increasing sequence IDs.
- **Sync Service (`service.py`)**: When connectivity is restored, the client posts its outbox batch to `/api/v1/sync/batch`. Operations are replayed idempotently, resolving conflicts using client-server timestamp reconciliation and state hashing.

### 4.10 Database & Immutable Migration Ledger (`migrations/` & `central_platform/db.py`)
- **50 Relational Tables**: Full authoritative schema across identity, courses, knowledge chunks, learning events, fees, and sync receipts.
- **Migration Ledger**: Migrations `001` through `008` execute sequentially. Each migration script defines both forward `UP` and rollback `DOWN` logic:
  - `001_initial_schema.sql`: Core users, institutions, curricula.
  - `002_learning_events_and_state.sql`: Canonical state and learning event store.
  - `003_fee_management_schema.sql`: Invoicing, payments, receipts, discounts.
  - `004_course_independent_schema.sql`: Courses, versions, offerings, enrollments.
  - `005_classes_and_remedial_schema.sql`: Class groupings and remedial assignments.
  - `006_teacher_instructions_schema.sql`: 5-tier instruction cascade records.
  - `007_assessment_and_rubrics.sql`: Capability evaluators and rubric definitions.
  - `008_sync_operations_schema.sql`: Sync receipts, device registrations, idempotency log.

### 4.11 Multi-Persona Portals & UI Shell (`app/ui/` & `central_platform/portals/`)
- **Unified Design System**: Central theme tokens supporting dark mode (default) and light mode.
- **Application Shell**: Responsive sidebar navigation, notifications, account switcher, and 8-language localization (English, Hindi, Sanskrit, Tamil, Telugu, Kannada, Marathi, Bengali).
- **Student Portal**: Interactive curriculum tree, learning graph visualization, spaced repetition flashcards, assignment tracker, and real-time chat tutor.
- **Teacher Portal**: Class roster, at-risk student detection (`EXCELLENT`, `GOOD`, `NEEDS_ATTENTION`, `AT_RISK`), instruction composer, and AI teaching assistant.
- **Parent Portal**: Multi-child progress dashboard, attendance records, recommendation feed, and fee payment histories.
- **Fee Admin UI**: Fee schedule authoring, monthly batch billing generator, receipt printer, and exportable financial reports.

---

## 5. Security, RBAC & Multi-Tenant Isolation

1. **Role-Based Access Control (RBAC)**:
   - Built-in role hierarchy: `SUPER_ADMIN` > `ORG_ADMIN` > `TEACHER` > `STUDENT` > `PARENT` > `GUEST`.
   - Strict privilege boundaries: Students cannot invoke authoring or RAG ingestion endpoints; Teachers cannot publish courses without Admin review; Parents can only view records of their linked children.

2. **Tenant Isolation**:
   - Every database query in multi-tenant contexts requires `tenant_id` filtering.
   - Cross-tenant access attempts return `403 Forbidden` and trigger a security audit log.

3. **Prompt Injection Defense**:
   - Incoming student queries are evaluated by `SecurityAuditor.sanitize_prompt()`.
   - Pattern scanning detects system prompt leaks, roleplay bypasses, and instruction injection.
   - Flagged inputs are stopped before reaching the AI model, and the student receives a gentle pedagogical redirection.

4. **Parent Privacy Model**:
   - Parent data visibility is filtered through `ParentPrivacyEngine` with four discrete policy levels:
     - `FULL_TRANSPARENCY`: Complete access to all session logs, attempts, and chat transcripts.
     - `SUMMARY_ONLY`: High-level aggregate mastery percentages and attendance.
     - `RESTRICTED`: High-level summaries only, with sensitive conversational logs redacted.
     - `BLOCKED`: All parent data access temporarily disabled (e.g. pending dispute).

---

## 6. Reliability, Failure Injection & Recovery Model

The platform enforces a zero-silent-failure architecture. All potential failure points are handled by `FailureRecoveryManager` (`central_platform/recovery/manager.py`), returning a standardized `RecoveryResult`:

```python
@dataclass
class RecoveryResult:
    failure_category: str       # e.g., "MODEL_TIMEOUT", "RAG_UNAVAILABLE"
    status: RecoveryStatus      # FAILED, DEGRADED, RECOVERED
    user_message: str          # Safe, pedagogical user-facing message
    technical_diagnostic: str  # Actionable debug logging for engineers
    retryable: bool             # Whether the client should retry the operation
    commit_decision: CommitDecision # COMMIT, ROLLBACK, NOOP, RETRY
```

### The 12 Concrete Failure Handlers

1. **Missing Model (`handle_missing_model`)**: Triggers automatic fallback to the next available provider in strategy chain.
2. **Corrupt Model (`handle_corrupt_model`)**: Quarantines model file and routes requests to cloud fallback.
3. **Provider Timeout (`handle_provider_timeout`)**: Returns degraded offline fallback response without crashing.
4. **Provider Malformed Response (`handle_provider_malformed_response`)**: Invokes self-healing JSON repair parser.
5. **RAG Retrieval Failure (`handle_rag_failure`)**: Falls back to course curriculum syllabus nodes and basic prompts.
6. **Database Offline (`handle_database_offline`)**: Switches local runtime into in-memory queue mode.
7. **Broken Migration (`handle_broken_migration`)**: Halts startup and executes rollback to last verified schema checksum.
8. **Broken Content Upload (`handle_broken_upload`)**: Rejects corrupted uploads, cleans temporary staging artifacts.
9. **Interrupted Version Publish (`handle_interrupted_publish`)**: Transactional rollback preserves `DRAFT` status.
10. **Expired Instruction (`handle_expired_instruction`)**: Silently prunes expired directives without throwing exceptions.
11. **Duplicate Sync Request (`handle_duplicate_sync`)**: Returns cached receipt with idempotency acknowledgement.
12. **Mid-Turn Application Crash (`handle_mid_turn_crash`)**: Restores previous `CanonicalLearningState` with zero orphaned events.

---

## 7. Testing & Quality Strategy

The platform maintains 100% green test execution across 1,114 automated tests:

- **Unit & Component Tests**: Covering every individual module, data structure, and utility function.
- **Integration Tests**: Testing interactions across database, API routes, orchestrator, and RAG pipelines.
- **Failure Injection Tests (`test_phase23_reliability_failure_injection_recovery.py`)**: 12 dedicated tests asserting that all 12 failure modes fail safely and execute correct `CommitDecision` directives.
- **Security & Privacy Audits (`test_phase22_security_privacy_isolation_audit.py`)**: 12 penetration-style attack tests verifying RBAC boundaries and prompt injection defenses.
- **Regression Master**: Continuous verification ensuring zero regressions across all 23 development phases.
