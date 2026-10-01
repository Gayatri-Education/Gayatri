-- Migration 008 Down: Rollback Sync Operations Table (Phase 14)

DROP INDEX IF EXISTS idx_sync_operations_student;
DROP TABLE IF EXISTS sync_operations;
