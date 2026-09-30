-- Down migration for Phase 09: Curriculum Abstraction
-- Removes board and metadata from curricula table.

-- Note: SQLite does not support DROP COLUMN directly in older versions, 
-- but modern SQLite supports it. If Postgres, it works natively.
ALTER TABLE curricula DROP COLUMN board;
ALTER TABLE curricula DROP COLUMN metadata;
