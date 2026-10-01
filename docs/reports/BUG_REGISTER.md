# Comprehensive Bug Register

**Document:** `docs/reports/BUG_REGISTER.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Maintained Per:** Section 47 of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## Active Architectural & Defect Findings

### BUG-ARCH-001
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Generic Platform Core, Curriculum, RAG, UI (`core/curriculum/`, `core/runtimes/`, `app/bridge/`)
- **Reproduction:** Inspect concept resolution keywords in `core/curriculum/` or run `rg "chemistry|thermodynamics|hess" core/ central_platform/ app/`.
- **Expected:** Generic platform runtime contains zero subject-specific keywords or hardcoded curriculum paths.
- **Actual:** 115 files in generic layers assume Chemistry as the sole or default subject.
- **Root Cause:** Historical design of Gayatri as a Chemistry tutor without course abstraction.
- **Fix:** Extract all Chemistry-specific logic to `adapters/chemistry/` and make core curriculum and orchestrator data-driven.
- **Test:** Course genericity static guard test + generic course creation test.
- **Verification:** Pending (Scheduled for Phase 3, Phase 9, Phase 15).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

---

### BUG-ARCH-002
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** AI Inference Pipeline (`core/inference/service.py`, `core/runtimes/chemistry.py`, `core/runtimes/general.py`)
- **Reproduction:** `python -c "import core.inference.service; print(core.inference.service._local_chat_stream)"`
- **Expected:** Tutor core calls AI Gateway (`central_platform.ai`), which dispatches to Provider Adapters.
- **Actual:** Production modules import directly from `legacy.agents.default_agents`.
- **Root Cause:** Incomplete migration to the new AI Gateway abstraction.
- **Fix:** Redirect all inference calls to `central_platform.ai.model_router` and eliminate all callers of `legacy/`.
- **Test:** Static architecture guard forbidding imports from `legacy.*`.
- **Verification:** Pending (Scheduled for Phase 8, Phase 16).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

---

### BUG-ARCH-003
- **Severity:** P0
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Bridge & Server UI State (`app/bridge/facade.py`, `server.py`, `core/session.py`)
- **Reproduction:** Load student portal with clean database; observe fake students (`Rahul Kumar`, `Priya Sharma`, `Amit Patel`) injected into roster.
- **Expected:** Empty state rendered honestly when no students or classes are enrolled.
- **Actual:** Mock roster data hardcoded in production bridge methods.
- **Root Cause:** Placeholder bridge methods developed for quick demoing without real service backing.
- **Fix:** Connect bridge methods directly to `central_platform.db` repositories with honest empty states.
- **Test:** Clean database startup test verifying 0 fake students rendered.
- **Verification:** Pending (Scheduled for Phase 11, Phase 14).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

---

### BUG-ARCH-004
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** SQLite Session & RAG Storage (`core/session.py`, `core/rag/store.py`, `core/tutor/state.py`)
- **Reproduction:** Inspect `core/session.py` lines 128-171; note repeated `ALTER TABLE` statements inside `try...except Exception: pass`.
- **Expected:** Schema managed strictly via migration scripts (`migrations/*.sql`).
- **Actual:** Runtime DDL statements executed on connection instantiation, swallowing errors.
- **Root Cause:** Incremental schema modifications bolted onto runtime initialization.
- **Fix:** Consolidate all table columns into deterministic migration scripts and enforce startup schema checks.
- **Test:** Dynamic DDL scan assertion ensuring 0 `ALTER TABLE` in runtime execution.
- **Verification:** Pending (Scheduled for Phase 2).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

---

### BUG-ARCH-005
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Database Migrations (`migrations/001_initial_schema.sql`)
- **Reproduction:** Inspect line 351 and line 448 of `migrations/001_initial_schema.sql`.
- **Expected:** Each table defined exactly once in canonical DDL.
- **Actual:** `assignments` table defined twice with differing column definitions.
- **Root Cause:** Merge conflict concatenation in initial migration file.
- **Fix:** Deduplicated and consolidated `assignments` table definition into a single authoritative schema in `migrations/001_initial_schema.sql`.
- **Test:** Migration integrity architecture guard test (`tests/architecture/test_migration_integrity.py`).
- **Verification:** **VERIFIED FIXED** (Migration integrity test passes; zero duplicate tables).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

---

### BUG-ARCH-006
- **Severity:** P1
- **Date Found:** 2026-10-01
- **Commit Found:** `bf47a63`
- **Subsystem:** Model Manifest & Configuration (`model_manifest.json`, `core/config.py`)
- **Reproduction:** Compare `model_manifest.json` default model ID with `core/config.py` search list.
- **Expected:** Single authoritative model registry/manifest declaring active models and capabilities.
- **Actual:** Contradictory model filenames, quantization tags, and prompt template parameters across files.
- **Root Cause:** Divergent configuration updates in documentation vs code.
- **Fix:** Create a single authoritative model registry in `central_platform/ai/models.py`.
- **Test:** Model registry schema validation test.
- **Verification:** Pending (Scheduled for Phase 8).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** CONFIRMED.

---

### BUG-RAG-007
- **Severity:** P2
- **Date Found:** 2026-10-01
- **Commit Found:** `424f343`
- **Subsystem:** Plug-and-Play RAG Retrieval (`central_platform/db.py`)
- **Reproduction:** Insert RAG source with uppercase enum status (`PUBLISHED`); query `get_rag_chunks_by_course(only_published=True)`.
- **Expected:** Chunks are returned regardless of whether the status string is uppercase or lowercase.
- **Actual:** Exact match `rs.status = 'published'` filtered out records stored with uppercase enum value.
- **Root Cause:** Direct literal comparison in SQLite/PostgreSQL SQL condition without `LOWER()`.
- **Fix:** Updated `central_platform/db.py` to use `LOWER(rs.status) = 'published'` and `LOWER(status) = ?`.
- **Test:** `tests/test_phase05_knowledge_assets.py::test_phase_gate_student_visibility_invariant`.
- **Verification:** **VERIFIED FIXED** (All 12 Phase 05 tests pass; all 898 suite tests pass).
- **GitHub Issue:** Queued in `docs/reports/GITHUB_SYNC_QUEUE.md`.
- **Status:** VERIFIED.

