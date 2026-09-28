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
- `tests/test_phase02_platform_api.py`
- `tests/test_phase03_postgresql_data_layer.py`
- `tests/test_phase04_auth_rbac.py`
- `tests/test_phase05_learning_events.py`
- `tests/test_phase06_authoritative_slr.py`
- `tests/test_phase07_connect_learning_engine.py`
- `tests/test_phase08_desktop_platform_sync.py`
- `tests/test_phase09_student_progress.py`
- `tests/test_phase10_teacher_portal_web.py`
- `tests/test_phase11_teacher_instructions_platform.py`
- `tests/test_phase12_teacher_intervention_platform.py`
- `tests/test_phase13_teacher_copilot_platform.py`
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
| 2026-09-27 | Phase 02 Platform API | FULL SUITE | 433 | 433 | 0 | 0 | `scripts/verify_sync.py` (5/5) | PASSED |
| 2026-09-27 | Phase 03 PostgreSQL Data | FULL SUITE | 448 | 448 | 0 | 0 | `scripts/verify_sync.py` (5/5) | PASSED |
| 2026-09-27 | Phase 04 Auth & RBAC | FULL SUITE | 465 | 465 | 0 | 0 | `scripts/verify_sync.py` (5/5) | PASSED |
| 2026-09-27 | Phase 05 Learning Events | FULL SUITE | 475 | 475 | 0 | 0 | `tests/test_phase05_learning_events.py` (10/10) | PASSED |
| 2026-09-27 | Phase 06 Authoritative SLR | FULL SUITE | 486 | 486 | 0 | 0 | `tests/test_phase06_authoritative_slr.py` (11/11) | PASSED |
| 2026-09-27 | Phase 07 Connect Learning Engine | FULL SUITE | 497 | 497 | 0 | 0 | `tests/test_phase07_connect_learning_engine.py` (11/11) | PASSED |
| 2026-09-27 | Phase 08 Desktop ↔ Platform Sync | FULL SUITE | 508 | 508 | 0 | 0 | `tests/test_phase08_desktop_platform_sync.py` (11/11) | PASSED |
| 2026-09-27 | Phase 09 Student Progress API + UI | FULL SUITE | 518 | 518 | 0 | 0 | `tests/test_phase09_student_progress.py` (10/10) | PASSED |
| 2026-09-27 | Phase 10 Teacher Web Portal | FULL SUITE | 525 | 525 | 0 | 0 | `tests/test_phase10_teacher_portal_web.py` (7/7) | PASSED |
| 2026-09-27 | Phase 11 Teacher AI Instructions | FULL SUITE | 536 | 536 | 0 | 0 | `tests/test_phase11_teacher_instructions_platform.py` (11/11) | PASSED |
| 2026-09-27 | Phase 12 Teacher Intervention System | FULL SUITE | 546 | 546 | 0 | 0 | `tests/test_phase12_teacher_intervention_platform.py` (10/10) | PASSED |
| 2026-09-28 | Phase 13 Teacher Copilot | FULL SUITE | 557 | 557 | 0 | 0 | `tests/test_phase13_teacher_copilot_platform.py` (11/11) | PASSED |
| 2026-09-28 | Phase 14 Admin Web Portal | FULL SUITE | 570 | 570 | 0 | 0 | `tests/test_phase14_admin_portal_platform.py` (13/13) | PASSED |
| 2026-09-28 | Phase 15 Plug-and-Play Curriculum | FULL SUITE | 580 | 580 | 0 | 0 | `tests/test_phase15_plug_and_play_curriculum_platform.py` (10/10) | PASSED |
| 2026-09-28 | Phase 17 Real AI Gateway + Model Router | FULL SUITE | 605 | 605 | 0 | 0 | `tests/test_phase17_ai_gateway_model_router_platform.py` (14/14) | PASSED |
| 2026-09-28 | Phase 18 AI Governance / Observability | FULL SUITE | 611 | 611 | 0 | 0 | `tests/test_phase18_ai_governance_observability_platform.py` (6/6) | PASSED |
| 2026-09-28 | Phase 19 Assessment Platform | FULL SUITE | 618 | 618 | 0 | 0 | `tests/test_phase19_assessment_platform.py` (7/7) | PASSED |
| 2026-09-28 | Phase 20 Analytics Platform | FULL SUITE | 622 | 622 | 0 | 0 | `tests/test_phase20_analytics_platform.py` (4/4) | PASSED |
| 2026-09-28 | Phase 21 Notifications Platform | FULL SUITE | 627 | 627 | 0 | 0 | `tests/test_phase21_notifications_platform.py` (5/5) | PASSED |
| 2026-09-28 | Phase 22 Security Hardening Master | FULL SUITE | 637 | 637 | 0 | 0 | `tests/test_phase22_security_hardening_master.py` (10/10) | PASSED |
| 2026-09-28 | Phase 23 Real End-to-End Testing | FULL SUITE | 640 | 640 | 0 | 0 | `tests/test_phase23_e2e_journeys_master.py` (3/3) | PASSED |
| 2026-09-28 | Phase 24 Failure / Recovery Testing | FULL SUITE | 645 | 645 | 0 | 0 | `tests/test_phase24_failure_recovery_master.py` (5/5) | PASSED |





