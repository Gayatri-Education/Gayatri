# Phase 06 Execution Plan — Scoped RAG & Knowledge Authorization

**Document:** `docs/reports/PHASE_06_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.6)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Transform RAG from a passive retrieval index into an **authorization-aware academic knowledge subsystem**. Scoping must be strictly bound to:
1. **Multi-tenant Organization Scoping:** Private courses and knowledge assets from Organization A are completely invisible and forbidden to users from Organization B.
2. **Course Version Isolation:** Pinned course versions strictly isolate content; queries under version `1.0` never leak chunks from version `2.0` (or vice versa).
3. **Class / Cohort Scoping:** Class-specific notes and teacher directives (`visibility_scope = "CLASS"`) are strictly visible only to students belonging to that specific `class_id`.
4. **Targeted Remedial Scoping:** Personalized remediation assets (`visibility_scope = "STUDENT_TARGETED"`) are strictly visible only to explicitly targeted students.
5. **No Fallback Leakage:** Scoped and restricted queries that yield zero authorized chunks return deterministic `RAG_EMPTY` or `RAG_DENIED`; they **never fall back to global or un-scoped documents**.
6. **Authorization Diagnostics:** Return diagnostic reasons (`RAG_OK`, `RAG_EMPTY`, `RAG_DENIED`, `RAG_ERROR`) without leaking confidential chunk text in error payloads.

---

## 2. Forensic Findings & Architectural Pipeline Strategy

1. **Current Couplings & Gaps:**
   - `rag_sources` and `rag_chunks` in database lack explicit columns for `course_version_id`, `visibility_scope`, `class_id`, and `target_student_ids`.
   - `RAGService.query()` currently filters primarily on `(course_id, subject, concept)` and published status, but does not perform organization tenancy checks, enrollment verification, version matching, class matching, or student-targeted remedial checks.
   - If a course query yields no results, legacy behavior previously considered falling back to global NCERT files. Phase 05 closed global fallback for course queries; Phase 06 formally guarantees zero unauthorized fallbacks across all tenancy/version/class boundaries.

2. **Target Architecture:**
   - **Knowledge Visibility Scope (`KnowledgeVisibilityScope` Enum):**
     - `COURSE`: Visible to all students enrolled in the course offering.
     - `CLASS`: Visible only to students enrolled in the specified `class_id` / cohort.
     - `STUDENT_TARGETED`: Visible only to students whose `student_id` is in `target_student_ids` (e.g. remedial worksheets).
   - **Database Migration 006 (`migrations/006_scoped_rag_authorization.sql` & down):**
     - Alter `rag_sources` and `rag_chunks` to add `course_version_id`, `visibility_scope`, `class_id`, `target_student_ids`.
     - Index `visibility_scope`, `course_version_id`, `class_id`.
   - **Authorization-Aware Retrieval Gate:**
     - Query accepts `context: Optional[CourseLearningContext]`, `student_id: Optional[str]`, `course_id: Optional[str]`, `course_version_id: Optional[str]`, `class_id: Optional[str]`, `user: Optional[User]`.
     - Checks organization tenancy: if student is from Org B and course is private to Org A, returns `status="RAG_DENIED"` with zero chunks.
     - Evaluates version matching: only chunks matching `course_version_id` (or unversioned global course material) are returned.
     - Evaluates visibility scope: filters out class-notes for other classes, and filters out student-targeted items where student is not targeted.
     - Enforces deterministic responses: `RAG_OK`, `RAG_EMPTY`, `RAG_DENIED`.

---

## 3. Planned Implementation Details

### Step 1: Schema & Model Entities (`central_platform/models/schema.py`)
- Define `KnowledgeVisibilityScope` enum: `COURSE`, `CLASS`, `STUDENT_TARGETED`.
- Extend `RAGSource` dataclass with `course_version_id`, `visibility_scope`, `class_id`, `target_student_ids: List[str]`.
- Extend `RAGChunk` dataclass with `course_version_id`, `visibility_scope`, `class_id`.

### Step 2: Database Migration 006 (`migrations/006_scoped_rag_authorization.sql` & `_down.sql`)
- Add columns to `rag_sources`: `course_version_id`, `visibility_scope`, `class_id`, `target_student_ids`.
- Add columns to `rag_chunks`: `course_version_id`, `visibility_scope`, `class_id`.
- Add indexes on `rag_sources(visibility_scope)`, `rag_sources(course_version_id)`, `rag_sources(class_id)`.
- Update `PlatformDatabase` CRUD methods for `rag_sources` and `rag_chunks` to persist and load new columns.
- Update `get_rag_chunks_by_course` in `PlatformDatabase` to support filtering by `course_version_id`, `class_id`, and `visibility_scope`.

### Step 3: Authorization-Aware Service Layer (`central_platform/rag/service.py`)
- Update `upload_knowledge_asset()` and `register_source()` to accept and persist `course_version_id`, `visibility_scope`, `class_id`, `target_student_ids`.
- Enhance `query()` method:
  - Multi-tenant boundary check: verify student organization against course organization and course visibility.
  - Course version filtering: strict isolation between course versions.
  - Class scoping: class notes only accessible to matching `class_id`.
  - Student remedial scoping: targeted items only accessible if `student_id in target_student_ids`.
  - Invariant: Zero leakage of unauthorized content.

---

## 4. Test Strategy & Acceptance Gate

Create dedicated test suite `tests/test_phase06_scoped_rag_authorization.py` covering:
1. **Course Textbook Scoping:** Enrolled student can retrieve course textbook material.
2. **Multi-Tenant Org Isolation:** Student from Org B querying private course in Org A receives `RAG_DENIED` with 0 chunks.
3. **Class Scope Isolation:** Class notes for Class 10-A are invisible to students in Class 10-B.
4. **Remedial Student Targeted Scope:** Remedial worksheet targeted at Student X is invisible to Student Y, and visible to Student X.
5. **Course Version Isolation:** Material tagged version `1.0` is invisible to queries targeting version `2.0`.
6. **No Fallback Under Restriction:** Scoped search with 0 matches returns `RAG_EMPTY` (never falls back to global docs).
7. **Diagnostic Transparency:** Diagnostics report reason (`DENIED`, `EMPTY`) without content leakage.
8. **Full Suite Regression:** All 898 existing tests remain 100% green.

---

## 5. Artifacts to Generate Upon Completion

- `docs/reports/PHASE_06_PLAN.md` (this document)
- `docs/reports/PHASE_06_TEST_REPORT.md`
- `docs/reports/PHASE_06_TEST_RESULTS.json`
- Updates to `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`
