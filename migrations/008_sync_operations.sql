-- Migration 008: Sync Operations and Idempotency Ledger (Phase 14)

CREATE TABLE IF NOT EXISTS sync_operations (
    operation_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    device_id TEXT,
    course_id TEXT,
    synced_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    acknowledged_ids_json TEXT NOT NULL DEFAULT '[]',
    conflicts_resolved INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'SYNCED',
    latest_mastery REAL DEFAULT 0.0,
    server_timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_operations_student
ON sync_operations (student_id, created_at);
