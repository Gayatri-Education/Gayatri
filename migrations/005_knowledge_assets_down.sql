-- Gayatri AI Central Platform — DDL Migration 005 Down: Rollback Knowledge Assets Schema
-- Compatible with PostgreSQL and SQLite (3.35.0+)

DROP INDEX IF EXISTS idx_rag_sources_content_type;
DROP INDEX IF EXISTS idx_rag_sources_uploaded_by;
DROP INDEX IF EXISTS idx_rag_sources_published_by;

ALTER TABLE rag_sources DROP COLUMN content_type;
ALTER TABLE rag_sources DROP COLUMN uploaded_by;
ALTER TABLE rag_sources DROP COLUMN published_by;
ALTER TABLE rag_sources DROP COLUMN published_at;
ALTER TABLE rag_sources DROP COLUMN error_message;
