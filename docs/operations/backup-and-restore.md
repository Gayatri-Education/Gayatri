# Gayatri AI Platform: Database Backup and Disaster Recovery Runbook (Phase 26)

## Overview
This runbook defines the authoritative operational procedures for creating database snapshots, verifying cryptographic integrity, and executing point-in-time disaster recovery across Gayatri Platform deployments.

## 1. Automated Online Backup Procedure

### Command Line Execution
To capture a non-blocking ACID snapshot of the active platform database:
```powershell
python -c "from scripts.backup_restore_db import create_backup; print(create_backup('data/gayatri_platform.db', 'backups/'))"
```

### SQLite Online Backup API
The backup engine utilizes the native SQLite C API (`sqlite3_backup_init` via Python `sqlite3.backup()`), ensuring:
- Zero write locking on active tutoring sessions.
- In-flight transactions are committed atomically.
- Page checksum validation during snapshot transmission.

## 2. Disaster Recovery & Restoration Procedure

### Command Line Execution
To restore the platform from an authoritative snapshot:
```powershell
python -c "from scripts.backup_restore_db import restore_backup; restore_backup('backups/gayatri_db_backup_20260928_120000.sqlite3', 'data/gayatri_platform.db')"
```

### Post-Restore Verification
Run database integrity and relational consistency checks:
```powershell
python -c "from scripts.backup_restore_db import verify_database_integrity; print(verify_database_integrity('data/gayatri_platform.db'))"
```

## 3. Preservation Invariants
1. **Student Learning Record (SLR) Invariant**: All 15 dimensions of student mastery, retention decay constants, and misconception codes are preserved byte-for-byte.
2. **Learning Events Immutability Invariant**: Append-only event logs cannot be truncated or mutated during backup/restore.
3. **Multi-Tenant Scoping Invariant**: Foreign key relationships between organizations, courses, and users are strictly verified upon restoration.
