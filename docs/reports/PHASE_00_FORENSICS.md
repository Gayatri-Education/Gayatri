# Phase 00 — Comprehensive Forensic Architecture Baseline

**Document:** `docs/reports/PHASE_00_FORENSICS.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Execution Context:** Forensic baseline established per Section 48 & Section 78 of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  
**Baseline Date:** 2026-10-01T11:26:00+05:30  
**Active Branch:** `master` at commit `bf47a63273e936b7617937be199e44efb4d9cb5d`  
**Target Head:** `main` at commit `9ca3c652dc0dbcfa4340af351f6b05594c3cae45`  

---

## 1. Executive Forensic Summary

Before any code modifications or structural refactorings are initiated, an exhaustive forensic analysis of the repository was conducted. 

The Gayatri repository currently contains:
- **607 Total Tracked Files** across Python, HTML, CSS, JavaScript, Markdown, SQL, and configuration formats.
- **856 Test Cases** in `tests/`, all passing (exit code 0, 80.32s execution time).
- **0 Bytecode Compilation Errors** across all packages (`app`, `core`, `central_platform`, `tests`, `scripts`).
- **5,188 Linter Warnings / Diagnostics** identified by Ruff.

However, in accordance with the **Non-Negotiable Agent Contract (Section 0)**, a passing test suite is evidence only of the behaviors that existing tests specifically exercise. The forensics revealed 5 critical structural defect classes embedded in the active codebase:
1. **Pervasive Chemistry Hardcoding:** 115 files in generic core and UI layers assume Chemistry as the sole or default domain.
2. **Active Legacy Pipeline Dependency:** 3 production runtime files (`core/inference/service.py`, `core/runtimes/chemistry.py`, `core/runtimes/general.py`) import directly from `legacy.agents.default_agents`.
3. **Hardcoded Demo Users and Fallbacks:** 13 non-test production modules inject fabricated user identities (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`, `local_user_1`).
4. **Dynamic DDL Runtime Mutations:** 5 modules run inline `ALTER TABLE` statements inside silent `try...except Exception: pass` blocks instead of relying on deterministic migration versioning.
5. **Database Migration Schema Duplication:** `migrations/001_initial_schema.sql` contains duplicate `CREATE TABLE IF NOT EXISTS assignments` statements.

---

## 2. Repository & Branch Reconciliation

See full report: [`docs/reports/BRANCH_RECONCILIATION_REPORT.md`](file:///c:/Users/user/Desktop/gayatri/Gayatri%20AI%20-%20Godess%20of%20Knowledge/docs/reports/BRANCH_RECONCILIATION_REPORT.md).

- **Remote Default Branch:** `main` (tracked at `origin/main`).
- **Active Working Branch:** `master` (tracked at `origin/master`).
- **Lineage:** `origin/main` merged `origin/master` up to commit `f74ccbe` (Phase 34). `origin/master` continued forward by 10 commits to commit `bf47a63` (Phase 43 and code review fixes).
- **Unique Commits on `main`:** 0 non-merge commits.
- **Divergence:** `master` is 10 commits ahead of `main`.
- **Safety Measure:** Immutable backup tags `backup-main-9ca3c65` and `backup-master-bf47a63` were created before any modification.

---

## 3. Runtime Entry Points Inventory

A scan for application startup routines, HTTP routers, and process entry points identified 43 entry points across the codebase. Key primary entry points:

1. **Central HTTP API Gateway & Live Server:**
   - Location: `server.py`
   - Framework: FastAPI (`app = FastAPI(...)`)
   - Ports/Modes: Port 8000, provides `/api/v1/*` routes, student & teacher portals, and live telemetry sync.
2. **Desktop GUI Application:**
   - Location: `app/desktop.py` & `app/main.py`
   - Framework: PySide6 (Qt WebEngine / QMainWindow)
   - Function: Native window wrapping local bridge and UI shell.
3. **Database Migration Runner:**
   - Location: `scripts/migrate_db.py`
   - Function: Applies forward migrations (`migrations/*.sql`) and down scripts with SHA-256 checksum tracking.
4. **Local Environment Seeder:**
   - Location: `scripts/seed_local_environment.py`
   - Function: Seeds organizations, courses, users, and fee accounts into `gayatri_local.db`.
5. **Standalone Service Launchers:**
   - `scripts/launch_local_environment.py`: Orchestrates FastAPI server and desktop shell.
   - `scripts/verify_release.py`: Release package integrity and signature validation.

---

## 4. Subsystem Coupling & Architecture Infiltration

See detailed matrix: [`docs/reports/PHASE_00_DEPENDENCY_GRAPH.md`](file:///c:/Users/user/Desktop/gayatri/Gayatri%20AI%20-%20Godess%20of%20Knowledge/docs/reports/PHASE_00_DEPENDENCY_GRAPH.md).

### 4.1 Legacy Infiltration
Despite prior deprecation notices, the `legacy/` directory is actively reached by runtime inference:
- `core/inference/service.py:40` -> `from legacy.agents.default_agents import _local_chat_stream`
- `core/runtimes/chemistry.py:115` -> `from legacy.agents.default_agents import _build_messages, _get_tutor_context`
- `core/runtimes/general.py:68` -> `from legacy.agents.default_agents import _build_messages`

**Mandatory Target:** All AI inference must route strictly through `central_platform.ai` (AI Gateway -> Model Router -> Provider Adapters). Zero imports from `legacy` may remain, after which `legacy/` will be deleted.

### 4.2 Chemistry Domain Coupling
115 files exhibit tight coupling to Chemistry. Examples of coupling in generic platform paths:
- `core/curriculum/`: Hardcodes concept names such as `hesss_law`, `gibbs_free_energy`, `ionization_enthalpy`.
- `core/tutor/chemistry_tools.py`: Placed under generic tutor core rather than an adapter package.
- `app/ui/index.html`: Contains hardcoded UI tabs and strings for "Chemistry sessions" alongside "General sessions".
- `app/bridge/facade.py`: Defaults `course_id="crs-chem-101"` and `chapter="thermodynamics"`.

**Mandatory Target:** Generic core (`core/`, `central_platform/`) must be agnostic to subjects. Chemistry must be extracted cleanly into `adapters/chemistry/`.

### 4.3 Hardcoded Demo Roster & Data Infiltration
The production runtime and application bridge contain hardcoded mock users:
- `app/bridge/facade.py` defines static lists of students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`) and mock grades.
- `server.py` falls back to `local_user_1` and `local_student_1`.
- `core/session.py` defaults `user_id` to `'local_user_1'`.

**Mandatory Target:** Strict prohibition of hardcoded fake data in production code. Empty states must be displayed when no data exists. Demo seed data must reside solely in fixtures or seed scripts.

---

## 5. Database Schema & Migration Forensics

### 5.1 Migration History
1. `migrations/001_initial_schema.sql` (21,990 bytes): Initial 40-table DDL.
   - **Defect Identified:** `CREATE TABLE IF NOT EXISTS assignments` appears twice (line 351 and line 448).
2. `migrations/002_curriculum_abstraction.sql` (254 bytes): Added `board` and `metadata` columns to `curricula`.
3. `migrations/003_fee_management_schema.sql` (6,183 bytes): Added 8 fee management tables.

### 5.2 Dynamic Schema Mutations
In parallel with official migrations, 4 runtime modules invoke inline `ALTER TABLE` statements inside `try...except Exception: pass`:
- `core/session.py` (adds `mode`, `user_id`, `profile_id`, `summary`, dynamic context columns).
- `core/rag/store.py` (adds `section`, `provenance_type`).
- `core/tutor/state.py` (adds `hint_count`, `learning_status`).

**Mandatory Target:** Zero runtime DDL statements. Database schemas must be fully defined and versioned via migration scripts.

---

## 6. Configuration Forensics

### 6.1 Model Configuration Contradictions
- `model_manifest.json` specifies `qwen2.5-0.5b-instruct-q4_k_m.gguf`.
- `core/config.py` searches a sequence of alternative names (`Gayatri-Tutor-v3-Q4_K_M.gguf`, `qwen2.5-3b-instruct-q4_k_m.gguf`).
- Neither GGUF file exists by default on a fresh clone.
- Provider configurations contain different fallback and prompt templates across `core/inference/` and `central_platform/ai/`.

**Mandatory Target:** Single authoritative model registry/manifest where metadata, capabilities, context windows, and paths are centrally declared.

---

## 7. Deliverables Checklist for Phase 00

| Deliverable | Status | Location |
|---|---|---|
| Branch Reconciliation Report | COMPLETE | `docs/reports/BRANCH_RECONCILIATION_REPORT.md` |
| Forensic Architecture Baseline | COMPLETE | `docs/reports/PHASE_00_FORENSICS.md` |
| File Inventory (607 files) | COMPLETE | `docs/reports/PHASE_00_FILE_INVENTORY.csv` |
| Dependency Graph & Coupling Analysis | COMPLETE | `docs/reports/PHASE_00_DEPENDENCY_GRAPH.md` |
| Initial Test Baseline Report | COMPLETE | `docs/reports/PHASE_00_TEST_BASELINE.md` |
| Initial Test Results JSON | COMPLETE | `docs/reports/PHASE_00_TEST_RESULTS.json` |
| Development Log (Append-Only) | INITIALIZED | `docs/reports/DEVELOPMENT_LOG.md` |
| Bug Register | INITIALIZED | `docs/reports/BUG_REGISTER.md` |
| Requirements Traceability Matrix | INITIALIZED | `docs/reports/REQUIREMENTS_TRACEABILITY.md` |
| GitHub Remote Sync Queue | INITIALIZED | `docs/reports/GITHUB_SYNC_QUEUE.md` |
| Authoritative Project State | UPDATED | `PROJECT_STATE.yaml` |

Phase 00 forensic baseline is fully documented. The repository is ready to proceed to **Phase 1: Architecture Freeze**.
