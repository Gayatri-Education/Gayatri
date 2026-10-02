# Phase 26 Plan: Packaging, Clean Install & Deployment Validation

## 1. Executive Summary & Objective

**Phase 26** is the Packaging, Clean Install, and Deployment Validation phase of the Gayatri AI Educational Platform, executing Section 36 of `GAYATRI_MASTER_PHASE_BY_PHASE_EXECUTION_AND_RECOVERY_GUIDE.md` and Section 12.26 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`.

The primary objective is to prove that the release works outside the developer machine in a completely clean environment without developer-machine residue, verifies all packaging scripts, cryptographic signatures, integrity manifests, and performs **real** (non-simulated) subsystem probes.

---

## 2. Requirements & Traceability

| Requirement ID | Specification | Target Component | Validation Strategy |
|---|---|---|---|
| **REQ-26.1** | Distribution Packaging Completeness | `scripts/package_release.py` | Package all runtime modules (`central_platform`, `migrations`, `app`, `core`, `scripts`) into distribution artifact. |
| **REQ-26.2** | Release Integrity & Cryptographic Signatures | `scripts/verify_release.py` | Cryptographically verify SHA-256 file manifest and optional Ed25519 digital signature. Detect tampered/extra files. |
| **REQ-26.3** | Clean Environment Bootstrap & Migration | `scripts/migrate_db.py`, `setup.bat` | Execute clean database creation, full migration replay (001 through 008) in isolated directory. |
| **REQ-26.4** | Real Subsystem Health Probing | `central_platform/deployment/validator.py` | Probe real database connection, AI gateway, RAG service, payment service, and i18n registry. Zero fake "UP" strings. |
| **REQ-26.5** | Secret Enforcement | `central_platform/deployment/validator.py` | Missing or weak secrets must fail readiness in production or strict mode. |
| **REQ-26.6** | Full Lifecycle Clean-Install Journey | `tests/test_phase26_packaging_clean_install.py` | Fresh bootstrap -> schema migration -> course provisioning -> RAG publish -> student turn -> close -> restart -> state verification. |
| **REQ-26.7** | Windows Setup & Launch Scripts | `setup.bat`, `launch.bat` | Verify Python 3.12 compatibility check, venv creation, database migration step, and clean execution paths. |

---

## 3. Forensic Inspection & Remediations Identified

1. **`scripts/package_release.py` Missing Core Packages:**
   - Previous packaging only included `["app", "core", "data", "docs", "legacy"]`.
   - **Remediation:** Must include `central_platform`, `migrations`, `scripts` so the central backend and database migrations are properly packaged.
2. **`central_platform/deployment/validator.py` Mocked Health Checks:**
   - Lines 275-288 hardcoded `{"database": "UP", "ai_gateway": "UP", "rag_service": "UP", ...}` without probing actual subsystems.
   - Lines 155-162 treated missing secret as `WARN` instead of `FAIL`.
   - **Remediation:** Implement real socket/database/service probes. Fail readiness on missing secrets in production/strict mode.
3. **`setup.bat` / `launch.bat` Migration Step:**
   - `setup.bat` lacked automatic database schema initialization via `python scripts/migrate_db.py up`.
   - **Remediation:** Add database migration step to installer to guarantee schema is provisioned on clean install.

---

## 4. Test Suite Architecture

Test suite: `tests/test_phase26_packaging_clean_install.py`
- `test_packaging_completeness_and_manifest`: Verifies package generation with all required directories, files, and valid SHA-256 hashes.
- `test_release_integrity_verification`: Verifies `verify_release.py` on signed and unsigned bundles, detects file tampering and unauthorized files.
- `test_clean_environment_bootstrap_and_migrations`: Initializes fresh database in temp directory, applies all migrations (001-008), verifies 49 core tables.
- `test_clean_lifecycle_provision_publish_turn_restart`: End-to-end clean journey (org -> course -> version -> RAG publish -> turn -> close -> restart -> verify persistence).
- `test_deployment_validator_real_probes`: Tests `DeploymentValidator` probing live database, AI provider, RAG, payments, and i18n, verifying real probe execution.
- `test_deployment_validator_secret_enforcement`: Tests that missing/weak secrets fail validation in strict mode or production.
- `test_setup_and_launch_script_hygiene`: Validates syntax, Python 3.12 support, and migration steps in batch files.

---

## 5. Execution & Verification Checklist

- [x] Create `docs/reports/PHASE_26_PLAN.md`
- [ ] Fix `scripts/package_release.py` to package `central_platform`, `migrations`, `scripts`
- [ ] Upgrade `central_platform/deployment/validator.py` with real subsystem probing and strict secret enforcement
- [ ] Update `setup.bat` with migration command
- [ ] Implement `tests/test_phase26_packaging_clean_install.py`
- [ ] Execute tests locally and verify 100% pass rate
- [ ] Generate `docs/reports/PHASE_26_TEST_REPORT.md`, `docs/reports/PHASE_26_TEST_RESULTS.json`, and `docs/reports/PHASE_26_CLEAN_INSTALL_REPORT.md`
- [ ] Update `PROJECT_STATE.yaml` and `docs/reports/REQUIREMENTS_TRACEABILITY.md`
- [ ] Commit and push to GitHub master
- [ ] Monitor GitHub Actions CI to green status
