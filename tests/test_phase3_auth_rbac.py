"""Unit and matrix test suite for Authentication and RBAC (Phase 3)."""

import pytest
from central_platform.models.schema import UserRole
from central_platform.rbac.engine import (
    Permission,
    has_permission,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    password = "SuperSecretPassword123!"
    p_hash, salt_hex = hash_password(password)

    assert verify_password(password, p_hash, salt_hex) is True
    assert verify_password("WrongPassword", p_hash, salt_hex) is False


def test_rbac_permission_matrix():
    # Super Admin has all permissions
    assert has_permission(UserRole.SUPER_ADMIN, Permission.GLOBAL_SYSTEM_CONTROL)
    assert has_permission(UserRole.SUPER_ADMIN, Permission.WRITE_AI_INSTRUCTION)

    # Teacher has teacher permissions but not admin/global control
    assert has_permission(UserRole.TEACHER, Permission.VIEW_STUDENT_PROGRESS)
    assert has_permission(UserRole.TEACHER, Permission.WRITE_AI_INSTRUCTION)
    assert not has_permission(UserRole.TEACHER, Permission.MANAGE_ORGANIZATION)
    assert not has_permission(UserRole.TEACHER, Permission.GLOBAL_SYSTEM_CONTROL)

    # Student has learn permission but not teacher/admin permissions
    assert has_permission(UserRole.STUDENT, Permission.STUDENT_LEARN)
    assert not has_permission(UserRole.STUDENT, Permission.VIEW_STUDENT_PROGRESS)
    assert not has_permission(UserRole.STUDENT, Permission.WRITE_AI_INSTRUCTION)
