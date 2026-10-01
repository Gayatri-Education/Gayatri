# Phase 02 — Database Migration & Schema Evolution Report

**Document:** `docs/reports/PHASE_02_MIGRATION_REPORT.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.2)  
**Execution Timestamp:** 2026-10-01T17:45:30+05:30  
**Migration Version:** `004` (`migrations/004_course_domain_model.sql`)  
**Rollback Script:** `migrations/004_course_domain_model_down.sql`  
**Target Database:** `gayatri_local.db` & Test SQLite instances  

---

## 1. Migration Summary

Migration 004 establishes relational support for the Canonical Course Domain Model:
1. **`courses.visibility`**: Added column `visibility TEXT NOT NULL DEFAULT 'PRIVATE'`.
2. **`course_versions`**: Created table for immutable version snapshots (`id`, `course_id`, `version_number`, `status`, `tool_policy`, `tutor_policy`, `checksum`, `created_by`, `published_by`, `created_at`, `published_at`, `is_deleted`).
3. **`organization_course_offerings`**: Created table mapping organizations to courses and pinning specific versions (`id`, `org_id`, `course_id`, `pinned_version_id`, `is_active`, `enrolled_at`).
4. **`sessions`**: Added columns `course_version_id TEXT` and `class_id TEXT`.
5. **`enrollments`**: Added columns `course_offering_id TEXT` and `class_id TEXT`.

---

## 2. Mandatory Migration Verification Checklist (Section 26)

| Verification Step | Result | Evidence |
|---|---|---|
| **1. Fresh Database Installation** | **PASS** | Clean run applies all migrations (001, 002, 003, 004) without errors (`test_migrations_fresh_db_and_idempotency`). |
| **2. Migration Idempotency** | **PASS** | Second consecutive run applies 0 migrations: `"Already up to date"`. |
| **3. Clean Rollback** | **PASS** | Running down script drops `course_versions`, `organization_course_offerings`, and cleanly drops added columns (`test_migrations_rollback_and_reapply`). |
| **4. Clean Re-Application** | **PASS** | Reapplying 004 after rollback succeeds with 0 errors. |
| **5. Foreign Key Integrity** | **PASS** | `course_versions(course_id)` and `organization_course_offerings(course_id)` verified with cascading deletes. |
| **6. Unique Constraints** | **PASS** | `UNIQUE(course_id, version_number)` and `UNIQUE(org_id, course_id)` enforced. |
| **7. Active Database Upgrade** | **PASS** | Applied to `gayatri_local.db` (`[OK] Applied 1 migration(s): 004`). |
| **8. Duplicate DDL Guard** | **PASS** | Verified 0 duplicate `CREATE TABLE` definitions across all migration files (`test_migrations_no_duplicate_create_table_statements`). |

---

## 3. Schema Diagram (Course Subsystem)

```text
organizations (id, name, code)
    ▲                       ▲
    │ (owner_org_id)        │ (org_id)
    │                       │
courses ───────────────────► organization_course_offerings ◄─── enrollments
    │ (id, code, visibility)         │ (pinned_version_id)
    ▼                                ▼
course_versions (id, version_number, status, tool_policy)
```

---

## 4. Certification

Migration 004 is certified production-ready, idempotent, and reversible.
