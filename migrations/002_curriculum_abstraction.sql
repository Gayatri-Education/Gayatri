-- Up migration for Phase 09: Curriculum Abstraction
-- Adds board enumeration and metadata to curricula table.

ALTER TABLE curricula ADD COLUMN board TEXT NOT NULL DEFAULT 'custom';
ALTER TABLE curricula ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';
