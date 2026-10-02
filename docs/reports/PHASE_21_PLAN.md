# Phase 21 Implementation & Test Plan: Database & Migration Hardening

**Document:** `docs/reports/PHASE_21_PLAN.md`  
**Phase:** 21  
**Section:** 12.21 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  

---

## 1. Objective

Reconcile all schema definitions, verify SQLite and supported PostgreSQL behavior, enforce immutable migration checksums, and eliminate silent migration failures.

Per Section 12.21:
- Reconcile all schema definitions across `migrations/`, `central_platform/db.py`, and dataclass models.
- Ensure every table has exactly one authoritative creation source.
- Enforce immutable migration identity via SHA-256 checksum tracking and tamper detection (`MigrationChecksumMismatchError`).
- Test migration lifecycle:
  1. Clean migration on empty database.
  2. Idempotent rerun (migrate twice yields 0 duplicate operations).
  3. Step-by-step incremental migration execution.
  4. Symmetric reverse rollback of all migrations (008 -> 001) and clean reapplication.
  5. Foreign-key violation enforcement (`IntegrityError`).
  6. Uniqueness constraint enforcement (Primary keys and unique indexes).
  7. Data preservation across incremental migration runs.
  8. Concurrent multithreaded database access without deadlocks or corrupt locks.
  9. Honest environment reporting: SQLite verified; PostgreSQL driver verified, live daemon unverified.

---

## 2. Test Architecture Plan

Create `tests/test_phase21_database_migration_hardening.py` with 12 comprehensive test cases:
1. `test_empty_database_migration_all_versions`: Run migrations 001 through 008 on empty DB, verify all 50 tables created.
2. `test_migrations_idempotency_rerun`: Run `run_all_migrations` a second time; assert returns empty list and no-op.
3. `test_incremental_migration_stepping`: Apply migrations one by one in sequence, asserting table availability increases deterministically.
4. `test_full_rollback_and_reapplication`: Roll back all migrations in reverse order (008 to 001), verify all tables dropped, reapply cleanly.
5. `test_immutable_checksum_verification`: Verify `verify_migration_checksums()` returns 0 mismatches on pristine migrations.
6. `test_tampered_migration_checksum_detection`: Intentionally mutate migration file or recorded checksum and verify `MigrationChecksumMismatchError` is raised.
7. `test_foreign_key_constraint_enforcement`: Attempt inserting records referencing non-existent parent foreign keys; verify `sqlite3.IntegrityError`.
8. `test_uniqueness_constraint_enforcement`: Attempt inserting duplicate primary keys and unique slugs; verify `sqlite3.IntegrityError`.
9. `test_data_preservation_across_migrations`: Insert data after migration 001, execute migrations 002-008, verify initial data remains intact.
10. `test_concurrent_database_reads_and_writes`: Verify concurrent multithreaded readers/writers operate reliably without corruption.
11. `test_authoritative_table_manifest_consistency`: Verify every table declared across migrations has exactly 1 creation source.
12. `test_dual_engine_compatibility_and_environment_reporting`: Verify PostgreSQL driver availability (`psycopg2`) and honest local daemon reporting.
