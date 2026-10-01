# Gayatri System Architecture Map

This document maps all modules, layers, components, data stores, entry points, and dependencies across the Gayatri platform.

## High-Level Component Map

| Component | Location | Purpose | Dependencies | Entry Points | Consumers | Data Stored | External Dependencies | Verification Status |
|-----------|----------|---------|--------------|--------------|-----------|-------------|-----------------------|---------------------|
| FastAPI Server | `server.py` | Main API backend server | `core/`, `app/`, `central_platform/` | `server.py` main | Frontend/Desktop/APIs | Request logs, transient session | Python packages | Unverified |
| Desktop App Bridge | `app/bridge/` | PyQt/PySide GUI bridge facade | `core/` | `facade.py`, `chat.py` | Qt UI Desktop App | Desktop state | Local model files | Unverified |
| Portals (Admin, Parent, Student, Teacher) | `app/portals/` | User role controllers & views | `core/`, `central_platform/` | `controller.py` in each portal | End Users | Portal configurations | None | Unverified |
| Central Platform | `central_platform/` | Central services, RAG, RBAC, Multi-tenancy | DB, SQLite | Modules in `central_platform/` | `server.py`, `app/` | `gayatri_local.db` | Local SLM model | Unverified |
| Core Modules | `core/` | Learning state, graph, AI router, pedagogical policy | Python stdlib, PyTorch/llama.cpp | Engine modules | Server, Bridge, Portals | Learning events, models | Local SLM, PyTorch | Unverified |
| Database | `gayatri_local.db` | SQLite Database | SQLite 3 | `sqlite3` driver | Central platform, Core | Identity, courses, mastery, fees | File system | Unverified |
| Migrations | `migrations/` | Schema migration scripts | SQLite / Python | Run scripts | DB Engine | Schema versions | File system | Unverified |
| Scripts | `scripts/` | System maintenance, setup, verification scripts | Python | CLI commands | Developers/CI | Log outputs | OS CLI | Unverified |

---

## Detailed Directory Breakdown

```text
c:\Users\user\Desktop\gayatri\Gayatri AI - Godess of Knowledge\
├── app/                  # Desktop application & GUI bridge
│   ├── bridge/           # PyQt/Python GUI bridge facades & view controllers
│   └── portals/          # Admin, Parent, Student, Teacher controllers
├── central_platform/     # Core platform backend, auth, tenant isolation, RAG, DB models
├── core/                 # Educational AI engine, learning graph, model routing, prompts
├── data/                 # Datasets, curriculum data, static content
├── docs/                 # Documentation, implementation logs, QA reports
├── legacy/               # Deprecated/archived modules
├── migrations/           # Database migration files
├── packaging/            # Desktop app installers and build setup
├── scripts/              # Verification, setup, and maintenance scripts
├── tests/                # Automated pytest unit, integration, and regression tests
├── server.py             # FastAPI entry point
└── gayatri_local.db      # SQLite local database instance
```
