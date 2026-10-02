# Phase 02 Execution Plan — Canonical Course, Version & Offering Domain

**Document:** `docs/reports/PHASE_02_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.2)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Implement the foundational domain model and persistence layer that transforms Gayatri into a genuinely course-independent platform:
1. Establish `Course` entities with explicit `visibility` (`PUBLIC` vs `PRIVATE`).
2. Implement immutable `CourseVersion` management with administrative publication approval gates.
3. Decouple course creation from organization adoption via `OrganizationCourseOffering` (version pinning).
4. Add versioned migration `migrations/004_course_domain_model.sql` and `migrations/004_course_domain_model_down.sql`.
5. Implement `CourseService` in `central_platform/courses/service.py` enforcing multi-tenant isolation, cross-org denial, and server-side tool policies.

---

## 2. Planned Implementation Details

1. **Schema & Model Entities (`central_platform/models/schema.py`):**
   - `CourseVisibility` (`PUBLIC`, `PRIVATE`)
   - `CourseStatus` (`DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `PUBLISHED`, `ARCHIVED`, `FAILED`)
   - `CourseToolPolicy` (server-side tool capability dictionary)
   - `CoursePolicy` (pedagogical threshold parameters)
   - `CourseVersion` (immutable published snapshot)
   - `OrganizationCourseOffering` (organization course selection and pinned version)
   - `Course` with `visibility: CourseVisibility`

2. **Database Migration & DAL (`migrations/004_course_domain_model.sql`, `central_platform/db.py`):**
   - DDL for `course_versions` and `organization_course_offerings`.
   - Add `visibility` column to `courses`.
   - Update `PlatformDatabase` CRUD methods for courses, versions, and offerings with backward-compatible row parsing.

3. **Domain Service (`central_platform/courses/service.py`):**
   - `create_course()`: initializes course and version 1.0 in `DRAFT`.
   - `get_course()`: enforces `PUBLIC` visibility vs `PRIVATE` tenant boundary (returns 403 / `CourseAuthorizationError` on cross-org private access).
   - `list_public_courses()`: cross-org catalog.
   - `create_course_version()`: teachers can draft new versions; immutable once published.
   - `approve_and_publish_version()`: strictly requires `ORG_ADMIN` or `SUPER_ADMIN` role.
   - `select_course_for_org()`: creates organization offering with version pinning.
   - `validate_tool_access()`: server-side tool validation.

4. **Testing & Verification:**
   - `tests/test_phase02_course_domain_model.py`: Public course selection, private cross-org denial, version state machine, approval gate, and cross-tenant tampering.
   - `tests/test_phase02_migrations.py`: Fresh DB installation, idempotency, rollback down to 000, and re-upgrade.

---

## 3. Phase 02 Acceptance Gate

Phase 02 is certified `VERIFIED` when:
1. All domain models and migration scripts are syntactically and functionally verified.
2. Migration idempotency and rollback tests pass completely.
3. Unit and integration tests in `test_phase02_course_domain_model.py` and `test_phase02_migrations.py` pass 100%.
4. Existing regression suite remains 100% green.
5. All Phase 02 reports (`PHASE_02_PLAN.md`, `PHASE_02_TEST_REPORT.md`, `PHASE_02_MIGRATION_REPORT.md`, `PHASE_02_TEST_RESULTS.json`) are recorded and committed.
