# Phase 23 Implementation & Test Plan: Reliability, Failure Injection & Recovery

**Document:** `docs/reports/PHASE_23_PLAN.md`  
**Phase:** 23  
**Section:** 12.23 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  

---

## 1. Objective

Prove the system fails safely and recovers predictably under extreme, degraded, and interrupted conditions. Specifically designed to prevent silent-fail bugs from recurring across identity, RAG, course authoring, instruction lifecycles, provider routing, database transactions, offline sync, and tutor turn lifecycles.

Per Section 12.23 requirements:
- Refactor recovery paths so all failures have:
  1. **classification** (`failure_category`)
  2. **observable status** (`status`)
  3. **safe user message** (`user_message`)
  4. **technical diagnostic** (`technical_diagnostic`)
  5. **retryability** (`retryable`)
  6. **rollback/commit decision** (`commit_decision`)
- Inject and verify 12 concrete failure scenarios:
  1. Missing model
  2. Corrupt model
  3. Provider timeout
  4. Provider malformed response
  5. RAG unavailable
  6. DB unavailable
  7. Broken migration
  8. Broken upload
  9. Interrupted publish
  10. Expired instruction
  11. Duplicate sync
  12. App crash mid-turn

---

## 2. Failure Recovery & Reliability Architecture Refinements

### 2.1 Refactor `RecoveryResult` and `FailureRecoveryManager` (`central_platform/recovery/manager.py`)
- Enhance `FailureCategory` to represent all 12 failure domains:
  - `MISSING_MODEL` & `MODEL_UNAVAILABLE`
  - `CORRUPT_MODEL`
  - `PROVIDER_TIMEOUT`
  - `PROVIDER_MALFORMED` & `MALFORMED_MODEL_OUTPUT`
  - `RAG_UNAVAILABLE` & `RAG_FAILURE`
  - `DATABASE_UNAVAILABLE` & `DATABASE_FAILURE`
  - `BROKEN_MIGRATION`
  - `BROKEN_UPLOAD`
  - `INTERRUPTED_PUBLISH`
  - `EXPIRED_INSTRUCTION`
  - `DUPLICATE_SYNC`
  - `APP_CRASH_MID_TURN`
- Define `CommitDecision` enum (`COMMIT`, `ROLLBACK`, `NOOP`, `RETRY`).
- Expand `RecoveryResult` to include `user_message`, `technical_diagnostic`, `retryable`, and `commit_decision` while preserving backwards compatibility.
- Add and standardize dedicated recovery handlers in `FailureRecoveryManager`:
  - `handle_model_failure`: Missing vs corrupt weights classification, fallback SLM routing, retryable decision.
  - `handle_provider_timeout`: Multi-retry timeout recording, switch to offline router, user-facing notice.
  - `repair_malformed_model_output`: Self-healing regex/markdown extraction with parse verification.
  - `handle_rag_failure`: Scoped fallback to syllabus without interrupting tutoring.
  - `handle_database_failure`: Safe in-memory read-only state snapshot buffer.
  - `handle_broken_migration`: Transaction rollback, checksum ledger protection, pre-migration restoration.
  - `handle_broken_upload`: Discard incomplete byte stream, clean up temporary chunks.
  - `handle_interrupted_publish`: Revert version to previous verified draft state, prevent catalog corruption.
  - `handle_expired_instruction`: Prune stale instructions from context hierarchy.
  - `handle_duplicate_sync`: Idempotent cached receipt return without duplicate event creation.
  - `handle_crash_mid_turn`: Transactional state rollback discarding all staged uncommitted mutations.

### 2.2 Resilient Orchestrator Integration (`central_platform/tutor/orchestrator.py`)
- Catch unhandled exceptions in the 16-step turn lifecycle.
- Prevent orphan database records or half-committed mastery state when an error occurs before step 15.
- Return a classified, user-safe error recovery turn result (`CRASH_RECOVERED`) rather than crashing the API or worker.

### 2.3 Course Publishing Resilience (`central_platform/courses/service.py`)
- Wrap `approve_and_publish_version` in a guarded transactional boundary.
- If publish step fails midway, revert to prior status and log technical diagnostics.

### 2.4 Sync Replay Resilience (`central_platform/sync/service.py`)
- Bind duplicate sync requests to `FailureRecoveryManager.handle_duplicate_sync`.
- Guarantee exact event deduplication count and state preservation.

---

## 3. Test Architecture Plan

Create `tests/test_phase23_reliability_failure_injection_recovery.py` with 12 end-to-end failure injection test suites:
1. `test_inject_missing_model`: Primary model missing -> classified `MISSING_MODEL`/`MODEL_UNAVAILABLE`, falls back to local SLM, `retryable=True`, `commit_decision=NOOP`, safe user message.
2. `test_inject_corrupt_model`: Corrupt weights/checksum -> classified `CORRUPT_MODEL`, safe user message, `retryable=False`, `commit_decision=ROLLBACK`, no corrupted data committed.
3. `test_inject_provider_timeout`: Cloud provider timeout -> classified `PROVIDER_TIMEOUT`, switches to local router, safe user message, `retryable=True`, `commit_decision=NOOP`.
4. `test_inject_provider_malformed_response`: LLM returns malformed JSON -> repaired via markdown fence or regex, or wrapped in safe payload, `commit_decision=COMMIT` when healed, `status=RECOVERED`.
5. `test_inject_rag_unavailable`: Vector DB / retrieval error -> classified `RAG_FAILURE`, degrades to syllabus context, `retryable=True`, `commit_decision=NOOP`, tutor turn continues.
6. `test_inject_database_unavailable`: DB disk error -> classified `DATABASE_FAILURE`, read-only fallback, safe user message, `retryable=True`, `commit_decision=ROLLBACK`, state unmutated.
7. `test_inject_broken_migration`: Migration script fails -> classified `BROKEN_MIGRATION`, schema rolled back, safe user message, `retryable=False`, `commit_decision=ROLLBACK`, schema integrity maintained.
8. `test_inject_broken_upload`: Truncated upload or checksum mismatch -> classified `BROKEN_UPLOAD`, partial buffer purged, safe user message, `retryable=True`, `commit_decision=ROLLBACK`, 0 orphan chunks.
9. `test_inject_interrupted_publish`: Error during version publishing -> classified `INTERRUPTED_PUBLISH`, version preserved in pre-publish state, safe user message, `retryable=True`, `commit_decision=ROLLBACK`.
10. `test_inject_expired_instruction`: Instruction past expires_at -> classified `EXPIRED_INSTRUCTION`, marked EXPIRED and excluded from tutor prompt hierarchy, `commit_decision=NOOP`.
11. `test_inject_duplicate_sync`: Resubmitted sync operation -> classified `DUPLICATE_SYNC`, idempotent receipt returned, safe user message, `retryable=False`, `commit_decision=NOOP`, no duplicate events.
12. `test_inject_app_crash_mid_turn`: Simulated unhandled exception mid-turn before commit -> classified `APP_CRASH_MID_TURN`, uncommitted state rolled back, safe user message, `retryable=True`, `commit_decision=ROLLBACK`, zero corrupted events.
