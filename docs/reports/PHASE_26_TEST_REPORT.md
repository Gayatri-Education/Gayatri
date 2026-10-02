# Phase 26 Test Report: Packaging, Clean Install & Deployment Validation

```text
commit SHA: 7a2242f
branch: master
timestamp: 2026-10-02T13:12:29Z
environment: Local clean test environment & Windows runner
python: 3.12.10
OS: Windows 11 (win32)
dependencies: pytest-7.4.4, fastapi, pydantic, sqlite3, cryptography
command: pytest tests/test_phase26_packaging_clean_install.py -v
scope: Packaging, release integrity, clean install, lifecycle replay, subsystem probes, and script hygiene
collected: 7
passed: 7
failed: 0
skipped: 0
xfailed: 0
duration: 13.30s
coverage: Full clean install lifecycle, packaging verification, live probing, and script validation
result: PASSED
```

---

## 1. Test Suite Summary

All 7 test cases covering the Phase 26 master plan specifications passed cleanly.

| Test ID | Test Name | Status | Duration | Requirement |
|---|---|---|---|---|
| **T-26.1** | `test_packaging_completeness_and_manifest` | **PASSED** | 4.12s | REQ-26.1 |
| **T-26.2** | `test_release_integrity_verification_signed_and_unsigned` | **PASSED** | 4.25s | REQ-26.2 |
| **T-26.3** | `test_clean_environment_bootstrap_and_migrations` | **PASSED** | 1.15s | REQ-26.3 |
| **T-26.4** | `test_clean_lifecycle_provision_publish_turn_restart` | **PASSED** | 1.82s | REQ-26.6 |
| **T-26.5** | `test_deployment_validator_real_subsystem_probes` | **PASSED** | 0.95s | REQ-26.4 |
| **T-26.6** | `test_deployment_validator_secret_enforcement` | **PASSED** | 0.05s | REQ-26.5 |
| **T-26.7** | `test_setup_and_launch_scripts_integrity` | **PASSED** | 0.03s | REQ-26.7 |

---

## 2. Issues Discovered and Remediated During Phase 26

### Issue 1: Packaging Omission of Core Architecture
- **Root Cause:** `scripts/package_release.py` hardcoded `include_dirs = ["app", "core", "data", "docs", "legacy"]`, omitting `central_platform`, `migrations`, and `scripts`.
- **Fix:** Added `central_platform`, `migrations`, and `scripts` to `include_dirs`, plus `model_manifest.json` and `LICENSE.md` to `include_files`.
- **Verification:** Package builder bundled 566 files and verified complete inclusion.

### Issue 2: Mocked Health Check Probes in Deployment Validator
- **Root Cause:** `central_platform/deployment/validator.py` returned hardcoded `"UP"` strings for `database`, `ai_gateway`, `rag_service`, `payments_gateway`, and `i18n_registry` without performing live probes.
- **Fix:** Replaced simulated strings with live probes:
  - Database: Executed `SELECT 1;` on target SQLite database.
  - AI Gateway: Verified model manifest and active models.
  - RAG Service: Initialized `RAGService` and queried test probe vector.
  - Payments Gateway: Initialized `FeeService` against target database.
  - i18n Registry: Verified loaded translations and `i18n.js` asset.
- **Verification:** When database file was removed/missing, health check reported `database: DOWN` and deployment was marked not ready (`is_ready=False`).

### Issue 3: Insecure Secrets Allowed Deployment Readiness
- **Root Cause:** Missing `SECRET_KEY` or `JWT_SECRET` returned `WARN`, allowing production deployments to pass validation without configured secrets.
- **Fix:** Added strict mode check (`APP_ENV=production` or `STRICT_SECRETS=true`) that raises `ValidationStatus.FAIL` and blocks deployment.
- **Verification:** `test_deployment_validator_secret_enforcement` verified that missing secrets fail readiness in production.

### Issue 4: Setup Script Lacked Automated Database Migration
- **Root Cause:** `setup.bat` installed packages but did not execute database schema migrations.
- **Fix:** Added step `[5/5] Initializing database schema...` executing `.venv\Scripts\python.exe scripts\migrate_db.py up --db-path gayatri_local.db`.
- **Verification:** `test_setup_and_launch_scripts_integrity` verified presence of the migration command in setup batch file.
