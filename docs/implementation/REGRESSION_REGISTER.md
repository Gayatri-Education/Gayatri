# V2 Platform Regression Register

Authoritative regression suite definition and verification history for Gayatri AI.

---

## 1. Regression Test Classes

### 1.1 `CORE_REGRESSION`
Core student tutor runtime, adaptive algorithms, BKT, LDG, assessment grading, and deterministic chemistry tooling.
- `tests/test_phase6_adaptive_engine_v2.py`
- `tests/test_phase6_evaluator.py`
- `tests/test_phase6_prompt_system.py`
- `tests/test_phase6_spaced_review.py`
- `tests/test_phase7_assessment_engine.py`
- `tests/test_phase7_concept_resolution.py`
- `tests/test_phase8_adaptive_engine.py`
- `tests/test_phase8_curriculum_validation.py`
- `tests/test_phase9_misconceptions.py`
- `tests/test_tutor_mode_realtime.py`
- `tests/test_student_dashboard.py`

### 1.2 `PLATFORM_REGRESSION`
Central platform APIs, sync pipelines, database operations, auth & RBAC, server live synchronization, and teacher workflows.
- `tests/test_server_live_sync.py`
- `tests/test_teacher_dashboard_bridge.py`
- `tests/test_phase2_central_platform.py`
- `tests/test_phase3_auth_rbac.py`
- `tests/test_phase4_sync.py`
- `tests/test_phase4_student_isolation.py`
- `tests/test_phase5_learning_events.py`
- `tests/test_phase5_slr.py`
- `tests/test_phase7_teacher_instructions.py`
- `tests/test_phase8_teacher_portal.py`
- `tests/test_phase9_teacher_intervention.py`
- `tests/test_phase10_teacher_copilot.py`
- `tests/test_phase13_admin_portal.py`
- `tests/test_phase14_database.py`
- `tests/test_phase15_database_hardening.py`
- `tests/test_phase20_production_readiness.py`

### 1.3 `INTELLIGENCE_REGRESSION`
RAG retrieval accuracy, SLM pedagogical alignment, anti-answer leakage invariants, prompt injection defenses, and knowledge graph queries.
- `tests/test_phase4_hybrid_rag.py`
- `tests/test_phase5_knowledge_graph_rag.py`
- `tests/test_phase9_rag.py`
- `tests/test_phase13_rag_audit.py`
- `tests/test_phase15_security.py`
- `tests/test_phase17_prompt_security.py`
- `tests/test_phase17_security_hardening.py`
- `tests/test_phase19_upload_security.py`
- `tests/test_slm_pedagogical_alignment.py`

---

## 2. Full Regression Execution Command
```powershell
pytest
```
To run targeted classes:
```powershell
pytest -k "adaptive or evaluator or prompt_system or spaced_review or assessment"
pytest -k "server or teacher or central_platform or sync or rbac"
pytest -k "rag or slm or security"
```

---

## 3. Regression Execution Log

| Date | Phase | Suite Class | Total Tests | Passed | Failed | Warnings | Verification Script | Status |
|---|---|---|---|---|---|---|---|---|
| 2026-09-26 | Pre-Phase 00 Baseline | FULL SUITE | 411 | 411 | 0 | 0 | `scripts/verify_sync.py` (5/5) | PASSED |
| 2026-09-27 | Phase 00 Verification | FULL SUITE | 411 | 411 | 0 | 0 | `scripts/verify_sync.py` (5/5) | PASSED |
| 2026-09-27 | Phase 01 Frozen Baseline | BENCHMARK + PYTEST | 455 | 455 | 0 | 0 | `scripts/run_frozen_baseline.py` (44/44) | PASSED |
