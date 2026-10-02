# Phase 05 Execution Plan — Knowledge Asset Ingestion & Publication Pipeline

**Document:** `docs/reports/PHASE_05_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.5)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Establish a controlled, secure content ingestion and publication pipeline for academic course assets. Teachers can upload and stage course materials, the system processes, cleans, chunks, and validates them, and only institutional administrators (`ORG_ADMIN` or `SUPER_ADMIN`) can approve and publish them. Strictly enforce the student visibility invariant: **no unpublished content is retrievable by student workflows**.

---

## 2. Forensic Findings & Architectural Pipeline Strategy

1. **Current Couplings & Gaps:**
   - `central_platform/models/schema.py`: `RAGSourceStatus` currently contains legacy lowercase states (`draft`, `ingested`, `validated`, `published`, `archived`) lacking `PROCESSING`, `READY_FOR_REVIEW`, `APPROVED`, and `FAILED`.
   - `rag_sources` database table lacks explicit fields for `content_type`, `uploaded_by`, `published_by`, `published_at`, and `error_message`.
   - `central_platform/rag/service.py`: `publish_source` currently lacks explicit role-based authorization gates, allowing any caller to transition sources directly to published.
2. **Target Architecture:**
   - **Formal Knowledge Asset Status Lifecycle:**
     `DRAFT` → `PROCESSING` → `READY_FOR_REVIEW` → `APPROVED` → `PUBLISHED` → `ARCHIVED` (with transition to `FAILED` upon parser/sanitization failure).
   - **Standard Content Classifications:**
     `TEXTBOOK`, `REFERENCE`, `TEACHER_NOTE`, `WORKSHEET`, `REMEDIAL`, `ASSESSMENT_SOURCE`, `SOLUTION_GUIDE`, `OTHER`.
   - **Pipeline Execution:**
     Upload → SHA256 checksum → format/size validation → persistent source creation → parser extraction → security sanitization → chunking → validation gate.
   - **Controlled Approval & Publication Gates:**
     - Teachers/Admins can upload drafts and trigger processing.
     - Students are forbidden from uploading knowledge assets.
     - ONLY `ORG_ADMIN` or `SUPER_ADMIN` can approve or publish assets.
     - Unauthorized approval attempts return 403 `PermissionError`.
   - **Student Visibility Invariant (Phase Gate):**
     - RAG retrieval workflows strictly filter on `status = 'PUBLISHED'`.
     - Assets in `DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `APPROVED`, `FAILED`, or `ARCHIVED` are completely invisible to student queries.

---

## 3. Planned Implementation Details

### Step 1: Schema & Model Entities (`central_platform/models/schema.py`)
- Define `KnowledgeContentType` enum.
- Expand `RAGSourceStatus` / `KnowledgeAssetStatus` with case-insensitive normalization:
  `DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `APPROVED`, `PUBLISHED`, `ARCHIVED`, `FAILED`.
- Extend `RAGSource` dataclass with `content_type`, `uploaded_by`, `published_by`, `published_at`, `error_message`.

### Step 2: Database Migration 005 (`migrations/005_knowledge_assets.sql` & `_down.sql`)
- Add columns to `rag_sources`: `content_type`, `uploaded_by`, `published_by`, `published_at`, `error_message`.
- Create corresponding reversible down script `migrations/005_knowledge_assets_down.sql`.
- Update `PlatformDatabase` CRUD methods for `rag_sources` to persist and load new columns.
- Update `get_rag_chunks_by_course` and `list_rag_sources` to use case-insensitive status matching (`LOWER(status) = 'published'`).

### Step 3: Knowledge Ingestion & Publication Service (`central_platform/rag/service.py`)
- Implement `upload_knowledge_asset()`:
  - Role check (rejects student uploads with 403).
  - Validation: non-empty content, size bounds (max 10MB), non-empty course_id.
  - Processing: computes checksum, parses sections, sanitizes, generates chunks, runs validation.
  - Success transitions to `READY_FOR_REVIEW`; failure transitions to `FAILED` with error message.
- Implement `approve_knowledge_asset()`:
  - Role check: requires `ORG_ADMIN` or `SUPER_ADMIN`.
  - Transitions `READY_FOR_REVIEW` → `APPROVED`.
- Implement `publish_knowledge_asset()`:
  - Role check: requires `ORG_ADMIN` or `SUPER_ADMIN`.
  - Transitions `APPROVED` (or `READY_FOR_REVIEW`) → `PUBLISHED`. Sets `published_at`.
- Implement `archive_knowledge_asset()`:
  - Transitions to `ARCHIVED`.
- Grounded `query()`:
  - Enforces that student queries only retrieve chunks from `PUBLISHED` sources.

---

## 4. Test Strategy & Acceptance Gate

Create dedicated test suite `tests/test_phase05_knowledge_assets.py` covering:
1. **Multi-Format Ingestion:** Markdown, Plain Text, JSON, and PDF/mock.
2. **End-to-End State Lifecycle Transitions:**
   `DRAFT` → `PROCESSING` → `READY_FOR_REVIEW` → `APPROVED` → `PUBLISHED` → `ARCHIVED`.
3. **Failure Isolation:**
   Malformed, corrupted, or empty uploads transition to `FAILED` and can never be approved or published.
4. **Role-Based Authorization Gates:**
   - Teachers can upload but CANNOT approve or publish (403 PermissionError).
   - Students CANNOT upload knowledge assets (403 PermissionError).
   - Only Org Admins or Super Admins can approve and publish.
5. **Phase Gate: Student Visibility Invariant:**
   - Content in `DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `APPROVED`, `FAILED`, and `ARCHIVED` is queried by a student -> returns 0 results.
   - Only upon publication does the content become retrievable.
6. **Full Regression Gate:** All 886 existing tests pass 100% green.

---

## 5. Artifacts to Generate Upon Completion

- `docs/reports/PHASE_05_PLAN.md` (this plan)
- `docs/reports/PHASE_05_TEST_REPORT.md`
- `docs/reports/PHASE_05_TEST_RESULTS.json`
- Updates to `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`
