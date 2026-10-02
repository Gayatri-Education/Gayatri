# Phase 03 Evidence — RAG Authorization, Retrieval, and Grounding

## Objective
Make RAG authoritative, course/version/class/student scoped, fail-closed, and impossible to bypass through legacy paths. Eliminate hardcoded chemistry fallbacks and retrieve-anyway vector leakages.

## Starting commit
`6f6d6dd` (`master`)

## Files changed
- `central_platform/rag/service.py`:
  - Removed hardcoded Chemistry fallback chunk (`chunk-thermo-01` / `Delta U = q + w`) from `_legacy_fallback_query`.
  - Empty retrieval strictly returns status `"RAG_EMPTY"`, count `0`, empty results list, and empty `data_context`.
  - Fixed legacy parser to inspect `sections` from NCERT JSON datasets and properly attribute chapter and chunk ID.
- `core/rag/retriever.py`:
  - Removed unfiltered vector fallback (`if not filtered_candidates: filtered_candidates = vector_candidates`).
  - Added robust hierarchy/subtopic metadata filtering and broadened vector candidate pool (`max(15, top_k * 5)`) to maintain high recall while strictly enforcing metadata boundaries.
- `central_platform/api/routes/rag.py`:
  - Replaced all `get_current_user_optional` with mandatory `get_current_user`.
  - Added strict authentication and organization boundary checks across all RAG endpoints (`/sources`, `/ingest`, `/validate`, `/publish`, `/chunks`, `/query`).
  - Enforced anti-spoofing check for student query callers (`req.student_id == current_user.id`).
  - Enforced active course enrollment / course offering check on private courses before retrieval.
- `tests/test_phase16_rag_plug_and_play_platform.py`:
  - Updated RAG API tests to provide valid authorization headers and asserted HTTP 401 on unauthenticated requests.
- `tests/test_phase06_scoped_rag_authorization.py`:
  - Updated API flow tests to assert HTTP 401 on unauthenticated calls and provide teacher headers on authorized operations.
- `tests/test_phase02_platform_api.py`:
  - Added negative unauthenticated assertion (401) and student auth token for `/api/v1/rag/query`.
- `tests/test_phase22_security_privacy_isolation_audit.py`:
  - Added negative unauthenticated assertion (401) and beta student authorization for cross-boundary leak prevention.
- `tests/test_phase24_e2e_journeys_real.py`:
  - Added explicit student course enrollment for private defense course before executing class-scoped query.
- `tests/test_phase03_rag_remediation.py`:
  - Added 9 adversarial and contract tests verifying F-005, F-006, F-007, F-008, and F-009.

## Defects addressed
- **F-005 (P0):** Hardcoded Chemistry fallback chunk in RAG service. Fixed: Replaced with fail-closed `RAG_EMPTY` return.
- **F-006 (P0):** Retriever fallback leaks cross-chapter chunks when filter yields zero matches. Fixed: Removed unfiltered fallback; returns empty `RAGContext`.
- **F-007 (P0):** Missing RAG route authentication. Fixed: Mandatory `get_current_user` across all RAG endpoints.
- **F-008 (P0):** RAG student identity spoofing and unenrolled private course querying. Fixed: Enforced `req.student_id == current_user.id` and checked active enrollment in private courses.
- **F-009 (P1):** Grounding attribution. Fixed: Groundings are strictly attributed to verified retrieved chunks; misses produce empty grounding with zero leaks.

## Tests added
- `tests/test_phase03_rag_remediation.py`:
  - `test_F005_empty_query_never_returns_chemistry_chunk_thermo_01`
  - `test_F005_legacy_fallback_never_fabricates_chunk_on_miss`
  - `test_F006_metadata_filtering_mismatch_returns_empty_never_leaks_unfiltered`
  - `test_F007_rag_routes_unauthenticated_rejected_401`
  - `test_F008_student_cannot_spoof_another_student_id_in_query`
  - `test_F008_student_cannot_query_private_course_without_enrollment`
  - `test_F008_teacher_cannot_create_source_for_another_organization`
  - `test_F009_enrolled_student_retrieves_exact_grounded_chunks`
  - `test_F009_enrolled_student_querying_missing_concept_returns_rag_empty`

## Tests executed
- `pytest -v tests/test_phase03_rag_remediation.py`: 9 passed in 8.98s.
- `pytest tests/test_phase03_rag_remediation.py tests/test_phase06_scoped_rag_authorization.py tests/test_phase16_rag_plug_and_play_platform.py tests/test_phase4_hybrid_rag.py tests/test_phase5_knowledge_graph_rag.py tests/test_phase9_rag.py tests/test_phase13_rag_audit.py tests/test_phase23_rag_reliability.py tests/test_phase18_teacher_instruction_rag_integration.py`: 68 passed in 20.51s.
- `pytest -q`: 1,167 passed in 287.55s (0 failures, 0 skipped, 100% pass rate).
- `python -m compileall .`: 0 errors.

## Runtime verification
- Unauthenticated requests to `/api/v1/rag/*` return HTTP 401.
- Student attempting to query another student's ID returns HTTP 403.
- Student querying private course without active enrollment returns HTTP 403.
- Teacher attempting cross-org source registration returns HTTP 403.
- Unmatched queries return `status="RAG_EMPTY"`, `count=0`, `results=[]`, `data_context=""`.
- `chunk-thermo-01` is eliminated from production runtime.

## Failure-injection results
- Injected missing query -> `RAG_EMPTY` with 0 chunks.
- Injected metadata mismatch -> `RAG_EMPTY`, zero unfiltered vector chunks leaked.
- Injected anonymous query -> HTTP 401.
- Injected student spoofed ID -> HTTP 403.
- Injected cross-tenant source ingestion -> HTTP 403.

## Ending commit
`34f22cc` (`fix/phase-03-rag-remediation`)

## Next phase
Phase 04: AI Gateway and Model Failure Semantics
