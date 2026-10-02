-- Migration 007: Teacher Instruction Hierarchy & Scoping
-- Up Migration: Add organizational, version, class, session, and audit columns to teacher_instructions

ALTER TABLE teacher_instructions ADD COLUMN organization_id TEXT;
ALTER TABLE teacher_instructions ADD COLUMN course_version_id TEXT;
ALTER TABLE teacher_instructions ADD COLUMN class_id TEXT;
ALTER TABLE teacher_instructions ADD COLUMN session_id TEXT;
ALTER TABLE teacher_instructions ADD COLUMN scope_type TEXT NOT NULL DEFAULT 'COURSE';
ALTER TABLE teacher_instructions ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE teacher_instructions ADD COLUMN safety_status TEXT NOT NULL DEFAULT 'VALIDATED';
ALTER TABLE teacher_instructions ADD COLUMN start_at TEXT;
ALTER TABLE teacher_instructions ADD COLUMN expires_at TEXT;
ALTER TABLE teacher_instructions ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE teacher_instructions ADD COLUMN audit_trail_json TEXT DEFAULT '[]';
ALTER TABLE teacher_instructions ADD COLUMN updated_at TEXT;

CREATE INDEX IF NOT EXISTS idx_teacher_inst_scope ON teacher_instructions(scope_type, is_active);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_class ON teacher_instructions(class_id);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_org ON teacher_instructions(organization_id);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_session ON teacher_instructions(session_id);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_hierarchy ON teacher_instructions(course_id, class_id, student_id, is_active);
