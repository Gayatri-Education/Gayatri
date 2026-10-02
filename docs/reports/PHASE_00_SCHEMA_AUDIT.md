# Phase 00 — Database Schema & Migration Forensics Audit

**Document:** `docs/reports/PHASE_00_SCHEMA_AUDIT.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Inspection Date:** 2026-10-01  
**Commit SHA:** `bf47a63`  

---

## 1. Migration History & Authoritative DDL

The database evolution is tracked in `migrations/` and executed via `scripts/migrate_db.py` with SHA-256 checksum validation:

| Migration File | Description | Target Tables / Columns | Checksum Status |
|---|---|---|---|
| `001_initial_schema.sql` | Core Platform Schema (Phases 1-8) | 39 unique relational tables | Verified (Duplicate `assignments` resolved in Phase 0) |
| `002_curriculum_abstraction.sql` | Curriculum Board & Metadata | Adds `board`, `metadata` to `curricula` | Verified |
| `003_fee_management_schema.sql` | Fee Management Subsystem (Phase 30) | 8 fee structures, accounts, invoices, payments | Verified |
| `004_course_domain_model.sql` | Course Domain & Multi-Tenancy (Phase 2) | Adds `course_versions`, `organization_course_offerings`, `courses.visibility` | Verified |

---

## 2. Dynamic Runtime Schema Mutations (Architectural Defects)

In contradiction to deterministic migration management, 4 legacy modules invoke inline `ALTER TABLE` statements at runtime inside swallowed `try...except Exception: pass` blocks:

| Module File | Line(s) | Dynamic SQL Executed | Risk / Consequence |
|---|---|---|---|
| `core/session.py` | 128 | `ALTER TABLE sessions ADD COLUMN mode TEXT DEFAULT 'general_assistant'` | Hidden concurrency locking failures; magic default |
| `core/session.py` | 132 | `ALTER TABLE sessions ADD COLUMN user_id TEXT DEFAULT 'local_user_1'` | Hardcoded fake user identity injection |
| `core/session.py` | 152 | `ALTER TABLE tutor_contexts ADD COLUMN {col} {defn}` | Unsanitized dynamic column addition from runtime dictionary |
| `core/session.py` | 157 | `ALTER TABLE sessions ADD COLUMN profile_id TEXT DEFAULT 'default'` | Swallowed locking exceptions |
| `core/session.py` | 171 | `ALTER TABLE sessions ADD COLUMN summary TEXT DEFAULT ''` | Swallowed locking exceptions |
| `core/rag/store.py` | 73 | `ALTER TABLE rag_chunks ADD COLUMN section TEXT DEFAULT ''` | Redundant schema alteration on every store instantiation |
| `core/rag/store.py` | 78 | `ALTER TABLE rag_chunks ADD COLUMN provenance_type TEXT DEFAULT 'NCERT'` | Hardcodes Chemistry/NCERT into generic RAG chunk schema |
| `core/tutor/state.py` | 264 | `ALTER TABLE student_concept_mastery ADD COLUMN hint_count INTEGER DEFAULT 0` | Runtime DDL overhead on learning state load |
| `core/tutor/state.py` | 269 | `ALTER TABLE student_concept_mastery ADD COLUMN learning_status TEXT DEFAULT 'NEW'` | Runtime DDL overhead on learning state load |

---

## 3. SQLite vs PostgreSQL Compatibility Findings

1. `BOOLEAN` types are stored as `INTEGER` (0/1) for universal SQLite and PostgreSQL compatibility.
2. `scripts/migrate_db.py` handles both SQLite connections and PostgreSQL psycopg connections when `DATABASE_URL` specifies a Postgres connection string.
3. Automated rollback scripts (`*_down.sql`) exist for all migrations, ensuring full two-way schema versioning.

---

## 4. Remediation Plan
1. Eliminate all 9 inline `ALTER TABLE` statements in `core/session.py`, `core/rag/store.py`, and `core/tutor/state.py`.
2. Enforce startup verification via `scripts/migrate_db.py status`, rejecting application boot if pending migrations exist.
