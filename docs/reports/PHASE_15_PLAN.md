# Phase 15 Plan: Admin Course & Content Workflow UI

**Phase:** Phase 15 (Section 12.15 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`)  
**Objective:** Connect the admin workflows to real services: public/private course handling, course selection, approval and publication, review queue, archiving, and audit trail, with 100% honest empty states, RBAC enforcement, and zero fake demo data.

---

## 1. Architectural Analysis & Problem Statement

### Current State & Findings
1. **Course Service Foundation:**
   - In Phases 02, 04, and 12, `CourseService` and `PlatformDatabase` were established with core public/private visibility and course versioning (`DRAFT`, `READY_FOR_REVIEW`, `PUBLISHED`).
2. **Missing Administrative Capabilities in Course Service:**
   - No explicit `archive_course()` or `archive_course_version()` methods in `CourseService` or `PlatformDatabase`.
   - No dedicated `get_review_queue()` method for querying course versions awaiting administrator review.
   - Missing REST endpoints for archiving and review queue:
     - `GET /api/v1/courses/review-queue`
     - `POST /api/v1/courses/{course_id}/archive`
     - `POST /api/v1/courses/{course_id}/versions/{version_id}/archive`
3. **Admin Web Portal UI Gap:**
   - In `app/ui/admin_portal.html`, the `#/courses` view currently renders a rudimentary table without:
     - Visibility badges (PUBLIC vs PRIVATE).
     - Selection of public courses into organization offerings.
     - Review queue for approving pending submissions.
     - Knowledge content upload/attachment modal.
     - Actionable archive buttons.
     - Honest empty states, loading indicators, and 403 Forbidden error handling.
4. **Desktop Python Bridge Controller Gap:**
   - `app/portals/admin/controller.py` lacks course lifecycle orchestration methods (`get_courses`, `create_course`, `get_review_queue`, `publish_version`, `archive_course`) connecting directly to `CourseService`.

---

## 2. Target Design & Components

### 2.1 Backend Persistence & Service (`central_platform/db.py`, `central_platform/courses/service.py`)
1. **Database Methods:**
   - `archive_course(course_id: str) -> bool`: Soft-deletes course, sets `is_deleted = 1` and `deleted_at`.
   - `archive_course_version(version_id: str, archived_by: str) -> bool`: Sets status to `ARCHIVED`.
   - `get_course_versions_by_status(status: CourseStatus, organization_id: Optional[str] = None) -> List[CourseVersion]`: Retrieves versions matching status with optional tenant filter.
2. **Course Service Methods:**
   - `archive_course(actor: User, course_id: str) -> bool`: Enforces ORG_ADMIN/SUPER_ADMIN and tenant ownership.
   - `archive_course_version(actor: User, version_id: str) -> CourseVersion`: Enforces RBAC and tenant ownership.
   - `get_review_queue(actor: User, organization_id: Optional[str] = None) -> List[Dict[str, Any]]`: Returns course versions in `READY_FOR_REVIEW` (and `DRAFT`), joined with course metadata.
   - Audit logging: Records `AdminAuditEvent` / `AuditLog` on all lifecycle operations (`CREATE_COURSE`, `ARCHIVE_COURSE`, `CREATE_VERSION`, `SUBMIT_FOR_REVIEW`, `APPROVE_AND_PUBLISH`, `ARCHIVE_VERSION`, `SELECT_OFFERING`).

### 2.2 REST API Routes (`central_platform/api/routes/courses.py`, `central_platform/api/schemas.py`)
1. `GET /api/v1/courses/review-queue`:
   - Returns list of `CourseReviewQueueItemResponse` items.
   - Enforces admin auth (ORG_ADMIN / SUPER_ADMIN).
2. `POST /api/v1/courses/{course_id}/archive`:
   - Archives course. Returns status.
3. `POST /api/v1/courses/{course_id}/versions/{version_id}/archive`:
   - Archives course version. Returns updated version schema.

### 2.3 Desktop Bridge Controller (`app/portals/admin/controller.py`)
- Wire `AdminPortalController` to `CourseService`, `RAGService`, and `PlatformDatabase`.
- Provide clean Python methods for listing courses, creating public/private courses, submitting versions, querying review queue, publishing, and archiving.

### 2.4 Frontend Web UI (`app/ui/admin_portal.html`)
- **Enhanced Course Catalog View:**
  - Public/Private filters.
  - Create Course Modal with code, title, description, visibility radio (PUBLIC / PRIVATE).
  - Select Public Course Modal for assigning offerings to organizations.
  - Action buttons: View Versions, Select for Org, Archive.
- **Dedicated Content & Version Review Queue View:**
  - Table of pending course versions awaiting administrative review.
  - Quick action buttons: "Approve & Publish", "Archive", "View Content Chunks".
  - Knowledge content upload modal connecting to `/api/v1/rag/sources` and `/api/v1/rag/sources/{id}/ingest`.
- **Honest Empty & Error States:**
  - "No courses in catalog" empty state with clear CTA.
  - "No versions pending review" empty state.
  - Dynamic 403 Forbidden and error alerts.

---

## 3. Test Strategy (`tests/test_phase15_admin_course_content_workflow.py`)

12 comprehensive tests:
1. `test_admin_create_private_course_tenant_isolation`: Org Admin creates private course; verified restricted to own tenant.
2. `test_admin_create_public_course`: Super Admin creates public course; verified visible globally.
3. `test_admin_select_public_course_for_organization`: Org Admin selects public course to create active organization offering.
4. `test_admin_select_private_course_cross_tenant_forbidden`: Org Admin attempting to select another org's private course receives 403 Forbidden.
5. `test_teacher_create_draft_version`: Teacher creates new version in `DRAFT` status.
6. `test_content_upload_and_rag_ingest_to_course_version`: Upload and ingest knowledge source attached to course version.
7. `test_teacher_submit_version_for_review`: Version status transitions from `DRAFT` to `READY_FOR_REVIEW`.
8. `test_admin_review_queue_scoping`: Review queue returns pending versions scoped to the requesting admin's organization.
9. `test_admin_approve_and_publish_version`: Admin approves version; status transitions to `PUBLISHED`.
10. `test_student_and_teacher_forbidden_actions`: Students and teachers attempting to approve/publish or archive are rejected with 403.
11. `test_admin_archive_course_and_version`: Archiving version sets `ARCHIVED` status; archiving course sets `is_deleted = 1`.
12. `test_ui_controller_and_audit_trail_durability`: Controller reflects real DB state after simulated reload; audit trail captures complete lifecycle.

---

## 4. Execution Steps
1. Extend `central_platform/db.py` with `archive_course`, `archive_course_version`, and `get_course_versions_by_status`.
2. Extend `central_platform/courses/service.py` with `archive_course`, `archive_course_version`, and `get_review_queue`.
3. Add schemas in `central_platform/api/schemas.py` and routes in `central_platform/api/routes/courses.py`.
4. Update `app/portals/admin/controller.py` with full course lifecycle methods.
5. Enhance `app/ui/admin_portal.html` with catalog, review queue, content attachment modal, and honest empty states.
6. Implement `tests/test_phase15_admin_course_content_workflow.py` (12 tests) and verify all pass.
7. Run full regression suite (`pytest -q`) to ensure 1,017 tests pass (1,005 + 12).
8. Generate reports, update ledgers, commit, and push.
