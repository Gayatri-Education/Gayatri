# Phase 18 Implementation Plan: Teacher Instruction + RAG Integration

**Document:** `docs/reports/PHASE_18_PLAN.md`  
**Phase:** 18  
**Status:** IN_PROGRESS  
**Target:** Teacher Instruction + RAG Integration, Deterministic Context Assembly, Provenance Tracking, Scoped Directives vs Evidence Separation, and Contribution Auditing  

---

## 1. Architectural Scope & Objectives

Section 12.18 of the Master Plan mandates:
- **Combine Core Context Sources**: The tutor orchestrator receives exactly the authorized knowledge and applicable instructions.
- **Deterministic 7-Layer Context Assembly**:
  1. Platform Policy (System invariant)
  2. Course Policy (Tutor & Tool policy)
  3. Teacher Instructions (Hierarchical resolution: SESSION > STUDENT > CLASS > COURSE > ORGANIZATION)
  4. Learner State (BKT/SLR mastery, confidence, misconceptions)
  5. Authorized RAG (Course textbook + Class notes + Student remedial, strictly scoped)
  6. Conversation History (Trimmed, formatted)
  7. Student Query
- **Directives vs Evidence Separation**:
  - Directives (Instructions) placed in system prompt framed as behavioral constraints.
  - Evidence (RAG chunks) placed in reference context safely enveloped in XML to prevent prompt injection and answer leakage.
- **Provenance & Contribution Audit**:
  - Each RAG chunk carries rich provenance: `source_id`, `chunk_id`, `authority`, `provenance_type`, `visibility_scope`, `class_id`.
  - Every turn records `applied_instruction_ids`, `contributed_source_ids`, and `contributed_chunk_ids`.
  - Redacted / clean provenance traces for audit without leaking private student notes.
- **Mandatory Negative & Boundary Tests**:
  - Course textbook + class note + student remedial merged context
  - Broad + narrow instruction cascade (SESSION overrides STUDENT overrides CLASS overrides COURSE overrides ORG)
  - Expired instruction exclusion
  - Unauthorized content (cross-class, cross-student notes) excluded
  - No content / empty RAG graceful handling
  - No instructions graceful handling
  - Mixed scopes
  - Course version pinning and updates

---

## 2. Component Modifications

### 2.1 Context Builder (`central_platform/ai/context_builder.py`)
- Integrate `TeacherInstructionEngine` for hierarchical instruction resolution.
- Pass `student_id`, `class_id`, `course_version_id`, and `organization_id` into `RAGService.query()`.
- Add provenance structures:
  - `ProvenanceRecord` dataclass (`source_id`, `chunk_id`, `source_title`, `authority`, `provenance_type`, `visibility_scope`, `citation`).
  - Track `applied_instruction_ids: List[str]`.
  - Track `contributed_source_ids: List[str]`.
  - Track `contributed_chunk_ids: List[str]`.
  - Track `provenance_records: List[ProvenanceRecord]`.
- Provide `build_context()` with full scoping parameters (`student_id`, `course_id`, `concept_id`, `class_id`, `session_id`, `version_id`, `organization_id`).
- Keep evidence safely separated from directives:
  - Directives formatted with provenance IDs.
  - Evidence formatted with `<rag_evidence_data>` envelopes.

### 2.2 Generic Tutor Orchestrator (`central_platform/tutor/orchestrator.py`)
- Replace non-existent `self.rag_service.search_chunks` call with `self.rag_service.query(...)` passing full scoping context.
- Pass resolved instructions and scoped RAG chunks into `ContextBuilder.build_context()`.
- Attach `applied_instruction_ids`, `contributed_source_ids`, `contributed_chunk_ids`, and `provenance_records` to `TutorTurnResult`.
- Record provenance audit logs.

### 2.3 Schemas & API (`central_platform/api/schemas.py`, `central_platform/api/routes/tutor.py`)
- Extend `TutorTurnApiResponse` and `TutorTurnResult` with `applied_instruction_ids`, `contributed_source_ids`, `contributed_chunk_ids`, and `provenance_summary`.

---

## 3. Verification & Acceptance Criteria
- 12 comprehensive unit and integration tests in `tests/test_phase18_teacher_instruction_rag_integration.py`.
- 100% green pass on regression suite (1,041 + 12 = 1,053 tests).
- All reports, state files, and sync queue updated.
- Git commit and push to `origin/master`.
