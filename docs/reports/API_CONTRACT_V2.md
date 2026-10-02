# Gayatri AI Platform — API Contract Specification (V2)

**Phase:** Phase 12 (Real Online API Boundary)  
**Status:** Canonical Active Platform Specification  
**OpenAPI Snapshot:** [`docs/reports/OPENAPI_SNAPSHOT_V2.json`](OPENAPI_SNAPSHOT_V2.json)  
**Base URL:** `http://localhost:8000` / `/api/v1`

---

## 1. Architectural Principles & Invariants

1. **Course Independence (Rule 8):** Zero subject-specific or hardcoded course models (e.g. Chemistry, stoichiometry, periodic table) in generic API routing logic. Courses, subjects, and topics are first-class database entities.
2. **Explicit Identity (Rule 4):** No magic student fallback (`student_id = session_id` or default user assignments). All requests require authenticated credentials and valid entity references.
3. **Anti-Answer-Leakage (Phase 11):** Student examination endpoints (`/assessments/{id}/sanitized`) strictly strip all correct answers, answer keys, rubrics, and instructor explanations before payload serialization.
4. **Uniform Response Envelope:** Standard envelope across all endpoints:
   ```json
   {
     "ok": true,
     "data": { ... },
     "error": null,
     "meta": {
       "request_id": "req-uuid4",
       "timestamp": "2026-10-01T23:30:00Z"
     }
   }
   ```
5. **Real Live Subsystem Probes:** Kubernetes-style endpoints (`/healthz`, `/readyz`, `/livez`) execute live, non-mocked probes against the SQLite database connection, model manifest registry, and storage subsystems.

---

## 2. Authentication & Authorization

All authenticated endpoints accept a JSON Web Token (JWT) in the HTTP `Authorization` header:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### Role-Based Access Control (RBAC) Hierarchy

| Role | Scope | Permissions |
|---|---|---|
| `SUPER_ADMIN` | Global platform-wide | Full read/write access to all organizations, courses, users, and audit logs. |
| `ORG_ADMIN` | Organization-scoped | Manage classes, cohorts, teachers, students, course offerings, and fee structures within the organization. |
| `COURSE_ADMIN` | Organization + Course | Author courses, publish versions, edit question banks, and review syllabus changes. |
| `TEACHER` | Assigned cohorts/classes | Create formative assessments, grade submissions, issue hierarchical instructions, access teacher copilot. |
| `STUDENT` | Enrolled courses | Participate in tutoring sessions, take sanitized assessments, view own mastery state. |
| `PARENT` | Linked student | View linked student progress and fee balances (privacy-restricted). |

---

## 3. Subsystem Route Specifications

### 3.1 Platform Health & Diagnostics
- `GET /healthz` — Basic liveness probe (200 OK).
- `GET /livez` — Server responsiveness check.
- `GET /readyz` — Full readiness check verifying database connectivity, storage readability, and AI model routing readiness. Returns 503 if any subsystem fails.
- `GET /api/v1/health` — Detailed health telemetry returning per-subsystem probe latencies and status flags.

### 3.2 Authentication & User Security
- `POST /api/v1/auth/register` — Register a new user with email, password hash, role, and organization ID.
- `POST /api/v1/auth/login` — Authenticate credentials via PBKDF2/argon2; returns JWT access token.
- `POST /api/v1/auth/refresh` — Refresh expired access token with valid refresh token.
- `POST /api/v1/auth/logout` — Invalidate and blacklist active JWT token.
- `GET /api/v1/auth/me` — Return profile metadata of authenticated actor.
- `POST /api/v1/auth/users/{user_id}/suspend` — Administrative action to suspend account; instantly blocks all authenticated requests with `403 Account Suspended`.

### 3.3 Organizations & Multi-Tenancy
- `POST /api/v1/organizations` — Provision new organization tenant (`SUPER_ADMIN` required).
- `GET /api/v1/organizations` — List active organizations with pagination.
- `GET /api/v1/organizations/{org_id}` — Retrieve organization details and configuration.
- `PUT /api/v1/organizations/{org_id}` — Update organization branding, policies, or domain.

### 3.4 Courses & Curriculum Versioning
- `GET /api/v1/courses` — List public catalog courses plus courses owned by requester's organization.
- `POST /api/v1/courses` — Create new course (`TEACHER`, `ORG_ADMIN`, `SUPER_ADMIN`).
- `GET /api/v1/courses/{course_id}` — Retrieve course metadata (enforces private visibility scoping).
- `POST /api/v1/courses/{course_id}/select` — Select course for organization offering, pinning active version.
- `GET /api/v1/courses/{course_id}/versions` — List all versions of a course.
- `POST /api/v1/courses/{course_id}/versions` — Create new draft version.
- `POST /api/v1/courses/{course_id}/versions/{version_id}/submit` — Submit draft for administrative review.
- `POST /api/v1/courses/{course_id}/versions/{version_id}/publish` — Approve and publish course version.

### 3.5 Classes, Cohorts & Enrollments
- `POST /api/v1/classes` — Create class group within organization.
- `GET /api/v1/classes` — List class groups filtered by organization.
- `POST /api/v1/classes/{class_id}/cohorts` — Create academic cohort within class group.
- `GET /api/v1/classes/{class_id}/cohorts` — List cohorts for class group.
- `POST /api/v1/enrollments` — Enroll student into course, cohort, or class group.
- `GET /api/v1/enrollments/student/{student_id}` — List active course enrollments for a student.

### 3.6 Hierarchical Teacher Instructions (Phase 07)
- `POST /api/v1/instructions` — Issue teacher instruction at Organization, Course, Class, Cohort, or Student scope.
- `GET /api/v1/instructions/resolve` — Query effective instruction cascade for a student session using 5-tier inheritance.

### 3.7 Question Bank & Assessment Delivery (Phase 11)
- `POST /api/v1/assessments/questions` — Create question bank item with rubric, difficulty, bloom level.
- `GET /api/v1/assessments/questions` — Filter questions by course, concept, difficulty, or item type.
- `POST /api/v1/assessments` — Create diagnostic, formative, summative, or adaptive assessment.
- `GET /api/v1/assessments/{assessment_id}/sanitized` — Retrieve student examination payload (answers and rubrics scrubbed).
- `POST /api/v1/assessments/attempts/start` — Start timed assessment attempt.
- `POST /api/v1/assessments/attempts/{attempt_id}/submit` — Submit answers; triggers hybrid auto-grading and logs central learning events.
- `POST /api/v1/assessments/attempts/{attempt_id}/review` — Teacher score adjustment and feedback sign-off.
- `POST /api/v1/assessments/attempts/{attempt_id}/reassess` — Automatically generate targeted reassessment on weak concepts.

### 3.8 Tutor Orchestrator & Live Turn Execution (Phase 10)
- `POST /api/v1/tutor/turn` — Execute 16-step generic tutoring turn.
  - **Request:**
    ```json
    {
      "student_id": "usr-student-01",
      "session_id": "sess-uuid4",
      "course_id": "crs-cs-101",
      "student_input": "How does quicksort partition work?"
    }
    ```
  - **Response:**
    ```json
    {
      "ok": true,
      "turn_id": "trn-uuid4",
      "student_id": "usr-student-01",
      "course_id": "crs-cs-101",
      "response_text": "Quicksort selects a pivot element...",
      "pedagogical_action": "SocraticQuestion",
      "validation_passed": true,
      "state_committed": true
    }
    ```

---

## 4. Error Status Codes & Failure Protocol

| Code | Meaning | Condition |
|---|---|---|
| `400 Bad Request` | Validation failure | Malformed payload, invalid difficulty range, missing mandatory fields. |
| `401 Unauthorized` | Missing / Invalid Token | Missing Authorization header, expired JWT, or tampered signature. |
| `403 Forbidden` | Access Denied | Suspended account, unauthorized role, unassigned cohort, or access to private course of another org. |
| `404 Not Found` | Entity Missing | Course, user, assessment, attempt, or version ID not found in database. |
| `409 Conflict` | Unique Constraint | Duplicate user email, duplicated course code, or active concurrent attempt. |
| `503 Service Unavailable` | Subsystem Failure | Critical probe down during readiness check (`/readyz`). |
