"""Unit and tenant isolation test suite for Central Platform Foundation (Phase 2)."""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, Organization, User, UserRole


@pytest.fixture
def platform_db(tmp_path):
    db_file = str(tmp_path / "platform_test.db")
    return PlatformDatabase(db_file)


def test_organization_and_user_creation(platform_db):
    org = Organization(id="org_1", name="Gayatri Academy", slug="gayatri-academy")
    platform_db.create_organization(org)

    user = User(
        id="user_1",
        email="teacher@gayatri.edu",
        full_name="Teacher One",
        role=UserRole.TEACHER,
        organization_id="org_1",
    )
    platform_db.create_user(user)

    users = platform_db.get_users_by_organization("org_1")
    assert len(users) == 1
    assert users[0].email == "teacher@gayatri.edu"
    assert users[0].role == UserRole.TEACHER


def test_tenant_isolation_boundary(platform_db):
    org_a = Organization(id="org_a", name="Org A", slug="org-a")
    org_b = Organization(id="org_b", name="Org B", slug="org-b")
    platform_db.create_organization(org_a)
    platform_db.create_organization(org_b)

    user_a = User(id="u_a", email="a@org.com", full_name="User A", role=UserRole.STUDENT, organization_id="org_a")
    user_b = User(id="u_b", email="b@org.com", full_name="User B", role=UserRole.STUDENT, organization_id="org_b")
    platform_db.create_user(user_a)
    platform_db.create_user(user_b)

    course_a = Course(id="c_a", organization_id="org_a", code="MATH101", title="Math 101")
    course_b = Course(id="c_b", organization_id="org_b", code="PHYS101", title="Physics 101")
    platform_db.create_course(course_a)
    platform_db.create_course(course_b)

    # Assert tenant isolation
    users_a = platform_db.get_users_by_organization("org_a")
    courses_a = platform_db.get_courses_by_organization("org_a")
    assert len(users_a) == 1
    assert users_a[0].id == "u_a"
    assert len(courses_a) == 1
    assert courses_a[0].id == "c_a"

    users_b = platform_db.get_users_by_organization("org_b")
    courses_b = platform_db.get_courses_by_organization("org_b")
    assert len(users_b) == 1
    assert users_b[0].id == "u_b"
    assert len(courses_b) == 1
    assert courses_b[0].id == "c_b"
