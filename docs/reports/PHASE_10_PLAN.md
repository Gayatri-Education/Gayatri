# Phase 10 Implementation Plan: Generic Tutor Orchestrator

**Document ID:** `PHASE_10_PLAN`  
**Phase:** 10  
**Parent Plan:** [GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md](../../GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md) (Section 12.10)  
**Target Branch:** `master`  
**Author:** Antigravity AI  
**Status:** DRAFT - PENDING APPROVAL  

---

## 1. Executive Summary & Objectives

The primary objective of Phase 10 is to build the central tutoring flow around course context rather than a hardcoded Chemistry mode. The new `GenericTutorOrchestrator` unifies the end-to-end 16-step tutoring lifecycle across identity, enrollment, versioning, hierarchy-aware instruction, scoped RAG, pedagogy planning, AI gateway execution, response validation, transactional state commit, and telemetry.

### Key Objectives
1. **Generic Course Orchestrator (`central_platform/tutor/orchestrator.py`)**:
   - Zero hardcoded subject keywords (`chemistry`, `thermodynamics`, `hess`).
   - Pure course-independent execution driven by `CourseLearningContext` and domain models.
2. **Deterministic 16-Step Turn Lifecycle**:
   - Step 1: Identity validation (non-empty `student_id`, `session_id`, rejecting magic defaults per Rule 4).
   - Step 2: Enrollment validation (verifies student enrollment in `course_id`).
   - Step 3: Course & Version resolution (`CourseService` / DB, verifying course status).
   - Step 4: Class/Cohort resolution (resolves class-targeted context).
   - Step 5: Learning state resolution (`LearningStateManager` isolated by `(student_id, course_id)`).
   - Step 6: Hierarchical instruction resolution (`TeacherInstructionEngine` cascading `SESSION > STUDENT > CLASS > COURSE > ORGANIZATION`).
   - Step 7: Course policy enforcement (`CoursePolicy` permissions, Socratic strictness).
   - Step 8: Course tool policy check (`CourseToolPolicy` / `ToolRegistry`).
   - Step 9: Scoped RAG retrieval (`RAGService` scoped to `course_id` and `course_version_id`).
   - Step 10: 7-Layer conversation context assembly (`ContextBuilder`).
   - Step 11: Pedagogical response planning (`ResponsePlannerEngine`).
   - Step 12: AI Gateway execution (`AIGatewayService` with local/fallback routing).
   - Step 13: 7-Invariant response validation (`ResponseValidatorEngine`).
   - Step 14: Learning evidence staging (buffer proposed mastery and misconceptions).
   - Step 15: Transactional two-phase state commit (`StateCommitPipeline`, rolling back on validation failure).
   - Step 16: Telemetry and audit logging.
3. **Core Orchestrator Reconciliation (`core/orchestrator.py`)**:
   - Preserve backward-compatibility for legacy callers and tests.
   - Clean up magic identities and ensure generic course awareness.
4. **REST API & Platform Integration**:
   - Provide `/api/v1/tutor/turn` REST endpoint mounted on the FastAPI platform app.
5. **Comprehensive Integration Test Suite (`tests/test_phase10_generic_tutor_orchestrator.py`)**:
   - Valid course execution across multiple subjects (Physics, Programming, History, Chemistry).
   - Invalid course rejection (`CourseNotFoundError`).
   - Unauthorized enrollment rejection (`EnrollmentError`).
   - Empty curriculum handling.
   - RAG empty graceful fallback.
   - Model unavailable fallback.
   - State rollback when response validation fails (anti-answer leakage, safety).
   - Streaming interruption & duplicate turn deduplication.
   - Zero Chemistry branch invariants in generic layer.

---

## 2. Architecture & Call Graph

```text
Student Client / API / Bridge
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│               GenericTutorOrchestrator                       │
│                                                             │
│  [1. Validate Identity]       [2. Validate Enrollment]      │
│  [3. Resolve Course/Version]  [4. Resolve Class/Cohort]     │
│  [5. Fetch SLR State]         [6. Hierarchical Instructions]│
│  [7. Course Policy]           [8. Tool Policy]              │
│  [9. Scoped RAG Search]       [10. ContextBuilder 7-Layer]  │
│  [11. ResponsePlanner]        [12. AIGatewayService]        │
│  [13. ResponseValidator]      [14. Stage Learning Evidence] │
│  [15. StateCommitPipeline]    [16. Telemetry & Return]      │
└─────────────────────────────────────────────────────────────┘
      │               │                   │              │
      ▼               ▼                   ▼              ▼
LearningState    TeacherEngine        AIGateway      CommitPipeline
```

---

## 3. Detailed Implementation Steps

### Step 1: Implement `GenericTutorOrchestrator` (`central_platform/tutor/orchestrator.py`)
- Define `TutorTurnRequest` and `TutorTurnResult` dataclasses.
- Implement `GenericTutorOrchestrator` with full 16-step pipeline.
- Implement both `execute_turn()` (synchronous complete turn) and `stream_turn()` (streaming tokens).

### Step 2: REST Endpoints in `central_platform/api/routes/tutor.py`
- Mount `/api/v1/tutor/turn` on FastAPI app with OpenAPI schemas and JWT authentication.

### Step 3: Align `core/orchestrator.py`
- Maintain legacy signatures (`TurnOptions`, `submit`) while ensuring generic course parameter passing without hardcoded Chemistry branching.

### Step 4: Write `tests/test_phase10_generic_tutor_orchestrator.py`
- Cover all mandatory test scenarios specified in Section 12.10.

---

## 4. Verification and Rollout Gate

1. `pytest tests/test_phase10_generic_tutor_orchestrator.py -v` (100% pass)
2. Full suite run: `pytest` (946+ tests passing, 0 regressions)
3. Generate `docs/reports/PHASE_10_TEST_REPORT.md` and `docs/reports/PHASE_10_TEST_RESULTS.json`
4. Update tracking ledgers: `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`
5. Commit and push to `origin/master`
