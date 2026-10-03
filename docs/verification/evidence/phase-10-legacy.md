# Phase 10 Verification Evidence: Legacy, Dead Ends and False-Green Paths

## 1. Executive Summary

Phase 10 of the forensic remediation plan addresses legacy code debt, circular/reverse import dependencies, unauthenticated demo endpoints, silent exception swallowing, and route verification completeness:
- **Canonical ASGI Production Server Entrypoint**: Created `central_platform.api.server` as the single canonical ASGI server entrypoint exporting `app` and `run_server` via `uvicorn`. Root `server.py` is refactored into a thin backwards-compatibility shim delegating `run_server` to `central_platform.api.server:run_server`.
- **Zero Reverse Dependencies**: Completely eliminated all reverse imports (`from server import ...`) from `central_platform/` (`app.py`, `teachers.py`, `students.py`, `sync.py`). The core platform architecture is now strictly layered and independent.
- **Teacher Dashboard HTML View Extraction**: Extracted `HTML_TEMPLATE` and `render_teacher_dashboard_html` from `server.py` into a modular platform package `central_platform.teacher.views`.
- **Shared Portal Service Architecture**: Decoupled default `TeacherPortalService` instances (clean, 0 mock students for unit/e2e tests) from the interactive web platform routes via `get_shared_portal_service()` with explicit seeding, ensuring complete backward compatibility across existing API tests and offline runtime tests without conflict.
- **Production Gating for Demo Tokens**: Gated `/api/v1/auth/demo-tokens` with `is_production_mode()`. In development/testing it provides convenient access, but in production (`GAYATRI_ENV=production`) it returns HTTP 404 Not Found to prevent credential leakage.
- **Silent Exception Swallowing Elimination**: Replaced bare `except: pass` blocks in `central_platform/sync/service.py` with structured diagnostic logging with exception tracing (`logger.debug(..., exc_info=True)`).
- **Route Reachability Matrix**: Generated authoritative `docs/verification/ROUTE_REACHABILITY_MATRIX.md` covering all 64 API and web endpoints across 11 required dimensions.
- **Zero Regressions**: Entire test suite of 1,235 tests passes cleanly with 0 failures and 0 errors.

---

## 2. Invariants Certified

| ID | Invariant | Enforcement Mechanism | Verification Status |
|---|---|---|---|
| **I1** | **Canonical Production Entrypoint** | `central_platform.api.server` exports `app` and `run_server` | **PASS** (`test_canonical_server_entrypoint_exists_and_exports_app`) |
| **I2** | **Zero Reverse Imports** | `central_platform/` contains zero import references to root `server` | **PASS** (`test_zero_server_imports_in_central_platform`) |
| **I3** | **Root server.py Delegation** | `server.py` delegates server execution to `central_platform.api.server` | **PASS** (`test_server_py_delegates_to_central_platform`) |
| **I4** | **Production Demo Token Gating** | `/api/v1/auth/demo-tokens` returns HTTP 404 when `GAYATRI_ENV=production` | **PASS** (`test_demo_tokens_disabled_in_production_mode`) |
| **I5** | **Route Reachability Documentation** | `ROUTE_REACHABILITY_MATRIX.md` exists and covers all required dimensions | **PASS** (`test_route_reachability_matrix_file_exists_and_complete`) |
| **I6** | **Teacher View Renderer Independence** | `render_teacher_dashboard_html` operates independently without root `server.py` | **PASS** (`test_teacher_dashboard_view_renderer_independence`) |
| **I7** | **Zero Endpoint Divergence** | `/api/health` and `/api/v1/teachers/dashboard` maintain backward-compatible parity | **PASS** (`test_zero_divergence_fastapi_and_legacy_endpoints`) |
| **I8** | **No Bare Swallowed Exceptions** | Active sync service methods log diagnostics instead of silent suppression | **PASS** (`test_active_services_have_no_bare_swallowed_exceptions`) |

---

## 3. Modified and Created Files

- `central_platform/api/server.py` (NEW) — Canonical production ASGI entrypoint with `run_server` using uvicorn.
- `central_platform/teacher/views.py` (NEW) — Extracted dashboard HTML template and renderer.
- `central_platform/teacher/portal.py` — Added `seed_demo_teacher_roster` and `get_shared_portal_service()` for platform API routes; re-exported dashboard view renderer.
- `central_platform/api/app.py` — Removed reverse `server.py` imports; uses `get_shared_portal_service()` and `central_platform.teacher.views`.
- `central_platform/api/routes/teachers.py` — Removed reverse `server.py` imports; uses `get_shared_portal_service()`.
- `central_platform/api/routes/students.py` — Removed reverse `server.py` imports; uses `get_shared_portal_service()`.
- `central_platform/api/routes/sync.py` — Removed reverse `server.py` sync manager import.
- `central_platform/auth/dependencies.py` — Added `is_production_mode()` helper function.
- `central_platform/api/routes/auth.py` — Gated `/api/v1/auth/demo-tokens` to return 404 in production mode.
- `central_platform/sync/service.py` — Replaced bare `except: pass` blocks with structured exception logging.
- `server.py` — Re-exports views from `central_platform.teacher.views`; `run_server` delegates to `central_platform.api.server`.
- `docs/verification/ROUTE_REACHABILITY_MATRIX.md` (NEW) — Comprehensive 11-column route reachability matrix covering all 64 endpoints.
- `tests/test_phase10_legacy_routes_audit.py` (NEW) — 8-test regression and architectural compliance test suite.

---

## 4. Test Suite Execution Summary

- Total Repository Tests: **1,235 passed**
- Failures: **0**
- Errors: **0**
- Passing Rate: **100%**
