# Architecture Audit (Phase 02)

## 1. Directory & Layer Mapping
- **`app/`**: Contains the frontend/bridge logic (`bridge/facade.py`). `facade.py` is oversized (~62KB) and acts as a massive mediator between the central server, local DB, and AI core.
- **`central_platform/`**: The new Postgres-backed multi-tenant system. Contains `admin/`, `api/`, `auth/`, `db.py` (massive 100KB+ data model), `models/`, `rag/`, `teacher/`, `rbac/`.
- **`core/`**: The local AI tutor engine. Contains `tutor/`, `learning/`, `rag/`, `inference/`, `assessment/`.
- **`legacy/`**: Old, deprecated codebase components.
- **`scripts/`**: Utility scripts, training generation, and demo scenarios.

## 2. Oversized Modules (God Classes)
- **`central_platform/db.py`** (~100KB): Contains schemas, models, execution logs, organization, user, everything. Needs modularization.
- **`app/bridge/facade.py`** (~62KB): Monolithic bridge controller managing state, networks, and UI telemetry.
- **`server.py`** (~44KB): Root HTTP server.
- **`central_platform/teacher/copilot.py`** (~39KB): Contains massive instructional logic.
- **`central_platform/api/schemas.py`** (~36KB): Giant Pydantic schema dump.

## 3. Duplicate Systems
- **Database & State:** 
  - `core/db.py` uses local SQLite, and `core/tutor/state.py` manages `TutorStateManager`.
  - `central_platform/db.py` uses PostgreSQL, and `central_platform/models/schema.py` contains models like `StudentLearningRecord` and `StudentMisconceptionRecord`.
- **RAG:**
  - `core/rag/` contains local NCERT RAG logic.
  - `central_platform/rag/` contains server-side RAG endpoints.

## 4. Tightly Coupled Code
- `app/bridge/facade.py` tightly couples `central_platform` HTTP API requests with local `core/tutor/controller.py` execution.

## 5. Legacy/Demo Code
- Isolated hardcoded demo student artifacts exist in `core/tutor/adaptive.py` and `core/learning/progress.py`.

## Actionable Requirements for Later Phases
1. **Consolidate State (Phase 11)**: Reconcile SQLite state tracking in `core` with `central_platform` PostgreSQL records.
2. **Refactor Oversized Modules**: Break `central_platform/db.py` and `api/schemas.py` into feature-specific domains (auth, organizations, learning_graph, assessments).
