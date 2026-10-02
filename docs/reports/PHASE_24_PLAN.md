# Phase 24 Plan: Real End-to-End Journeys & Browser/Desktop Verification

**Document:** `docs/reports/PHASE_24_PLAN.md`  
**Phase:** 24  
**Section:** Section 34 of `GAYATRI_MASTER_PHASE_BY_PHASE_EXECUTION_AND_RECOVERY_GUIDE.md` & Section 12.24 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  
**Status:** APPROVED / IN_PROGRESS  

---

## 1. Objective

Replace synthetic or isolated unit assumptions with authoritative, multi-persona End-to-End (E2E) journeys operating directly across the live application boundaries:
`Frontend/Desktop UI` → `Central Platform REST API (FastAPI)` → `Auth & RBAC Layer` → `Course & Version Domain` → `Scoped RAG Engine` → `AI Gateway` → `Two-Phase State Commit Pipeline` → `Persistent SQLite Database`.

---

## 2. Current vs. Target Behavior

| Subsystem | Current State (Pre-Phase 24) | Target Behavior (Phase 24) |
|---|---|---|
| **E2E Testing Coverage** | Unit and route-level integration tests pass; previous `test_phase23_e2e_journeys_master.py` was limited to 3 smoke tests hardcoding `crs-chem-101`. | Comprehensive multi-course E2E test suite covering full lifecycles for Student, Teacher, and Admin personas over clean dynamic loopback sockets. |
| **Course Independence** | Course models and tutor orchestrator support generic courses; E2E journeys must prove multi-course execution across non-chemistry subjects (e.g. Physics, History, Programming). | E2E journeys execute against real generic courses with zero Chemistry default coupling. |
| **Negative Journey Verification** | Security and failure recovery tested in isolation (Phase 22/23). | 11 adversarial negative journeys exercised directly through live HTTP API and application facades. |
| **Desktop / Portal Shell Verification** | Portal controllers exist; headless test verification of controller bindings, HTML/CSS asset delivery, and theme/i18n switching required. | Programmatic headless verification of PySide6 portal bridges and design system asset delivery. |

---

## 3. Mandatory User Journeys

### Journey A: Student Real E2E Loop
1. Student registers / authenticates via signed JWT token cryptographically bound to user ID, org ID, and `STUDENT` role.
2. Student discovers available public courses and enrolled org offerings (`GET /api/v1/courses`).
3. Student enrolls in generic course (e.g. `crs-physics-101`).
4. Student starts learning session (`POST /api/v1/sessions`).
5. Student asks pedagogical question over live HTTP API (`POST /api/v1/tutor/turn`).
6. Tutor routes question through Scoped RAG, AI Gateway, Socratic response planner, and anti-answer leakage sanitizer.
7. Learning events staged and atomically committed to persistent DB (`learning_events` and `mastery_states`).
8. Student inspects SLR progress and mastery state (`GET /api/v1/students/{student_id}/progress`).
9. Application restart simulation: instantiate new runtime engine from DB, verify session resumption and state continuity.

### Journey B: Teacher Real E2E Loop
1. Teacher authenticates (`UserRole.TEACHER`).
2. Teacher inspects assigned courses and class groups.
3. Teacher uploads course knowledge asset (`POST /api/v1/rag/sources`).
4. Teacher submits knowledge asset for review (`READY_FOR_REVIEW`).
5. Admin approves and publishes knowledge asset (`PUBLISHED`).
6. Teacher creates hierarchical pedagogical instruction (`POST /api/v1/instructions`).
7. Teacher inspects class student roster, mastery analytics, and student health metrics.
8. Teacher assigns intervention / review to student.

### Journey C: Admin Real E2E Loop
1. Organization Admin authenticates (`UserRole.ORG_ADMIN`).
2. Admin creates new generic course and defines visibility policy (`PUBLIC` vs `PRIVATE`).
3. Admin creates course version draft, uploads curriculum, and submits for review.
4. Admin approves and publishes course version (verifying immutability gate).
5. Admin creates organization course offering (`POST /api/v1/courses/offerings`).
6. Admin inspects platform audit logs (`GET /api/v1/audit/logs`) and system health probes (`/healthz`, `/readyz`, `/livez`).

---

## 4. Mandatory Adversarial & Negative Journeys

1. **NJ-1 (Wrong Tenant Isolation):** Student from Org B attempts to access private course of Org A → HTTP 403 Forbidden.
2. **NJ-2 (IDOR Student Isolation):** Student A attempts to access Student B's session or SLR → HTTP 403 Forbidden.
3. **NJ-3 (Class-Scoped RAG Isolation):** Student from Class Y queries RAG for Class X-restricted notes → 0 chunks returned (zero leakage).
4. **NJ-4 (Wrong Course Rejection):** Tutor turn request with non-existent `course_id` → HTTP 404 CourseNotFoundError.
5. **NJ-5 (Unpublished Course Version):** Student turn request against `DRAFT` course version → HTTP 403/404 Forbidden.
6. **NJ-6 (Unpublished Content Invariant):** Draft or processing knowledge assets must never appear in student RAG responses.
7. **NJ-7 (Expired Instruction Eviction):** Instruction past its expiration timestamp must be excluded from prompt directive hierarchy.
8. **NJ-8 (Unauthorized Tool Denial):** Student invokes tool disabled by course tool policy → ToolExecutionError / HTTP 403.
9. **NJ-9 (Missing Model Resilience):** AI Gateway handles missing model file gracefully, returning safe diagnostic message without 500 crash.
10. **NJ-10 (RAG Failure Tolerance):** RAG service error degrades gracefully to curriculum syllabus without session crash.
11. **NJ-11 (Database Failure Atomic Rollback):** Database write failure triggers state rollback (`state_committed=False`) with zero partial writes.

---

## 5. Affected Files & Modules

- **Test Suite:** `tests/test_phase24_e2e_journeys_real.py` (New comprehensive E2E test file)
- **Portal Controllers:** `central_platform/portals/student.py`, `teacher.py`, `parent.py`, `fee_admin.py`
- **Application Shell:** `app/windows/main_window.py`, `app/bridge/facade.py`
- **API Routers:** `central_platform/api/routes/` (`courses.py`, `tutor.py`, `rag.py`, `instructions.py`, `students.py`, `assessments.py`)
- **Documentation & Tracking:** `docs/reports/PHASE_24_PLAN.md`, `docs/reports/PHASE_24_TEST_REPORT.md`, `docs/reports/PHASE_24_TEST_RESULTS.json`, `docs/reports/DEVELOPMENT_LOG.md`, `PROJECT_STATE.yaml`

---

## 6. Acceptance Criteria & Gate

- [ ] All 3 mandatory positive journeys (Student, Teacher, Admin) execute successfully end-to-end.
- [ ] All 11 negative journeys fail safely with explicit, classified errors and zero security breaches.
- [ ] PySide6 portal controllers and design system asset delivery verified headless.
- [ ] Zero hardcoded Chemistry defaults in new tests.
- [ ] Regression suite remains 100% green (1,114+ tests passing).
- [ ] `docs/reports/PHASE_24_TEST_REPORT.md` and `docs/reports/PHASE_24_TEST_RESULTS.json` generated with honest metrics.
- [ ] Changes committed and pushed to GitHub with verified matching remote SHA.
