# Local Runtime & Route Matrix Forensic Audit

**Audit Date:** 2026-10-02T15:55:00+05:30  
**Repository:** `Gayatri-Education/Gayatri`  
**Platform Version:** v5.0.0  

---

## 1. Runtime Entry-Point Audit

The codebase contains three distinct application runtime entry points and three administrative CLI tools. Their authority, status, and target environments are classified below:

| Entry Point | Implementation File | Runtime Type | Authority | Status | Operational Port / Target | Notes |
|---|---|---|---|---|---|---|
| **Online REST API Server** | `central_platform/api/server.py` | FastAPI / Uvicorn | **AUTHORITATIVE** | Production | `0.0.0.0:8000` | 182 OpenAPI routes, 16 modular `/api/v1` routers, `/healthz`, `/readyz`, `/livez`. |
| **Desktop Application Shell** | `app/main.py` | PySide6 / Qt GUI | **AUTHORITATIVE** | Production | Native Desktop Window | Multi-persona shell (Student, Teacher, Parent, Fee Admin) with WebEngine bridge. |
| **Offline Local Runtime** | `central_platform/local_runtime/cache.py` | SQLite / Local Files | **AUTHORITATIVE** | Edge / Offline | Local On-Device Storage | Encrypted local cache with SHA-256 tamper quarantine and local sync outbox. |
| **Legacy Teacher Portal Server** | `server.py` | `http.server.HTTPServer` | **NON-AUTHORITATIVE** | Legacy Compatibility | `127.0.0.1:8000` | Standalone simple HTTP server from Phase 00-09 with hardcoded demo cohort. Retained only for `test_server_live_sync.py`. |
| **Deployment Validator** | `central_platform/deployment/validator.py` | CLI Script | Administrative Tool | Verified | Console Output | 9-point automated infrastructure validation check. |
| **Demo Seeder** | `scripts/seed_local_environment.py` | CLI Script | Development Tool | Explicit Dev Only | Local Database | Explicit manual seed generator; never invoked automatically at runtime. |

### Decision on Runtime Authority:
- **`central_platform.api.server`** is the **sole authoritative online runtime**.
- **`app.main`** is the **sole authoritative desktop runtime**.
- **`server.py`** is marked **LEGACY / NON-AUTHORITATIVE**. In this reconciliation task, `central_platform/api/app.py` has been completely decoupled from `server.py` so that starting the production FastAPI server never invokes `server.py`'s demo seeding logic.

---

## 2. Route & Endpoint Forensic Audit

A programmatic inspection of `central_platform.api.app:create_app().openapi()["paths"]` identified **182 distinct HTTP routes**.

### 2.1 Route Subsystem Summary
| Route Prefix | Subsystem Handler | Endpoint Count | Auth Required | Real Database Access | Primary Purpose |
|---|---|---|---|---|---|
| `/api/v1/auth/*` | `routes/auth.py` | 7 | Partial (Login/Reset public; Me/Logout/Refresh protected) | Yes (`users`, `user_credentials`) | JWT lifecycle, login, refresh, password reset, demo tokens. |
| `/api/v1/users/*` | `routes/users.py` | 2 | Yes (`SUPER_ADMIN` / `ORG_ADMIN`) | Yes (`users`) | User provisioning, profile queries. |
| `/api/v1/students/*` | `routes/students.py` | 12 | Yes (`STUDENT`, `TEACHER`, `ADMIN`) | Yes (`student_learning_records`, `courses`) | Learning progress, multi-course switcher, mastery heatmaps. |
| `/api/v1/teachers/*` | `routes/teachers.py` | 24 | Yes (`TEACHER`, `ADMIN`) | Yes (`classes`, `interventions`, `slr`) | Class rosters, alert queue, copilot briefing, teacher notes. |
| `/api/v1/admin/*` | `routes/admin.py` | 21 | Yes (`SUPER_ADMIN`, `ORG_ADMIN`) | Yes (`organizations`, `courses`, `ai_providers`) | Kill-switches, feature flags, AI budgets, audit trails. |
| `/api/v1/courses/*` | `routes/courses.py` | 8 | Yes (RBAC enforced) | Yes (`courses`, `course_versions`) | Course creation, version submission, review queue, publication. |
| `/api/v1/curricula/*` | `routes/curricula.py` | 7 | Yes (Teacher/Admin) | Yes (`curricula`, `modules`, `concepts`) | Curriculum DAG hierarchy, JSON import/export, cycle validation. |
| `/api/v1/enrollments/*` | `routes/enrollments.py` | 2 | Yes (Admin/Teacher) | Yes (`enrollments`, `offerings`) | Offering enrollment provisioning and query. |
| `/api/v1/classes/*` | `routes/classes.py` | 3 | Yes (Teacher/Admin) | Yes (`class_groups`, `cohorts`) | Section grouping, cohort assignment. |
| `/api/v1/organizations/*`| `routes/organizations.py` | 2 | Yes (`SUPER_ADMIN`) | Yes (`organizations`) | Tenant lifecycle, institution settings. |
| `/api/v1/instructions/*` | `routes/instructions.py`| 2 | Yes (`TEACHER+`) | Yes (`teacher_instructions`) | 5-tier instruction cascade management. |
| `/api/v1/sessions/*` | `routes/sessions.py` | 2 | Yes (`STUDENT`) | Yes (`sessions`) | Tutoring session start, status check. |
| `/api/v1/learning/*` | `routes/learning.py` | 5 | Yes (`STUDENT`, `TEACHER`) | Yes (`learning_events`) | Idempotent event logging, batch sync, recommendation. |
| `/api/v1/assessments/*` | `routes/assessments.py` | 16 | Yes (Role-specific) | Yes (`assessments`, `attempts`, `rubrics`) | Assessment authoring, delivery, grading, adaptive next. |
| `/api/v1/rag/*` | `routes/rag.py` | 7 | Yes (`TEACHER+` for ingest; `ADMIN+` for publish) | Yes (`rag_sources`, `rag_chunks`) | Hybrid semantic/lexical RAG search, document chunking. |
| `/api/v1/ai/*` | `routes/ai.py` | 14 | Yes (`ADMIN+`) | Yes (`ai_providers`, `ai_models`, logs) | Model routing, allowlist, circuit breakers, cost analytics. |
| `/api/v1/analytics/*` | `routes/analytics.py` | 5 | Yes (`TEACHER`, `ADMIN`) | Yes (Aggregate events & mastery) | System, cohort, class, and student analytics. |
| `/api/v1/notifications/*`| `routes/notifications.py`| 7 | Yes (Authenticated user) | Yes (`notifications`) | User notification queue, read acknowledgements. |
| `/api/v1/sync/*` | `routes/sync.py` | 2 | Yes (`STUDENT`, `TEACHER`) | Yes (`sync_operations`) | Bi-directional offline sync outbox batching and replay. |
| `/api/v1/tools/*` | `routes/tools.py` | 3 | Yes (Authenticated) | Yes (`courses`) | Dynamic tool registry inspection and sandboxed execution. |
| `/api/v1/tutor/*` | `routes/tutor.py` | 1 | Yes (`STUDENT`, `TEACHER`) | Yes (Full 16-step orchestrator) | Core interactive 16-step turn execution (`/turn`). |
| `/healthz`, `/readyz`, `/livez` | `central_platform/api/app.py` | 3 | Public (Probes) | Memory / DB ping | Liveness, readiness, uptime diagnostics. |
| Legacy Compatibility | `central_platform/api/app.py` | 11 | Legacy / Public | Mock / Delegated | `/api/health`, `/api/teacher/dashboard`, etc. |

---

## 3. Component Reachability Matrix

| Component | Defined At | Imported By | Runtime Reachable | Production Reachable | Status |
|---|---|---|---|---|---|
| `GenericTutorOrchestrator` | `central_platform/tutor/orchestrator.py` | `central_platform/api/routes/tutor.py`, `app/bridge/facade.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `CourseService` | `central_platform/courses/service.py` | `central_platform/api/routes/courses.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `RAGService` | `central_platform/rag/service.py` | `central_platform/api/routes/rag.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `TeacherInstructionEngine` | `central_platform/teacher/instruction.py` | `central_platform/api/routes/instructions.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `EvaluatorRegistry` | `central_platform/assessment/evaluators.py` | `central_platform/api/routes/assessments.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `ToolRegistry` | `central_platform/tools/registry.py` | `central_platform/api/routes/tools.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `AIGateway` | `central_platform/ai/gateway.py` | `central_platform/api/routes/ai.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `SyncService` | `central_platform/sync/service.py` | `central_platform/api/routes/sync.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `LocalCourseCache` | `central_platform/local_runtime/cache.py`| `app/main.py`, desktop offline handlers | Yes | Yes | **ACTIVE / CANONICAL** |
| `FailureRecoveryManager` | `central_platform/recovery/manager.py` | `tutor/orchestrator.py`, `courses/service.py`, `sync/service.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `SecurityAuditor` | `central_platform/security/auditor.py` | `central_platform/api/routes/tutor.py`, `tutor/orchestrator.py` | Yes | Yes | **ACTIVE / CANONICAL** |
| `PlatformDatabase` | `central_platform/db.py` | All domain services and API route handlers | Yes | Yes | **ACTIVE / CANONICAL** |
| `TeacherPortalHTTPHandler` | `server.py` | `tests/test_server_live_sync.py` | No (API runtime) | No (Offline runtime) | **LEGACY / COMPATIBILITY ONLY** |
