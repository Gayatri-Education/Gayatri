# Gayatri AI Platform — Database Schema Manifest & Migration Matrix

**Document:** `docs/reports/DATABASE_SCHEMA_MANIFEST.md`  
**Phase:** 21 (Database & Migration Hardening)  
**Maintained Per:** Master Plan Section 12.21  
**Total Authoritative Tables:** 50  
**Migration Scripts:** 8 forward (`001` - `008`), 8 symmetric rollback (`_down.sql`)  
**Backend Support:** Dual-Engine (SQLite Authoritative/Verified; PostgreSQL Driver Present, Live Daemon Unverified)  
**Date:** 2026-10-02  

---

## 1. Authoritative Table Manifest (50 Tables)

Each table has exactly one authoritative creation source across all migrations:

| # | Table Name | Authoritative Migration Source | Primary Key | Foreign Key Targets | Purpose |
|---|---|---|---|---|---|
| 1 | `schema_migrations` | `001_initial_schema.sql` | `version` | None | Migration version ledger with immutable SHA-256 checksums |
| 2 | `organizations` | `001_initial_schema.sql` | `id` | None | Multi-tenant organization boundaries |
| 3 | `users` | `001_initial_schema.sql` | `id` | `organizations(id)` | User identities with RBAC roles and tenant scoping |
| 4 | `user_credentials` | `001_initial_schema.sql` | `user_id` | `users(id)` | Argon2/bcrypt password and PIN authentication hashes |
| 5 | `roles` | `001_initial_schema.sql` | `name` | None | RBAC role definitions (`STUDENT`, `TEACHER`, `ORG_ADMIN`, `SUPER_ADMIN`) |
| 6 | `permissions` | `001_initial_schema.sql` | `code` | None | Fine-grained security permissions |
| 7 | `user_roles` | `001_initial_schema.sql` | `(user_id, role_name)` | `users(id)`, `roles(name)` | User-to-role mappings |
| 8 | `role_permissions` | `001_initial_schema.sql` | `(role_name, permission_code)` | `roles(name)`, `permissions(code)` | Role-to-permission mappings |
| 9 | `subjects` | `001_initial_schema.sql` | `id` | None | Generic academic subjects (Physics, Math, History, CS, Chemistry) |
| 10 | `curricula` | `001_initial_schema.sql` | `id` | `subjects(id)` | Curriculum boards and catalog entities |
| 11 | `curriculum_versions` | `001_initial_schema.sql` | `id` | `curricula(id)` | Versioned curriculum specifications with DAG graphs |
| 12 | `modules` | `001_initial_schema.sql` | `id` | `curriculum_versions(id)` | Hierarchical curriculum modules |
| 13 | `topics` | `001_initial_schema.sql` | `id` | `modules(id)` | Curriculum topics within modules |
| 14 | `concepts` | `001_initial_schema.sql` | `id` | `topics(id)` | Atomic learning concepts with difficulty ratings |
| 15 | `prerequisites` | `001_initial_schema.sql` | `(concept_id, prerequisite_concept_id)` | `concepts(id)`, `concepts(id)` | Concept prerequisite directed acyclic graph |
| 16 | `misconceptions` | `001_initial_schema.sql` | `id` | `concepts(id)` | Domain misconception catalog with remedial hints |
| 17 | `rag_sources` | `001_initial_schema.sql` | `id` | `organizations(id)` | Knowledge asset sources (textbook, class notes, remedial) |
| 18 | `rag_chunks` | `001_initial_schema.sql` | `id` | `rag_sources(id)` | Chunked text representations for BM25 and vector retrieval |
| 19 | `question_bank_items` | `001_initial_schema.sql` | `id` | `concepts(id)` | Standardized assessment items |
| 20 | `assessments` | `001_initial_schema.sql` | `id` | None | Multi-item assessment instances |
| 21 | `assessment_items` | `001_initial_schema.sql` | `(assessment_id, item_id)` | `assessments(id)`, `question_bank_items(id)` | Assessment-to-question mappings |
| 22 | `assessment_attempts` | `001_initial_schema.sql` | `id` | `assessments(id)`, `users(id)` | Student evaluation submissions and scores |
| 23 | `student_learning_records` | `001_initial_schema.sql` | `id` | `users(id)` | Student learning profiles |
| 24 | `mastery_states` | `001_initial_schema.sql` | `id` | `student_learning_records(id)`, `concepts(id)` | Concept mastery levels and confidence ratings |
| 25 | `student_misconceptions` | `001_initial_schema.sql` | `id` | `student_learning_records(id)`, `misconceptions(id)` | Active student misconceptions and remedial progress |
| 26 | `learning_events` | `001_initial_schema.sql` | `id` | `users(id)` | Append-only learning event stream |
| 27 | `ai_providers` | `001_initial_schema.sql` | `id` | None | Local and cloud inference providers |
| 28 | `ai_models` | `001_initial_schema.sql` | `id` | `ai_providers(id)` | Registered AI model manifests |
| 29 | `ai_execution_logs` | `001_initial_schema.sql` | `id` | `ai_models(id)`, `users(id)` | Audit trail of LLM inferences and tokens |
| 30 | `sessions` | `001_initial_schema.sql` | `id` | `users(id)` | Active and historical tutoring sessions |
| 31 | `interventions` | `001_initial_schema.sql` | `id` | `users(id)` | Pedagogical alerts and teacher interventions |
| 32 | `reassessments` | `001_initial_schema.sql` | `id` | `users(id)` | Follow-up evaluation triggers |
| 33 | `notifications` | `001_initial_schema.sql` | `id` | `users(id)` | In-app user notifications |
| 34 | `audit_logs` | `001_initial_schema.sql` | `id` | `users(id)` | Immutable security audit trail |
| 35 | `fee_structures` | `003_fee_management_schema.sql` | `id` | `organizations(id)` | Institutional fee models |
| 36 | `fee_plans` | `003_fee_management_schema.sql` | `id` | `fee_structures(id)` | Grade/course billing plans |
| 37 | `discounts` | `003_fee_management_schema.sql` | `id` | `organizations(id)` | Scholarships and concessions |
| 38 | `fee_accounts` | `003_fee_management_schema.sql` | `id` | `users(id)` | Student financial ledgers |
| 39 | `invoices` | `003_fee_management_schema.sql` | `id` | `fee_accounts(id)` | Billing statements |
| 40 | `payments` | `003_fee_management_schema.sql` | `id` | `invoices(id)` | Remittance transactions |
| 41 | `receipts` | `003_fee_management_schema.sql` | `id` | `payments(id)` | Official payment vouchers |
| 42 | `refunds` | `003_fee_management_schema.sql` | `id` | `payments(id)` | Reversals and returns |
| 43 | `courses` | `001_initial_schema.sql` | `id` | `organizations(id)` | Independent course entities |
| 44 | `course_versions` | `004_course_domain_model.sql` | `id` | `courses(id)` | Versioned course specifications |
| 45 | `organization_course_offerings` | `004_course_domain_model.sql` | `id` | `organizations(id)`, `courses(id)` | Tenant course enrollment catalog |
| 46 | `cohorts` | `001_initial_schema.sql` | `id` | `class_groups(id)` | Class cohorts |
| 47 | `enrollments` | `001_initial_schema.sql` | `id` | `users(id)`, `courses(id)` | Student course enrollments |
| 48 | `class_groups` | `001_initial_schema.sql` | `id` | `organizations(id)`, `courses(id)` | Classroom rosters |
| 49 | `assignments` | `001_initial_schema.sql` | `id` | `courses(id)` | Teacher homework and tasks |
| 50 | `sync_operations` | `008_sync_operations.sql` | `operation_id` | None | Desktop client synchronization records |

---

## 2. Migration Order & Rollback Symmetry

| Migration Version | Description | Forward Script | Down Script | Checksum Verified |
|---|---|---|---|---|
| `001` | Initial Authoritative Platform Schema | `001_initial_schema.sql` | `001_initial_schema_down.sql` | **YES** |
| `002` | Curriculum Abstraction | `002_curriculum_abstraction.sql` | `002_curriculum_abstraction_down.sql` | **YES** |
| `003` | Fee Management Schema | `003_fee_management_schema.sql` | `003_fee_management_schema_down.sql` | **YES** |
| `004` | Course Domain Model | `004_course_domain_model.sql` | `004_course_domain_model_down.sql` | **YES** |
| `005` | Knowledge Assets | `005_knowledge_assets.sql` | `005_knowledge_assets_down.sql` | **YES** |
| `006` | Scoped RAG Authorization | `006_scoped_rag_authorization.sql` | `006_scoped_rag_authorization_down.sql` | **YES** |
| `007` | Teacher Instruction Hierarchy | `007_teacher_instruction_hierarchy.sql` | `007_teacher_instruction_hierarchy_down.sql` | **YES** |
| `008` | Sync Operations | `008_sync_operations.sql` | `008_sync_operations_down.sql` | **YES** |

---

## 3. Database Compatibility Matrix

| Feature / Capability | SQLite (Authoritative Local / CI) | PostgreSQL (Production Scaled) | Verification Evidence |
|---|---|---|---|
| **Engine Availability** | Present (Built-in `sqlite3`) | Driver Present (`psycopg2`), Daemon Unverified | SQLite verified via live unit & integration suites. PG driver verified via import. |
| **Foreign Key Enforcement** | Enforced via `PRAGMA foreign_keys = ON;` | Enforced natively by RDBMS engine | Negative foreign key tests verify `sqlite3.IntegrityError`. |
| **Transaction Atomicity** | Atomic `BEGIN ... COMMIT / ROLLBACK` | ACID Compliant | Verified via transactional migration application. |
| **Idempotent Reruns** | Verified (`schema_migrations` checks) | Supported | Verified via `test_migrations_idempotency_rerun`. |
| **Reverse Rollback** | Verified symmetric down scripts | Supported | Verified via `test_migrations_full_rollback_and_reapply`. |
| **Checksum Integrity** | SHA-256 tamper detection enforced | SHA-256 tamper detection enforced | Verified via `MigrationChecksumMismatchError`. |
