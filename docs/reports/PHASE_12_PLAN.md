# Phase 12 Plan: Real Online API Boundary

**Phase:** Phase 12 (Section 12.12 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`)  
**Objective:** Introduce an authoritative online service boundary so client portals do not bypass domain services and so E2E tests exercise the real application path over HTTP.

---

## 1. Architectural Analysis & Current Baseline

### Current State
1. **Existing API Routes & Architecture:**
   - FastAPI application factory in `central_platform/api/app.py` (`create_app()`) mounts versioned routers under `/api/v1/`.
   - Core domain services exist: `CourseService`, `RAGService`, `CurriculumService`, `AssessmentService`, `GenericTutorOrchestrator`, `LearningStateManager`, `SyncService`, `TeacherInstructionEngine`.
2. **Identified Gaps & Mock Data:**
   - `central_platform/api/routes/courses.py`: Returns hardcoded `_COURSES` (`crs-chem-101`, `crs-math-09`) instead of calling `CourseService`. Lacks course creation, version creation, submission, and publishing endpoints.
   - `central_platform/api/routes/enrollments.py`: Returns hardcoded `_ENROLLMENTS` instead of querying database or enforcing course offering checks. Lacks student enrollment creation.
   - `central_platform/api/routes/classes.py`: Does not exist as a dedicated router. Class groups and cohorts are only accessible through admin routes.
   - `central_platform/api/routes/organizations.py`: Does not exist as a dedicated router; only embedded in `admin.py`.
   - `central_platform/api/routes/instructions.py`: Teacher instructions are fragmented across `teachers.py` and `app.py`. A dedicated instruction router is needed for hierarchical resolution.
   - `central_platform/api/routes/assessments.py`: Missing the anti-leakage sanitized question delivery endpoint (`GET /assessments/{id}/sanitized`) implemented in Phase 11.
   - Health probes (`/healthz`, `/readyz`, `/livez`) in `app.py`: Return static JSON (`{"ready": True, "database": "CONNECTED", "models": "AVAILABLE"}`) without checking real database connectivity, model registry readiness, or handling subsystem degradation.
3. **Regression Baseline:**
   - 969 tests currently passing (100% green).

---

## 2. Implementation Scope: 16 Core Subsystems

In accordance with Section 12.12, route/service separation will be enforced across all 16 domains:

1. **Authentication (`central_platform/api/routes/auth.py`):**
   - PBKDF2 authentication against real database users (`authenticate_user`).
   - Cryptographically signed JWT access (60 min) and refresh tokens (7 days).
   - Account suspension verification (`is_suspended -> 403 Forbidden`).
   - Token revocation on logout.
2. **Organizations (`central_platform/api/routes/organizations.py`):**
   - `GET /api/v1/organizations`: List organizations from `PlatformDatabase.list_organizations()`.
   - `GET /api/v1/organizations/{org_id}`: Retrieve organization details.
   - `POST /api/v1/organizations`: Create organization (restricted to `SUPER_ADMIN`).
3. **Course Catalog (`central_platform/api/routes/courses.py`):**
   - Eliminate hardcoded `_COURSES`.
   - `GET /api/v1/courses`: List public courses or org-scoped courses via `CourseService.list_public_courses()` and `list_courses_for_org()`.
   - `GET /api/v1/courses/{course_id}`: Retrieve course details via `CourseService.get_course()`.
   - `POST /api/v1/courses`: Create course via `CourseService.create_course()` (requires `TEACHER` or `ADMIN`).
   - `GET /api/v1/courses/{course_id}/versions`: List versions via `db.get_course_versions_by_course()`.
   - `POST /api/v1/courses/{course_id}/versions`: Create version via `CourseService.create_course_version()`.
4. **Course Selection (`central_platform/api/routes/courses.py`):**
   - `POST /api/v1/courses/{course_id}/select`: Select course for organization via `CourseService.select_course_for_org()`. Creates version-pinned `CourseOffering`.
5. **Enrollments (`central_platform/api/routes/enrollments.py`):**
   - Eliminate hardcoded `_ENROLLMENTS`.
   - `POST /api/v1/enrollments`: Enroll student into course/offering with course visibility and org tenant checks.
   - `GET /api/v1/enrollments`: List enrollments by `student_id`, `course_id`, or `organization_id`.
   - `GET /api/v1/enrollments/{enrollment_id}`: Retrieve enrollment by ID.
6. **Classes (`central_platform/api/routes/classes.py`):**
   - `POST /api/v1/classes`: Create class group via `db.create_class_group()`.
   - `GET /api/v1/classes/{class_id}`: Get class group by ID.
   - `GET /api/v1/classes`: List class groups (optionally filtered by `course_id` and `organization_id`).
   - `POST /api/v1/classes/{class_id}/cohorts`: Create cohort via `db.create_cohort()`.
7. **Content Ingestion (`central_platform/api/routes/rag.py` & `curricula.py`):**
   - `POST /api/v1/rag/assets/upload`: Ingest Markdown, Text, or JSON knowledge assets via `RAGService.upload_knowledge_asset()`.
   - `POST /api/v1/curricula/import`: Import declarative curriculum package via `CurriculumService.import_package()`.
8. **Review Workflow (`central_platform/api/routes/`):**
   - `POST /api/v1/courses/{course_id}/versions/{version_id}/submit`: Submit course version for review via `CourseService.submit_version_for_review()`.
   - `POST /api/v1/rag/assets/{source_id}/approve`: Approve knowledge asset via `RAGService.approve_knowledge_asset()` (`ORG_ADMIN` / `SUPER_ADMIN` only).
   - `POST /api/v1/assessments/attempts/{attempt_id}/review`: Teacher reviews and adjusts assessment attempt score/feedback via `AssessmentService.review_attempt()`.
9. **Publication Workflow (`central_platform/api/routes/`):**
   - `POST /api/v1/courses/{course_id}/versions/{version_id}/publish`: Approve & publish course version via `CourseService.approve_and_publish_version()`.
   - `POST /api/v1/rag/assets/{source_id}/publish`: Publish knowledge asset via `RAGService.publish_knowledge_asset()`.
   - `POST /api/v1/curricula/versions/{version_id}/publish`: Publish curriculum version via `CurriculumService.publish_version()`.
10. **Instructions (`central_platform/api/routes/instructions.py`):**
    - `POST /api/v1/instructions`: Create teacher instruction with 5-tier hierarchy (`SESSION > STUDENT > CLASS > COURSE > ORGANIZATION`).
    - `GET /api/v1/instructions`: List hierarchical instructions with scope filtering.
    - `GET /api/v1/instructions/{instruction_id}`: Get instruction by ID.
    - `DELETE /api/v1/instructions/{instruction_id}`: Delete instruction.
11. **Assignments (`central_platform/api/routes/assessments.py`):**
    - `POST /api/v1/assessments/assignments`: Create assignment for class or student via `AssessmentService.create_assignment()`.
    - `GET /api/v1/assessments/assignments/{assignment_id}`: Retrieve assignment.
    - `GET /api/v1/assessments/assignments`: List assignments.
12. **Assessments (`central_platform/api/routes/assessments.py`):**
    - `POST /api/v1/assessments/items`: Create question bank item.
    - `GET /api/v1/assessments/items`: Query question bank items.
    - `POST /api/v1/assessments`: Create assessment definition.
    - `GET /api/v1/assessments/{assessment_id}/sanitized`: Deliver anti-leakage sanitized question items to students (answers/rubrics scrubbed).
    - `POST /api/v1/assessments/attempts/start`: Start attempt.
    - `POST /api/v1/assessments/attempts/submit`: Submit attempt and evaluate.
13. **Tutor (`central_platform/api/routes/tutor.py`):**
    - `POST /api/v1/tutor/turn`: Execute 16-step generic course turn via `GenericTutorOrchestrator`. Enforce identity checks, scoped RAG, anti-leakage invariant, and 2-phase commit.
14. **Progress (`central_platform/api/routes/students.py` & `learning.py`):**
    - `GET /api/v1/students/{student_id}/progress`: Retrieve mastery states and progress.
    - `GET /api/v1/students/{student_id}/slr`: Retrieve authoritative Student Learning Record.
    - `GET /api/v1/learning/events`: Chronological learning event stream.
15. **Sync (`central_platform/api/routes/sync.py`):**
    - `POST /api/v1/sync/events`: Offline batch event synchronization and reconciliation via `SyncService.process_sync_batch()`.
16. **Health (`central_platform/health/service.py` & Probes):**
    - Create `PlatformHealthService` performing live probes:
      - Database connectivity (`SELECT 1` on SQLite cursor).
      - Model registry availability (`model_manifest.json` parsing).
      - Storage / RAG source status.
      - Test failure injection hook (`simulate_subsystem_failure`).
    - Mount `/healthz`, `/readyz`, `/livez`, and `/api/v1/health`.
    - Return 200 when healthy, 503 when critical subsystem fails.

---

## 3. Real HTTP Testing & Verification Plan

Mandatory testing required by Section 12.12:
1. **Real Server Execution:**
   - Launch FastAPI application with `uvicorn` in a daemon background thread on an ephemeral port (`http://127.0.0.1:<port>`).
   - Use `httpx.Client` to perform real socket HTTP requests.
2. **Auth & RBAC Test Cases:**
   - Valid user login and JWT issuance.
   - Invalid credentials rejection (401).
   - Suspended user rejection (403).
   - Student token forbidden on teacher/admin endpoints (403).
   - Teacher token forbidden on cross-organization resources (403).
3. **Course & Selection CRUD:**
   - Create course, verify retrieval.
   - List public courses.
   - Select course for organization (create offering).
   - Create and list course versions.
4. **Content & Curriculum Lifecycle:**
   - Upload knowledge asset draft -> approve -> publish.
   - Verify published asset queryable via scoped RAG.
5. **Class & Enrollment Lifecycle:**
   - Create class group and cohort.
   - Enroll student in course offering.
   - Verify enrollment listed for student.
6. **Instruction Hierarchy:**
   - Create instructions at COURSE and CLASS levels.
   - Verify hierarchical query returns both.
7. **Assessment Delivery & Teacher Review:**
   - Create assessment with question bank items.
   - Student calls `GET /api/v1/assessments/{id}/sanitized` and verifies 0 answers/rubrics leaked.
   - Student submits attempt.
   - Teacher calls `POST /api/v1/assessments/attempts/{id}/review` to adjust score and sign off.
8. **Tutor Turn Execution:**
   - Call `POST /api/v1/tutor/turn` over HTTP with real payload and verify 200 response with typed pedagogical plan.
9. **Health & Intentionally Broken Subsystem:**
   - Normal state: `/healthz`, `/readyz`, `/api/v1/health` return 200 OK (`HEALTHY`).
   - Broken state: inject simulated database or model failure, verify `/readyz` or `/api/v1/health` returns 503 Service Unavailable with descriptive diagnostics.
10. **Evidence Generation:**
    - Export OpenAPI schema snapshot to `docs/reports/OPENAPI_SNAPSHOT_V2.json`.
    - Generate API contract document in `docs/reports/API_CONTRACT_V2.md`.
    - Generate Phase 12 test report and results JSON.

---

## 4. Phase Gate Invariants

1. **Zero Mock In-Memory Data:** `_COURSES` and `_ENROLLMENTS` removed; all endpoints query or mutate authoritative database/services.
2. **Strict Route/Service Separation:** Route functions validate request bodies and tokens, invoke domain services, and return typed responses. Zero domain business logic in routes.
3. **Real HTTP Boundary:** Integration suite verifies actual HTTP networking over loopback sockets.
4. **Deterministic Error Payloads:** Error responses follow standard `{ "ok": false, "error": { "code": "...", "message": "..." } }` contract.
5. **Zero Regressions:** 100% green across all existing 969 tests.
