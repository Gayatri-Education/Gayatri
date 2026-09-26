"""RBAC permission matrix and server-side policy enforcement engine."""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Set

from central_platform.models.schema import UserRole


class Permission(str):
    VIEW_STUDENT_PROGRESS = "teacher.view_student_progress"
    CREATE_ASSIGNMENT = "teacher.create_assignment"
    WRITE_AI_INSTRUCTION = "teacher.write_ai_instruction"
    VIEW_STUDENT_SESSIONS = "teacher.view_student_sessions"
    MANAGE_ORGANIZATION = "org_admin.manage_organization"
    MANAGE_COURSES = "course_admin.manage_courses"
    GLOBAL_SYSTEM_CONTROL = "super_admin.global_system_control"
    STUDENT_LEARN = "student.learn"


ROLE_PERMISSIONS: dict[UserRole, Set[str]] = {
    UserRole.SUPER_ADMIN: {
        Permission.GLOBAL_SYSTEM_CONTROL,
        Permission.MANAGE_ORGANIZATION,
        Permission.MANAGE_COURSES,
        Permission.VIEW_STUDENT_PROGRESS,
        Permission.CREATE_ASSIGNMENT,
        Permission.WRITE_AI_INSTRUCTION,
        Permission.VIEW_STUDENT_SESSIONS,
        Permission.STUDENT_LEARN,
    },
    UserRole.ORG_ADMIN: {
        Permission.MANAGE_ORGANIZATION,
        Permission.MANAGE_COURSES,
        Permission.VIEW_STUDENT_PROGRESS,
        Permission.CREATE_ASSIGNMENT,
    },
    UserRole.COURSE_ADMIN: {
        Permission.MANAGE_COURSES,
        Permission.VIEW_STUDENT_PROGRESS,
        Permission.CREATE_ASSIGNMENT,
    },
    UserRole.TEACHER: {
        Permission.VIEW_STUDENT_PROGRESS,
        Permission.CREATE_ASSIGNMENT,
        Permission.WRITE_AI_INSTRUCTION,
        Permission.VIEW_STUDENT_SESSIONS,
    },
    UserRole.STUDENT: {
        Permission.STUDENT_LEARN,
    },
}


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Hash password using PBKDF2 with SHA-256."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex(), salt.hex()


def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    """Verify password against stored hash."""
    salt = bytes.fromhex(salt_hex)
    key, _ = hash_password(password, salt)
    return secrets.compare_digest(key, password_hash)


def has_permission(role: UserRole, permission: str) -> bool:
    """Check if role has given permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
