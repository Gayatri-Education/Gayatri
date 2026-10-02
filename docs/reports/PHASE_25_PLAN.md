# Phase 25 Plan: Performance & Capacity Verification

**Document:** `docs/reports/PHASE_25_PLAN.md`  
**Phase:** 25  
**Section:** Section 35 of `GAYATRI_MASTER_PHASE_BY_PHASE_EXECUTION_AND_RECOVERY_GUIDE.md` & Section 12.25 of `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`  
**Author:** Gayatri AI Core Architecture Team  
**Date:** 2026-10-02  

---

## 1. Objective

> *"Measure, don't guess."* (Section 35)

Establish concrete, empirically verified performance and capacity boundaries across the authoritative runtime components of Gayatri AI. All measurements must be performed against genuine application services with explicit justification for every target budget.

---

## 2. Measurement Dimensions & Justified Budgets

| Metric | Target Budget | Engineering Justification | Measurement Methodology |
|--------|---------------|---------------------------|-------------------------|
| **Startup Time** | `< 1,500 ms` | Desktop application and containerized runtime must initialize quickly without blocking user workflow | Measure duration from process launch through route mounting and DB initialization |
| **REST Health Probe P95** | `< 200 ms` | Kubernetes liveness/readiness probes run every 5-10s; must not induce CPU spikes or latency bloat | 50 consecutive queries against `/healthz` and `/api/v1/health` via TestClient |
| **Complete Turn Response P95** | `< 800 ms` | Interactive conversational flow requires sub-second perceived response latency in local inference mode | 25 full tutoring turns through `GenericTutorOrchestrator` across 16 lifecycle steps |
| **RAG Retrieval P95** | `< 250 ms` | Hybrid BM25 + dense retrieval must not bottleneck generation pipeline | 50 retrieval queries over multi-chapter course corpus |
| **DB Read Latency P95** | `< 50 ms` | Student learning state (SLR) and session lookups must execute with minimal overhead | 100 queries against user, session, and course tables |
| **DB Write Latency P95** | `< 100 ms` | Transactional two-phase state commits must persist atomically | 50 learning event and mastery state commits |
| **Batch Ingestion Throughput** | `> 100 events/sec` | High-frequency telemetry and offline sync batch uploads require rapid bulk processing | Ingest batch of 200 `LearningEvent` items into `LearningEventStore` |
| **Multi-Threaded Concurrency** | `0 deadlocks, 0% errors` | Multi-core desktop and container deployments handle simultaneous background sync and interactive turns | 8 concurrent worker threads executing 32 simultaneous transactions on SQLite |
| **Repeated Session Memory Growth** | `< 50 MB / 50 sessions` | Memory leaks in session caching or context building must not exhaust RAM during prolonged student usage | Measure process RSS via `psutil` before and after 50 complete session lifecycles |
| **Offline Storage Growth** | `< 1.5 KB / event` | Local devices with limited storage (16GB-64GB eMMC) must accommodate hundreds of hours of learning history | Measure SQLite file size delta after 500 committed events |

---

## 3. Required Test Suite Structure

A dedicated test suite `tests/test_phase25_performance_capacity_verification.py` will implement the following verification methods:

1. `test_perf_api_probes_and_startup`: Validate server startup and health probe response distributions.
2. `test_perf_single_user_turn_latency`: Measure complete 16-step turn latency percentiles (P50, P95).
3. `test_perf_rag_retrieval_latency`: Measure hybrid RAG retrieval speed under varied query lengths.
4. `test_perf_batch_event_ingestion_throughput`: Verify event ingestion throughput exceeds 100 events/sec.
5. `test_perf_multithreaded_db_concurrency`: Stress-test simultaneous readers and writers across threads.
6. `test_perf_memory_stability_repeated_sessions`: Audit memory footprint across 50 consecutive sessions.
7. `test_perf_offline_storage_growth_envelope`: Measure byte growth rate of the local SQLite database.

---

## 4. Phase 25 Verification Gate Criteria

- All 7 performance scenarios pass within justified thresholds.
- Zero mock bypasses; all measurements execute against real `PlatformDatabase`, `GenericTutorOrchestrator`, and `RAGService`.
- Zero regressions across the full existing platform test suite (1,119 tests).
- Generate `PHASE_25_TEST_REPORT.md`, `PHASE_25_TEST_RESULTS.json`, and `PHASE_25_CAPACITY_REPORT.md`.
