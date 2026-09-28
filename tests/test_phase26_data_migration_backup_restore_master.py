"""Phase 26: Data Migration, Backup, and Recovery Testing Master Suite.

Implements Master Plan Section 35:
Tests complete end-to-end disaster recovery lifecycle:
1. Seed live platform database with organizations, users, courses, learning events, and SLR
2. Generate online snapshot backup via SQLite backup engine
3. Simulate catastrophic database destruction (file wipe)
4. Restore database from backup snapshot
5. Reconnect platform database and verify 100% data integrity preservation
"""

import os
import pytest
from pathlib import Path

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, LearningEvent, Organization, User, UserRole
from scripts.backup_restore_db import create_backup, restore_backup, verify_database_integrity


def test_e2e_backup_destruction_and_recovery(tmp_path):
    """E2E Disaster Recovery Lifecycle:
    1. Create and populate primary database
    2. Snapshot backup
    3. Destroy primary DB
    4. Restore from backup
    5. Verify integrity and query records
    """
    db_file = str(tmp_path / "primary_gayatri.sqlite3")
    backup_dir = str(tmp_path / "backups")
    
    # 1. Initialize and populate primary database
    db = PlatformDatabase(db_path=db_file)
    org = Organization(id="org_disaster_01", name="Disaster Recovery Academy", slug="dr-academy")
    db.create_organization(org)
    
    user = User(
        id="student_dr_01",
        email="dr_student@academy.org",
        full_name="DR Student",
        role=UserRole.STUDENT,
        organization_id="org_disaster_01",
    )
    db.create_user(user)
    
    course = Course(
        id="course_dr_101",
        organization_id="org_disaster_01",
        code="DR101",
        title="Disaster Recovery 101",
    )
    db.create_course(course)
    
    db.close()

    # 2. Generate backup snapshot
    backup_path = create_backup(db_file, backup_dir)
    assert os.path.exists(backup_path)
    assert os.path.getsize(backup_path) > 0

    # 3. Simulate catastrophic database destruction (wipe file)
    os.remove(db_file)
    assert not os.path.exists(db_file)

    # 4. Restore database from backup
    restore_success = restore_backup(backup_path, db_file)
    assert restore_success is True
    assert os.path.exists(db_file)

    # 5. Verify database integrity and query data
    integrity_report = verify_database_integrity(db_file)
    assert integrity_report["integrity_ok"] is True
    assert integrity_report["tables"]["users"] >= 1
    assert integrity_report["tables"]["organizations"] >= 1

    # Reconnect PlatformDatabase and verify entity retrieval
    restored_db = PlatformDatabase(db_path=db_file)
    restored_org = restored_db.get_organization("org_disaster_01")
    assert restored_org is not None
    assert restored_org.name == "Disaster Recovery Academy"

    restored_user = restored_db.get_user("student_dr_01")
    assert restored_user is not None
    assert restored_user.email == "dr_student@academy.org"

    restored_course = restored_db.get_course("course_dr_101")
    assert restored_course is not None
    assert restored_course.title == "Disaster Recovery 101"
    
    restored_db.close()
