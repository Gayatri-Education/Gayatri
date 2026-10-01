-- Gayatri AI Central Platform — DDL Migration 004: Course Domain Model & Multi-Tenancy (Phase 02)
-- Compatible with PostgreSQL and SQLite

-- 1. Extend courses table with visibility
ALTER TABLE courses ADD COLUMN visibility TEXT NOT NULL DEFAULT 'PRIVATE';

-- 2. Create course_versions table
CREATE TABLE IF NOT EXISTS course_versions (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    version_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    tool_policy TEXT NOT NULL DEFAULT '{}',
    tutor_policy TEXT NOT NULL DEFAULT '{}',
    checksum TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT '',
    published_by TEXT,
    created_at TEXT NOT NULL,
    published_at TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(course_id, version_number)
);
CREATE INDEX IF NOT EXISTS idx_course_versions_course ON course_versions(course_id);
CREATE INDEX IF NOT EXISTS idx_course_versions_status ON course_versions(status);

-- 3. Create organization_course_offerings table
CREATE TABLE IF NOT EXISTS organization_course_offerings (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    pinned_version_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    enrolled_at TEXT NOT NULL,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(pinned_version_id) REFERENCES course_versions(id) ON DELETE SET NULL,
    UNIQUE(org_id, course_id)
);
CREATE INDEX IF NOT EXISTS idx_org_course_offerings_org ON organization_course_offerings(org_id);
CREATE INDEX IF NOT EXISTS idx_org_course_offerings_course ON organization_course_offerings(course_id);

-- 4. Extend sessions table with course_version_id and class_id
ALTER TABLE sessions ADD COLUMN course_version_id TEXT;
ALTER TABLE sessions ADD COLUMN class_id TEXT;

-- 5. Extend enrollments table with course_offering_id and class_id
ALTER TABLE enrollments ADD COLUMN course_offering_id TEXT;
ALTER TABLE enrollments ADD COLUMN class_id TEXT;
