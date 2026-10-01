-- Migration 007 Down: Rollback Teacher Instruction Hierarchy
-- Drops indexes and removes added columns via table rebuild for SQLite compatibility

DROP INDEX IF EXISTS idx_teacher_inst_scope;
DROP INDEX IF EXISTS idx_teacher_inst_class;
DROP INDEX IF EXISTS idx_teacher_inst_org;
DROP INDEX IF EXISTS idx_teacher_inst_session;
DROP INDEX IF EXISTS idx_teacher_inst_hierarchy;

CREATE TABLE IF NOT EXISTS teacher_instructions_down_tmp (
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

INSERT INTO teacher_instructions_down_tmp (
    id, teacher_id, student_id, course_id, instruction_text, concept_scope, priority, is_active, created_at
)
SELECT id, teacher_id, student_id, course_id, instruction_text, concept_scope, priority, is_active, created_at
FROM teacher_instructions;

DROP TABLE teacher_instructions;

ALTER TABLE teacher_instructions_down_tmp RENAME TO teacher_instructions;

CREATE INDEX IF NOT EXISTS idx_teacher_inst_course ON teacher_instructions(course_id);
CREATE INDEX IF NOT EXISTS idx_teacher_inst_student ON teacher_instructions(student_id);
