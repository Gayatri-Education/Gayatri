"""Platform central database storage layer and tenant isolation manager."""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from central_platform.models.schema import Course, Enrollment, Organization, User, UserRole


class PlatformDatabase:
    """Central data layer manager supporting multi-tenant isolation."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    organization_id TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(organization_id) REFERENCES organizations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS enrollments (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    enrolled_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
                    UNIQUE(student_id, course_id)
                );
            """)

    def create_organization(self, org: Organization) -> Organization:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO organizations (id, name, slug, created_at) VALUES (?, ?, ?, ?)",
                (org.id, org.name, org.slug, org.created_at),
            )
        return org

    def create_user(self, user: User) -> User:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, email, full_name, role, organization_id, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user.id, user.email, user.full_name, user.role.value, user.organization_id, 1 if user.is_active else 0, user.created_at),
            )
        return user

    def get_users_by_organization(self, organization_id: str) -> List[User]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, email, full_name, role, organization_id, is_active, created_at FROM users WHERE organization_id = ?",
                (organization_id,),
            ).fetchall()
            return [
                User(
                    id=r["id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    organization_id=r["organization_id"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_course(self, course: Course) -> Course:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO courses (id, organization_id, code, title, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (course.id, course.organization_id, course.code, course.title, course.description, course.created_at),
            )
        return course

    def get_courses_by_organization(self, organization_id: str) -> List[Course]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, organization_id, code, title, description, created_at FROM courses WHERE organization_id = ?",
                (organization_id,),
            ).fetchall()
            return [
                Course(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    code=r["code"],
                    title=r["title"],
                    description=r["description"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_enrollment(self, enrollment: Enrollment) -> Enrollment:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO enrollments (id, student_id, course_id, enrolled_at) VALUES (?, ?, ?, ?)",
                (enrollment.id, enrollment.student_id, enrollment.course_id, enrollment.enrolled_at),
            )
        return enrollment
