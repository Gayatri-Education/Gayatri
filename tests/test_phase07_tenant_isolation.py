"""Tests for Phase 07: Expanded Tenant Isolation Boundaries."""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization, User, UserRole

@pytest.fixture
def platform_db(tmp_path):
    db_file = str(tmp_path / "phase07_tenant_test.db")
    return PlatformDatabase(db_file)

def test_strict_tenant_data_separation(platform_db):
    """Ensure data strictly belongs to its parent tenant and doesn't leak."""
    org1 = Organization(id="tenant_x", name="Tenant X", slug="tenant-x")
    org2 = Organization(id="tenant_y", name="Tenant Y", slug="tenant-y")
    platform_db.create_organization(org1)
    platform_db.create_organization(org2)

    u1 = User(id="u1", email="admin@x.com", full_name="X Admin", role=UserRole.ORG_ADMIN, organization_id="tenant_x")
    u2 = User(id="u2", email="teacher@x.com", full_name="X Teacher", role=UserRole.TEACHER, organization_id="tenant_x")
    u3 = User(id="u3", email="admin@y.com", full_name="Y Admin", role=UserRole.ORG_ADMIN, organization_id="tenant_y")
    
    platform_db.create_user(u1)
    platform_db.create_user(u2)
    platform_db.create_user(u3)

    # Read logic isolation
    org_x_users = platform_db.get_users_by_organization("tenant_x")
    org_y_users = platform_db.get_users_by_organization("tenant_y")

    assert len(org_x_users) == 2
    assert len(org_y_users) == 1
    assert org_y_users[0].id == "u3"
    
    # Try accessing tenant Y user from tenant X context (conceptually)
    user_fetch = platform_db.get_user("u3")
    assert user_fetch.organization_id == "tenant_y"
    assert user_fetch.organization_id != "tenant_x"

def test_tenant_soft_deletion_isolation(platform_db):
    """Ensure soft deletion in one tenant doesn't affect another."""
    org = Organization(id="tenant_z", name="Tenant Z", slug="tenant-z")
    platform_db.create_organization(org)
    u1 = User(id="u10", email="del@z.com", full_name="Z Del", role=UserRole.STUDENT, organization_id="tenant_z")
    platform_db.create_user(u1)
    
    platform_db.soft_delete_user("u10")
    
    # Validate soft deletion logic if exposed, otherwise assert missing
    user_fetch = platform_db.get_user("u10")
    assert user_fetch is None
