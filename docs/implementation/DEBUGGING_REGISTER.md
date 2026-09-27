# V2 Platform Debugging Register

Defect tracking registry for Gayatri AI V2 Platform Reconciliation.

## Severity Definitions
- **P0**: Catastrophic failure (data corruption, security bypass, unauthorized access, crash on startup).
- **P1**: Major functionality broken (API route failure, BKT update failure, sync failure).
- **P2**: Important defect with existing workaround.
- **P3**: Minor defect, cosmetic inconsistency, or logging nuisance.

## Open Defects Summary
- **Open P0**: 0
- **Open P1**: 0
- **Open P2**: 0
- **Open P3**: 0

---

## Resolved & Historical Defect Records

## BUG-0001

Severity: P1  
Phase: Phase 00 (Pre-reconciliation baseline)  
Component: `central_platform.teacher.instruction`  
Detected: 2026-09-26  
Environment: Local / Windows PowerShell  
Commit: `b56bed2`  

### Reproduction
Call `engine.get_instructions_for_student("verify_student_usa", "crs-chem-101")` when a class-wide directive with `student_id="all"` exists.

### Expected
Directive scoped to `"all"` or `"*"` or blank matches all students within that course.

### Actual
`inst.student_id != student_id` rejected class-wide instructions, causing only exact matching IDs to receive directives.

### Root Cause
Condition `if inst.student_id != student_id:` did not account for class-wide wildcard scoping.

### Fix
Updated match check in `central_platform/teacher/instruction.py` to `if inst.student_id not in (student_id, "all", "*", ""): continue`.

### Regression Test
`tests/test_phase7_teacher_instructions.py::test_teacher_instruction_scoping_and_priority` and `scripts/verify_sync.py` Gate 4.

### Verification
Passed in `pytest` and `scripts/verify_sync.py` (5/5 gates).

### Status
VERIFIED

---

## BUG-0002

Severity: P1  
Phase: Phase 00 (Pre-reconciliation baseline)  
Component: `central_platform.db`  
Detected: 2026-09-26  
Environment: Local / Windows PowerShell  
Commit: `ba4b1ca`  

### Reproduction
Run `python server.py` on fresh clone.

### Expected
Database automatically initializes required tables (`organizations`, `users`, `audit_logs`, `courses`, `classes`, `enrollments`) on connection.

### Actual
`sqlite3.OperationalError: no such table: organizations` thrown because table initialization was not automatically triggered in constructor.

### Root Cause
`db.create_organization` called before `_init_db` execution completed.

### Fix
Added self-healing `_init_db` check in `CentralPlatformDB.__init__` and `server.py` startup sequence.

### Regression Test
`tests/test_server_live_sync.py` and `tests/test_phase2_central_platform.py`.

### Verification
Verified with server startup and live API tests.

### Status
VERIFIED
