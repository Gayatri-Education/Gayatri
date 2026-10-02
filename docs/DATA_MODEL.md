# Data Model & Schema Specification — Gayatri AI Platform

## 1. Overview

The **Gayatri AI Platform** data model is architected around an authoritative 50-table relational database schema (`gayatri_local.db` in SQLite for local/offline runtimes, and migration-compatible with PostgreSQL for cloud deployments), paired with canonical, strongly-typed Python dataclasses and Pydantic models in `central_platform/models/`.

The schema is governed by an immutable SQL DDL migration ledger (`migrations/001` through `008`), supporting both forward migrations and atomic rollbacks with SHA-256 checksum verification.

---

## 2. Relational Schema Architecture (50 Tables)

### 2.1 Schema Versioning & Migrations
- **`schema_migrations`**: Records applied migrations, version hashes, applied timestamps, and checksums to prevent schema drift and tampering.

### 2.2 Multi-Tenant Identity, Authentication & RBAC
- **`organizations`**: Multi-tenant institutions/schools (`org_id`, `name`, `code`, `settings`, `created_at`).
- **`users`**: Platform user accounts (`user_id`, `org_id`, `email`, `name`, `role`, `status`, `created_at`).
- **`user_credentials`**: Salted password hashes, token salts, and auth metadata.
- **`roles`**: System and custom roles (`SUPER_ADMIN`, `ORG_ADMIN`, `TEACHER`, `STUDENT`, `PARENT`, `GUEST`).
- **`permissions`**: Granular platform permissions (e.g., `course:create`, `course:publish`, `rag:ingest`, `instruction:write`).
- **`role_permissions`**: Many-to-many role-to-permission mapping table.

### 2.3 Course-Independent Architecture & Offerings (`migrations/004`)
- **`courses`**: Root course definitions independent of subject matter (`course_id`, `org_id`, `title`, `description`, `visibility`, `status`).
- **`course_versions`**: Immutable snapshots of course content (`version_id`, `course_id`, `version_tag`, `status`, `curriculum_dag`, `created_by`, `published_at`).
- **`organization_course_offerings`**: Active institutional deployments of a course version (`offering_id`, `org_id`, `course_id`, `version_id`, `academic_term`, `is_active`).
- **`enrollments`**: Student enrollments into specific offerings (`enrollment_id`, `student_id`, `offering_id`, `status`, `enrolled_at`).
- **`class_groups`**: Academic sections / classes within an institution (`class_id`, `org_id`, `name`, `grade_level`).
- **`cohorts`**: Student cohort groupings for collaborative or cohort-paced tracking.

### 2.4 Curriculum DAG & Concept Hierarchy (`migrations/001`, `002`)
- **`subjects`**: Subject category descriptors (`subject_id`, `name`, `code`).
- **`curricula`**: Curriculum framework definitions (e.g. CBSE, NCERT, Cambridge, Custom).
- **`curriculum_versions`**: Versioned curriculum trees.
- **`modules`**: High-level chapters or thematic units.
- **`topics`**: Granular topics within modules.
- **`concepts`**: Atomic learning concept nodes forming the DAG vertices.
- **`prerequisites`**: Directed edges representing prerequisite dependencies between concepts (`concept_id`, `prerequisite_concept_id`, `relationship_type`).

### 2.5 Canonical Learning State & Event Store (`migrations/002`)
- **`sessions`**: Active tutoring session boundaries (`session_id`, `student_id`, `offering_id`, `started_at`, `ended_at`).
- **`learning_events`**: Append-only immutable log of student interactions (`event_id`, `student_id`, `course_id`, `event_type`, `concept_id`, `payload`, `timestamp`).
- **`student_learning_records`**: Consolidated student state snapshots (`student_id`, `course_id`, `mastery_data`, `misconceptions`, `updated_at`).
- **`mastery_states`**: Granular per-concept mastery levels (`student_id`, `course_id`, `concept_id`, `mastery_score`, `confidence`, `last_evaluated_at`).
- **`misconceptions`**: Catalog of known diagnostic misconceptions.
- **`student_misconceptions`**: Active and resolved misconceptions per student.

### 2.6 Scoped Knowledge Pipeline & RAG (`migrations/005`, `006`)
- **`rag_sources`**: Ingested documents and textbooks (`source_id`, `course_id`, `version_id`, `filename`, `file_hash`, `uploaded_by`).
- **`rag_chunks`**: Text and formula chunks (`chunk_id`, `source_id`, `course_id`, `version_id`, `content`, `embedding_id`, `chunk_metadata`).

### 2.7 Scoped Teacher Instructions & Interventions (`migrations/007`)
- **`teacher_instructions`**: 5-tier instruction cascade directives (`instruction_id`, `scope_tier`, `scope_target_id`, `teacher_id`, `instruction_text`, `valid_from`, `valid_until`, `created_at`).
- **`interventions`**: Targeted pedagogical interventions assigned to at-risk students.
- **`notifications`**: System notifications for teachers, students, and parents.

### 2.8 Capability-Driven Assessments & Question Bank
- **`question_bank_items`**: Reusable questions with capability tags and difficulty ratings.
- **`assessments`**: Formal tests or diagnostic quizzes.
- **`assessment_items`**: Mapping of items to assessments.
- **`assignments`**: Homework and practice tasks assigned to class groups.
- **`assessment_attempts`**: Student submission records (`attempt_id`, `student_id`, `assessment_id`, `score`, `evaluation_status`).
- **`reassessments`**: Remedial re-testing attempts following targeted practice.

### 2.9 AI Gateway & Execution Observability
- **`ai_providers`**: Registered AI providers (Local, OpenAI, Anthropic, Gemini).
- **`ai_models`**: Available model weights and endpoints with latency metrics.
- **`ai_execution_logs`**: Comprehensive token usage, routing latency, and validation scores.
- **`audit_logs`**: Security, privilege, and sensitive action audit trail.

### 2.10 Fee Management & Invoicing Subsystem (`migrations/003`)
- **`fee_structures`**: Standard fee categories (tuition, laboratory, library).
- **`fee_plans`**: Billing schedules linked to student tiers.
- **`fee_accounts`**: Student balance ledgers (`account_id`, `student_id`, `balance_due`, `total_billed`, `total_paid`).
- **`invoices`**: Monthly student billing invoices.
- **`payments`**: Payment transaction logs (Razorpay, UPI, Cash).
- **`receipts`**: Formal issued receipts with receipt numbers.
- **`discounts`**: Scholarships and concessions.
- **`refunds`**: Payment reversal ledgers.

### 2.11 Offline Bi-Directional Sync Operations (`migrations/008`)
- **`sync_operations`**: Central idempotency ledger recording processed client operations (`operation_id`, `client_device_id`, `sequence_number`, `operation_type`, `payload_hash`, `applied_at`, `status`).

---

## 3. Core Python Dataclass Specifications

### 3.1 `CanonicalLearningState` (`central_platform/learning/state.py`)
```python
@dataclass
class CanonicalLearningState:
    student_id: str
    tenant_id: str
    course_id: str
    concept_mastery: Dict[str, float]      # concept_id -> mastery score [0.0 - 1.0]
    concept_confidence: Dict[str, float]   # concept_id -> Bayesian confidence [0.0 - 1.0]
    misconceptions: List[Dict[str, Any]]    # Active diagnosed misconceptions
    recent_events: List[Dict[str, Any]]     # Last 20 learning events for context
    due_reviews: List[str]                  # Concept IDs due for spaced repetition
    active_teacher_instructions: List[str] # Active directives applicable to student
    last_updated: str                       # ISO-8601 timestamp
```

### 3.2 `Course` & `CourseVersion` (`central_platform/courses/models.py`)
```python
@dataclass
class Course:
    course_id: str
    tenant_id: str
    title: str
    description: str
    subject: str
    visibility: CourseVisibility  # PUBLIC or PRIVATE
    created_at: str

@dataclass
class CourseVersion:
    version_id: str
    course_id: str
    version_tag: str              # e.g., "v1.0.0"
    status: VersionStatus         # DRAFT, IN_REVIEW, APPROVED, PUBLISHED, ARCHIVED
    curriculum_dag: Dict[str, Any]
    created_by: str
    published_at: Optional[str] = None
```

### 3.3 `TeacherInstruction` (`central_platform/teacher/instruction.py`)
```python
@dataclass
class TeacherInstruction:
    instruction_id: str
    scope_tier: InstructionTier   # SESSION, STUDENT, CLASS, COURSE, ORGANIZATION
    scope_target_id: str          # ID matching the scope tier
    teacher_id: str
    instruction_text: str
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
```

### 3.4 `RecoveryResult` (`central_platform/recovery/manager.py`)
```python
@dataclass
class RecoveryResult:
    failure_category: str          # Machine-readable error code
    status: RecoveryStatus         # FAILED, DEGRADED, RECOVERED
    user_message: str             # Student-safe pedagogical message
    technical_diagnostic: str     # Engineer-level actionable logging
    retryable: bool                # Guiding client retry policy
    commit_decision: CommitDecision # COMMIT, ROLLBACK, NOOP, RETRY
```

---

## 4. Schema Integrity & Tamper Protection

1. **Deterministic Checksum Validation**:
   - Every migration file has an authoritative SHA-256 hash recorded in the `schema_migrations` table.
   - During engine startup, the `MigrationRunner` validates all applied migrations against on-disk files. Tampered SQL scripts immediately fail closed.

2. **Transactional Migration Execution**:
   - Each migration runs inside a single database transaction. If any statement encounters a syntax error or constraint violation, the entire migration rolls back cleanly.

3. **Reversible Rollbacks**:
   - Every `*_schema.sql` file has an accompanying `*_down.sql` file providing complete rollback statements for safe unwinding in testing and production rollbacks.
