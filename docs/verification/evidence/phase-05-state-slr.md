# Phase 05 Evidence — Transactional Learning State and Authoritative SLR

## Objective
Make learning-state mutation truly atomic across all Section 12/15 persistence operations, enforce database-level event deduplication, and ensure the Student Learning Record (SLR) reflects actual evidence rather than fabricated defaults.

## Starting commit
`8b9cddd` (`master`)

## Files changed
- `central_platform/db.py`:
  - Added `_ConnectionContextWrapper` class that suppresses per-operation auto-commit whenever an outer transaction is active.
  - Added `in_transaction: bool` property on `PlatformDatabase`.
  - Added `transaction(self)` context manager on `PlatformDatabase` supporting nested transactions via SQLite `SAVEPOINT`s (`SAVEPOINT tx_sp_N`, `RELEASE SAVEPOINT`, `ROLLBACK TO SAVEPOINT`) and root-level `COMMIT` / `ROLLBACK`.
- `central_platform/learning/commit_pipeline.py`:
  - Wrapped all state mutations (mastery states, misconception records, learning events) in `with self.db.transaction():`.
  - Added support for explicit fault injection points (`after_mastery`, `after_misconceptions`, `after_events`) to deterministically verify that failure at any point rolls back all prior operations in the transaction.
- `central_platform/slr/models.py`:
  - Updated `SLRMastery` model defaults: `overall_score = 0.0` (was 0.50), `retention_rate = 0.0` (was 0.85), `evidence_status = "INSUFFICIENT_EVIDENCE"` (new field).
- `central_platform/slr/service.py`:
  - Removed early hardcoded `target_course = course_id or "crs-chem-101"`. Added `_resolve_target_course` resolving course from student active enrollments or parameter.
  - In `get_authoritative_slr`:
    - Eliminated synthetic `concept_scores["chem_thermo_first_law"] = 0.50` baseline.
    - When unassessed, returns `evidence_status="INSUFFICIENT_EVIDENCE"`, `overall_score=0.0`, `retention_rate=0.0`, `concept_scores={}`.
    - When evidence exists, calculates real average score and sets `evidence_status="EVALUATED"`.
    - Eliminated hardcoded Chemistry course codes/titles for non-chemistry courses.
  - In `update_concept_mastery`, `record_student_misconception`, `project_from_events`:
    - Enforced atomic single database transaction via `with self.db.transaction():`.
- `tests/test_phase09_student_progress.py`:
  - Updated `test_empty_student_progress_state` to assert authentic zero-evidence baseline (`overall_mastery == 0.0`) per F-017 contract rather than obsolete 0.50 baseline.
- `tests/test_phase05_state_slr_remediation.py`:
  - Added 9 comprehensive contract and adversarial tests.

## Defects addressed
- **F-015 (P0):** Learning state mutations saved without a unified database transaction, creating partial writes on failure. Fixed: Unified atomic transaction wraps all operations in `commit_pipeline` and `SLRService`. Fault injection tests verify 0 partial writes.
- **F-016 (P0):** Learning events lack durable database-level uniqueness. Fixed: Verified `learning_events.id` primary key deduplication and idempotency.
- **F-017 (P0):** SLR fabricates synthetic Chemistry baseline (50% score, 85% retention, `chem_thermo_first_law`). Fixed: Completely eliminated fabricated baselines. Unassessed students yield `INSUFFICIENT_EVIDENCE` and score 0.0. Real evidence produces `EVALUATED` and real score averages.
- **F-018 (P1):** Multi-tenant course scoping isolation. Fixed: Scoped state records strictly to student and course with zero cross-course or cross-student state leakage.

## Tests added
- `tests/test_phase05_state_slr_remediation.py`:
  - `test_atomic_transaction_full_success`: Verifies complete commit across mastery, misconceptions, and events.
  - `test_fault_injection_after_mastery_zero_partial_writes`: Verifies fault after mastery write rolls back all writes with zero partial records.
  - `test_fault_injection_after_misconceptions_zero_partial_writes`: Verifies fault after misconceptions rolls back mastery and misconceptions with zero partial records.
  - `test_fault_injection_after_events_zero_partial_writes`: Verifies fault after events rolls back all records with zero partial records.
  - `test_event_deduplication_idempotency`: Verifies database-level idempotent deduplication by unique event ID.
  - `test_unassessed_learner_has_insufficient_evidence_status`: Verifies zero fabricated defaults for fresh students.
  - `test_real_evidence_produces_evaluated_status_and_correct_score`: Verifies real score calculation when evidence is present.
  - `test_multi_course_slr_isolation`: Verifies course isolation between different courses for the same student.
  - `test_database_nested_savepoints`: Verifies SQLite nested savepoint commit/rollback mechanics in `PlatformDatabase`.

## Verification result
- **Test Suite Pass Rate:** 1,187 passed in 268.60s (100% pass rate, 0 failures).
- **Targeted Suites:**
  - `tests/test_phase05_state_slr_remediation.py`: 9/9 passed.
  - `tests/test_phase06_authoritative_slr.py`: 11/11 passed.
  - `tests/test_phase20_state_commit_pipeline.py`: 3/3 passed.
  - `tests/test_phase09_student_progress.py`: 10/10 passed.
