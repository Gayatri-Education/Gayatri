# Gayatri AI Platform — Current State Architecture & Reconciliation Inventory
## Phase 00 Authoritative Architecture & Inventory Baseline

---

## 1. System Overview & Context

Gayatri is a three-sided adaptive AI learning platform supporting **Students**, **Teachers**, and **Administrators**.
The platform operates as a dual-tier system:
1. **Student Desktop Application**: PySide6 + QWebEngine application with local adaptive learning intelligence, Bayesian Knowledge Tracing (BKT), Learning Dependency Graph (LDG) navigation, chemistry calculation tools, hybrid RAG retrieval over NCERT chemistry datasets, and local/remote LLM inference.
2. **Central Platform & Teacher Portal**: FastAPI/HTTP server architecture (`server.py` and `central_platform/`) providing teacher monitoring, cohort mastery analytics, directive injection, student telemetry synchronization, and administrative governance.

---

## 2. Directory Inventory (Task 1)

| Directory | Purpose | Primary Modules / Contents | Status Classification |
|---|---|---|---|
| `app/` | Student desktop app UI, PySide6 window management, WebChannel bridge | `main.py`, `bridge/facade.py`, `bridge/chat.py`, `ui/index.html` | `ACTIVE` |
| `central_platform/` | Central platform server, databases, service prototypes, teacher/admin logic | `server.py`, `db.py`, `teacher/`, `slr/`, `sync/`, `rbac/`, `ai_governance/` | `PROTOTYPE` / `INTEGRATION_PENDING` |
| `core/` | Core tutoring algorithms, BKT, LDG, assessment engine, RAG stores, chemistry runtime | `tutor/adaptive.py`, `runtimes/chemistry.py`, `rag/`, `assessment/`, `security/` | `ACTIVE` |
| `data/` | Knowledge bases, NCERT chemistry datasets, curriculum graphs | `data/rag/`, `data/curriculum/chemistry/` | `ACTIVE` |
| `docs/` | Authoritative documentation, architecture specifications, implementation tracking | `docs/implementation/`, `docs/architecture/`, `docs/evaluation/` | `ACTIVE` |
| `hooks/` | PyInstaller runtime hooks for llama.cpp packaging | `hook-llama_cpp.py`, `rthook-llama_cpp.py` | `ACTIVE` |
| `legacy/` | Deprecated initial agent prototypes | `legacy/agents/default_agents.py` | `LEGACY` |
| `packaging/` | Installer scripts, PyInstaller build specs | `gayatri_demo.spec`, `installer.iss` | `ACTIVE` |
| `scripts/` | Tooling, dataset generation, sync verification, benchmarking | `verify_sync.py`, `benchmark_performance.py`, `run_evaluation.py` | `ACTIVE` |
| `tests/` | Complete 71-suite pytest automated test suite (411 tests) | `tests/test_*.py` | `ACTIVE` |
| `training/` | Fine-tuning datasets, prompt contracts, notebook recipes | `train_slm.py`, `prompts/chemistry_tutor_system_v1.txt` | `ACTIVE` |

---

## 3. Entry Points Inventory (Tasks 2 & 3)

### 3.1 Backend Entry Points
1. **`server.py`**: Central platform HTTP server entry point (`python server.py`). Starts `TeacherPortalHTTPHandler` on port 8000. Provides web UI for teachers and REST APIs for health, telemetry sync, directive injection, and alert resolution.
2. **`app/main.py`**: PySide6 desktop application entry point (`python app/main.py` or `run_gayatri.bat`). Initializes Qt event loop, WebEngine view, and WebChannel bridge.
3. **`scripts/verify_sync.py`**: End-to-end verification CLI (`python scripts/verify_sync.py --url <URL>`). Validates 5 synchronization gates between teacher server and student device.
4. **`scripts/check_environment.py`**: Environment and hardware preflight verification script.
5. **`install_llama.py`**: Local inference pre-requisite installer for `llama-cpp-python`.

### 3.2 Frontend Entry Points
1. **`app/ui/index.html`**: Comprehensive desktop student and teacher UI. Contains chat interface, concept roadmap graph, mastery gauges, chapter matrix, focus areas, and live telemetry.
2. **`server.py` HTML Template (`HTML_TEMPLATE`)**: Browser-accessible Teacher Command Center at `http://localhost:8000/`. Features cohort mastery tiers, chapter mastery matrix, diagnostic misconception tags, copilot briefing, alert queue, student roster, and pedagogical directive injector.

---

## 4. Databases & Current Persistence (Tasks 4 & 12)

| Persistence Store | Technology | Location | Tables / Schema | Authoritative Role |
|---|---|---|---|---|
| Central Platform DB | SQLite3 (WAL mode) | `central_platform.db` (via `central_platform/db.py`) | `organizations`, `users`, `audit_logs`, `courses`, `classes`, `enrollments` | Current central prototype (Target: PostgreSQL) |
| Local Student Profile | JSON | `student_profile.json` (via `core/tutor/adaptive.py`) | Student ID, concept masteries, active concept, review queue, hints used | Local client cache / offline store |
| Chemistry RAG Store | In-memory + JSON | `data/rag/*.json` | NCERT chunks, equations, definitions, metadata, atomic concepts | Authoritative chemistry domain knowledge |
| Curriculum Graph | JSON | `data/curriculum/chemistry/ncert_class11_12.json` | 4 chapters, 12 topics, concepts, prerequisites, difficulty | Authoritative chemistry curriculum DAG |

---

## 5. Services & Subsystems Inventory (Tasks 5 & 13)

### 5.1 Central Platform Services (`central_platform/`)
- **`TeacherPortalService`**: Aggregates cohort mastery, student rosters, alerts, and copilot briefings.
- **`TeacherInstructionEngine`**: Ingests, priorities, and scopes pedagogical directives from teachers to students.
- **`TeacherInterventionEngine`**: Manages intervention alerts triggered by persistent misconceptions or drop-offs.
- **`TeacherCopilot`**: RAG-augmented teacher assistant generating contextual student diagnostics and summaries.
- **`SyncManager`**: Ingests student telemetry snapshots and batches of learning events.
- **`RBACEngine`**: Role-based access control engine (`SUPER_ADMIN`, `ORG_ADMIN`, `TEACHER`, `STUDENT`).
- **`StudentLearningRecord (SLR)`**: In-memory prototype aggregating student learning history.
- **`AIGovernanceEngine`**: Tracks AI execution logs, token budgets, rate limits, and provider kill switches.
- **`AnalyticsEngine`**: Cohort-level learning analytics, velocity, and retention calculations.
- **`CurriculumManager`**: Curriculum versioning and publishing service.
- **`AssessmentBuilder`**: Central assessment and question bank management.
- **`NotificationManager`**: Notification routing and dispatch manager.
- **`OperationsReadiness`**: Platform health check, readiness probe, and system metrics.

### 5.2 Core Intelligence Subsystems (`core/`)
- **`BayesianKnowledgeTracing (BKT)`**: Probabilistic knowledge tracing tracking $P(L_0), P(T), P(S), P(G)$.
- **`LearningDependencyGraph (LDG)`**: Concept prerequisite DAG ensuring students master fundamentals before advanced topics.
- **`SpacedReviewScheduler`**: Half-life decay review scheduler with retention capping.
- **`AdaptivePolicy`**: Evidence-driven difficulty adjuster and pedagogical strategy selector.
- **`ChemistryTutorRuntime`**: 7-layer prompt compiler embedding teacher directives, RAG evidence, active concepts, and safety invariants.
- **`AssessmentEngine`**: Deterministic grading for MCQs, numerical tolerances, and stoichiometric balancing.
- **`MisconceptionClassifier`**: Catalog-based diagnostic classifier identifying NCERT chemistry misconceptions.

### 5.3 External Integrations
- **Local Inference**: `llama-cpp-python` executing GGUF quantized models locally with CPU/Vulkan/CUDA acceleration.
- **API Providers**: Configured provider abstractions in `core/providers/` (OpenAI, Anthropic, Gemini, OpenRouter).

---

## 6. Test Suites Inventory (Task 6)

The repository contains **71 test files** in `tests/` with **411 test cases**:
- **Core Adaptive & BKT Tests**: `test_phase6_adaptive_engine_v2.py`, `test_phase8_adaptive_engine.py`, `test_accuracy_and_seeding.py`
- **Assessment Engine Tests**: `test_phase7_assessment_engine.py`, `test_phase11_assessment_engine.py`, `test_phase11_assessment_platform.py`
- **Tutor Runtime & Prompts**: `test_phase6_prompt_system.py`, `test_phase6_evaluator.py`, `test_slm_pedagogical_alignment.py`, `test_tutor_mode_realtime.py`
- **RAG & Knowledge Graph**: `test_phase4_hybrid_rag.py`, `test_phase5_knowledge_graph_rag.py`, `test_phase9_rag.py`, `test_phase13_rag_audit.py`
- **Teacher Portal & Directives**: `test_phase7_teacher_instructions.py`, `test_phase8_teacher_portal.py`, `test_phase9_teacher_intervention.py`, `test_phase10_teacher_copilot.py`, `test_teacher_dashboard_bridge.py`
- **Central Platform & Sync**: `test_server_live_sync.py`, `test_phase2_central_platform.py`, `test_phase4_sync.py`, `test_phase5_learning_events.py`, `test_phase5_slr.py`
- **Security & Hardening**: `test_phase15_security.py`, `test_phase16_security_audit.py`, `test_phase17_security_hardening.py`, `test_phase19_upload_security.py`, `test_phase3_silent_failures.py`

**Baseline Result**: 411 passed in 11.40s (0 failures, 0 warnings).

---

## 7. Module Classification Matrix (Tasks 7, 8, 9, 10)

| Module Path | Classification | Rationale & Current Role | Target State |
|---|---|---|---|
| `app/main.py` | `ACTIVE` | Primary desktop entry point running PySide6 UI | Preserved and linked to `/api/v1/*` |
| `app/bridge/facade.py` | `ACTIVE` | WebChannel bridge between JS and Python | Preserved and integrated with central sync |
| `app/ui/index.html` | `ACTIVE` | Desktop HTML/CSS/JS frontend | Preserved, updated to consume authoritative SLR |
| `core/tutor/adaptive.py` | `ACTIVE` | Core BKT, LDG, and spaced review algorithms | Preserved; wrapped by Central Learning Engine in Phase 07 |
| `core/runtimes/chemistry.py` | `ACTIVE` | Chemistry tutor runtime and prompt compiler | Preserved; teacher directive injection active |
| `core/rag/store.py` | `ACTIVE` | Hybrid keyword and semantic RAG retrieval | Preserved; generalized to plug-and-play in Phase 16 |
| `core/assessment/engine.py` | `ACTIVE` | Local assessment grading and anti-leakage | Preserved; connected to Central Assessment Platform |
| `server.py` | `ACTIVE` | Standalone HTTP server for Teacher Portal & APIs | Reconciled into production FastAPI platform in Phase 02 |
| `central_platform/db.py` | `PROTOTYPE` | SQLite persistence for organizations/users | Replaced by PostgreSQL authoritative data layer in Phase 03 |
| `central_platform/slr/record.py` | `PROTOTYPE` | In-memory student learning record dictionary | Upgraded to PostgreSQL-backed authoritative SLR in Phase 06 |
| `central_platform/sync/manager.py` | `PROTOTYPE` | Basic sync manager accepting snapshots | Upgraded to robust network event sync in Phase 08 |
| `central_platform/teacher/portal.py` | `ACTIVE` | Teacher dashboard aggregation and KPIs | Integrated with Central Platform API in Phase 10 |
| `central_platform/teacher/instruction.py` | `ACTIVE` | Teacher directive scoping and persistence | Fully integrated with SLR and AI tutor context |
| `central_platform/teacher/intervention.py` | `ACTIVE` | Alert queue management and resolution | Integrated into central intervention pipeline |
| `central_platform/teacher/copilot.py` | `PROTOTYPE` | Mock-assisted teacher copilot summaries | Upgraded to real RAG-backed assistant in Phase 13 |
| `central_platform/rbac/engine.py` | `PROTOTYPE` | Role checking prototype without JWT auth | Upgraded to production Auth + RBAC in Phase 04 |
| `central_platform/ai_governance/engine.py` | `PROTOTYPE` | Prototype AI token tracker and rate limiter | Upgraded to AI Gateway & Governance in Phases 17–18 |
| `central_platform/analytics/engine.py` | `PROTOTYPE` | Prototype analytics calculations | Upgraded to event-driven analytics in Phase 20 |
| `central_platform/notifications/manager.py` | `PROTOTYPE` | Prototype notification dispatcher | Upgraded to multi-channel notifications in Phase 21 |
| `central_platform/curriculum/manager.py` | `PROTOTYPE` | Prototype curriculum versioning | Upgraded to plug-and-play curriculum in Phase 15 |
| `central_platform/assessment/builder.py` | `PROTOTYPE` | Prototype assessment item builder | Upgraded to assessment platform in Phase 19 |
| `legacy/agents/default_agents.py` | `LEGACY` | Superseded prototype agent classes | Kept for backwards compatibility; marked legacy |
| `scripts/verify_sync.py` | `ACTIVE` | 5-gate sync verification CLI | Preserved as primary sync gatekeeper |

---

## 8. Capability Gap Matrix (Required Output)

| Capability | Existing Location | Actual State | Target State | Gap & Action Required |
|---|---|---|---|---|
| **Authoritative Platform Database** | `central_platform/db.py` | Local SQLite with 6 tables; student progress still largely stored in local JSON (`student_profile.json`). | Central PostgreSQL database with complete relational schema (organizations, users, roles, SLR, learning events, teacher instructions, assessments, AI logs). | Phase 03 will implement PostgreSQL schema, migrations, connection pooling, and multi-tenant scoping. |
| **Platform API Layer** | `server.py` (`TeacherPortalHTTPHandler`) | Python standard library `http.server` with custom route dispatching (`/api/health`, `/api/student/snapshot`, `/api/teacher/*`). | Production FastAPI application with versioned routes (`/api/v1/*`), Pydantic validation, OpenAPI specs, auth middleware, request IDs. | Phase 02 will build the unified FastAPI platform layer. |
| **Authentication & RBAC** | `central_platform/rbac/engine.py` | In-memory role check with hardcoded roles; no JWT tokens, no password hashing, no session management. | Production Auth service with Argon2/bcrypt password hashing, JWT access/refresh tokens, session invalidation, org/course scoping. | Phase 04 will implement production Authentication and RBAC middleware. |
| **Learning Event Pipeline** | `central_platform/sync/manager.py` | In-memory list storing raw event dictionaries; no idempotency enforcement, no replay capability. | Central, immutable, idempotent learning event pipeline storing events in PostgreSQL with schema versioning. | Phase 05 will implement the authoritative learning event stream. |
| **Student Learning Record (SLR)** | `central_platform/slr/record.py` | In-memory dictionary aggregating profile data. | Canonical, authoritative SLR derived from event stream; exposes mastery, timeline, misconceptions, alerts. | Phase 06 will build the authoritative PostgreSQL-backed SLR. |
| **Adaptive Learning Integration** | `core/tutor/adaptive.py` | Working BKT, LDG, and spaced review running locally against `student_profile.json`. | Adaptive engine driven by central learning events and updating canonical SLR. | Phase 07 will wire existing BKT/LDG to central events and SLR. |
| **Client ↔ Server Network Sync** | `scripts/verify_sync.py` & `app/bridge/facade.py` | Snapshot POST and instruction GET; basic offline fallback. | Robust sync engine with client-side event queue, retry with exponential backoff, conflict resolution, idempotency keys. | Phase 08 will implement production network sync engine. |
| **Student Progress Web/App UI** | `app/ui/index.html` | Rich desktop UI displaying mastery, chapter cards, roadmaps, and misconceptions. | Full web and desktop progress interfaces powered strictly by `/api/v1/students/:id/slr` endpoints. | Phase 09 will connect UI states (loading, empty, offline, error) to real API. |
| **Teacher Web Portal** | `server.py` HTML template | Server-rendered HTML dashboard with KPIs, mastery tiers, roster, alerts, copilot, and directives. | Comprehensive responsive web application with dedicated views for `/dashboard`, `/students/:id`, `/timeline`, `/alerts`. | Phase 10 will deliver full browser teacher application. |
| **Teacher AI Instructions** | `central_platform/teacher/instruction.py` | Scoped instruction engine with priority and course/student matching; injected into prompt. | Formal instruction workflow with policy validation, expiration, audit trail, and tutor context integration. | Phase 11 will harden teacher instruction lifecycle. |
| **Teacher Interventions** | `central_platform/teacher/intervention.py` | In-memory alert queue with status toggle and priority. | Auditable intervention workflow triggered by SLR patterns (declining scores, persistent misconceptions) with teacher notes. | Phase 12 will implement full intervention lifecycle. |
| **Teacher Copilot** | `central_platform/teacher/copilot.py` | Prototype generating heuristic summaries. | RAG-grounded copilot answering diagnostic questions with citations to authoritative student records. | Phase 13 will build real RAG-backed Copilot. |
| **Admin Web Portal** | `central_platform/admin/` | Code skeleton; no web UI. | Browser admin portal for managing orgs, users, courses, curricula, AI providers, and system kill switches. | Phase 14 will build browser admin application. |
| **Plug-and-Play Curriculum** | `core/curriculum/` & `data/curriculum/` | Hardcoded NCERT chemistry JSON files. | Abstracted curriculum pipeline supporting versioning, publishing, import/export for any subject/grade. | Phase 15 will implement plug-and-play curriculum engine. |
| **Plug-and-Play RAG** | `core/rag/` | Fixed NCERT chemistry JSON files in `data/rag/`. | Knowledge ingestion pipeline accepting PDF/DOCX/HTML/MD/JSON with chunking, embedding, indexing, and course attachment. | Phase 16 will build plug-and-play RAG platform. |
| **AI Gateway & Model Router** | `core/providers/` | Basic provider abstractions for local Llama, Ollama, and OpenAI. | Central AI Gateway with model allowlists, fallback routing, circuit breakers, rate limits, and cost tracking. | Phase 17 & Phase 18 will deliver unified AI Gateway. |
| **Assessment Platform** | `core/assessment/` | Local grading for MCQ, numerical, and chemistry equations. | Central assessment platform with item bank, diagnostic/formative tests, rubrics, and automated SLR feedback. | Phase 19 will implement assessment platform. |
| **Analytics & Reporting** | `central_platform/analytics/` | Prototype metrics calculations. | Event-driven analytics engine for student velocity, teacher cohort reports, and administrative ROI/usage. | Phase 20 will deliver analytics service. |
| **Notifications** | `central_platform/notifications/` | Prototype manager. | Multi-channel delivery engine (in-app, email, push) with queueing and retry backoff. | Phase 21 will implement notifications platform. |
| **Security Hardening** | `core/security/` | Input sanitization, anti-leakage regex, and prompt safety. | Comprehensive security hardening (RBAC bypass tests, IDOR prevention, prompt injection defenses, audit logging). | Phase 22 will complete full security pass. |

---

## 9. Baseline Verification & Reproducibility (Gate)

Before proceeding to subsequent architectural phases, the repository baseline was executed and verified:
1. **Pytest Full Suite**:
   ```powershell
   pytest
   # Result: 411 passed in 11.40s (0 failures, 0 warnings, 0 errors)
   ```
2. **Sync Verification Gatekeeper**:
   ```powershell
   python scripts/verify_sync.py
   # Result: All 5/5 gates passed (Connectivity, Telemetry push, Directive dispatch, Student pull, AI Prompt alteration)
   ```
3. **Open Defects**: 0 open P0, 0 open P1, 0 open P2.
4. **Repository Tree**: Clean; all active code paths mapped and classified.

---

## 10. Phase 00 Completion Status
- **Status**: `VERIFIED`
- **Baseline Established**: Yes (411 tests passing, 0 warnings)
- **Authoritative Documents Created**:
  - `docs/implementation/V2_PLATFORM_MASTER_PLAN.md`
  - `docs/implementation/V2_PLATFORM_PROGRESS.md`
  - `docs/implementation/DEBUGGING_REGISTER.md`
  - `docs/implementation/REGRESSION_REGISTER.md`
  - `docs/implementation/DECISION_LOG.md`
  - `docs/architecture/current-state.md`
