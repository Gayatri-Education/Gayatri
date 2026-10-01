# Testing Strategy & E2E Validation Target Specification — Gayatri Platform

**Document:** `docs/TESTING_STRATEGY_TARGET.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** FROZEN (Phase 1 Deliverable)  
**Governing Plan:** `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## 1. 5-Level Testing Pyramid (Section 30)

```text
                           ▲
                          / \
                         /   \     Level 5: Failure Injection (Network, Stale Versions, Corruption)
                        /     \
                       /───────\   Level 4: Real Application E2E (UI -> API -> DB -> RAG -> AI -> State)
                      /         \
                     /───────────\ Level 3: Integration (Services, Repositories, RAG, Evaluators)
                    /             \
                   /───────────────\ Level 2: Unit Tests (Algorithms, DAGs, Evaluators, Resolvers)
                  /                 \
                 /───────────────────\ Level 1: Static Architectural Guards & Lints
```

### Level 1: Static Architectural Guards
Automated checks enforced during CI and pre-commit validation:
- **Zero Legacy Imports Guard:** CI fails if any production module under `core/`, `central_platform/`, or `app/` imports `legacy.*`.
- **Zero Generic Chemistry Coupling Guard:** CI fails if modules in generic layers contain hardcoded chemistry keywords (`thermodynamics`, `hess`, `ncert`, `crs-chem-101`) outside `adapters/chemistry/`, `tests/`, and `docs/`.
- **Zero Hardcoded Demo Roster Guard:** CI fails if fake user names (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`, `local_student_1`) appear in production code.
- **Bytecode & Schema Hygiene:** `compileall` must pass with 0 errors; migrations must not define duplicate tables.

### Level 2: Unit Testing
- Mathematical and algorithmic verification in isolation:
  - DAG cycle detection, topological prerequisite traversal.
  - Multi-factor mastery calculation with Ebbinghaus forgetting curve.
  - Spaced repetition scheduling and retention bounds ($[0.0, 1.0]$).
  - Deterministic evaluation logic (MCQ, numerical tolerance, unit conversion, rubric).
  - Hierarchical instruction resolver precedence rules.

### Level 3: Integration Testing
- Multi-component interaction testing:
  - Repository CRUD operations against SQLite and PostgreSQL.
  - Content parsing $\rightarrow$ cleaning $\rightarrow$ chunking $\rightarrow$ indexing pipeline.
  - Scoped RAG pre-retrieval authorization filters.
  - AI Gateway provider fallback and timeout policies.
  - Two-phase state staging and atomic commit/rollback.

### Level 4: Real Application E2E Testing
- Tests crossing the **actual application boundary**:
  $$\text{Web/Desktop UI} \longrightarrow \text{HTTP API} \longrightarrow \text{Domain Service} \longrightarrow \text{Database} \longrightarrow \text{Scoped RAG} \longrightarrow \text{AI Model} \longrightarrow \text{State Commit} \longrightarrow \text{UI Assertion}$$
- Directly calling Python engine methods in memory (e.g. `LearningEngine.calculate(...)`) is NOT an E2E test.

### Level 5: Failure Injection & Resilience
- Intentionally induced environmental failures:
  - Local model missing or corrupted.
  - Cloud provider timeout or invalid JSON syntax.
  - Vector store / RAG service unavailable.
  - Database connection locked or network partitioned during state commit.
  - Offline sync with partial network interruption, replay, and duplicate events.

---

## 2. Mandatory Acceptance Journeys (Section 27)

### Journey A: Public Course Lifecycle
1. Admin creates Course $C_{pub}$ with `visibility = PUBLIC`.
2. Course Version 1.0 created in `DRAFT`.
3. Teacher uploads course textbook. Content transitions `PROCESSING` $\rightarrow$ `READY_FOR_REVIEW`.
4. Admin reviews and approves content. Version 1.0 status transitions to `PUBLISHED`.
5. An unrelated School B discovers $C_{pub}$ in the public catalog and creates a local Course Offering pinned to Version 1.0.
6. School B enrolls students. School B students access $C_{pub}$ and query tutor.
7. Verification: School B students successfully retrieve textbook RAG chunks, but School B has zero visibility into School A students or notes.

### Journey B: Private Course Access Enforcement
1. School A creates Course $C_{priv}$ with `visibility = PRIVATE`.
2. School A teacher uploads proprietary content; admin approves and publishes.
3. School A students enroll and access $C_{priv}$.
4. A student or teacher from School B attempts to query, retrieve, or enroll in $C_{priv}$.
5. Verification: School B request is rejected with `403 Forbidden` (`AUTHORIZATION_ERROR`).

### Journey C: Class-Scoped Teacher Notes
1. Teacher uploads supplementary notes with `visibility_scope = CLASS` for `class_A`.
2. Content is approved and published.
3. Student in `class_A` asks a question; RAG retrieves the supplementary teacher notes.
4. Student in `class_B` (same course, different class) asks the identical question.
5. Verification: Student in `class_B` retrieves textbook content but CANNOT retrieve `class_A` notes.

### Journey D: Student-Scoped Remedial Material
1. Teacher creates remedial worksheet targeted specifically to students $S_1$ and $S_2$.
2. Content published with `visibility_scope = STUDENT` and `target_student_ids = ["S1", "S2"]`.
3. Students $S_1$ and $S_2$ view assignments and receive remedial explanations.
4. Student $S_3$ logs into portal and queries progress.
5. Verification: $S_3$ cannot view, search, or retrieve the remedial worksheet.

### Journey E: Multi-Course Student Mastery Isolation
1. Student $S_1$ enrolls simultaneously in Course 1 (Physics), Course 2 (Chemistry), and Course 3 (History).
2. $S_1$ completes 10 interactive problem turns in Physics with high accuracy.
3. Verification:
   - Physics concept mastery increases.
   - Chemistry concept mastery remains completely unchanged.
   - History progress remains completely unchanged.

### Journey F: Course Version Immutability & Session Pinning
1. Course Version 1.0 is `PUBLISHED`.
2. Student starts learning session linked to Version 1.0.
3. Teacher uploads major curriculum revisions as Version 2.0 (`DRAFT`).
4. Student continues session: Version 2.0 changes are not visible.
5. Admin approves and publishes Version 2.0.
6. Verification:
   - Existing historical session remains pinned to Version 1.0.
   - New sessions initiated after publication use Version 2.0.

### Journey G: Offline Operation & Idempotent Sync
1. Student launches desktop app in offline mode (no network connectivity).
2. Local tutor operates using local SQLite database, cached course content, and local SLM (`llama.cpp`).
3. Student completes 5 learning turns; learning events recorded in local `sync_outbox`.
4. App process terminates abruptly (simulated crash); app restarts offline.
5. State is restored completely from local SQLite database.
6. Network connectivity restored; sync outbox initiates batch upload to central server.
7. Verification:
   - Events committed to central server once.
   - Resending duplicate sync batch produces HTTP 200 with 0 duplicate learning events or state drift.

---

## 3. Anti-False-Green Rules (Section 33)

To ensure honesty and integrity in test reporting:
1. **No Assertion Degradation:** Assertions must not be weakened or simplified merely to make failing tests pass.
2. **No Silent Mocks in Integration:** Tests labeled "integration" or "E2E" must exercise real database, service, and RAG boundaries.
3. **No Unjustified Skips or XFails:** Tests must not be marked `@pytest.mark.skip` or `xfail` to conceal defects.
4. **No Synthetic Fallback Injections:** Production code must never return fake data or demo rosters to appease test runners.
5. **Mandatory Reporting Format:** Every phase generates machine-readable `PHASE_<N>_TEST_RESULTS.json` and Markdown `PHASE_<N>_TEST_REPORT.md` including exact command lines, exit codes, and timing.
