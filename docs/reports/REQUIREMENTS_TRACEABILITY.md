# Requirements Traceability Matrix

**Document:** `docs/reports/REQUIREMENTS_TRACEABILITY.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Established Per:** Section 55 of `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## Traceability Mapping

| Req ID | Requirement Description | Design Document | Target Implementation | Unit / Integration Test | Acceptance Journey | Failure / Negative Test | Verification Report | Status |
|---|---|---|---|---|---|---|---|---|
| **REQ-01** | **Course Independence:** Core tutor runtime operates completely independent of any subject/Chemistry assumptions. | `docs/ARCHITECTURE_TARGET.md` | `core/tutor/`, `core/orchestrator.py` | `tests/test_course_independent_tutor.py` | Journey A, Journey E | Non-chemistry subject execution without Chemistry adapter | Pending Phase 9 | PENDING |
| **REQ-02** | **Public vs Private Courses:** Support public courses discoverable across orgs and private courses restricted to owning org. | `docs/DATA_MODEL_TARGET.md`, `docs/SECURITY_MODEL_TARGET.md` | `central_platform/courses/service.py` | `tests/test_course_visibility_isolation.py` | Journey A, Journey B | Unauthorized cross-org access attempts return HTTP 403 | Pending Phase 2 | PENDING |
| **REQ-03** | **Immutable Course Versioning:** Content and curricula versioned; historical student sessions pinned to session version. | `docs/DATA_MODEL_TARGET.md` | `central_platform/models/schema.py`, `central_platform/courses/` | `tests/test_course_version_immutability.py` | Journey F | Attempt to mutate published version rejected | Pending Phase 2 | PENDING |
| **REQ-04** | **Content Ingestion & Administrative Approval:** Content upload requires parsing, indexing, review, and admin approval before publish. | `docs/ARCHITECTURE_TARGET.md` | `central_platform/rag/ingestion.py`, `central_platform/content/` | `tests/test_content_ingestion_pipeline.py` | Journey A, Journey B | Unpublished content invisible to student RAG | Pending Phase 5 | PENDING |
| **REQ-05** | **Multi-Course Student Enrollment:** Single student can enroll in multiple courses concurrently with isolated mastery states. | `docs/DATA_MODEL_TARGET.md` | `central_platform/learning/mastery.py` | `tests/test_multi_course_mastery_isolation.py` | Journey E | Activity in Course A does not mutate Course B mastery | Pending Phase 4 | PENDING |
| **REQ-06** | **Scoped Teacher Instructions:** Instructions resolved hierarchically (Org -> Course -> Class -> Student -> Session). | `docs/ARCHITECTURE_TARGET.md` | `central_platform/instructions/resolver.py` | `tests/test_instruction_hierarchy_resolver.py` | Journey C, Journey D | Expired instructions excluded; unauthorized teacher instructions rejected | Pending Phase 7 | PENDING |
| **REQ-07** | **Course-Specific Tools Policy:** Courses declare allowed tools via capability policy enforced server-side. | `docs/ARCHITECTURE_TARGET.md` | `central_platform/tools/registry.py` | `tests/test_course_tool_policy_enforcement.py` | Journey A | Invocation of non-enabled tool blocked | Pending Phase 2 | PENDING |
| **REQ-08** | **Scoped RAG Retrieval:** Authorization enforced before vector search (Course, Class, Student, Published). | `docs/SECURITY_MODEL_TARGET.md` | `central_platform/rag/service.py` | `tests/test_scoped_rag_retrieval.py` | Journey C, Journey D | Class B student cannot retrieve Class A teacher notes | Pending Phase 6 | PENDING |
| **REQ-09** | **Generic AI Gateway & Legacy Removal:** Unify inference under Gateway with zero imports from `legacy/`. | `docs/ARCHITECTURE_TARGET.md` | `central_platform/ai/` | `tests/test_ai_gateway_providers.py` | All Journeys | Static guard fails CI if legacy imported | Pending Phase 8 | PENDING |
| **REQ-10** | **Online & Offline Dual Operation:** Shared business logic running over SQLite offline and PostgreSQL/Cloud online. | `docs/ARCHITECTURE_TARGET.md` | `central_platform/db.py`, `app/local_service/` | `tests/test_offline_persistence_recovery.py` | Journey G | App restart restores state offline | Pending Phase 12 | PENDING |
| **REQ-11** | **Reliable & Idempotent Synchronization:** Offline learning events sync outbox with deduplication and conflict policy. | `docs/ARCHITECTURE_TARGET.md` | `central_platform/sync/service.py` | `tests/test_sync_idempotency_conflict.py` | Journey G | Duplicate event sync produces exactly one logical state update | Pending Phase 13 | PENDING |
| **REQ-12** | **Chemistry Domain Adapter:** Chemistry extracted into clean plugin/adapter package without core dependencies. | `docs/ARCHITECTURE_TARGET.md` | `adapters/chemistry/` | `tests/test_chemistry_adapter.py` | Journey A, Journey E | Platform boots and runs normally when Chemistry adapter is uninstalled | Pending Phase 15 | PENDING |
