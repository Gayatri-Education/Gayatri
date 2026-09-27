# V2 Platform Progress

## Overall

Status: IN_PROGRESS  
Current Phase: 12  
Overall Completion: 40.0% (12/30 Phases)  
Last Verified Commit: d8d1271 (Phase 11)  
Last Full Regression: 2026-09-27 (536/536 passed)  
Last Full Backtest: 2026-09-27 (scripts/run_frozen_baseline.py 44/44 passed)  
Open P0: 0  
Open P1: 0  
Open P2: 0  
Open P3: 0  

## Phase Matrix

| Phase | Description | Status | Unit | Integration | Regression | Backtest | Security | Frontend | Docs | Debug | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 00 | Truth Reset / Repo Reconciliation | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 1481123 |
| 01 | Stabilize the Core Tutor | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | e754ed5 |
| 02 | Real Platform API | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | a6c3417 |
| 03 | PostgreSQL Central Data Layer | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 086ca24 |
| 04 | Authentication + RBAC | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | bccd694 |
| 05 | Central Learning Event System | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | c8de429 |
| 06 | Authoritative Student Learning Record | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 7da7d79 |
| 07 | Connect Existing Learning Engine | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 5dd4890 |
| 08 | Real Desktop ↔ Platform Sync | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 1b23c00 |
| 09 | Student Progress API + UI | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 4a3c131 |
| 10 | Teacher Web Portal | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | 7c9ec5d |
| 11 | Teacher AI Instructions | VERIFIED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | d8d1271 |
| 12 | Teacher Intervention System | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 13 | Teacher Copilot | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 14 | Admin Web Portal | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 15 | Plug-and-Play Curriculum | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 16 | RAG Plug-and-Play | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 17 | Real AI Gateway + Model Router | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 18 | AI Governance / Observability | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 19 | Assessment Platform | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 20 | Analytics | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 21 | Notifications | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 22 | Security Hardening | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 23 | Real End-to-End Testing | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 24 | Failure / Recovery Testing | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 25 | Performance / Scale Testing | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 26 | Data Migration / Backup / Restore | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 27 | Production Operations | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 28 | Final Cleanup | NOT_STARTED | - | - | - | - | - | - | - | - | - |
| 29 | Final Audit | NOT_STARTED | - | - | - | - | - | - | - | - | - |

## Current Phase

### Objective
Execute Phase 11 (Teacher AI Instructions): Enable teachers to influence AI tutoring for specific students safely and deterministically without ever bypassing critical system safeguards. Implement scope (student, cohort, course, concept), priority, temporal bounds (start_at, expires_at), status lifecycle, immutable audit trail, policy validation enforcing 5 non-negotiable invariants (security, safety, system policy / anti-answer leakage, authorization, deterministic calculations), and AI context builder tutor prompt injection with invariant guardrails.

### Implemented
- Canonical Teacher Instruction entity (`central_platform/teacher/instruction.py` and `central_platform/models/schema.py`) covering all Section 20 fields (`instruction_id`, `teacher_id`, `student_id`, `course_id`, `instruction_text`, `concept_scope`, `scope_type`, `priority`, `start_at`, `expires_at`, `status`, `safety_status`, `safety_reasons`, `audit_trail`, `version`).
- Robust Policy & Invariant Validation Engine (`TeacherInstructionValidator` in `central_platform/teacher/instruction.py`) enforcing zero tolerance for overrides on:
  1. Security (prompt injection, jailbreak, system prompt reveal, code execution)
  2. Safety (toxicity, slurs, harassment, abuse)
  3. System Policy (anti-answer leakage, skipping questioning, giving direct solutions)
  4. Authorization (privilege escalation, secret harvesting, data dumps)
  5. Deterministic Calculations (forcing mastery scores, overriding stoichiometry / chemistry facts)
- Enhanced `TeacherInstructionEngine` with student context resolution, temporal filtering (`start_at <= now <= expires_at`), priority hierarchy sorting, update/revocation tracking with immutable audit trail, and prompt directive generation.
- Tutor prompt injection integration in `core/runtimes/chemistry.py` safely binding teacher instructions within explicit `[SYSTEM INVARIANT NOTE]` guardrails.
- Central REST API endpoints in `central_platform/api/routes/teachers.py`:
  - `POST /teachers/instructions/validate` (pre-flight validation endpoint)
  - `POST /teachers/instructions` (create directive with invariant validation, returning 422 if safety violated)
  - `GET /teachers/instructions` (list directives with filtering by student, course, status, active_only)
  - `GET /teachers/instructions/{id}` (fetch single directive with full audit trail)
  - `PATCH /teachers/instructions/{id}` (update priority, scope, expiration, status with audit logging)
  - `DELETE /teachers/instructions/{id}` (revoke directive with audit recording)
  - `POST /teachers/instructions/toggle` (enable/disable active state)
  - Strict RBAC: Student access is blocked with 403 Forbidden.
- Teacher Web Portal UI (`app/ui/teacher_portal.html`) enhanced with interactive directive creation form, priority selectors, concept scope input, expiration presets (24h, 7d, 30d, Never), real-time policy safety violation alerts, and one-click Revoke actions.
- Comprehensive Phase 11 test suite in `tests/test_phase11_teacher_instructions_platform.py` (11/11 passed, 0 failures, 0 warnings).
- Full regression suite: 536/536 tests passing repository-wide (0 failures, 0 warnings).
- Frozen baseline: 44/44 benchmarks passing (100.0%).

### Files Changed
- `central_platform/teacher/instruction.py` (enhanced with Section 20 fields, validator, engine methods)
- `central_platform/models/schema.py` (updated TeacherInstructionRecord with Section 20 fields)
- `central_platform/api/schemas.py` (updated request/response schemas and validate request/response)
- `central_platform/api/routes/teachers.py` (added validate, get_by_id, update, delete endpoints, 422 validation error handling)
- `core/runtimes/chemistry.py` (integrated prompt directive formatting with invariant guardrails)
- `app/ui/teacher_portal.html` (enhanced teacher directives UI with priority, scope, expiry, audit, and revoke)
- `tests/test_phase11_teacher_instructions_platform.py` (created, 11 test cases)
- `docs/implementation/REGRESSION_REGISTER.md` (updated)
- `docs/implementation/V2_PLATFORM_PROGRESS.md` (updated)

### Tests Added
- `tests/test_phase11_teacher_instructions_platform.py` (11 test cases covering: allowed pedagogical instructions, rejection of prompt injection, rejection of anti-answer leakage attempts, rejection of authorization escalation and calculation falsification, scoping isolation across student/cohort/concept, temporal expiration and auto-transition to EXPIRED, immutable audit trail lifecycle across create/update/revoke, prompt directive generation with invariant reminders, REST API pre-flight validation endpoint, REST API full CRUD and 422 error rejection, and RBAC 403 Forbidden enforcement against student tokens).

### Tests Passed
- 536 / 536 pytest tests passed (0 failures, 0 warnings).
- 44 / 44 frozen baseline benchmarks passed (100%).

### Security
- Teacher instructions undergo deterministic invariant validation before creation or update; unsafe instructions are rejected with 422 Unprocessable Entity.
- RBAC strictly prohibits students from creating, updating, revoking, or inspecting other students' instructions (403 Forbidden).
- Tutor runtime injects directives wrapped with explicit invariant constraints ensuring LLM cannot be commanded to leak answers or violate policies.

### Frontend
- Teacher portal single-page application (`app/ui/teacher_portal.html`) enhanced in the `instructions` subview with priority badges, concept scopes, expiration countdowns, validation error banners, and revocation controls.

### Bugs Found
- 0 open bugs.

### Bugs Fixed
- Expanded `CALC_PATTERNS` regex to detect compound terms like "mastery score" alongside standalone "mastery".
- Replaced deprecated `status.HTTP_422_UNPROCESSABLE_ENTITY` with `422` to eliminate StarletteDeprecationWarning.
- Added missing `datetime` and `timezone` imports in `central_platform/api/routes/teachers.py`.

### Known Issues
- None.

### Remaining Work
- Phase 11 complete and verified. Ready to present and execute Phase 12 (Teacher Intervention System).

### Commit
- d8d1271 (Phase 11: Teacher AI Instructions)

### Verification Evidence
- `pytest` run output: 536 passed in 42.09s.
- `python scripts/run_frozen_baseline.py` output: 44/44 passed (100.0%).

