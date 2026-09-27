# Gayatri AI Platform — API Contract Specification (V2)

## 1. Overview & Architectural Principles

The Gayatri AI Platform exposes a unified, authoritative, versioned REST API under `/api/v1/*`.
All external clients (Student Desktop GUI, Teacher Web Command Center, Institution Admin Portal, and Automated CI/CD Pipelines) interact with this API.

### Core Tenets
1. **Authoritative State**: Central API is the source of truth for organizations, users, curricula, and canonical Student Learning Records (SLR).
2. **Three-Sided Architecture**: Clean RBAC boundaries separating `STUDENT`, `TEACHER`, and `ADMIN` personas.
3. **Correlation & Traceability**: Every request carries an `X-Request-ID` header; missing IDs are automatically generated as UUIDv4 and echoed in responses.
4. **Structured Envelopes**: All responses adhere to standard success or error JSON envelopes.
5. **Backwards Compatibility**: Legacy endpoints (`/api/health`, `/api/student/snapshot`, `/api/teacher/*`, `/instruction/*`, `/alert/*`) are maintained with 100% parity.

---

## 2. Standard Envelopes & Error Contracts

### 2.1 Standard Success Envelope (`ApiResponse[T]`)
```json
{
  "ok": true,
  "data": { ... },
  "meta": {
    "request_id": "req-9a8b7c6d5e",
    "timestamp": "2026-09-27T18:00:00Z",
    "api_version": "v1"
  }
}
```

### 2.2 Standard Error Envelope
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR | HTTP_404 | HTTP_401 | UNHANDLED_SERVER_ERROR",
    "message": "Human-readable explanation of error",
    "details": { ... }
  },
  "meta": {
    "request_id": "req-9a8b7c6d5e",
    "timestamp": "2026-09-27T18:00:00Z",
    "api_version": "v1"
  }
}
```

---

## 3. Versioned Route Groups (`/api/v1/*`)

| # | Route Prefix | Group Name | Description & Key Operations |
|---|--------------|------------|------------------------------|
| 1 | `/auth` | Authentication | `/login`, `/me`, `/refresh`, `/logout` (Bearer JWT / API Key) |
| 2 | `/users` | Identity & Users | CRUD for platform users, RBAC roles (`STUDENT`, `TEACHER`, `ADMIN`) |
| 3 | `/students` | Student Operations | Profile lookup, telemetry snapshot ingestion, canonical SLR retrieval |
| 4 | `/teachers` | Teacher Operations | Live cohort dashboard, pedagogical instructions, intervention alerts, copilot briefing |
| 5 | `/admin` | Administration | Organization management, system telemetry, kill switches, audit logs |
| 6 | `/courses` | Courses | Course catalog, subjects (Physics, Chemistry, Math, Biology), metadata |
| 7 | `/curricula` | Curricula | Syllabus tree, chapters, concepts, prerequisite dependency graphs |
| 8 | `/enrollments`| Enrollments | Student enrollment, class assignment, active status |
| 9 | `/sessions` | Tutoring Sessions | Interactive session lifecycle: `start`, status lookup, `end` |
| 10 | `/learning` | Learning Telemetry | Real-time event ingestion (`turn_completed`, `hint_used`), adaptive next-step recommendations |
| 11 | `/assessments`| Assessments | Diagnostic item retrieval, student answer submission, scoring |
| 12 | `/rag` | Knowledge Retrieval| NCERT-grounded RAG retrieval, citation verification, evidence cards |
| 13 | `/ai` | AI Gateway | Model provider status (Local GGUF, Central Fine-Tuned, Claude, DeepSeek fallback) |
| 14 | `/analytics` | Cohort Analytics | Mastery distribution, misconception frequency analysis, retention trends |
| 15 | `/notifications`| Notifications | System alerts, teacher direct notices, student milestones |
| 16 | `/sync` | Synchronization | Batch offline event sync, idempotent replay, device-to-student authorization |

---

## 4. Platform Probes & Telemetry

| Endpoint | Method | Response Model | Description |
|----------|--------|----------------|-------------|
| `/healthz` | GET | `HealthStatusResponse` | Service online state, component status, version |
| `/readyz` | GET | `{"ready": true, ...}` | Readiness probe for Kubernetes / Load Balancer |
| `/livez` | GET | `{"alive": true}` | Liveness heartbeat probe |

---

## 5. Security & Authentication Scheme

- **Mechanism**: Bearer token authentication via HTTP `Authorization: Bearer <token>`.
- **RBAC Roles**:
  - `STUDENT`: Scoped to own learning sessions, SLR, and telemetry sync.
  - `TEACHER`: Scoped to assigned cohorts, instructions dispatch, and alert resolution.
  - `ADMIN`: Global scope for org onboarding, model configuration, and platform kill switches.
- **Correlation**: `X-Request-ID` is mandatory for audit logging across microservices.
