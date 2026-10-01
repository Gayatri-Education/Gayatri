# Phase 02 — Canonical Course, Version & Offering Domain Test Report

**Document:** `docs/reports/PHASE_02_TEST_REPORT.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.2)  
**Execution Timestamp:** 2026-10-01T17:47:00+05:30  
**Commit SHA:** `48e5e5f`  
**Branch:** `master`  
**Host Environment:** Windows (win32), Python 3.12.10, Pytest 7.4.4  
**Phase Status:** `VERIFIED`  

---

## 1. Test Execution Command & Summary

```bash
python -m pytest -q --tb=short
```

| Metric | Result |
|---|---|
| **Collected Tests** | 874 |
| **Passed Tests** | 874 |
| **Failed Tests** | 0 |
| **Skipped Tests** | 0 |
| **XFailed Tests** | 0 |
| **Duration** | 97.45 seconds |
| **Exit Code** | `0` (SUCCESS) |

### Bytecode Compilation Hygiene
```bash
python -m compileall app core central_platform tests scripts
```
- **Result:** PASS (0 errors across all 600+ repository files).

---

## 2. Phase 02 Test Suite Breakdown

### 2.1 Course Domain Model (`tests/test_phase02_course_domain_model.py`)

| Test Function | Scenarios Exercised | Result |
|---|---|---|
| `test_public_course_lifecycle_and_cross_org_selection` | Admin creates public course $\rightarrow$ version 1.0 drafted $\rightarrow$ reviewed $\rightarrow$ published $\rightarrow$ Org B discovers in catalog $\rightarrow$ Org B selects offering $\rightarrow$ version 1.0 pinned $\rightarrow$ student access verified. | **PASS** |
| `test_private_course_tenant_isolation` | Org A creates private course $\rightarrow$ Org A students access $\rightarrow$ course excluded from public catalog $\rightarrow$ Org B students denied (403 `CourseAuthorizationError`) $\rightarrow$ Org B admin selection rejected. | **PASS** |
| `test_course_versioning_and_admin_approval_gate` | Version 1.0 published $\rightarrow$ Teacher creates Version 2.0 with custom tools (`calculator`, `graphing`) $\rightarrow$ submitted for review $\rightarrow$ Teacher publication attempt rejected $\rightarrow$ Admin approves $\rightarrow$ server-side tool validation verified. | **PASS** |
| `test_cross_tenant_tampering_rejected` | Negative tests: Org B teacher attempts version creation on Org A course $\rightarrow$ denied; Org B admin attempts approval on Org A course $\rightarrow$ denied. | **PASS** |

### 2.2 Database Migrations (`tests/test_phase02_migrations.py`)

| Test Function | Scenarios Exercised | Result |
|---|---|---|
| `test_migrations_fresh_db_and_idempotency` | Clean DB install (migrations 001-004) $\rightarrow$ second run applies 0 $\rightarrow$ all tables and columns verified $\rightarrow$ 0 duplicate tables. | **PASS** |
| `test_migrations_rollback_and_reapply` | Reversible down migration drops added tables and columns $\rightarrow$ clean re-application of 004 succeeds. | **PASS** |

---

## 3. Acceptance Criteria Checklist (Section 12.2)

- [x] `Course` entity with explicit `visibility` (`PUBLIC` / `PRIVATE`).
- [x] Public course discoverable across organizations; private course restricted to owner organization.
- [x] Cross-tenant private course query or selection raises explicit `CourseAuthorizationError`.
- [x] Immutable `CourseVersion` with `DRAFT` $\rightarrow$ `READY_FOR_REVIEW` $\rightarrow$ `PUBLISHED` lifecycle.
- [x] Teacher upload vs Admin publish authorization boundary enforced.
- [x] Organization course selection decoupled via `OrganizationCourseOffering` with version pinning.
- [x] Course tool policy declared and validated server-side.
- [x] Migration 004 tested on fresh database, verified idempotent, and tested for rollback.
- [x] Zero hardcoded Chemistry defaults in new course domain models.
- [x] Full regression suite (874 tests) passing.

---

## 4. Phase 02 Gate Certification

Phase 02 (Canonical Course, Version & Offering Domain) is certified as **VERIFIED**. The course domain core is established. The platform is ready to proceed to **Phase 3: Generic Curriculum & Versioned Learning Graph**.
