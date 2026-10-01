# Phase 00 — Initial Test & Forensic Verification Baseline

**Document:** `docs/reports/PHASE_00_TEST_BASELINE.md`  
**Generated At:** 2026-10-01T11:26:00+05:30  
**Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Commit SHA:** `bf47a63273e936b7617937be199e44efb4d9cb5d`  
**OS Platform:** Windows (win32)  
**Python Runtime:** Python 3.12.10  
**Test Framework:** Pytest 7.4.4  

---

## 1. Test Execution Summary

The baseline execution exercised all test suites registered in `tests/` prior to any architectural refactoring.

```bash
python -m pytest -q --tb=short
```

| Metric | Result |
|---|---|
| **Collected Tests** | 856 |
| **Passed Tests** | 856 |
| **Failed Tests** | 0 |
| **Skipped Tests** | 0 |
| **XFailed Tests** | 0 |
| **Execution Duration** | 80.32 seconds |
| **Test Exit Code** | `0` (SUCCESS) |

---

## 2. Static Code Verification

### 2.1 Bytecode Compilation
```bash
python -m compileall app core central_platform tests scripts
```
- **Result:** PASS
- **Errors:** 0 syntax errors or byte-compilation failures across all 607 tracked repository files.

### 2.2 Static Linting & Code Hygiene (`ruff 0.16.0`)
```bash
ruff check central_platform core app --statistics
```
- **Total Diagnostic Issues Found:** 5,188
- **Primary Categories:**
  - `E501` (Line too long): 1,691
  - `UP006` (Non-PEP 585 annotations): 915
  - `UP045` (Non-PEP 604 optional annotations): 829
  - `UP035` (Deprecated imports): 224
  - `F401` (Unused imports): 157
  - `S110` (Swallowed `try...except Exception: pass`): 55
  - `B008` (Function call in default argument): 136

---

## 3. Forensic Defect & Regression Surface

While all 856 tests pass, the forensic inspection mandated by **Section 0** and **Section 2** reveals that passing tests currently mask structural and architectural defects:

1. **Chemistry Hardcoded into Generic Core:**
   - 115 files outside adapters/tests/docs contain hardcoded references to `chemistry`, `thermodynamics`, `hess`, `ncert`, or `crs-chem-101`.
   - `core/curriculum/`, `core/runtimes/chemistry.py`, and `app/bridge/facade.py` directly bake Chemistry concepts into what should be generic runtime interfaces.

2. **Legacy Inference Coupling:**
   - 3 active files directly import legacy agent logic:
     - `core/inference/service.py:40` (`from legacy.agents.default_agents import _local_chat_stream`)
     - `core/runtimes/chemistry.py:115` (`from legacy.agents.default_agents import _build_messages, _get_tutor_context`)
     - `core/runtimes/general.py:68` (`from legacy.agents.default_agents import _build_messages`)

3. **Hardcoded Demo Users in Production/Bridge Paths:**
   - 13 non-test files contain hardcoded fake student/user identities (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`, `local_user_1`, `local_student_1`).
   - `app/bridge/facade.py` injects fake roster entries instead of rendering an honest empty state or querying canonical course enrollments.

4. **Dynamic Runtime DDL Invocations:**
   - 5 files execute inline `ALTER TABLE` DDL at runtime inside `try...except Exception: pass`:
     - `core/session.py` (lines 128, 132, 152, 157, 171)
     - `core/rag/store.py` (lines 73, 78)
     - `core/tutor/state.py` (lines 264, 269)
     - `core/db.py` (line 139)

5. **Migration Schema Duplication:**
   - `migrations/001_initial_schema.sql` defines `CREATE TABLE IF NOT EXISTS assignments` twice (at line 351 and line 448).

---

## 4. Conclusion & Baseline Certification

The 856 passing tests confirm that the existing feature implementation operates according to its historical specification. However, per the **Non-Negotiable Agent Contract**, this does NOT indicate course-independence, clean multi-tenancy, or production readiness.

This baseline is certified as the forensic starting point for Phase 1 (Architecture Freeze) and Phase 2 (Course Domain Model).
