# Phase 00 Execution Plan — Forensic Baseline & Branch Reconciliation

**Document:** `docs/reports/PHASE_00_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master` (SHA: `bf47a63`) vs `main` (SHA: `9ca3c65`)  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Establish an unyielding, forensic baseline of the Gayatri codebase before initiating any feature refactoring. Determine canonical branch authority, map runtime call graphs, catalog hardcoded Chemistry assumptions, identify active legacy imports, verify database schema integrity, and document exact test suite results across all 856 tests.

---

## 2. Discovery Scope & Modules to Audit

1. **Git Lineage & Branches:**
   - `origin/main` vs `origin/master` ahead/behind metrics, commit log graph, and remote HEAD pointer.
2. **File Tree & Inventory:**
   - 607 tracked files classified as: `ACTIVE`, `TEST_ONLY`, `LEGACY`, `DUPLICATE`, `OBSOLETE`, or `UNKNOWN`.
3. **Runtime Call Graphs & Entry Points:**
   - Desktop application path: `app/main.py` $\rightarrow$ `app/desktop.py` $\rightarrow$ `app/bridge/facade.py` $\rightarrow$ `core/orchestrator.py` $\rightarrow$ `core/inference/service.py`.
   - Central HTTP API path: `server.py` $\rightarrow$ `central_platform/api/*` $\rightarrow$ `central_platform/ai/*` $\rightarrow$ `central_platform/db.py`.
4. **Configuration Consistency:**
   - Reconcile `model_manifest.json` (`qwen2.5-0.5b-instruct-q4_k_m.gguf`) with `core/config.py` search list and disk presence.
5. **Database Schema & Migrations:**
   - `migrations/001_initial_schema.sql`, `002_curriculum_abstraction.sql`, `003_fee_management_schema.sql`.
   - Inventory dynamic runtime `ALTER TABLE` statements in `core/session.py`, `core/rag/store.py`, `core/tutor/state.py`.
6. **Chemistry Domain Coupling:**
   - Enumerate all occurrences of `chemistry`, `thermodynamics`, `hess`, `ncert`, `chemical`, `crs-chem-101` in generic core and UI paths.
7. **Legacy Reachability:**
   - Enumerate all active runtime callers of `legacy/` (`core/inference/service.py`, `core/runtimes/chemistry.py`, `core/runtimes/general.py`).
8. **Test Suite Baseline:**
   - Execute `python -m pytest -q --tb=short` (856 tests).
   - Execute `python -m compileall app core central_platform tests scripts`.
   - Execute `ruff check central_platform core app --statistics`.

---

## 3. Planned Deliverables

| Deliverable | Purpose |
|---|---|
| `docs/reports/BRANCH_RECONCILIATION_REPORT.md` | Formal branch comparison between `main` and `master`. |
| `docs/reports/PHASE_00_FORENSICS.md` | Comprehensive forensic architecture report. |
| `docs/reports/PHASE_00_FILE_INVENTORY.csv` | Full file manifest with sizes, line counts, and categories. |
| `docs/reports/PHASE_00_RUNTIME_GRAPH.md` | Architectural runtime traces for desktop and server. |
| `docs/reports/PHASE_00_CONFIG_AUDIT.md` | Authoritative model and environment configuration audit. |
| `docs/reports/PHASE_00_SCHEMA_AUDIT.md` | DDL migrations vs dynamic inline runtime schema mutations. |
| `docs/reports/PHASE_00_CHEMISTRY_COUPLING.md` | Catalog of 115 Chemistry-coupled files outside adapters. |
| `docs/reports/PHASE_00_LEGACY_REACHABILITY.md` | Proof of callers importing from `legacy.agents.default_agents`. |
| `docs/reports/PHASE_00_TEST_BASELINE.md` | Exact test results and environment baseline. |
| `docs/reports/PHASE_00_TEST_RESULTS.json` | Machine-readable Pytest execution report. |
| `PROJECT_STATE.yaml` | Authoritative single-source-of-truth project tracking file. |
| `docs/reports/DEVELOPMENT_LOG.md` | Append-only ledger of changes and bug discoveries. |
| `docs/reports/BUG_REGISTER.md` | Formal bug register tracking P0-P3 architectural defects. |
| `docs/reports/REQUIREMENTS_TRACEABILITY.md` | Traceability matrix from requirements to tests. |
| `docs/reports/GITHUB_SYNC_QUEUE.md` | Queue of remote actions for GitHub synchronization. |

---

## 4. Phase 00 Acceptance Gate

Phase 00 is considered `VERIFIED` and ready to transition to Phase 01 when:
1. Canonical branch selection is justified by immutable git evidence.
2. Backup references (`backup-master-bf47a63`, `backup-main-9ca3c65`) are established.
3. All 856 tests pass with 0 bytecode compile errors.
4. All 15 forensic and tracking documents are written with empirical data.
5. No code refactoring or architecture modifications have been introduced prematurely.
