-- Gayatri AI Central Platform — DDL Migration 006: Scoped RAG & Knowledge Authorization (Phase 06)
-- Compatible with PostgreSQL and SQLite

-- 1. Extend rag_sources table with scoping and version columns
ALTER TABLE rag_sources ADD COLUMN course_version_id TEXT;
ALTER TABLE rag_sources ADD COLUMN visibility_scope TEXT NOT NULL DEFAULT 'course';
ALTER TABLE rag_sources ADD COLUMN class_id TEXT;
ALTER TABLE rag_sources ADD COLUMN target_student_ids TEXT NOT NULL DEFAULT '[]';

CREATE INDEX IF NOT EXISTS idx_rag_sources_scope ON rag_sources(visibility_scope);
CREATE INDEX IF NOT EXISTS idx_rag_sources_version ON rag_sources(course_version_id);
CREATE INDEX IF NOT EXISTS idx_rag_sources_class ON rag_sources(class_id);

-- 2. Extend rag_chunks table with scoping and version columns
ALTER TABLE rag_chunks ADD COLUMN course_version_id TEXT;
ALTER TABLE rag_chunks ADD COLUMN visibility_scope TEXT NOT NULL DEFAULT 'course';
ALTER TABLE rag_chunks ADD COLUMN class_id TEXT;

CREATE INDEX IF NOT EXISTS idx_rag_chunks_version ON rag_chunks(course_version_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_class ON rag_chunks(class_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_scope ON rag_chunks(visibility_scope);
