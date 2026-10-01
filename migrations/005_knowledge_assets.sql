-- Gayatri AI Central Platform — DDL Migration 005: Knowledge Asset Ingestion & Publication Pipeline (Phase 05)
-- Compatible with PostgreSQL and SQLite

ALTER TABLE rag_sources ADD COLUMN content_type TEXT NOT NULL DEFAULT 'textbook';
ALTER TABLE rag_sources ADD COLUMN uploaded_by TEXT;
ALTER TABLE rag_sources ADD COLUMN published_by TEXT;
ALTER TABLE rag_sources ADD COLUMN published_at TEXT;
ALTER TABLE rag_sources ADD COLUMN error_message TEXT;

CREATE INDEX IF NOT EXISTS idx_rag_sources_content_type ON rag_sources(content_type);
CREATE INDEX IF NOT EXISTS idx_rag_sources_uploaded_by ON rag_sources(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_rag_sources_published_by ON rag_sources(published_by);
