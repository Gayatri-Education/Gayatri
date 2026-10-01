# Architecture Target Specification — Gayatri Course-Independent Platform

**Document:** `docs/ARCHITECTURE_TARGET.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** FROZEN (Phase 1 Deliverable)  
**Governing Plan:** `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## 1. Executive Architectural Vision

Gayatri is transformed from a Chemistry-centric tutoring system into a **course-independent, multi-organization learning and tutoring platform**. The platform supports:
1. **Arbitrary academic subjects** (Physics, Mathematics, History, Programming, Chemistry, etc.) driven entirely by data-driven course packages, without altering generic Python code.
2. **Multi-tenant organization isolation** with public courses (cross-organization discoverable) and private courses (strictly bounded to owning organizations).
3. **Immutable course versioning** and a strict content approval pipeline (Upload $\rightarrow$ Parse $\rightarrow$ Chunk $\rightarrow$ Review $\rightarrow$ Admin Approve $\rightarrow$ Publish).
4. **Course-scoped student learning state** allowing students to enroll in multiple independent courses concurrently without mastery state cross-contamination.
5. **Hierarchical teacher instructions** resolved deterministically (Organization $\rightarrow$ Course $\rightarrow$ Class $\rightarrow$ Student $\rightarrow$ Session).
6. **Dual Online and Offline operation** sharing identical business logic, backed by PostgreSQL/Cloud online and SQLite/Local-SLM offline, synchronized idempotently via an event outbox.
7. **Clean adapter boundary** isolating Chemistry-specific tools, evaluators, and misconceptions into `adapters/chemistry/`, completely decoupling generic core runtime.

---

## 2. High-Level System Architecture

```text
                           GAYATRI PLATFORM
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
           ONLINE MODE                       OFFLINE MODE
                 │                                 │
        Web/Desktop Clients                   Desktop App
                 │                                 │
           FastAPI Server                    Local Services
                 │                                 │
            Auth & RBAC                       Local RBAC
                 │                                 │
            PostgreSQL                           SQLite
                 │                                 │
        Object/RAG Storage                  Local Course Cache
                 │                                 │
            AI Gateway                         AI Gateway
                 │                                 │
                 └────────────────┬────────────────┘
                                  │
                         GENERIC TUTOR CORE
                                  │
        ┌───────────────┬─────────┴┬───────────┬──────────────┐
        │               │          │           │              │
     Course         Curriculum  Learning   Assessment   Instructions
     Engine          Engine      Engine     Engine       Engine
        │               │          │           │              │
        └───────────────┴──────────┼───────────┴──────────────┘
                                   │
                         Tool / Adapter Layer
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
          Chemistry               Math             Programming
          (Adapter)            (Adapter)            (Adapter)
```

---

## 3. Subsystem Breakdown & Boundaries

### 3.1 Course Engine (`central_platform/courses/`)
- Manages `Course`, `CourseVersion`, and `CourseOffering`.
- Enforces visibility policies: `PUBLIC` vs `PRIVATE`.
- Enforces course content lifecycle states: `DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `PUBLISHED`, `ARCHIVED`, `FAILED`.
- Enforces course-level tool policy and tutor policy.

### 3.2 Generic Curriculum Engine (`core/curriculum/`, `central_platform/curriculum/`)
- Pure data-driven hierarchy: `CourseVersion` $\rightarrow$ `Subject` $\rightarrow$ `Module` $\rightarrow$ `Topic` $\rightarrow$ `Concept` $\rightarrow$ `Prerequisites`.
- Directed Acyclic Graph (DAG) validation, cycle detection, and topological prerequisite ordering.
- Namespaced deterministic concept IDs: `course:<course_id>:version:<version_id>:concept:<stable_key>`.
- Prohibits all subject-specific keyword matching in generic core code.

### 3.3 Course-Scoped Learning Engine (`central_platform/learning/`)
- Learning state is strictly composite: `(student_id, course_id, course_version_id, concept_id)`.
- **Mastery Engine:** Evidence-backed multi-factor mastery calculation (recency, recall streak, hint penalty, forgetting decay). Neural models NEVER directly set mastery.
- **Next Action Engine:** Pedagogical state machine determining next step (`CONTINUE`, `EXPLAIN`, `HINT`, `REMEDIATE`, `PRACTICE`, `REVIEW`, `ASSESS`, `CHALLENGE`, `ADVANCE`).
- **Learning Event Store:** Append-only event store recording student interaction evidence.

### 3.4 Scoped Content Ingestion & RAG Subsystem (`central_platform/rag/`)
- Document parsers (`PDF`, `DOCX`, `TXT`, `MD`), cleaning, and chunking with rich security metadata.
- Pre-retrieval authorization filter: Verifies student enrollment, course version, class membership, remedial assignment, and publication status before executing vector/lexical retrieval.
- Unauthorized chunks are filtered at retrieval time; never filtered in UI.

### 3.5 Hierarchical Instructions Engine (`central_platform/instructions/`)
- Resolves applicable teacher instructions deterministically:
  $$\text{System Policy} \succ \text{Org Directive} \succ \text{Course Directive} \succ \text{Class Directive} \succ \text{Student Remediation} \succ \text{Session Directive}$$
- Filters expired, inactive, or unauthorized teacher instructions before AI context construction.
- Strict prompt injection barrier: Teacher instructions are directives; uploaded documents are knowledge; system safety policy is authoritative.

### 3.6 Generic AI Gateway (`central_platform/ai/`)
- Provides unified AI provider interface (`Local llama.cpp`, `OpenAI-Compatible`, `Anthropic`, `Gemini`).
- Manifest-driven model registry (`central_platform/ai/models.py`) with explicit capability flags.
- **Zero Legacy Dependency:** Completely replaces `legacy.agents.default_agents`. No production module may import `legacy`.
- Handles timeouts, fallbacks, token usage telemetry, and cancellation tokens.

### 3.7 Assessment & Evaluation Abstraction (`central_platform/assessment/`)
- Deterministic evaluators: Multiple Choice (`MCQEvaluator`), Numerical with tolerance/units (`NumericalEvaluator`), Rubric (`RubricEvaluator`).
- Returns `EvaluationResult` with structured evidence (`CORRECT`, `PARTIAL`, `INCORRECT`, `UNCERTAIN`).
- Evaluation failure returns `UNCERTAIN` and prevents accidental mastery advancement.

### 3.8 Online & Offline Synchronization Subsystem (`central_platform/sync/`)
- **Offline Outbox Pattern:** Local operations record append-only learning events in `sync_outbox`.
- **Idempotency:** Server verifies `event_id` and `operation_id` to prevent duplicate state commits.
- **Conflict Resolution:** Events are append-only. Derived student mastery is deterministically recomputed from merged events.

### 3.9 Chemistry Domain Adapter (`adapters/chemistry/`)
- Encapsulates equation balancers, stoichiometry calculators, periodic table tools, chemistry misconception catalogs, and domain evaluators.
- Platform boots, initializes courses, and serves non-chemistry subjects even if `adapters/chemistry/` is absent or uninstalled.

---

## 4. Contract Specifications Between Boundaries

| Boundary | Request Contract | Response Contract | Failure / Error Policy |
|---|---|---|---|
| **UI $\rightarrow$ API** | REST / JSON with JWT Bearer Token & explicit `course_id` | Standardized JSON payload with status & data | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| **API $\rightarrow$ Application Service** | Strongly typed Pydantic request models | Strongly typed domain entities / DTOs | Explicit typed domain exceptions (`AuthorizationError`, `NotFoundError`) |
| **Service $\rightarrow$ Repository / DB** | Domain models & parameterized queries with tenant & course scoping | Domain entities or mapped tuples | Transaction rollback on error; connection retry on lock |
| **Service $\rightarrow$ RAG Retriever** | `RetrievalQuery(student_id, org_id, course_id, version_id, class_id, query_text)` | List of authorized `RAGChunk` with provenance & confidence | RAG failure returns empty results with error log; never crashes tutor turn |
| **Service $\rightarrow$ AI Gateway** | `AIExecutionRequest(messages, model, tools, max_tokens, temperature)` | `AIExecutionResult(content, token_usage, latency_ms, success)` | Provider error triggers configured fallback; returns structured failure on exhaustion |
| **Tutor $\rightarrow$ Learning State** | Staged `LearningEvent` and `AssessmentEvidence` | Updated `MasteryState` and persisted event record | Two-phase commit: State commits ONLY if response validator succeeds |
| **Offline App $\rightarrow$ Sync API** | Batch `SyncPayload(device_id, outbox_events, last_synced_timestamp)` | `SyncResponse(acknowledged_event_ids, server_state_updates)` | Network failure keeps outbox records intact for exponential backoff retry |

---

## 5. Architectural Invariants (Non-Negotiable)

1. **Course Genericity:** Generic core modules (`core/`, `central_platform/`) MUST NOT import or reference Chemistry keywords, files, or concepts.
2. **Zero Legacy Runtime:** Active production runtime MUST NOT import from `legacy/`.
3. **Zero Magic Defaults:** Silent creation or assumption of student IDs (`local_user_1`), course IDs (`crs-chem-101`), or organization IDs is prohibited. Missing context must result in explicit rejection.
4. **Honest Empty States:** Absence of data in courses, classes, or student progress MUST render clear, honest empty states. Injecting mock data into production paths is prohibited.
5. **Deterministic Schema Evolution:** Schema changes MUST occur strictly through versioned migration scripts in `migrations/`. Runtime `ALTER TABLE` execution is prohibited.
6. **Pre-Retrieval Authorization:** Unauthorized course content or teacher notes MUST NOT be returned from RAG queries under any circumstances.
