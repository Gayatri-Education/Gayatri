"""Tests for Phase 13: Multi-Level Admin Portal."""

import pytest
from central_platform.admin.service import AdminService
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole


@pytest.fixture
def db(tmp_path):
    db_file = str(tmp_path / "admin_test.db")
    return PlatformDatabase(db_file)


@pytest.fixture
def admin_service(db):
    return AdminService(db)


@pytest.fixture
def super_admin(db):
    user = User(
        id="usr-super-1",
        email="super@gayatri.edu",
        full_name="Super Administrator",
        role=UserRole.SUPER_ADMIN,
    )
    return db.create_user(user)


@pytest.fixture
def sample_org(db, super_admin, admin_service):
    return admin_service.create_organization(super_admin, "Delhi Science Academy", "dsa")


@pytest.fixture
def org_admin(db, admin_service, super_admin, sample_org):
    return admin_service.create_org_user(
        super_admin,
        email="orgadmin@dsa.edu",
        full_name="DSA Org Admin",
        role=UserRole.ORG_ADMIN,
        target_org_id=sample_org.id,
    )


@pytest.fixture
def course_admin(db, admin_service, org_admin, sample_org):
    return admin_service.create_org_user(
        org_admin,
        email="courseadmin@dsa.edu",
        full_name="Physics Course Admin",
        role=UserRole.COURSE_ADMIN,
    )


def test_super_admin_organization_lifecycle(admin_service, super_admin):
    org = admin_service.create_organization(super_admin, "Global Edu Org", "geo")
    assert org.id.startswith("org-")
    assert org.name == "Global Edu Org"

    health = admin_service.get_system_health(super_admin)
    assert health["status"] == "HEALTHY"
    assert health["active_models"] >= 2

    # Verify Audit Trail
    trail = admin_service.get_audit_trail()
    assert len(trail) >= 1
    assert trail[0].action == "CREATE_ORGANIZATION"


def test_super_admin_global_config(admin_service, super_admin, org_admin):
    config = admin_service.update_global_config(super_admin, {"maintenance_window": True})
    assert config["maintenance_window"] is True

    # Org admin cannot modify global config
    with pytest.raises(PermissionError):
        admin_service.update_global_config(org_admin, {"maintenance_window": False})


def test_org_admin_user_provisioning_and_isolation(admin_service, super_admin, org_admin, sample_org):
    # Org Admin creates teacher and student
    teacher = admin_service.create_org_user(
        org_admin,
        email="teacher1@dsa.edu",
        full_name="Teacher One",
        role=UserRole.TEACHER,
    )
    student = admin_service.create_org_user(
        org_admin,
        email="student1@dsa.edu",
        full_name="Student One",
        role=UserRole.STUDENT,
    )
    assert teacher.organization_id == sample_org.id
    assert student.organization_id == sample_org.id

    # Create second organization
    other_org = admin_service.create_organization(super_admin, "Mumbai Tech Prep", "mtp")

    # Org Admin cannot create users for other_org
    with pytest.raises(PermissionError):
        admin_service.create_org_user(
            org_admin,
            email="hacker@mtp.edu",
            full_name="Hacker",
            role=UserRole.TEACHER,
            target_org_id=other_org.id,
        )


def test_course_admin_course_and_enrollment(admin_service, course_admin, org_admin, sample_org):
    # Course Admin creates course
    course = admin_service.create_course(course_admin, "PHY-101", "Mechanics")
    assert course.organization_id == sample_org.id
    assert course.code == "PHY-101"

    # Org Admin creates student
    student = admin_service.create_org_user(
        org_admin,
        email="student2@dsa.edu",
        full_name="Student Two",
        role=UserRole.STUDENT,
    )

    # Course Admin enrolls student
    enrollment = admin_service.enroll_student(course_admin, student.id, course.id)
    assert enrollment.student_id == student.id
    assert enrollment.course_id == course.id


def test_organization_report_aggregation(admin_service, super_admin, org_admin, course_admin, sample_org):
    admin_service.create_org_user(org_admin, "t1@dsa.edu", "T1", UserRole.TEACHER)
    admin_service.create_org_user(org_admin, "s1@dsa.edu", "S1", UserRole.STUDENT)
    admin_service.create_org_user(org_admin, "s2@dsa.edu", "S2", UserRole.STUDENT)

    report = admin_service.generate_organization_report(org_admin)
    assert report["organization_id"] == sample_org.id
    assert report["teachers_count"] == 1
    assert report["students_count"] == 2
    assert report["total_users"] >= 4
