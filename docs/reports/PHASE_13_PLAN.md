# Phase 13 Plan: Offline Local Runtime Package & Sync Readiness

**Phase:** Phase 13 (Section 12.13 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`)  
**Objective:** Make the same course-independent system operate locally without network dependence for cached courses and local models, with honest degraded state detection, transactional persistence across restarts, and zero fake demo data.

---

## 1. Architectural Analysis & Problem Statement

### Current State & Findings
1. **Online/Offline Architecture Gap:**
   - In Phases 01–12, we built generic domain services (`CourseService`, `RAGService`, `GenericTutorOrchestrator`, `AssessmentService`, `LearningStateManager`, `PlatformDatabase`) and verified them over HTTP REST.
   - However, the desktop client and local offline environment still lack a cohesive, dedicated `local_runtime/` module that manages local course package caching, local RAG retrieval, offline capability detection, and offline session persistence.
2. **Hardcoded Demo Roster Bug (`BUG-ARCH-003`):**
   - In `app/bridge/facade.py` (lines 32–48), `get_teacher_portal_service()` injects fake students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`) with hardcoded `"crs-chem-101"` mastery and misconception data when running locally.
   - Section 12.13 explicitly mandates: *"Startup must detect missing course cache, detect missing model, show honest degraded state, and NEVER seed fake demo data."*
3. **Missing Offline Boundary & Cache Package Specification:**
   - Need an authoritative course cache format (`.gpk` / zipped JSON manifest with course metadata, curriculum DAG, concepts, question banks, and RAG knowledge chunks).
   - Need offline capability detector to probe:
     - Local SQLite database accessibility and write permissions.
     - Presence of local model weights (e.g. Ollama, GGUF/llama.cpp, or local fallback engine).
     - Cached vs uncached course availability.
     - Network connectivity status.
   - When offline without a cached course, system must honestly communicate that the course requires downloading rather than silently crashing or falling back to a hardcoded Chemistry course.
4. **Local State Survivability & Interruption Resilience:**
   - All session turns, mastery updates, and learning events logged offline must survive application restart.
   - Interrupted turns (power cut, app force-close mid-turn) must execute safe transactional rollback without corrupting local SQLite databases.
   - Read-only databases (e.g. locked file or read-only volume) must operate in graceful degraded "study-only" mode.

---

## 2. Target Design & Components (`local_runtime/`)

We will build the decoupled `local_runtime/` subsystem:

```
local_runtime/
├── __init__.py                 # Public package exports
├── detector.py                 # OfflineCapabilityDetector & Health Diagnostics
├── course_cache.py             # LocalCourseCache (package store, checksum validation, quarantine)
├── rag_cache.py                # LocalRAGCache (offline BM25/keyword scoped knowledge store)
├── session.py                  # LocalSessionPersistence (survives restart, handles interruptions)
├── engine.py                   # LocalRuntimeEngine (glues GenericTutorOrchestrator to local caches)
└── errors.py                   # Typed offline errors (OfflineCourseNotCachedError, ModelUnavailableError, etc.)
```

### Component Details:

1. **`OfflineCapabilityDetector` (`local_runtime/detector.py`):**
   - Methods:
     - `check_offline_status() -> OfflineCapabilitiesReport`: Checks network reachability, local DB writable status, available local models, and cached course count.
     - `is_course_available_offline(course_id: str) -> bool`
     - `is_model_available_offline(model_name: str) -> bool`
     - `get_honest_degraded_state(course_id: str) -> DegradedStateInfo`: Explains exactly what is missing (e.g., "Course not cached locally", "Local SLM model 'phi3-mini' not installed").

2. **`LocalCourseCache` (`local_runtime/course_cache.py`):**
   - Package structure: Stores course versions locally under a deterministic cache directory (`data/cache/courses/{course_id}/{version_tag}/`).
   - Validates SHA-256 package checksum on import/read.
   - **Quarantine protocol:** If a cached file fails SHA-256 checksum or has corrupted JSON, moves it to `data/cache/quarantine/` and marks the course as `CORRUPTED_CACHE`, alerting the user cleanly without crashing.
   - Enables offline export & import of course packages for distribution via USB or local network.

3. **`LocalRAGCache` (`local_runtime/rag_cache.py`):**
   - Course-isolated local knowledge search engine.
   - Uses BM25 / token matching against pre-chunked offline text assets.
   - Enforces course and version scoping: knowledge chunks from Course A can never be retrieved when Course B is active.

4. **`LocalSessionPersistence` (`local_runtime/session.py`):**
   - Wraps local SQLite database for session lifecycle.
   - Implements transactional atomic turn commits (`begin_turn()`, `commit_turn()`, `rollback_turn()`).
   - Interrupted turns (uncommitted turns flagged `PENDING_COMMIT`) are automatically rolled back on startup so state remains consistent.
   - Graceful read-only detection: if SQLite returns `sqlite3.OperationalError: attempt to write a readonly database`, switches to `READ_ONLY_MODE` and allows reading curriculum and existing session transcripts.

5. **`LocalRuntimeEngine` (`local_runtime/engine.py`):**
   - Unifies `GenericTutorOrchestrator`, `LocalCourseCache`, `LocalRAGCache`, `LocalSessionPersistence`, and `AI Gateway` into a single cohesive offline runtime interface.
   - Routes tutor turns through the standard 16-step course lifecycle without requiring an external internet connection or running HTTP server.

6. **Decouple `app/bridge/facade.py` from Fake Demo Data (`BUG-ARCH-003`):**
   - Remove hardcoded `"Rahul Kumar"`, `"Priya Sharma"`, `"Amit Patel"` and hardcoded Chemistry seeds in `get_teacher_portal_service()` and `get_teacher_instruction_engine()`.
   - Wire `TeacherPortalService` and `TeacherInstructionEngine` to `PlatformDatabase` / `LocalRuntimeEngine`.
   - Render honest empty states when no students or classes are enrolled.

---

## 3. Test Suite: `tests/test_phase13_offline_local_runtime.py`

12 comprehensive tests covering all requirements from Section 12.13:

1. `test_first_offline_launch_clean_environment`:
   - Verifies clean startup with empty cache and empty DB renders honest empty state with 0 fake demo roster entries (`BUG-ARCH-003` verification).
2. `test_offline_capability_detection`:
   - Verifies detection of network state, database read/write readiness, model availability, and cached courses.
3. `test_cached_course_import_and_checksum_verification`:
   - Imports valid course package into local cache, verifies SHA-256 checksum, and queries course metadata offline.
4. `test_corrupted_cache_detection_and_quarantine`:
   - Tampered/corrupted course package is detected, quarantined to quarantine directory, and reported cleanly without crashing.
5. `test_uncached_course_honest_degraded_state`:
   - Requesting an uncached course offline cleanly raises `OfflineCourseNotCachedError` with actionable user guidance instead of generic crash or fallback.
6. `test_local_tutor_turn_offline_execution`:
   - Executes a complete 16-step tutor turn offline using cached curriculum, local RAG chunks, and local SLM inference mock/provider.
7. `test_local_state_persistence_across_restart`:
   - Enrolls student, completes tutoring turns, logs mastery and learning events; shuts down runtime; creates new runtime instance; verifies 100% of state, history, and events are preserved.
8. `test_interrupted_turn_transactional_rollback`:
   - Simulates a mid-turn crash while writing state; restarts runtime; verifies partial turn was rolled back and database remains consistent.
9. `test_read_only_database_degraded_mode`:
   - Makes local database read-only; verifies runtime enters graceful `READ_ONLY_MODE`, allowing course navigation and history review while cleanly blocking new writes.
10. `test_missing_model_honest_alert_and_prompt`:
    - When requested offline model is missing, returns `ModelUnavailableError` with honest diagnostic info on how to download the model.
11. `test_zero_fake_demo_roster_in_bridge_and_portal`:
    - Tests `app/bridge/facade.py` with clean DB; verifies 0 fake students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`) exist.
12. `test_zero_chemistry_coupling_in_local_runtime`:
    - Scans AST and tokens of all `local_runtime/` files, verifying zero hardcoded chemistry keywords or course assumptions.

---

## 4. Full Regression Protocol

- Run `tests/test_phase13_offline_local_runtime.py` until 100% green.
- Run complete test suite (`pytest -q`) to guarantee zero regressions across all 981 existing tests (target: 993+ passing).
- Export Phase 13 verification artifacts:
  - `docs/reports/PHASE_13_TEST_REPORT.md`
  - `docs/reports/PHASE_13_TEST_RESULTS.json`
- Update tracking ledgers (`PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`).
- Commit and push to `origin/master`.
