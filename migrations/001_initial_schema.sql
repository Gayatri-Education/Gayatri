-- Gayatri AI Central Platform — Production DDL Migration 001
-- Authoritative Central Data Layer (Master Plan Section 12)
-- Compatible with PostgreSQL and SQLite

-- 0. Schema Migrations Ledger
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    checksum TEXT NOT NULL
);

-- 1. Organizations & Identity
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    organization_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE TABLE IF NOT EXISTS user_credentials (
    user_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt_hex TEXT NOT NULL,
    is_suspended INTEGER NOT NULL DEFAULT 0,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    password_reset_token TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_credentials_user ON user_credentials(user_id);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id TEXT NOT NULL,
    permission_id TEXT NOT NULL,
    PRIMARY KEY(role_id, permission_id),
    FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY(permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- 2. Academic Curriculum Hierarchy
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_courses_org ON courses(organization_id);

CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_subjects_course ON subjects(course_id);

CREATE TABLE IF NOT EXISTS curricula (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    title TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_curricula_course ON curricula(course_id);

CREATE TABLE IF NOT EXISTS curriculum_versions (
    id TEXT PRIMARY KEY,
    curriculum_id TEXT NOT NULL,
    version_num TEXT NOT NULL,
    change_log TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    published_at TEXT,
    schema_data TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(curriculum_id) REFERENCES curricula(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    curriculum_id TEXT NOT NULL,
    title TEXT NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    subject_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(curriculum_id) REFERENCES curricula(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_modules_curriculum ON modules(curriculum_id);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    title TEXT NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_topics_module ON topics(module_id);

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    difficulty REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_concepts_topic ON concepts(topic_id);

CREATE TABLE IF NOT EXISTS prerequisites (
    prerequisite_concept_id TEXT NOT NULL,
    dependent_concept_id TEXT NOT NULL,
    PRIMARY KEY(prerequisite_concept_id, dependent_concept_id),
    FOREIGN KEY(prerequisite_concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    FOREIGN KEY(dependent_concept_id) REFERENCES concepts(id) ON DELETE CASCADE
);

-- 3. Class Groups & Enrollments
CREATE TABLE IF NOT EXISTS class_groups (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    section TEXT NOT NULL DEFAULT 'A',
    created_at TEXT NOT NULL,
    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_class_groups_org ON class_groups(organization_id);

CREATE TABLE IF NOT EXISTS cohorts (
    id TEXT PRIMARY KEY,
    class_group_id TEXT NOT NULL,
    name TEXT NOT NULL,
    academic_year TEXT NOT NULL DEFAULT '2026-2027',
    created_at TEXT NOT NULL,
    FOREIGN KEY(class_group_id) REFERENCES class_groups(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollments (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    cohort_id TEXT,
    enrolled_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(cohort_id) REFERENCES cohorts(id) ON DELETE SET NULL,
    UNIQUE(student_id, course_id)
);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);

-- 4. Sessions & Granular Telemetry
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_course ON sessions(course_id);

CREATE TABLE IF NOT EXISTS learning_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    organization_id TEXT,
    course_id TEXT,
    concept_id TEXT NOT NULL DEFAULT '',
    event_type TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'student_desktop',
    payload TEXT NOT NULL DEFAULT '{}',
    score REAL,
    schema_version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_learning_events_session ON learning_events(session_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_student ON learning_events(student_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_org ON learning_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_type ON learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_events_created ON learning_events(created_at);

-- 5. Student Learning Records & Mastery
CREATE TABLE IF NOT EXISTS student_learning_records (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    authoritative INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(student_id, course_id)
);
CREATE INDEX IF NOT EXISTS idx_slr_student ON student_learning_records(student_id);

CREATE TABLE IF NOT EXISTS mastery_states (
    id TEXT PRIMARY KEY,
    slr_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0.5,
    confidence REAL NOT NULL DEFAULT 0.8,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(slr_id) REFERENCES student_learning_records(id) ON DELETE CASCADE,
    UNIQUE(slr_id, concept_id)
);
CREATE INDEX IF NOT EXISTS idx_mastery_slr ON mastery_states(slr_id);

CREATE TABLE IF NOT EXISTS misconceptions (
    id TEXT PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    remediation TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS student_misconceptions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    misconception_code TEXT NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    last_observed TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(misconception_code) REFERENCES misconceptions(code) ON DELETE CASCADE,
    UNIQUE(student_id, misconception_code)
);
CREATE INDEX IF NOT EXISTS idx_student_misc_student ON student_misconceptions(student_id);

-- 6. Assessments
CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    title TEXT NOT NULL,
    assessment_type TEXT NOT NULL DEFAULT 'formative',
    total_marks REAL NOT NULL DEFAULT 100.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_assessments_course ON assessments(course_id);

CREATE TABLE IF NOT EXISTS assessment_items (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    item_type TEXT NOT NULL DEFAULT 'MCQ',
    correct_answer TEXT NOT NULL,
    max_marks REAL NOT NULL DEFAULT 4.0,
    FOREIGN KEY(assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessment_attempts (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0.0,
    passed INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY(assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_asmt_attempt_student ON assessment_attempts(student_id);

-- 7. Teacher Directives & Interventions
CREATE TABLE IF NOT EXISTS teacher_instructions (
    id TEXT PRIMARY KEY,
    teacher_id TEXT NOT NULL,
    student_id TEXT NOT NULL DEFAULT 'all',
    course_id TEXT NOT NULL,
    instruction_text TEXT NOT NULL,
    concept_scope TEXT NOT NULL DEFAULT 'ALL',
    priority INTEGER NOT NULL DEFAULT 2,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_course ON teacher_instructions(course_id);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_student ON teacher_instructions(student_id);

CREATE TABLE IF NOT EXISTS interventions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning',
    alert_type TEXT NOT NULL DEFAULT 'learning_gap',
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_interventions_student ON interventions(student_id);
CREATE INDEX IF NOT EXISTS idx_interventions_course ON interventions(course_id);

CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    teacher_id TEXT NOT NULL,
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    recipient_id TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(recipient_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);

-- 8. AI Governance, Observability & Auditing
CREATE TABLE IF NOT EXISTS ai_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    base_url TEXT DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    context_window INTEGER NOT NULL DEFAULT 8192,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(provider_id) REFERENCES ai_providers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_execution_logs (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'SUCCESS',
    created_at TEXT NOT NULL,
    FOREIGN KEY(model_id) REFERENCES ai_models(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '{}',
    ip_address TEXT NOT NULL DEFAULT '127.0.0.1',
    created_at TEXT NOT NULL,
    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
