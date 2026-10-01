-- Gayatri AI Central Platform — DDL Migration 006 Down: Rollback Scoped RAG Authorization
-- Compatible with PostgreSQL and SQLite (3.35.0+)

DROP INDEX IF EXISTS idx_rag_chunks_scope;
DROP INDEX IF EXISTS idx_rag_chunks_class;
DROP INDEX IF EXISTS idx_rag_chunks_version;
DROP INDEX IF EXISTS idx_rag_sources_class;
DROP INDEX IF EXISTS idx_rag_sources_version;
DROP INDEX IF EXISTS idx_rag_sources_scope;

ALTER TABLE rag_chunks DROP COLUMN class_id;
ALTER TABLE rag_chunks DROP COLUMN visibility_scope;
ALTER TABLE rag_chunks DROP COLUMN course_version_id;

ALTER TABLE rag_sources DROP COLUMN target_student_ids;
ALTER TABLE rag_sources DROP COLUMN class_id;
ALTER TABLE rag_sources DROP COLUMN visibility_scope;
ALTER TABLE rag_sources DROP COLUMN course_version_id;
