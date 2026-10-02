# Gayatri AI Platform — Enterprise Course-Independent Adaptive Education Engine

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.md)
[![Build & Tests](https://img.shields.io/badge/tests-1144%2B%20passed%20%7C%200%20failed-brightgreen.svg)]()
[![Architecture](https://img.shields.io/badge/architecture-course--independent-orange.svg)]()
[![Platform Version](https://img.shields.io/badge/platform-v5.0.0--final--release-purple.svg)]()
[![Security & Reliability](https://img.shields.io/badge/resilience-12%2F12%20failure%20injections%20verified-teal.svg)]()

**Gayatri AI Platform** is an enterprise-grade, course-independent, offline-capable adaptive education system. Designed to transform any syllabus, textbook, or learning standard (NCERT, CBSE, university STEM, coding bootcamps, or vocational training) into an intelligent, personalized, and interactive tutoring experience, Gayatri combines local-first Small Language Models (SLMs), multi-cloud AI routing, version-pinned scoped RAG, evidence-backed mastery tracking, and a 16-step transactional orchestrator with zero orphaned state transitions.

---

## 🧭 Executive Overview for Incoming Engineers

If you are joining the project or reviewing this codebase, here is the state of the platform:

- **Codebase Health**: **1,144+ tests passing**, 0 failing, 0 skipped (`pytest -q` verified in ~220s).
- **Architecture Maturity**: **Phases 00 through 27 fully implemented, verified, audited, and release-gated**.
- **Course-Independence**: Fully generalized. Zero hardcoded subject logic in the core orchestrator or learning engine; subject-specific capabilities (e.g. chemical formula balancing, code execution, math evaluation) are dynamically registered via the `ToolRegistry` and `EvaluatorRegistry`.
- **Database Schema**: 50 authoritative tables managed by an immutable SQL DDL migration ledger (`migrations/001` through `008`) with SHA-256 tamper-detection and transactional rollback.
- **Inference Strategy**: Local-first CPU inference via `llama.cpp` with seamless, strategy-driven fallback to OpenAI, Anthropic, Gemini, and OpenRouter.
- **Dual Runtime**: Complete online REST API boundary (FastAPI, 16 modular routers) and standalone offline local runtime with atomic session persistence and conflict-resolving bi-directional sync (`LocalSyncOutbox` + `SyncService`).
- **Resilience Contract**: All failure modes implement the standardized `RecoveryResult` contract across 12 concrete failure categories with explicit `CommitDecision` (`COMMIT`, `ROLLBACK`, `NOOP`, `RETRY`).
- **Production Validation**: 100% live subsystem health probing, strict secret security enforcement, automated clean-install bootstrapping, and tamper-evident packaging.

---

## 🏛️ System Architecture

```text
                                       GAYATRI AI PLATFORM
                                                │
         ┌───────────────────────┬──────────────┴──────────────┬───────────────────────┐
         ▼                       ▼                             ▼                       ▼
    Student Portal         Teacher Portal                Parent Portal           Fee Admin UI
  (Learner Journeys)     (Class Roster & Copilot)      (Privacy & Feed)      (Billing & Invoicing)
         │                       │                             │                       │
         └───────────────────────┴──────────────┬──────────────┴───────────────────────┘
                                                │
                                                ▼
                                    Unified Application Shell
                                                │
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         ▼                                                                             ▼
   Online API Boundary                                                        Offline Local Runtime
  (FastAPI /api/v1/ - 16 Routers)                                             (LocalCache & Outbox)
         │                                                                             │
         └──────────────────────────────────────┬──────────────────────────────────────┘
                                                │
                                                ▼
                                 GenericTutorOrchestrator
                                 (16-Step Turn Lifecycle)
                                                │
         ┌──────────────────────────────┬───────┴──────────────┬────────────────────────┐
         ▼                              ▼                      ▼                        ▼
  AI Gateway Router             Scoped RAG Engine       Course Tool Engine       Canonical State
(Local SLM + Cloud Fallbacks)  (Hybrid Vector/BM25)    (Registry & Adapters)   (Two-Phase Commit)
         │                              │                      │                        │
         └──────────────────────────────┴───────┬──────────────┴────────────────────────┘
                                                │
                                                ▼
                                     Platform Database
                              (SQLite / PostgreSQL - 50 Tables)
                                                │
                                                ▼
                                     Sync & Recovery Subsystem
                              (SyncService + FailureRecoveryManager)
```

---

## 🌟 Core Subsystems & Technical Invariants

### 1. 16-Step Generic Tutor Orchestrator (`central_platform/tutor/orchestrator.py`)
Every student turn executes through an invariant, deterministic 16-step lifecycle:
1. **Enrollment Authorization**: Validates student active enrollment in the target course offering.
2. **State Retrieval**: Loads `CanonicalLearningState` with multi-course boundary isolation.
3. **Query Understanding**: Structured intent extraction (`ConceptExtraction`, `IntentType`).
4. **Prompt Injection & Safety**: Pre-inference security screen via `SecurityAuditor`.
5. **Instruction Cascade**: Resolves active 5-tier teacher instructions with temporal validity checks.
6. **Scoped RAG Retrieval**: Fetches evidence chunks strictly pinned to the active course version.
7. **Tool Capability Resolution**: Resolves authorized tools based on `CourseToolPolicy`.
8. **Context Assembly**: Constructs token-budgeted prompt incorporating all upstream context.
9. **Pedagogical Scaffolding**: Formulates structured scaffolding action (`HINT`, `EXPLAIN`, `PRACTICE`, etc.).
10. **Model Inference**: Executes generation via AI Gateway (local SLM or cloud provider).
11. **Tool Execution Engine**: Executes sandboxed tool calls requested by pedagogical logic.
12. **Pedagogical Validation**: Validates candidate response against 7 educational invariants.
13. **Anti-Answer Leakage**: Screens final response to prevent direct solutions during assessment.
14. **Mastery Calculation**: Deterministically calculates state delta based on student interaction.
15. **Two-Phase State Commit**: Commits state delta ONLY upon validation success; rolls back on failure.
16. **Event Store Logging**: Appends immutable learning event to `learning_events` with telemetry.

### 2. Course-Independent Content & Offering Model (`central_platform/courses/`)
- **Course Isolation**: Courses exist as first-class entities with organizational boundaries (`tenant_id`).
- **Version Pinning**: Content is drafted, reviewed, approved, and versioned (`CourseVersion`). Students learn against immutable published versions.
- **Offering & Group Scoping**: Students enroll into `CourseOffering` instances linked to classes and remedial groups, allowing multi-course enrollment without cross-course state bleed.
- **Review Queue**: Strict approval workflow where teacher uploads require `ORG_ADMIN` or `SUPER_ADMIN` review before publication.

### 3. Scoped RAG & Knowledge Pipeline (`central_platform/rag/`)
- **Version-Pinned Retrieval**: Knowledge chunks are tagged with `course_id` and `course_version_id`.
- **Hybrid Retrieval**: Combines semantic embeddings with BM25 lexical ranking for exact technical terminology recall.
- **Remedial & Class Scoping**: Queries can be scoped to specific class groups or remedial tracks.
- **Plug-and-Play Management**: Dynamic source ingestion, chunk validation, index rebuilding, and hot deletion over REST API.

### 4. 5-Tier Scoped Teacher Instruction Hierarchy (`central_platform/teacher/instruction.py`)
Pedagogical steering is governed by an explicit 5-tier priority hierarchy:
```text
SESSION  >  STUDENT  >  CLASS  >  COURSE  >  ORGANIZATION
(Highest)                                       (Lowest)
```
- Lower-tier instructions cannot override higher-tier restrictions.
- Supports temporal validity windows (`valid_from` to `valid_until`) with automated expiration.
- Verified deep prompt injection into the AI Context Builder.

### 5. Capability-Driven Assessment & Evaluation Engine (`central_platform/assessment/`)
- **Evaluator Registry**: Dynamic registry mapping assessment item capabilities to specialized evaluators.
- **Multi-Modal Evaluators**: `DeterministicEvaluator` (exact matching/MCQ), `RubricEvaluator` (criteria grading), and domain-specific code/math evaluators.
- **Anti-Leakage Sanitization**: Strips answers and grading keys before payloads reach student context.
- **Misconception Diagnosis**: Maps incorrect student answers directly to cataloged misconceptions to trigger targeted remediation.

### 6. Generic Course Tool Registry & Adapters (`central_platform/tools/`)
- Dynamic registry (`ToolRegistry`) decouples tools from core engines.
- Domain adapters (e.g. `ChemistryDomainAdapter`, Python code runners, LaTeX equation plotters) register custom actions, parameters, and validators.
- Enforces strict execution timeouts, sandboxing, and runtime disablement (`unregister_adapter`).

### 7. Local-First AI Gateway & Model Router (`central_platform/ai/`)
- **Local-First Execution**: Embedded `llama.cpp` runner executing quantized GGUF models (`Qwen2.5-0.5B-Instruct`) entirely offline on consumer CPUs.
- **Provider Decoupling**: Pluggable cloud adapters for **OpenAI**, **Anthropic**, **Gemini**, and **OpenRouter**.
- **Strategy Routing**: `LOCAL_ONLY`, `LOCAL_FIRST` (fallback on failure/high load), and `CLOUD_PREFERRED`.
- **Privacy Fail-Closed**: PII and sensitive student records are never transmitted externally.

### 8. Offline Local Runtime & Bi-Directional Sync (`central_platform/local_runtime/` & `sync/`)
- **Local Course Cache**: Encrypted local cache with SHA-256 integrity verification. Corrupted caches are automatically quarantined.
- **Local Session Persistence**: In-memory and SQLite-backed local state with crash recovery.
- **Bi-Directional Sync Pipeline**: `LocalSyncOutbox` records offline mutations and replays operations against central `SyncService` with operation-level idempotency and conflict resolution.
- **Migration 008**: Dedicated `sync_operations` schema tracking sync receipts, client sequence numbers, and state hashes.

### 9. Database & Immutable Migration Ledger (`migrations/` & `central_platform/db.py`)
- **50 Authoritative Relational Tables**: Covering users, courses, versions, offerings, enrollments, classes, RAG chunks, teacher instructions, learning events, mastery state, assessments, fees, payments, and sync operations.
- **Immutable Ledger**: Migrations `001` through `008` execute sequentially with SHA-256 checksum verification and reversible down-migration capabilities.
- **Dual Dialect Support**: Native SQLite for local/offline runtimes and full PostgreSQL compatibility for cloud production deployments.

### 10. Enterprise Security, Privacy & RBAC (`central_platform/security/` & `privacy/`)
- **RBAC Hierarchy**: `SUPER_ADMIN` > `ORG_ADMIN` > `TEACHER` > `STUDENT` > `PARENT` > `GUEST`.
- **Tenant Isolation**: Strict organizational tenancy prevents any cross-institution data access.
- **Prompt Injection Defense**: Multi-stage detection blocking prompt injection attacks and redirection attempts.
- **Parent Privacy Engine**: 4 policy levels (`FULL_TRANSPARENCY`, `SUMMARY_ONLY`, `RESTRICTED`, `BLOCKED`) governing parent data access.

### 11. Reliability, Failure Injection & Recovery (`central_platform/recovery/`)
- **Resilience Contract**: Every failure handler returns a standardized `RecoveryResult` with 6 mandatory fields:
  - `failure_category`: Machine-readable category string.
  - `status`: Lifecycle state (`FAILED`, `DEGRADED`, `RECOVERED`).
  - `user_message`: Safe, student-friendly pedagogical message (no stack traces).
  - `technical_diagnostic`: Internal debug diagnostics for observability.
  - `retryable`: Boolean flag guiding client retry strategies.
  - `commit_decision`: Explicit state directive (`COMMIT`, `ROLLBACK`, `NOOP`, `RETRY`).
- **12 Verified Failure Handlers**: Missing model, corrupt model, provider timeout, provider malformed response, RAG failure, database offline, broken migration, broken upload, interrupted publish, expired instruction, duplicate sync, and app crash mid-turn.
- **Crash Recovery Boundary**: Unhandled runtime exceptions mid-turn trigger automatic state rollback, leaving zero orphaned events.

---

## 📂 Repository Directory Layout

```text
Gayatri/
├── app/                              # Presentation & UI Layer
│   ├── bridge/                       # Facade bridging UI to core engines
│   └── ui/
│       ├── design_system/            # Theme tokens, dark/light styles, components
│       └── views/                    # Shell, Tutor UI, Student, Teacher, Parent, Fee UIs
├── central_platform/                 # Core Platform Logic
│   ├── ai/                           # AI Gateway, llama.cpp runner, cloud adapters
│   ├── api/                          # FastAPI server & 16 REST routers (/api/v1/...)
│   ├── assessment/                   # EvaluatorRegistry, rubrics, anti-leakage guards
│   ├── courses/                      # CourseService, versions, offerings, enrollments
│   ├── fees/                         # Fee accounts, invoicing, structures, receipts
│   ├── learning/                     # Canonical state, mastery engine, DAG graph
│   ├── local_runtime/                # Offline engine, local cache, device quarantine
│   ├── models/                       # Authoritative schema & dataclasses
│   ├── payments/                     # Payment gateway adapters (Razorpay, UPI, Mock)
│   ├── portals/                      # Portal controllers (Admin, Teacher, Student)
│   ├── privacy/                      # Parent privacy rules engine & visibility filter
│   ├── rag/                          # Knowledge pipeline, scoped chunking & retrieval
│   ├── recovery/                     # FailureRecoveryManager & resilience contracts
│   ├── security/                     # RBAC enforcement, prompt injection sanitizer
│   ├── sync/                         # Bi-directional sync service & conflict resolver
│   ├── teacher/                      # 5-tier instruction cascade & temporal filters
│   ├── tools/                        # ToolRegistry, ToolExecutionEngine, adapters
│   ├── db.py                         # PlatformDatabase interface (50 tables)
│   └── tutor/
│       └── orchestrator.py           # 16-Step GenericTutorOrchestrator
├── docs/                             # Architecture specs, security models, manuals
│   ├── reports/                      # Phase verification plans, test results & logs
│   └── security/                     # RBAC policies & security regression reports
├── migrations/                       # SQL DDL migrations (001 through 008)
├── tests/                            # Comprehensive automated test suite (1,114 tests)
├── GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md # Authoritative Master Execution Plan
├── PROJECT_STATE.yaml                # Machine-readable current project state
├── requirements.txt                  # Core platform dependencies
└── pyproject.toml                    # Pytest, linters, and packaging configuration
```

---

## 🚀 Installation & Local Setup

### Prerequisites
- **Python**: Version 3.12 or newer
- **Git**: 2.30+
- **C++ Build Tools / OpenBLAS** *(Optional, only needed if compiling `llama-cpp-python` from source)*

### 1. Clone & Virtual Environment Setup

```bash
# Clone the repository
git clone https://github.com/Gayatri-Education/Gayatri.git
cd Gayatri

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:

```env
# Database Configuration (defaults to local SQLite if omitted)
GAYATRI_DB_PATH=gayatri_local.db
GAYATRI_ENV=development

# AI Gateway Configuration
GAYATRI_AI_STRATEGY=LOCAL_FIRST
GAYATRI_LOCAL_MODEL_PATH=models/qwen2.5-0.5b-instruct-q4_k_m.gguf

# Optional Cloud Fallback Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# Security & Secrets
JWT_SECRET_KEY=dev-secret-key-change-in-production-32-bytes-min
GAYATRI_ENCRYPTION_KEY=
```

### 3. Initialize Database & Run Migrations

```bash
# Run all SQL DDL migrations (001 through 008)
python -c "from central_platform.db import PlatformDatabase; db = PlatformDatabase(); print('Database initialized, tables:', len(db.get_table_names()))"
```

---

## 🧪 Running Tests & Quality Verification

Gayatri enforces a strict 100% green test policy. All 1,133+ tests must pass before any code is merged.

```bash
# Run the entire test suite (1,133+ tests in ~3 minutes)
python -m pytest --tb=short -q -m "not gui"

# Run specific Phase verification suites
python -m pytest tests/test_phase26_packaging_clean_install.py -v
python -m pytest tests/test_phase25_performance_capacity_verification.py -v
python -m pytest tests/test_phase24_e2e_journeys_real.py -v
python -m pytest tests/test_phase23_reliability_failure_injection_recovery.py -v
python -m pytest tests/test_phase22_security_privacy_isolation_audit.py -v
```

---

## 🌐 Running the Application & API

### 1. Start the Online REST API Server
The platform exposes 16 modular routers under `/api/v1` along with Kubernetes-ready health probes:

```bash
# Launch FastAPI server on port 8000
python -m uvicorn central_platform.api.server:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Probes**:
  - `GET http://localhost:8000/healthz` (Liveness)
  - `GET http://localhost:8000/readyz` (Readiness)
  - `GET http://localhost:8000/livez` (Platform state & uptime)

### 2. Launch the Desktop Application Shell
```bash
# Launch the PySide6 unified UI shell
python app/main.py
```

---

## 📊 Phase-by-Phase Progress & Verification Matrix

The platform is engineered under the authoritative `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`.

| Phase | Subsystem / Focus | Status | Tests | Key Deliverables |
|---|---|---|---|---|
| **Phase 00** | Safety Baseline & Forensics | `VERIFIED` | 664 / 664 | Repository inventory, safety baselines, duplicate detection |
| **Phase 01** | Core-Independent Data Layer | `VERIFIED` | 670 / 670 | `Course`, `CourseVersion`, `CourseOffering` models |
| **Phase 02** | Schema Evolution & Migrations | `VERIFIED` | 676 / 676 | Migrations 004-006, database version tracking |
| **Phase 03** | Generic Curriculum & Multi-Course DAG | `VERIFIED` | 682 / 682 | Course-agnostic concept graph, cycle detection |
| **Phase 04** | Multi-Course Learning State | `VERIFIED` | 694 / 694 | Multi-course student learning record, mastery isolation |
| **Phase 05** | Scoped Knowledge Ingestion | `VERIFIED` | 704 / 704 | Course-scoped chunking, provenance metadata |
| **Phase 06** | Scoped RAG & Version Pinning | `VERIFIED` | 717 / 717 | Hybrid retrieval, version-pinned RAG, remedial scoping |
| **Phase 07** | 5-Tier Scoped Teacher Instructions | `VERIFIED` | 728 / 728 | SESSION > STUDENT > CLASS > COURSE > ORG cascade |
| **Phase 08** | Generic Course Tool Registry | `VERIFIED` | 742 / 742 | `ToolRegistry`, dynamic adapters, execution contracts |
| **Phase 09** | AI Gateway & Provider Decoupling | `VERIFIED` | 753 / 753 | Local SLM router, cloud adapters, fail-closed privacy |
| **Phase 10** | 16-Step Generic Tutor Orchestrator | `VERIFIED` | 765 / 765 | 16-step turn lifecycle, atomic two-phase commit |
| **Phase 11** | Capability-Driven Assessment Engine | `VERIFIED` | 777 / 777 | EvaluatorRegistry, rubrics, anti-leakage sanitization |
| **Phase 12** | Unified REST API Boundary | `VERIFIED` | 789 / 789 | 16 FastAPI routers, health probes, OpenAPI V2 export |
| **Phase 13** | Local Offline Runtime Engine | `VERIFIED` | 801 / 801 | LocalCourseCache, LocalRAGCache, device quarantine |
| **Phase 14** | Bi-Directional Sync & Conflicts | `VERIFIED` | 813 / 813 | SyncService, LocalSyncOutbox, migration 008 |
| **Phase 15** | Admin Course & Content Workflow UI | `VERIFIED` | 825 / 825 | Content upload, version approval queue, publishing |
| **Phase 16** | Teacher Pedagogical Workflow UI | `VERIFIED` | 837 / 837 | Instruction composer, class analytics, copilot |
| **Phase 17** | Student Multi-Course Journey UI | `VERIFIED` | 849 / 849 | Multi-course switcher, learning graph, spaced reviews |
| **Phase 18** | Instruction & RAG Prompt Integration | `VERIFIED` | 861 / 861 | Deep prompt injection, context budget allocation |
| **Phase 19** | Domain Adapter Isolation | `VERIFIED` | 873 / 873 | Chemistry extraction, dynamic plug-and-play tools |
| **Phase 20** | Legacy Removal & Dead-Code Elimination | `VERIFIED` | 886 / 886 | Deleted legacy directories, zero dead imports |
| **Phase 21** | Database & Migration Hardening | `VERIFIED` | 898 / 898 | 50 tables, migrations 001-008 verified, rollback tested |
| **Phase 22** | Security, Privacy & Isolation Audit | `VERIFIED` | 1102 / 1102 | 12 attack vectors closed, RBAC hardened, prompt defense |
| **Phase 23** | Reliability, Failure Injection & Recovery | `VERIFIED` | 1114 / 1114 | 12 failure handlers, FailureRecoveryManager, crash safety |
| **Phase 24** | Real End-to-End Journeys & Boundary Testing | `VERIFIED` | 1119 / 1119 | Journeys A, B, C and 11 adversarial negative vectors NJ-1..11 |
| **Phase 25** | Performance & Capacity Verification | `VERIFIED` | 1126 / 1126 | Latency budgets, high-throughput batching (>30k ev/s), scale |
| **Phase 26** | Packaging, Clean Install & Live Probing | `VERIFIED` | 1133 / 1133 | Fresh bootstrap, 001-008 migrations, live subsystem probes |
| **Phase 27** | Documentation, State Reconciliation & Release Gate | `VERIFIED` | 1133 / 1133 | Authoritative documentation, 30-item Release Gate, clean tree |

---

## 🛡️ Security, Resilience & Quality Assurance

- **Zero Tolerance for Silent Fails**: Phase 23 eliminated silent exception swallowing across the platform. All errors produce explicit `RecoveryResult` objects with observable diagnostics and defined rollback decisions.
- **Tenant Isolation**: Cross-organization requests are rejected with `403 Forbidden` across all API routers and database query boundaries.
- **Answer Leakage Prevention**: Candidate responses from AI models are parsed for exact solution strings and forbidden key patterns; violations are blocked and redirected to pedagogical hints.
- **Deterministic State Safety**: In-memory state mutation is staged in a scratchpad and only committed to the persistent database after full pedagogical verification passes. If an unexpected exception occurs mid-turn, the state rollback hook restores session state with zero orphaned events.

---

## 📚 Complete Documentation Index

For in-depth architectural and operational specifications, consult:

- **[System Architecture](docs/ARCHITECTURE.md)**: Deep dive into the 16-step orchestrator, data flows, and subsystem components.
- **[Data Model Specification](docs/DATA_MODEL.md)**: Authoritative documentation of the 50 database tables, relations, and dataclasses.
- **[Security & RBAC Policy](docs/security/RBAC_POLICY_V4.md)**: Role permissions, security invariants, and audit findings.
- **[Learning Graph & Mastery Engine](docs/LEARNING_GRAPH.md)**: Mathematical models for multi-factor mastery, Ebbinghaus decay, and prerequisite propagation.
- **[Phase 23 Failure Recovery Report](docs/reports/PHASE_23_TEST_REPORT.md)**: Comprehensive report on failure injection scenarios and recovery contracts.
- **[Requirements Traceability Matrix](docs/reports/REQUIREMENTS_TRACEABILITY.md)**: Mapping from design requirements to code and test implementations.
- **[Master Development Plan](GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md)**: Complete step-by-step roadmap and verification guidelines.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
