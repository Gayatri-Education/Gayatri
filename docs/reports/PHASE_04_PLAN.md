# Phase 04 Execution Plan — Course-Scoped Student Learning State & Sessions

**Document:** `docs/reports/PHASE_04_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.4)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Establish authoritative, course-scoped and version-aware student learning state across sessions, events, mastery records, misconceptions, review queues, and progress queries. The system must guarantee that a student enrolled in multiple courses simultaneously (e.g., Chemistry and Physics) experiences complete isolation between courses, preventing cross-course state or mastery contamination even when concepts share identical local names.

---

## 2. Forensic Findings & Multi-Course Isolation Strategy

1. **Current Couplings & Gaps:**
   - `central_platform/db.py`: `create_session` currently omits `course_version_id` and `class_id` from insert statements, even though the database schema columns exist.
   - `central_platform/learning/state.py`: `SessionRuntimeState` and `initialize_session` do not track `course_version_id` or `course_offering_id`.
   - `core/tutor/state.py`: `LearningEvent` and `TutorStateManager` omit `course_id`, defaulting implicitly to a single course context.
   - Ambiguous identity fallbacks: `student_id = session_id` or default fallbacks without explicit course context exist in legacy shims.
2. **Target Architecture:**
   - **Authoritative `CourseLearningContext`:** Strongly typed context requiring non-empty `student_id` and `course_id`, with optional `course_version_id`, `organization_id`, `cohort_id`, and `class_id`.
   - **Course-Scoped Sessions:** Every session explicitly binds to `course_id` and `course_version_id`.
   - **Composite Key Isolation:** `StudentLearningRecord` (SLR) is uniquely partitioned by `(student_id, course_id)`. Mastery states belong exclusively to their respective course's SLR.
   - **Idempotent Telemetry Events:** Learning events enforce idempotent deduplication via `event_id` or composite hash, preventing double-counting on network retries or replay.
   - **Cross-Course Isolation Invariant:** If a student practices a concept with the same identifier (e.g., `"thermo"` or `"functions"`) in two distinct courses, progress, mastery scores, confidence estimates, and learning history in Course A MUST remain strictly isolated from Course B.

---

## 3. Planned Implementation Details

### Step 1: Authoritative `CourseLearningContext` & Model Enhancements (`central_platform/models/schema.py`)
- Implement `CourseLearningContext`:
  - Fields: `student_id`, `course_id`, `organization_id`, `course_version_id`, `course_offering_id`, `cohort_id`, `class_id`.
  - Methods: `validate()`, `to_dict()`.
- Update `Session`: Ensure `course_version_id`, `course_offering_id`, and `class_id` are included in dataclass definition and serialization.
- Update `LearningEvent`: Ensure `course_id`, `organization_id`, `course_version_id` are fully integrated.

### Step 2: Database Layer Enhancements (`central_platform/db.py`)
- Update `create_session` and `get_session` to persist and load `course_version_id`, `course_offering_id`, and `class_id`.
- Update `get_sessions_for_student` to accept optional `course_id` parameter to filter sessions by course.
- Update `query_learning_events` to support course-scoped event retrieval.

### Step 3: Central Learning State Manager (`central_platform/learning/state.py`)
- Update `SessionRuntimeState` to include `course_version_id`, `course_offering_id`, and `class_id`.
- Refactor `LearningStateManager`:
  - `initialize_session(context: CourseLearningContext | dict, concept_id: str)`: Enforces valid course context and binds session.
  - `get_canonical_state(student_id: str, course_id: str)`: Strictly requires course_id; rejects empty course context.
  - `update_mastery(student_id: str, course_id: str, concept_id: str, score: float, ...)`: Modifies only the course-specific SLR.
  - `log_event(session_id: str, event_type: str, data: dict)`: Ingests events with session course scope and idempotent deduplication.

### Step 4: Core Tutor State Backwards-Compatible Course Scoping (`core/tutor/state.py`)
- Extend `LearningEvent` and `StudentConceptMastery` with optional `course_id: str = "chemistry"`.
- Update `TutorStateManager` methods to accept optional `course_id`.

---

## 4. Test Strategy & Acceptance Gate

Create dedicated test suite `tests/test_phase04_course_learning_state.py` covering:
1. **Cross-Course Contamination Matrix:**
   - Same student enrolled in Chemistry and Physics.
   - Practice concept `"thermo"` in Chemistry -> verifies Chemistry mastery updates, Physics mastery remains 0.0/unaffected.
   - Practice concept `"thermo"` in Physics -> verifies Physics mastery updates, Chemistry mastery remains unchanged.
2. **Session and Event Isolation:**
   - Sessions created in Course A are not listed when querying Course B.
   - Telemetry events logged in Course A are not returned when querying Course B.
3. **Idempotent Telemetry Enforcement:**
   - Submitting an event with the same `event_id` multiple times does not create duplicates or double-count attempts/mastery.
4. **State Persistence & Exact Recovery:**
   - Re-instantiating `LearningStateManager` or reopening database connection restores exact multi-course state without data drift.
5. **Authorization & Tenant Boundary:**
   - Attempting to query or modify state with missing `course_id` raises a validation error.
   - Cross-student access is denied.
6. **Full Regression Gate:** All 880 existing tests pass without modification.

---

## 5. Artifacts to Generate Upon Completion

- `docs/reports/PHASE_04_PLAN.md` (this plan)
- `docs/reports/PHASE_04_TEST_REPORT.md`
- `docs/reports/PHASE_04_TEST_RESULTS.json`
- Updates to `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`
