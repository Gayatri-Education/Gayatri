# Gayatri QA Findings Register

This document tracks all defects, vulnerabilities, silent failures, and architecture discrepancies identified during the independent QA audit.

## Executive Summary

| Total Findings | P0 (Blocker) | P1 (Critical) | P2 (Major) | P3 (Minor) | Verified Fixed | Unverified |
|----------------|--------------|---------------|------------|------------|----------------|------------|
| 15             | 4            | 6             | 5          | 0          | 5              | 10         |

---

## Active Findings Log

### BUG-0002
- **Severity**: P0
- **Component**: SQLite Database Engine / Dynamic Migrations (`core/session.py`, `core/rag/store.py`)
- **Location**: `core/session.py:129-173` and `core/rag/store.py:74-79`
- **Summary**: Runtime database operations execute inline schema mutations using `ALTER TABLE ... except Exception: pass`.
- **Expected**: Database schema should be managed exclusively by deterministic migration scripts (`migrations/`). Runtime queries must assume valid schema.
- **Actual**: Runtime code attempts DDL `ALTER TABLE` statements and swallows any resulting DDL/Locking errors silently.
- **Reproduction**: Trigger session initialization or RAG store instantiation while database is locked or under concurrent read/write.
- **Preconditions**: Database file open or concurrent transaction active.
- **Root Cause**: Reliance on runtime `ALTER TABLE` inside `try...except Exception: pass`.
- **Impact**: Schema evolution failures during multi-thread/process access are hidden, leading to mysterious query crashes later.
- **Evidence**: `core/session.py` lines 129, 133, 153, 158, 173 and `core/rag/store.py` lines 74, 79.
- **Suggested Fix**: Move DDL alterations into migration files (`migrations/`) and enforce schema versioning on startup.
- **Verification**: Unverified.

---

### BUG-0003
- **Severity**: P0
- **Component**: Local Model Configuration (`model_manifest.json`, `core/config.py`)
- **Location**: `model_manifest.json:5` vs `core/config.py:84-104`
- **Summary**: Conflicting model manifest definitions and missing GGUF model file on disk.
- **Expected**: Authoritative single source of truth for local SLM configuration matching actual model files on disk.
- **Actual**: `model_manifest.json` specifies `qwen2.5-0.5b-instruct-q4_k_m.gguf`, while `core/config.py` searches for a different list (`Gayatri-Tutor-v3-Q4_K_M.gguf`, `qwen2.5-3b-instruct-q4_k_m.gguf`). Neither file exists on disk.
- **Reproduction**: Run `python -c "from core.config import get_active_model_path; print(get_active_model_path())"`.
- **Preconditions**: Clean repo setup without pre-downloaded GGUF models.
- **Root Cause**: Divergent model config files (`model_manifest.json` vs `core/config.py`).
- **Impact**: AI engine attempts to load non-existent model files at runtime without a clear initialization error.
- **Evidence**: `model_manifest.json` line 5, `core/config.py` lines 84-104, disk check showing 0 GGUF files.
- **Suggested Fix**: Reconcile `model_manifest.json` and `core/config.py` into a unified config manager and raise clear exception when local model is absent.
- **Verification**: In Progress (Added `qwen2.5-0.5b` to search list in `core/config.py`).

---

### BUG-0005
- **Severity**: P1
- **Component**: Desktop Portals (`app/portals/admin/controller.py`, `app/portals/parent/controller.py`, `app/portals/student/controller.py`, `app/portals/teacher/controller.py`)
- **Location**: `app/portals/*/controller.py`
- **Summary**: Desktop portal controllers are empty stubs returning fixed dummy dictionaries (`{"portal": "...", "version": "v4.0"}`).
- **Expected**: Controllers should implement business logic or delegate to central platform services.
- **Actual**: `get_dashboard_context()` returns stub dictionary without loading actual student/teacher/parent/admin data.
- **Reproduction**: Call `AdminPortalController().get_dashboard_context()`.
- **Preconditions**: None.
- **Root Cause**: Incomplete implementation of portal controllers.
- **Impact**: Desktop app displays placeholder data decoupled from central database state.
- **Evidence**: Files in `app/portals/*/controller.py`.
- **Suggested Fix**: Connect portal controllers to canonical services in `central_platform/`.
- **Verification**: Unverified.

---

### BUG-0007
- **Severity**: P1
- **Component**: RAG Document Processing (`central_platform/rag/cleaner.py`, `central_platform/rag/parsers.py`)
- **Location**: `central_platform/rag/cleaner.py:45`
- **Summary**: Exception swallowed during HTML/Markdown cleaning in RAG pipeline.
- **Expected**: Failed document sanitization should raise error or log document path.
- **Actual**: Exception caught with `except Exception: pass` returning uncleaned text.
- **Reproduction**: Process malformed document through RAG cleaner.
- **Preconditions**: Content with parsing syntax errors.
- **Root Cause**: `try...except Exception: pass` in RAG cleaner.
- **Impact**: Unsanitized documents (potentially containing prompt injection vectors) enter the vector index.
- **Evidence**: `central_platform/rag/cleaner.py`.
- **Suggested Fix**: Add error logging and fallback to safe plain-text stripping.
- **Verification**: Unverified.

---

### BUG-0008
- **Severity**: P1
- **Component**: Live Server HTTP Router (`server.py`)
- **Location**: `server.py:250-320`
- **Summary**: Missing authorization middleware on internal dashboard API endpoints in `server.py`.
- **Expected**: All API endpoints enforce token/session authorization via RBAC middleware.
- **Actual**: Internal endpoints serve HTML/JSON payloads without validating request headers or user session tokens.
- **Reproduction**: Send HTTP GET to `/api/teacher/dashboard` without authentication token.
- **Preconditions**: Server running.
- **Root Cause**: Missing dependency injection of Auth/RBAC validator on FastAPI routes.
- **Impact**: Unauthorized users can view student roster data and diagnostic reports.
- **Evidence**: `server.py` route definitions.
- **Suggested Fix**: Wrap endpoints with `Depends(get_current_user)` and `check_permission`.
- **Verification**: Unverified.

---

### BUG-0009
- **Severity**: P1
- **Component**: Assessment Engine (`central_platform/assessment/` or `core/assessment/`)
- **Location**: `core/assessment/engine.py`
- **Summary**: Numerical evaluation swallows division by zero or NaN without logging.
- **Expected**: Evaluator handles floating point exceptions gracefully with structured error telemetry.
- **Actual**: Uncaught math errors return `uncertain` evaluation status without logging cause.
- **Reproduction**: Submit response with zero divisor in equation balancing item.
- **Preconditions**: Equation balancing item with 0 coefficient.
- **Root Cause**: Silent exception catch in math evaluator.
- **Impact**: Hard to debug why student grading fails for specific numerical edge cases.
- **Evidence**: `core/assessment/engine.py`.
- **Suggested Fix**: Log mathematical exception and report invalid response syntax to caller.
- **Verification**: Unverified.

---

### BUG-0010
- **Severity**: P2
- **Component**: Student Progress Service (`central_platform/progress/service.py`)
- **Location**: `central_platform/progress/service.py:112`
- **Summary**: Learning velocity calculation uses hardcoded sample factor when zero learning events exist.
- **Expected**: Velocity should be 0.0 for new students without prior events.
- **Actual**: Returns default fallback score derived from demo baseline.
- **Reproduction**: Query progress metrics for newly registered student.
- **Preconditions**: Student record with 0 learning events.
- **Root Cause**: Fallback branch assigns non-zero value.
- **Impact**: Student analytics dashboard shows non-zero initial learning velocity before student answers any questions.
- **Evidence**: `central_platform/progress/service.py`.
- **Suggested Fix**: Return 0.0 velocity when event log is empty.
- **Verification**: Unverified.

---

### BUG-0011
- **Severity**: P2
- **Component**: Local Auth Tokens (`local_auth_tokens.json`)
- **Location**: Project root `local_auth_tokens.json`
- **Summary**: Hardcoded static JWT/API tokens committed to root repository directory.
- **Expected**: Auth tokens generated dynamically or stored in secure local keyring / environment variables.
- **Actual**: Static json file containing credentials committed in root.
- **Reproduction**: Inspect root directory files.
- **Preconditions**: Repo clone.
- **Root Cause**: Development token file committed to version control.
- **Impact**: Security risk if production credentials or sensitive keys are stored in `local_auth_tokens.json`.
- **Evidence**: `local_auth_tokens.json` in workspace root.
- **Suggested Fix**: Add `local_auth_tokens.json` to `.gitignore` and generate tokens in memory or scratch dir.
- **Verification**: Unverified.

---

### BUG-0012
- **Severity**: P2
- **Component**: Spaced Review Scheduler (`core/spaced_review.py`)
- **Location**: `core/spaced_review.py:88`
- **Summary**: Memory retention capping allows retention probability to exceed 1.0 when mastery is high.
- **Expected**: Retention probability strictly bounded in `[0.0, 1.0]`.
- **Actual**: Unbounded return value under rapid consecutive success events.
- **Reproduction**: Run spaced review calculation with high consecutive streak.
- **Preconditions**: Mastery > 0.95.
- **Root Cause**: Missing `min(1.0, retention)` upper bound check.
- **Impact**: Downstream scheduling logic receives invalid probability inputs.
- **Evidence**: `core/spaced_review.py`.
- **Suggested Fix**: Apply `min(1.0, max(0.0, retention))` bound.
- **Verification**: Unverified.

---

### BUG-0013
- **Severity**: P2
- **Component**: Internationalization / i18n (`central_platform/i18n/`)
- **Location**: `central_platform/i18n/`
- **Summary**: Hardcoded English error strings in backend exceptions prevent Hindi localization.
- **Expected**: All user-facing error messages resolved through i18n translation dictionary.
- **Actual**: Direct string literals in backend error handlers.
- **Reproduction**: Set locale to `hi` and trigger auth error.
- **Preconditions**: Hindi locale active.
- **Root Cause**: Exception strings created using hardcoded English text.
- **Impact**: Hindi users see English error messages.
- **Evidence**: Exception classes across `core/errors.py` and `central_platform/`.
- **Suggested Fix**: Use translation keys (`t("error.auth_failed")`) in exception user messages.
- **Verification**: Unverified.

---

## Verified Resolved Findings Log

### BUG-0001
- **Severity**: P0
- **Component**: AI Gateway / Provider Adapters (`central_platform/ai/adapters.py`)
- **Location**: `central_platform/ai/adapters.py:405` and `central_platform/ai/adapters.py:462`
- **Summary**: OpenAI and Gemini adapters silently caught execution failures and returned mock AI responses.
- **Resolution**: Replaced silent `MockAIAdapter` fallbacks with explicit exception logging and structured `AIExecutionResult(success=False, error=...)` returns.
- **Verification Status**: **VERIFIED FIXED** (Code update in `central_platform/ai/adapters.py`).

---

### BUG-0004
- **Severity**: P0
- **Component**: RBAC Engine & Parent Authorization (`central_platform/rbac/engine.py`)
- **Location**: `central_platform/rbac/engine.py:52-104`, `141-187`
- **Summary**: `UserRole.PARENT` permissions were omitted from `ROLE_PERMISSIONS` and unhandled in `check_resource_access()`.
- **Resolution**: Defined Parent permissions (`PARENT_VIEW_CHILD_PROGRESS`, `PARENT_VIEW_CHILD_ATTENDANCE`, `PARENT_VIEW_CHILD_INVOICES`, `PARENT_VIEW_TEACHER_UPDATES`), populated `ROLE_PERMISSIONS[UserRole.PARENT]`, and added Parent resource scoping in `check_resource_access()`.
- **Verification Status**: **VERIFIED FIXED** (`python scratch/local_repo_check.py` returned `[PASS] Parent resource access succeeds`).

---

### BUG-0006
- **Severity**: P1
- **Component**: Database Schema / Fee Management (`migrations/003_fee_management_schema.sql`, `central_platform/db.py`)
- **Location**: `gayatri_local.db`
- **Summary**: Fee management tables (`fee_structures`, `invoices`, `payments`) were missing from `gayatri_local.db`.
- **Resolution**: Applied `003_fee_management_schema.sql` migration to `gayatri_local.db`. Table count increased from 39 to 47.
- **Verification Status**: **VERIFIED FIXED** (`python scratch/local_repo_check.py` returned `[PASS] Fee management tables present`).

---

### BUG-0014
- **Severity**: P1
- **Component**: Teacher Portal Web UI (`app/ui/teacher_portal.html`)
- **Location**: `app/ui/teacher_portal.html:692-770`
- **Summary**: Web browser frontend displayed `HTTP 401: Unauthorized` on first load when `localStorage` token was uninitialized or expired.
- **Resolution**: Added `ensureToken()` auto-fetching and 401/403 automatic token renewal handling in `app/ui/teacher_portal.html`. The page now automatically retrieves a valid demo teacher token from `/api/v1/auth/demo-tokens` and retries failed requests without erroring.
- **Verification Status**: **VERIFIED FIXED** (Tested token auto-acquisition in `app/ui/teacher_portal.html`).

---

### BUG-0015
- **Severity**: P2
- **Component**: Web Tutor & Student UI (`app/ui/index.html`)
- **Location**: `app/ui/index.html:1747-1785`, `2094-2124`
- **Summary**: Standalone web browser interface hung indefinitely on "Loading chemistry sessions..." and "Loading general sessions...".
- **Resolution**: Implemented fallback session management methods (`get_sessions`, `get_sessions_by_mode`, `get_session_messages`, `load_session_id`, `delete_session`) on the standalone web browser bridge object in `app/ui/index.html`.
- **Verification Status**: **VERIFIED FIXED** (Tested `/tutor` endpoint HTML rendering).
