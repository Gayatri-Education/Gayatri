# Phase 20 Implementation & Test Plan: Legacy Removal & Dead-Code Cleanup

**Document:** `docs/reports/PHASE_20_PLAN.md`  
**Phase:** 20  
**Section:** 12.20 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  

---

## 1. Objective

Safely remove deprecated, dead, and obsolete code assets after reachability proof rather than preserving indefinite compatibility shims.

Per Section 12.20:
- Build production import graph and test reference graph before deletion.
- Classify each candidate: identify replacement, verify zero callers.
- Delete only proven-unused code.
- Clean up:
  1. `legacy/` directory (`legacy/agents/default_agents.py`, `legacy/agents/__init__.py`, `legacy/__init__.py`).
  2. Dead configuration flags (`FEATURE_FLAGS = {"enable_legacy_agents": False}` in `core/config.py`).
  3. Stale scratch files in `scratch/` (temporary inspection scripts, old forensic json dumps, and leftover sqlite database `test_migrations.db`).
- Preserve all test fixtures, historical test reports, migrations, and active domain adapters.

---

## 2. Inventory & Classification Matrix

| Path | Category | Production Callers | Test Callers | Replacement | Action |
|---|---|---|---|---|---|
| `legacy/agents/default_agents.py` | Deprecated Agent Shim | 0 | 0 | `core.inference.service`, `core.inference.context` | **DELETE** |
| `legacy/agents/__init__.py` | Deprecated Package | 0 | 0 | None needed | **DELETE** |
| `legacy/__init__.py` | Deprecated Package Root | 0 | 0 | None needed | **DELETE** |
| `core/config.py` (`FEATURE_FLAGS`) | Dead Config | 0 | 0 | `config.py` core settings | **REMOVE DEAD FLAG** |
| `scratch/*.py` | Stale Diagnostics | 0 | 0 | `docs/reports/` documentation | **DELETE** |
| `scratch/*.json` | Stale Analysis Dumps | 0 | 0 | `docs/reports/` documentation | **DELETE** |
| `scratch/test_migrations.db` | Stale Temp SQLite DB | 0 | 0 | In-memory sqlite in tests | **DELETE** |

---

## 3. Architecture Guard & Verification

1. Enhance `tests/architecture/test_anti_legacy_imports.py` to assert that `legacy/` directory is completely eliminated from the filesystem.
2. Verify zero active code imports from `legacy/` or `scratch/`.
3. Create comprehensive test suite `tests/test_phase20_legacy_removal_dead_code_cleanup.py`:
   - Verify `legacy/` directory does not exist.
   - Verify zero modules import `legacy.*`.
   - Verify dead configuration `enable_legacy_agents` is absent from active runtime config.
   - Verify inference service, context builder, and providers execute normally without `legacy`.
   - Verify clean module imports across `core`, `central_platform`, `app`, and `local_runtime`.
   - Verify full platform startup and health check endpoints.
4. Execute full regression suite (all 1,065+ tests passing, 0 regressions).
