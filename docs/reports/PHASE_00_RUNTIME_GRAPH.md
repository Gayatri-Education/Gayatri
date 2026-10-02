# Phase 00 — Runtime Call Graph & Entry Points Audit

**Document:** `docs/reports/PHASE_00_RUNTIME_GRAPH.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Inspection Date:** 2026-10-01  
**Commit SHA:** `bf47a63`  

---

## 1. Runtime Entry Points Architecture

The Gayatri repository currently hosts two distinct runtime execution architectures:
1. **Desktop Client Runtime (PySide6 / Qt WebEngine):** Local-first tutoring interface running locally on student/teacher machines.
2. **Central Platform API Gateway (FastAPI):** Multi-tenant centralized backend service running on port 8000.

---

## 2. Desktop Client Runtime Call Graph

```text
app/main.py
    │
    ▼
app/desktop.py (GayatriTutorApp / QMainWindow)
    │
    ├─► Embedded WebEngineView (`app/ui/index.html`)
    │
    ▼
app/bridge/facade.py (DesktopBridgeFacade)
    │
    ├─► [ISSUE: Hardcoded Demo Data] Injects mock students ("Rahul Kumar", "Priya Sharma", "Amit Patel")
    │
    ├─► core/orchestrator.py (TutorOrchestrator)
    │       │
    │       ├─► core/curriculum/resolver.py (Resolves concept names via hardcoded keyword dictionaries)
    │       │
    │       ├─► core/rag/retriever.py (Hybrid RAG over local sqlite `core/rag/store.py`)
    │       │
    │       ▼
    │   core/inference/service.py (InferenceService)
    │       │
    │       ▼
    │   [CRITICAL DEFECT] legacy.agents.default_agents._local_chat_stream
    │
    └─► core/session.py (SessionStore)
            │
            ▼
        [CRITICAL DEFECT] Inline dynamic DDL: `ALTER TABLE sessions ADD COLUMN ...`
```

---

## 3. Central Platform API Gateway Call Graph

```text
server.py (FastAPI Application on :8000)
    │
    ├─► central_platform/api/routes/auth.py (JWT Authentication & Demo Token Dispenser)
    │
    ├─► central_platform/api/routes/tutor.py
    │       │
    │       ├─► central_platform/ai/query_understanding.py (Structured intent extraction)
    │       │
    │       ├─► central_platform/ai/context_builder.py (Layered context assembly)
    │       │
    │       ├─► central_platform/ai/model_router.py (Local-First vs Cloud router)
    │       │       │
    │       │       ├─► central_platform/ai/adapters.py (OpenAI, Gemini, Anthropic, Mock)
    │       │       └─► local llama.cpp SLM router
    │       │
    │       ├─► central_platform/ai/response_validator.py (Pedagogical invariants checks)
    │       │
    │       └─► central_platform/learning/commit_pipeline.py (Two-phase state commit)
    │               │
    │               ├─► central_platform/learning/mastery.py (Multi-factor mastery engine)
    │               │
    │               └─► central_platform/db.py (PlatformDatabase)
    │
    ├─► central_platform/api/routes/portals.py (Student, Teacher, Parent, Fee Admin endpoints)
    │
    └─► central_platform/sync/service.py (Offline outbox event sync and telemetry)
```

---

## 4. Key Architectural Breakages & Inconsistencies Identified

1. **Dual Orchestration Split:**
   - The desktop app uses `core/orchestrator.py` which bypasses `central_platform/ai` and routes into `legacy.agents.default_agents`.
   - The server API uses `central_platform/ai/context_builder.py` and `central_platform/ai/model_router.py`.
   - **Target Unification:** All execution must converge under the unified `Generic Tutor Core` and `AI Gateway`.

2. **Database Access Divergence:**
   - `core/session.py` maintains an independent SQLite connection with inline dynamic schema mutations (`ALTER TABLE`).
   - `central_platform/db.py` maintains a structured multi-tenant schema with versioned migrations (`migrations/`).
   - **Target Unification:** Eliminate `core/session.py` inline mutations; route all storage through canonical repositories backed by migration scripts.
