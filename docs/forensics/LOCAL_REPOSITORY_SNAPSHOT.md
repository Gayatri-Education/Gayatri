# Authoritative Local Repository Forensic Snapshot

**Audit Date:** 2026-10-02T15:55:00+05:30  
**Target Repository:** `Gayatri-Education/Gayatri`  
**Authoritative Local Commit:** `HEAD` (reconciled)  
**Safety Branch:** `forensic/local-truth-safety` (SHA `210d844495dab49b4f06d0bb4fb14387ef5ba5d9`)  
**Overall Release Status:** `RECONCILED_BUT_NOT_RELEASE_READY`  

---

## 1. Local File Classification & Inventory

The repository files have been exhaustively classified as follows:

| Category | Directories / Files | Description |
|---|---|---|
| **SOURCE** | `central_platform/`, `app/`, `core/`, `server.py` | 50 packages, 280+ Python source modules implementing backend, orchestrator, RAG, and shell. |
| **CONFIGURATION** | `pyproject.toml`, `model_manifest.json`, `.github/workflows/ci.yml`, `.gitignore` | Build metadata, model manifests, CI definitions, git exclusion rules. |
| **DEPENDENCY** | `requirements.txt`, `requirements.lock` | Runtime and dev dependency specifications. |
| **TEST** | `tests/` (1,114 tests) | Comprehensive test suite spanning unit, integration, architecture guardrails, and failure recovery. |
| **DATA** | `migrations/` (001-008 SQL scripts), `data/curriculum/` | SQL DDL migrations (50 tables) and reference curriculum schemas. |
| **MODEL** | `central_platform/models/`, `core/model_fetch/` | Authoritative Python dataclasses, schemas, and model fetch utilities. |
| **UI** | `app/ui/` | Shared design system, dark/light theme tokens, and HTML/CSS/JS presentation templates. |
| **BUILD / DEPLOYMENT**| `scripts/`, `central_platform/deployment/` | Packaging scripts, installer generators, and deployment validation CLI. |
| **DOCUMENTATION** | `README.md`, `docs/`, `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` | Architecture specs, data model, security policies, and phase logs. |
| **HISTORICAL / ARCHIVED**| `PROGRESS_TRACKER.yaml`, `CURRENT_REPO_AUDIT.md`, `FILE_DEPENDENCY_MAP.md`, `CLEANUP_REPORT.md` | Retained historical artifacts from earlier Chemistry Tutor iterations (Phase 00-09). |
| **GENERATED / TEMP** | `test_*.db`, `gayatri_local.db`, `__pycache__/`, `.pytest_cache/` | Local SQLite databases and bytecode caches (strictly gitignored). |
| **SCRATCH** | `scratch/` | Temporary scratch files (strictly gitignored). |
| **SECRET / PRIVATE** | `.env` | Protected by `.gitignore`; no API keys or private certificates exist in tracked files. |

---

## 2. Silent Failure & Exception Swallowing Audit

A full AST audit of all `try-except` blocks across `central_platform/` and `app/` identified 34 handlers with empty bodies or immediate returns:

| File & Line | Pattern | Handled Exception | Classification | Audit Finding |
|---|---|---|---|---|
| `central_platform/db.py:595` | `return []` | `sqlite3.OperationalError` | **SAFE** | Returns empty list when querying nonexistent schema tables during startup probe. |
| `central_platform/ai/adapters.py:332` | `return AIExecutionResult(...)` | `Exception` | **SAFE** | Returns failure object with error message; does not swallow or fake success. |
| `central_platform/analytics/service.py:29` | `return None` | `Exception` | **SAFE** | Helper `_parse_iso` returning `None` on malformed timestamp string. |
| `central_platform/learning/mastery.py:66` | `return None` | `Exception` | **SAFE** | Helper `_parse_iso` returning `None` on malformed timestamp string. |
| `central_platform/assessment/evaluators/code.py:57`| `return EvaluationOutcome(INCORRECT...)` | `SyntaxError` | **INTENTIONAL** | Treats invalid student code syntax as a deterministic incorrect attempt with feedback. |
| `central_platform/tools/adapters/programming.py:193`| `return ToolExecutionResult(success=False...)`| `Exception` | **SAFE** | Sandboxed tool execution failure capturing stderr. |
| `central_platform/recovery/manager.py:402-444` | `pass` | `json.JSONDecodeError` | **INTENTIONAL** | Multi-strategy JSON repair parser trying regex and AST fallbacks sequentially. |
| `central_platform/teacher/instruction.py:397` | `return True` | `Exception` | **AUDITED** | BUG-23A fix verified; returns `True` only if timestamp parsing fails, logging diagnostic. |
| `central_platform/auth/tokens.py:123` | `return False` | `Exception` | **SAFE** | Returns `False` on invalid token signature verification. |

**Audit Conclusion:** No unhandled dangerous false-success paths (e.g. fake counts, silent database fallback to fake data, or artificial passing grades) remain in active execution paths.

---

## 3. Identity, Tenant & Course Isolation Audit

An exhaustive search for hardcoded magic identifiers (`local_user_1`, `local_student_1`, `student_001`, `teacher_1`, `tchr-101`, `org-default`, `crs-chem-101`) revealed:

1. **Core Orchestrator (`central_platform/tutor/orchestrator.py`)**:
   - **Zero hardcoded IDs.**
   - All turn operations strictly require dynamic `student_id`, `course_id`, and `course_offering_id` validated against active enrollments in the database.
2. **Course Service (`central_platform/courses/service.py`)**:
   - **Zero hardcoded IDs.**
   - Multi-tenant organizational isolation is strictly enforced via `tenant_id` query parameters.
3. **Legacy Fallback Shims**:
   - In `central_platform/auth/dependencies.py` (lines 104), tokens without an explicit `org_id` fall back to `"org-default"`.
   - In 38 legacy route or test compatibility modules, query parameters default to `"crs-chem-101"` when optional `course_id` is omitted by legacy clients.
   - In `app/bridge/facade.py` and `core/session.py`, desktop single-user mode defaults to `"local_user_1"`.

---

## 4. Chemistry Domain vs Generic Platform Audit

- **Generic Courses Architecture (`central_platform/courses/`)**: 100% verified free of Chemistry coupling by architecture guardrail `test_courses_domain_zero_chemistry_coupling`.
- **Chemistry Domain Adapter (`central_platform/adapters/chemistry/` & `tools/adapters/chemistry.py`)**: Dedicated, decoupled adapters encapsulating chemical equation balancing, IUPAC naming, and stoichiometry.
- **Residual Keyword Audit**: 38 files outside the adapters package contain residual references to "Chemistry", "Thermodynamics", or "Hess" (primarily in default query parameters, sample catalog entries, or diagnostic misconception strings). These represent legacy test/demo fixtures rather than structural architectural coupling.

---

## 5. Documentation Status & Authority Matrix

| Document | Classification | Authority | Current Status | Description |
|---|---|---|---|---|
| `README.md` | `CURRENT` | **AUTHORITATIVE** | Accurate | System overview, 1,114 tests passed, 23 phases verified, setup guide. |
| `PROJECT_STATE.yaml` | `CURRENT` | **AUTHORITATIVE** | Accurate | Machine-readable project state reflecting verified local truth. |
| `docs/ARCHITECTURE.md` | `CURRENT` | **AUTHORITATIVE** | Accurate | System architecture specification covering the 16-step orchestrator. |
| `docs/DATA_MODEL.md` | `CURRENT` | **AUTHORITATIVE** | Accurate | 50 relational tables across migrations 001-008 and dataclasses. |
| `docs/SECURITY_MODEL.md`| `CURRENT` | **AUTHORITATIVE** | Accurate | 6-role RBAC hierarchy, multi-tenant isolation, prompt defense. |
| `docs/forensics/*` | `CURRENT` | **AUTHORITATIVE** | Accurate | Authoritative forensic evidence documents (Git, Deps, Matrix, Tests, Snapshot). |
| `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` | `CURRENT` | **AUTHORITATIVE** | Reference | Master execution roadmap guiding all phases. |
| `PROGRESS_TRACKER.yaml` | `HISTORICAL` | Non-Authoritative | Stale | Old Chemistry Tutor tracker (Phase 26, 269 tests) from 2026-09-20. |
| `CURRENT_REPO_AUDIT.md` | `HISTORICAL` | Non-Authoritative | Stale | Initial repository forensic audit from 2026-09-20. |
| `FILE_DEPENDENCY_MAP.md` | `HISTORICAL` | Non-Authoritative | Stale | Legacy 85-file dependency map from 2026-09-20. |
| `CLEANUP_REPORT.md` | `HISTORICAL` | Non-Authoritative | Stale | Historical cleanup log from earlier iteration. |

---

## 6. Open Finding & Defect Register

| ID | Severity | Category | Description | Remediation / Status |
|---|---|---|---|---|
| **FINDING-001** | **P1 (High)** | Packaging / CI | `requirements.txt` lacked 7 runtime dependencies (`fastapi`, `uvicorn`, `pyjwt`, `psutil`, `rank-bm25`, `pypdf`, `pymupdf`), causing remote GitHub Actions CI to fail. | **FIXED in this task.** Added declarations to `requirements.txt` and `pyproject.toml`. |
| **FINDING-002** | **P1 (High)** | Packaging | `pyproject.toml` excluded `central_platform` and `adapters` from setuptools package finding. | **FIXED in this task.** Updated `include = ["app*", "core*", "central_platform*", "adapters*", "tests*"]`. |
| **FINDING-003** | **P2 (Medium)** | Architecture | `central_platform/api/app.py` imported from legacy `server.py`, causing automatic demo cohort seeding when importing the FastAPI app. | **FIXED in this task.** Decoupled `central_platform/api/app.py` to instantiate its own domain services directly. |
| **FINDING-004** | **P2 (Medium)** | CI Configuration | `.github/workflows/ci.yml` lacked `QT_QPA_PLATFORM: offscreen` on Windows runner, risking headless display initialization crashes. | **FIXED in this task.** Added environment variable to CI headless test step. |
| **FINDING-005** | **P3 (Low)** | Code Cleanliness | 38 non-adapter files retain residual default parameter values referencing `"crs-chem-101"` or `"org-default"`. | **OPEN / BACKLOG.** To be cleaned during Phase 24 End-to-End migration. |
| **FINDING-006** | **P3 (Low)** | Documentation | Legacy tracking files (`PROGRESS_TRACKER.yaml`, `CURRENT_REPO_AUDIT.md`, `FILE_DEPENDENCY_MAP.md`) display obsolete metrics from 2026-09-20. | **CLASSIFIED AS HISTORICAL.** Preserved for audit provenance; authoritative status is exclusively in `PROJECT_STATE.yaml` and `docs/forensics/`. |
