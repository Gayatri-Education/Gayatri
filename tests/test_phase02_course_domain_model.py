"""Tests for Phase 02: Course Domain Model, Multi-Tenancy, and Versioning."""

import os
import pytest
from central_platform.db import PlatformDatabase
from central_platform.courses.service import (
    CourseService,
    CourseAuthorizationError,
    CourseNotFoundError,
    CourseValidationError,
)
from central_platform.models.schema import (
    CourseStatus,
    CourseToolPolicy,
    CoursePolicy,
    CourseVisibility,
    Organization,
    User,
    UserRole,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_course_domain.db"
    db = PlatformDatabase(db_path=str(db_file))
    return db


@pytest.fixture
def org_fixture(temp_db):
    org_a = Organization(id="org_a", name="School Alpha", slug="school_alpha")
    org_b = Organization(id="org_b", name="School Beta", slug="school_beta")
    temp_db.create_organization(org_a)
    temp_db.create_organization(org_b)

    admin_a = User(id="usr_admin_a", email="admin@alpha.edu", full_name="Admin Alpha", role=UserRole.ORG_ADMIN, organization_id="org_a")
    teacher_a = User(id="usr_teacher_a", email="teacher@alpha.edu", full_name="Teacher Alpha", role=UserRole.TEACHER, organization_id="org_a")
    student_a = User(id="usr_student_a", email="student@alpha.edu", full_name="Student Alpha", role=UserRole.STUDENT, organization_id="org_a")

    admin_b = User(id="usr_admin_b", email="admin@beta.edu", full_name="Admin Beta", role=UserRole.ORG_ADMIN, organization_id="org_b")
    student_b = User(id="usr_student_b", email="student@beta.edu", full_name="Student Beta", role=UserRole.STUDENT, organization_id="org_b")

    super_admin = User(id="usr_super", email="super@platform.org", full_name="Platform Super Admin", role=UserRole.SUPER_ADMIN, organization_id=None)

    temp_db.create_user(admin_a)
    temp_db.create_user(teacher_a)
    temp_db.create_user(student_a)
    temp_db.create_user(admin_b)
    temp_db.create_user(student_b)
    temp_db.create_user(super_admin)

    return {
        "admin_a": admin_a,
        "teacher_a": teacher_a,
        "student_a": student_a,
        "admin_b": admin_b,
        "student_b": student_b,
        "super_admin": super_admin,
    }


def test_public_course_lifecycle_and_cross_org_selection(temp_db, org_fixture):
    """Journey A: Admin creates public course, publishes it, and another org discovers and selects it."""
    service = CourseService(db=temp_db)
    admin_a = org_fixture["admin_a"]
    admin_b = org_fixture["admin_b"]
    student_b = org_fixture["student_b"]

    # 1. Admin A creates a public course
    course = service.create_course(
        actor=admin_a,
        code="CRS-MATH-10",
        title="Class 10 Mathematics",
        description="Comprehensive Class 10 Math curriculum",
        visibility=CourseVisibility.PUBLIC,
    )
    assert course.visibility == CourseVisibility.PUBLIC

    # Initial version 1.0 is created in DRAFT
    versions = temp_db.get_course_versions_by_course(course.id)
    assert len(versions) == 1
    v1 = versions[0]
    assert v1.version_number == "1.0"
    assert v1.status == CourseStatus.DRAFT

    # 2. Teacher or Admin submits version 1.0 for review
    v1_reviewed = service.submit_version_for_review(actor=admin_a, version_id=v1.id)
    assert v1_reviewed.status == CourseStatus.READY_FOR_REVIEW

    # 3. Admin A approves and publishes version 1.0
    v1_published = service.approve_and_publish_version(actor=admin_a, version_id=v1.id)
    assert v1_published.status == CourseStatus.PUBLISHED
    assert v1_published.published_by == admin_a.id

    # 4. Public catalog lists this course
    public_catalog = service.list_public_courses()
    assert any(c.id == course.id for c in public_catalog)

    # 5. School B Admin selects this public course for School B
    offering_b = service.select_course_for_org(actor=admin_b, organization_id="org_b", course_id=course.id)
    assert offering_b.organization_id == "org_b"
    assert offering_b.course_id == course.id
    assert offering_b.pinned_version_id == v1.id

    # 6. Student B can view and access the course
    course_for_student_b = service.get_course(actor=student_b, course_id=course.id)
    assert course_for_student_b.id == course.id

    # 7. Active version for Org B resolves to version 1.0
    active_version_b = service.get_active_course_version(organization_id="org_b", course_id=course.id)
    assert active_version_b is not None
    assert active_version_b.id == v1.id


def test_private_course_tenant_isolation(temp_db, org_fixture):
    """Journey B: School A creates private course. School B access is strictly denied."""
    service = CourseService(db=temp_db)
    admin_a = org_fixture["admin_a"]
    student_a = org_fixture["student_a"]
    admin_b = org_fixture["admin_b"]
    student_b = org_fixture["student_b"]

    # 1. School A creates a private course
    course = service.create_course(
        actor=admin_a,
        code="CRS-ADV-JEE",
        title="ABC Advanced JEE Math",
        visibility=CourseVisibility.PRIVATE,
    )
    assert course.visibility == CourseVisibility.PRIVATE

    # School A student can access it
    c_a = service.get_course(actor=student_a, course_id=course.id)
    assert c_a.id == course.id

    # 2. Private course does NOT appear in public catalog
    public_catalog = service.list_public_courses()
    assert not any(c.id == course.id for c in public_catalog)

    # 3. School B student attempts to query it -> Access Denied
    with pytest.raises(CourseAuthorizationError) as exc_info:
        service.get_course(actor=student_b, course_id=course.id)
    assert "Access Denied" in str(exc_info.value)

    # 4. School B admin attempts to select it -> Access Denied
    with pytest.raises(CourseAuthorizationError) as exc_info:
        service.select_course_for_org(actor=admin_b, organization_id="org_b", course_id=course.id)
    assert "restricted to organization" in str(exc_info.value)


def test_course_versioning_and_admin_approval_gate(temp_db, org_fixture):
    """Journey F: Course versioning, draft protection, and admin approval enforcement."""
    service = CourseService(db=temp_db)
    admin_a = org_fixture["admin_a"]
    teacher_a = org_fixture["teacher_a"]

    # Create course with version 1.0 published
    course = service.create_course(actor=admin_a, code="CRS-PHYS-11", title="Grade 11 Physics")
    v1_id = f"cv_{course.id}_v1_0"
    service.submit_version_for_review(actor=admin_a, version_id=v1_id)
    service.approve_and_publish_version(actor=admin_a, version_id=v1_id)

    # Teacher creates version 2.0 with custom policies
    tool_policy_v2 = CourseToolPolicy(calculator=True, graphing=True, code_execution=False)
    v2 = service.create_course_version(
        actor=teacher_a,
        course_id=course.id,
        version_number="2.0",
        tool_policy=tool_policy_v2,
    )
    assert v2.status == CourseStatus.DRAFT

    # Teacher submits version 2.0 for review
    v2_submitted = service.submit_version_for_review(actor=teacher_a, version_id=v2.id)
    assert v2_submitted.status == CourseStatus.READY_FOR_REVIEW

    # Non-admin (teacher) tries to publish -> REJECTED
    with pytest.raises(CourseAuthorizationError):
        service.approve_and_publish_version(actor=teacher_a, version_id=v2.id)

    # Admin approves and publishes
    v2_published = service.approve_and_publish_version(actor=admin_a, version_id=v2.id)
    assert v2_published.status == CourseStatus.PUBLISHED

    # Tool policy validated server-side on version 2.0
    assert service.validate_tool_access(course_version_id=v2.id, tool_name="calculator") is True
    assert service.validate_tool_access(course_version_id=v2.id, tool_name="graphing") is True
    assert service.validate_tool_access(course_version_id=v2.id, tool_name="code_execution") is False
    assert service.validate_tool_access(course_version_id=v2.id, tool_name="unregistered_tool") is False


def test_cross_tenant_tampering_rejected(temp_db, org_fixture):
    """Negative tests: Users cannot alter courses belonging to other organizations."""
    service = CourseService(db=temp_db)
    admin_a = org_fixture["admin_a"]
    teacher_b = org_fixture["admin_b"]

    course_a = service.create_course(actor=admin_a, code="CRS-BIO-12", title="Grade 12 Biology")

    # Teacher from Org B attempts to add a version to Org A course
    with pytest.raises(CourseAuthorizationError):
        service.create_course_version(actor=teacher_b, course_id=course_a.id, version_number="1.1")

    # Admin from Org B attempts to approve Org A course
    v1_id = f"cv_{course_a.id}_v1_0"
    with pytest.raises(CourseAuthorizationError):
        service.approve_and_publish_version(actor=teacher_b, version_id=v1_id)
