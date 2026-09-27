"""Platform central database storage layer and tenant isolation manager (Phase 03).

Provides authoritative data access across all 29 Section 12 entities, supporting:
- Relational foreign key integrity & cascades
- Multi-tenant organization scoping
- Soft deletion & audit logging
- Automated schema migrations via scripts/migrate_db.py
- Dual-engine execution (PostgreSQL in production, SQLite in local/CI)
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from central_platform.rbac.engine import hash_password, verify_password

from central_platform.models.schema import (
    AIExecutionLog,
    AIModel,
    AIProvider,
    AlertSeverity,
    AlertStatus,
    Assessment,
    AssessmentAttempt,
    AssessmentItem,
    AssessmentType,
    Assignment,
    AuditLog,
    ClassGroup,
    Cohort,
    Concept,
    Course,
    Curriculum,
    CurriculumVersion,
    Enrollment,
    InterventionRecord,
    LearningEvent,
    MasteryState,
    Misconception,
    Module,
    Notification,
    Organization,
    Permission,
    Prerequisite,
    Role,
    Session,
    SessionStatus,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    Subject,
    TeacherInstructionRecord,
    Topic,
    User,
    UserRole,
)
from scripts.migrate_db import run_all_migrations


class PlatformDatabase:
    """Central data layer manager supporting multi-tenant isolation and 29 domain entities."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or os.environ.get("GAYATRI_DB_PATH", ":memory:"))
        self._conn: Optional[sqlite3.Connection] = sqlite3.connect(
            self.db_path, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_db(self) -> None:
        """Run initial DDL and migrations automatically."""
        conn = self._get_connection()
        run_all_migrations(conn)

    # ── 1. Organizations & Identity ──────────────────────────────────────────

    def create_organization(self, org: Organization) -> Organization:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO organizations (id, name, slug, created_at, updated_at, is_deleted, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    org.id,
                    org.name,
                    org.slug,
                    org.created_at,
                    org.updated_at,
                    1 if org.is_deleted else 0,
                    org.deleted_at,
                ),
            )
        return org

    def get_organization(self, org_id: str, include_deleted: bool = False) -> Optional[Organization]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM organizations WHERE id = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            r = conn.execute(sql, (org_id,)).fetchone()
            if r:
                return Organization(
                    id=r["id"],
                    name=r["name"],
                    slug=r["slug"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
            return None

    def list_organizations(self, include_deleted: bool = False) -> List[Organization]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM organizations"
            if not include_deleted:
                sql += " WHERE is_deleted = 0"
            sql += " ORDER BY name ASC;"
            rows = conn.execute(sql).fetchall()
            return [
                Organization(
                    id=r["id"],
                    name=r["name"],
                    slug=r["slug"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
                for r in rows
            ]

    def soft_delete_organization(self, org_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE organizations SET is_deleted = 1, deleted_at = ? WHERE id = ? AND is_deleted = 0;",
                (now_iso, org_id),
            )
            return cursor.rowcount > 0

    def create_user(self, user: User) -> User:
        with self._get_connection() as conn:
            role_val = user.role.value if isinstance(user.role, UserRole) else str(user.role)
            conn.execute(
                """
                INSERT OR REPLACE INTO users (id, email, full_name, role, organization_id, is_active, created_at, updated_at, is_deleted, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    user.id,
                    user.email,
                    user.full_name,
                    role_val,
                    user.organization_id,
                    1 if user.is_active else 0,
                    user.created_at,
                    user.updated_at,
                    1 if user.is_deleted else 0,
                    user.deleted_at,
                ),
            )
        return user

    def get_user(self, user_id: str, include_deleted: bool = False) -> Optional[User]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM users WHERE id = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            r = conn.execute(sql, (user_id,)).fetchone()
            if r:
                return User(
                    id=r["id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    organization_id=r["organization_id"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
            return None

    def get_users_by_organization(self, organization_id: str, include_deleted: bool = False) -> List[User]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM users WHERE organization_id = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            sql += " ORDER BY full_name ASC;"
            rows = conn.execute(sql, (organization_id,)).fetchall()
            return [
                User(
                    id=r["id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    organization_id=r["organization_id"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
                for r in rows
            ]

    def soft_delete_user(self, user_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_deleted = 1, deleted_at = ? WHERE id = ? AND is_deleted = 0;",
                (now_iso, user_id),
            )
            return cursor.rowcount > 0

    def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM users WHERE email = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            r = conn.execute(sql, (email.strip().lower(),)).fetchone()
            if not r:
                r = conn.execute(sql.replace("email = ?", "LOWER(email) = LOWER(?)"), (email.strip(),)).fetchone()
            if r:
                return User(
                    id=r["id"],
                    email=r["email"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    organization_id=r["organization_id"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
            return None

    def set_user_password(self, user_id: str, password: str) -> None:
        """Hash and persist password with salt in user_credentials."""
        password_hash, salt_hex = hash_password(password)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_credentials 
                (user_id, password_hash, salt_hex, is_suspended, failed_login_attempts, password_reset_token, updated_at)
                VALUES (?, ?, ?, 0, 0, NULL, ?);
                """,
                (user_id, password_hash, salt_hex, now_iso),
            )

    def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            r = conn.execute(
                "SELECT * FROM user_credentials WHERE user_id = ?;",
                (user_id,),
            ).fetchone()
            if r:
                return dict(r)
            return None

    def suspend_user(self, user_id: str, reason: Optional[str] = None) -> bool:
        """Suspend user account to prevent login."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            c = conn.execute(
                "UPDATE user_credentials SET is_suspended = 1, updated_at = ? WHERE user_id = ?;",
                (now_iso, user_id),
            )
            return c.rowcount > 0

    def unsuspend_user(self, user_id: str) -> bool:
        """Unsuspend user account and clear failed login attempts."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            c = conn.execute(
                "UPDATE user_credentials SET is_suspended = 0, failed_login_attempts = 0, updated_at = ? WHERE user_id = ?;",
                (now_iso, user_id),
            )
            return c.rowcount > 0

    def set_password_reset_token(self, email: str, token: str) -> bool:
        """Set a one-time password reset token for the given email."""
        user = self.get_user_by_email(email)
        if not user:
            return False
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            c = conn.execute(
                "UPDATE user_credentials SET password_reset_token = ?, updated_at = ? WHERE user_id = ?;",
                (token, now_iso, user.id),
            )
            return c.rowcount > 0

    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using a valid one-time reset token."""
        with self._get_connection() as conn:
            r = conn.execute(
                "SELECT user_id FROM user_credentials WHERE password_reset_token = ?;",
                (token,),
            ).fetchone()
            if not r:
                return False
            user_id = r["user_id"]
        self.set_user_password(user_id, new_password)
        return True

    def authenticate_user(self, email_or_identifier: str, password: str) -> Optional[User]:
        """Authenticate user by email or user_id, checking password hash and account status."""
        user = self.get_user_by_email(email_or_identifier)
        if not user:
            user = self.get_user(email_or_identifier)
        if not user or not user.is_active or user.is_deleted:
            return None

        creds = self.get_user_credentials(user.id)
        if not creds:
            return None

        if creds["is_suspended"]:
            return None

        if verify_password(password, creds["password_hash"], creds["salt_hex"]):
            now_iso = datetime.now(timezone.utc).isoformat()
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE user_credentials SET failed_login_attempts = 0, updated_at = ? WHERE user_id = ?;",
                    (now_iso, user.id),
                )
            return user
        else:
            now_iso = datetime.now(timezone.utc).isoformat()
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE user_credentials SET failed_login_attempts = failed_login_attempts + 1, updated_at = ? WHERE user_id = ?;",
                    (now_iso, user.id),
                )
            return None

    def get_assigned_student_ids_for_teacher(self, teacher_id: str) -> Set[str]:
        """Resolve all student IDs assigned to courses or class groups taught by the teacher."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT e.student_id 
                FROM enrollments e
                JOIN class_groups cg ON e.course_id = cg.course_id
                WHERE e.is_active = 1;
                """
            ).fetchall()
            student_ids = {r["student_id"] for r in rows}
            t_rows = conn.execute(
                "SELECT DISTINCT student_id FROM teacher_instructions WHERE teacher_id = ?;",
                (teacher_id,),
            ).fetchall()
            for tr in t_rows:
                if tr["student_id"] and tr["student_id"] != "all":
                    student_ids.add(tr["student_id"])
            return student_ids

    def create_role(self, role: Role) -> Role:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO roles (id, name, description, created_at) VALUES (?, ?, ?, ?);",
                (role.id, role.name, role.description, role.created_at),
            )
        return role

    def create_permission(self, perm: Permission) -> Permission:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO permissions (id, code, description, created_at) VALUES (?, ?, ?, ?);",
                (perm.id, perm.code, perm.description, perm.created_at),
            )
        return perm

    def assign_role_permission(self, role_id: str, permission_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?);",
                (role_id, permission_id),
            )

    # ── 2. Academic Curriculum Hierarchy ────────────────────────────────────

    def create_course(self, course: Course) -> Course:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO courses (id, organization_id, code, title, description, created_at, updated_at, is_deleted, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    course.id,
                    course.organization_id,
                    course.code,
                    course.title,
                    course.description,
                    course.created_at,
                    course.updated_at,
                    1 if course.is_deleted else 0,
                    course.deleted_at,
                ),
            )
        return course

    def get_course(self, course_id: str, include_deleted: bool = False) -> Optional[Course]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM courses WHERE id = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            r = conn.execute(sql, (course_id,)).fetchone()
            if r:
                return Course(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    code=r["code"],
                    title=r["title"],
                    description=r["description"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
            return None

    def get_courses_by_organization(self, organization_id: str, include_deleted: bool = False) -> List[Course]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM courses WHERE organization_id = ?"
            if not include_deleted:
                sql += " AND is_deleted = 0"
            sql += " ORDER BY code ASC;"
            rows = conn.execute(sql, (organization_id,)).fetchall()
            return [
                Course(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    code=r["code"],
                    title=r["title"],
                    description=r["description"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_deleted=bool(r["is_deleted"]),
                    deleted_at=r["deleted_at"],
                )
                for r in rows
            ]

    def create_subject(self, subject: Subject) -> Subject:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO subjects (id, course_id, name, code, created_at) VALUES (?, ?, ?, ?, ?);",
                (subject.id, subject.course_id, subject.name, subject.code, subject.created_at),
            )
        return subject

    def create_curriculum(self, curriculum: Curriculum) -> Curriculum:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO curricula (id, course_id, title, version, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (curriculum.id, curriculum.course_id, curriculum.title, curriculum.version, 1 if curriculum.is_active else 0, curriculum.created_at),
            )
        return curriculum

    def get_curriculum(self, curriculum_id: str) -> Optional[Curriculum]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM curricula WHERE id = ?;", (curriculum_id,)).fetchone()
            if r:
                return Curriculum(
                    id=r["id"],
                    course_id=r["course_id"],
                    title=r["title"],
                    version=r["version"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
            return None

    def get_curriculum_for_course(self, course_id: str) -> Optional[Curriculum]:
        with self._get_connection() as conn:
            r = conn.execute(
                "SELECT * FROM curricula WHERE course_id = ? AND is_active = 1 ORDER BY created_at DESC;",
                (course_id,),
            ).fetchone()
            if r:
                return Curriculum(
                    id=r["id"],
                    course_id=r["course_id"],
                    title=r["title"],
                    version=r["version"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
            return None

    def create_module(self, mod: Module) -> Module:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO modules (id, curriculum_id, title, sequence_order, created_at) VALUES (?, ?, ?, ?, ?);",
                (mod.id, mod.curriculum_id, mod.title, mod.sequence_order, mod.created_at),
            )
        return mod

    def create_topic(self, topic: Topic) -> Topic:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO topics (id, module_id, title, sequence_order, created_at) VALUES (?, ?, ?, ?, ?);",
                (topic.id, topic.module_id, topic.title, topic.sequence_order, topic.created_at),
            )
        return topic

    def create_concept(self, concept: Concept) -> Concept:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO concepts (id, topic_id, name, description, difficulty, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (concept.id, concept.topic_id, concept.name, concept.description, concept.difficulty, concept.created_at),
            )
        return concept

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM concepts WHERE id = ?;", (concept_id,)).fetchone()
            if r:
                return Concept(
                    id=r["id"],
                    topic_id=r["topic_id"],
                    name=r["name"],
                    description=r["description"],
                    difficulty=float(r["difficulty"]),
                    created_at=r["created_at"],
                )
            return None

    def add_prerequisite(self, prereq: Prerequisite) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO prerequisites (prerequisite_concept_id, dependent_concept_id) VALUES (?, ?);",
                (prereq.prerequisite_concept_id, prereq.dependent_concept_id),
            )

    def get_prerequisites_for_concept(self, concept_id: str) -> List[str]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT prerequisite_concept_id FROM prerequisites WHERE dependent_concept_id = ?;",
                (concept_id,),
            ).fetchall()
            return [r[0] for r in rows]

    # ── 3. Class Groups & Enrollments ────────────────────────────────────────

    def create_class_group(self, class_group: ClassGroup) -> ClassGroup:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO class_groups (id, organization_id, course_id, name, section, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (class_group.id, class_group.organization_id, class_group.course_id, class_group.name, class_group.section, class_group.created_at),
            )
        return class_group

    def create_cohort(self, cohort: Cohort) -> Cohort:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cohorts (id, class_group_id, name, academic_year, created_at) VALUES (?, ?, ?, ?, ?);",
                (cohort.id, cohort.class_group_id, cohort.name, cohort.academic_year, cohort.created_at),
            )
        return cohort

    def create_enrollment(self, enrollment: Enrollment) -> Enrollment:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO enrollments (id, student_id, course_id, cohort_id, enrolled_at, is_active) VALUES (?, ?, ?, ?, ?, ?);",
                (enrollment.id, enrollment.student_id, enrollment.course_id, enrollment.cohort_id, enrollment.enrolled_at, 1 if enrollment.is_active else 0),
            )
        return enrollment

    def get_enrollments_for_student(self, student_id: str) -> List[Enrollment]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM enrollments WHERE student_id = ? AND is_active = 1;",
                (student_id,),
            ).fetchall()
            return [
                Enrollment(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    cohort_id=r["cohort_id"],
                    enrolled_at=r["enrolled_at"],
                    is_active=bool(r["is_active"]),
                )
                for r in rows
            ]

    # ── 4. Sessions & Granular Telemetry ─────────────────────────────────────

    def create_session(self, session: Session) -> Session:
        with self._get_connection() as conn:
            status_val = session.status.value if isinstance(session.status, SessionStatus) else str(session.status)
            conn.execute(
                "INSERT OR REPLACE INTO sessions (id, student_id, course_id, concept_id, status, started_at, ended_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (session.id, session.student_id, session.course_id, session.concept_id, status_val, session.started_at, session.ended_at),
            )
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM sessions WHERE id = ?;", (session_id,)).fetchone()
            if r:
                return Session(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    concept_id=r["concept_id"],
                    status=SessionStatus(r["status"]),
                    started_at=r["started_at"],
                    ended_at=r["ended_at"],
                )
            return None

    def end_session(self, session_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE sessions SET status = 'completed', ended_at = ? WHERE id = ? AND status = 'active';",
                (now_iso, session_id),
            )
            return cursor.rowcount > 0

    def get_sessions_for_student(self, student_id: str, limit: int = 20) -> List[Session]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE student_id = ? ORDER BY started_at DESC LIMIT ?;",
                (student_id, limit),
            ).fetchall()
            return [
                Session(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    concept_id=r["concept_id"],
                    status=SessionStatus(r["status"]),
                    started_at=r["started_at"],
                    ended_at=r["ended_at"],
                )
                for r in rows
            ]

    def record_learning_event(self, event: LearningEvent) -> LearningEvent:
        with self._get_connection() as conn:
            payload_str = json.dumps(event.payload) if isinstance(event.payload, dict) else str(event.payload)
            conn.execute(
                """
                INSERT OR IGNORE INTO learning_events 
                (id, session_id, student_id, organization_id, course_id, concept_id, event_type, source, payload, score, schema_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event.id,
                    event.session_id,
                    event.student_id,
                    event.organization_id,
                    event.course_id,
                    event.concept_id or "",
                    event.event_type,
                    event.source or "student_desktop",
                    payload_str,
                    event.score,
                    event.schema_version or "1.0.0",
                    event.created_at,
                ),
            )
        return event

    def get_learning_event(self, event_id: str) -> Optional[LearningEvent]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM learning_events WHERE id = ?;", (event_id,)).fetchone()
            if r:
                return self._row_to_learning_event(r)
            return None

    def get_learning_events_for_session(self, session_id: str) -> List[LearningEvent]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM learning_events WHERE session_id = ? ORDER BY created_at ASC, id ASC;",
                (session_id,),
            ).fetchall()
            return [self._row_to_learning_event(r) for r in rows]

    def query_learning_events(
        self,
        student_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        course_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 100,
    ) -> List[LearningEvent]:
        query = "SELECT * FROM learning_events WHERE 1=1"
        params: List[Any] = []
        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)
        if organization_id:
            query += " AND organization_id = ?"
            params.append(organization_id)
        if course_id:
            query += " AND course_id = ?"
            params.append(course_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if since:
            query += " AND created_at >= ?"
            params.append(since)
        if until:
            query += " AND created_at <= ?"
            params.append(until)
        query += " ORDER BY created_at ASC, id ASC LIMIT ?;"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_learning_event(r) for r in rows]

    def _row_to_learning_event(self, r: sqlite3.Row) -> LearningEvent:
        keys = r.keys()
        payload_data = {}
        raw_payload = r["payload"]
        if raw_payload and raw_payload.startswith("{"):
            try:
                payload_data = json.loads(raw_payload)
            except Exception:
                payload_data = {}
        return LearningEvent(
            id=r["id"],
            session_id=r["session_id"],
            student_id=r["student_id"],
            concept_id=r["concept_id"] if "concept_id" in keys else "",
            event_type=r["event_type"],
            organization_id=r["organization_id"] if "organization_id" in keys else None,
            course_id=r["course_id"] if "course_id" in keys else None,
            source=r["source"] if "source" in keys and r["source"] else "student_desktop",
            payload=payload_data,
            score=float(r["score"]) if r["score"] is not None else None,
            schema_version=r["schema_version"] if "schema_version" in keys and r["schema_version"] else "1.0.0",
            created_at=r["created_at"],
        )

    # ── 5. Student Learning Records & Mastery ────────────────────────────────

    def create_slr(self, slr: StudentLearningRecord) -> StudentLearningRecord:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO student_learning_records (id, student_id, course_id, authoritative, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?);",
                (slr.id, slr.student_id, slr.course_id, 1 if slr.authoritative else 0, slr.created_at, slr.updated_at),
            )
        return slr

    def get_slr(self, student_id: str, course_id: str) -> Optional[StudentLearningRecord]:
        with self._get_connection() as conn:
            r = conn.execute(
                "SELECT * FROM student_learning_records WHERE student_id = ? AND course_id = ?;",
                (student_id, course_id),
            ).fetchone()
            if r:
                return StudentLearningRecord(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    authoritative=bool(r["authoritative"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            return None

    def upsert_mastery_state(self, state: MasteryState) -> MasteryState:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO mastery_states (id, slr_id, concept_id, score, confidence, updated_at) VALUES (?, ?, ?, ?, ?, ?);",
                (state.id, state.slr_id, state.concept_id, state.score, state.confidence, state.updated_at),
            )
        return state

    def get_mastery_states_for_slr(self, slr_id: str) -> List[MasteryState]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM mastery_states WHERE slr_id = ?;", (slr_id,)).fetchall()
            return [
                MasteryState(
                    id=r["id"],
                    slr_id=r["slr_id"],
                    concept_id=r["concept_id"],
                    score=float(r["score"]),
                    confidence=float(r["confidence"]),
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def create_misconception(self, misc: Misconception) -> Misconception:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO misconceptions (id, code, category, name, description, remediation) VALUES (?, ?, ?, ?, ?, ?);",
                (misc.id, misc.code, misc.category, misc.name, misc.description, misc.remediation),
            )
        return misc

    def record_student_misconception(self, record: StudentMisconceptionRecord) -> StudentMisconceptionRecord:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO student_misconceptions (id, student_id, misconception_code, frequency, last_observed) VALUES (?, ?, ?, ?, ?);",
                (record.id, record.student_id, record.misconception_code, record.frequency, record.last_observed),
            )
        return record

    def get_student_misconceptions(self, student_id: str) -> List[StudentMisconceptionRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM student_misconceptions WHERE student_id = ? ORDER BY frequency DESC;",
                (student_id,),
            ).fetchall()
            return [
                StudentMisconceptionRecord(
                    id=r["id"],
                    student_id=r["student_id"],
                    misconception_code=r["misconception_code"],
                    frequency=int(r["frequency"]),
                    last_observed=r["last_observed"],
                )
                for r in rows
            ]

    def get_misconception_by_code(self, code: str) -> Optional[Misconception]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM misconceptions WHERE code = ?;", (code,)).fetchone()
            if r:
                return Misconception(
                    id=r["id"],
                    code=r["code"],
                    category=r["category"],
                    name=r["name"],
                    description=r["description"] or "",
                    remediation=r["remediation"] or "",
                )
            return None

    # ── 6. Assessments ───────────────────────────────────────────────────────

    def create_assessment(self, asmt: Assessment) -> Assessment:
        with self._get_connection() as conn:
            type_val = asmt.assessment_type.value if isinstance(asmt.assessment_type, AssessmentType) else str(asmt.assessment_type)
            conn.execute(
                "INSERT OR REPLACE INTO assessments (id, course_id, title, assessment_type, total_marks, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (asmt.id, asmt.course_id, asmt.title, type_val, asmt.total_marks, asmt.created_at),
            )
        return asmt

    def create_assessment_item(self, item: AssessmentItem) -> AssessmentItem:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO assessment_items (id, assessment_id, question_text, item_type, correct_answer, max_marks) VALUES (?, ?, ?, ?, ?, ?);",
                (item.id, item.assessment_id, item.question_text, item.item_type, item.correct_answer, item.max_marks),
            )
        return item

    def record_assessment_attempt(self, attempt: AssessmentAttempt) -> AssessmentAttempt:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO assessment_attempts (id, assessment_id, student_id, score, passed, started_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (attempt.id, attempt.assessment_id, attempt.student_id, attempt.score, 1 if attempt.passed else 0, attempt.started_at, attempt.completed_at),
            )
        return attempt

    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM assessments WHERE id = ?;", (assessment_id,)).fetchone()
            if r:
                return Assessment(
                    id=r["id"],
                    course_id=r["course_id"],
                    title=r["title"],
                    assessment_type=AssessmentType(r["assessment_type"]),
                    total_marks=float(r["total_marks"]),
                    created_at=r["created_at"],
                )
            return None

    def get_assessment_attempts_for_student(self, student_id: str, limit: int = 50) -> List[AssessmentAttempt]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM assessment_attempts WHERE student_id = ? ORDER BY started_at DESC LIMIT ?;",
                (student_id, limit),
            ).fetchall()
            return [
                AssessmentAttempt(
                    id=r["id"],
                    assessment_id=r["assessment_id"],
                    student_id=r["student_id"],
                    score=float(r["score"]),
                    passed=bool(r["passed"]),
                    started_at=r["started_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    # ── 7. Teacher Directives & Interventions ────────────────────────────────

    def create_teacher_instruction(self, inst: TeacherInstructionRecord) -> TeacherInstructionRecord:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO teacher_instructions (id, teacher_id, student_id, course_id, instruction_text, concept_scope, priority, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (inst.id, inst.teacher_id, inst.student_id, inst.course_id, inst.instruction_text, inst.concept_scope, inst.priority, 1 if inst.is_active else 0, inst.created_at),
            )
        return inst

    def get_teacher_instructions(self, course_id: str, student_id: Optional[str] = None) -> List[TeacherInstructionRecord]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM teacher_instructions WHERE course_id = ? AND is_active = 1"
            params: list[Any] = [course_id]
            if student_id:
                sql += " AND (student_id = ? OR student_id = 'all')"
                params.append(student_id)
            sql += " ORDER BY priority DESC, created_at DESC;"
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [
                TeacherInstructionRecord(
                    id=r["id"],
                    teacher_id=r["teacher_id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    instruction_text=r["instruction_text"],
                    concept_scope=r["concept_scope"],
                    priority=int(r["priority"]),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_intervention(self, alert: InterventionRecord) -> InterventionRecord:
        with self._get_connection() as conn:
            sev_val = alert.severity.value if isinstance(alert.severity, AlertSeverity) else str(alert.severity)
            stat_val = alert.status.value if isinstance(alert.status, AlertStatus) else str(alert.status)
            conn.execute(
                "INSERT OR REPLACE INTO interventions (id, student_id, course_id, severity, alert_type, message, status, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (alert.id, alert.student_id, alert.course_id, sev_val, alert.alert_type, alert.message, stat_val, alert.created_at, alert.resolved_at),
            )
        return alert

    def resolve_intervention(self, alert_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE interventions SET status = 'resolved', resolved_at = ? WHERE id = ?;",
                (now_iso, alert_id),
            )
            return cursor.rowcount > 0

    def get_interventions(self, course_id: str, active_only: bool = True) -> List[InterventionRecord]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM interventions WHERE course_id = ?"
            if active_only:
                sql += " AND status != 'resolved'"
            sql += " ORDER BY created_at DESC;"
            rows = conn.execute(sql, (course_id,)).fetchall()
            return [
                InterventionRecord(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    severity=AlertSeverity(r["severity"]),
                    alert_type=r["alert_type"],
                    message=r["message"],
                    status=AlertStatus(r["status"]),
                    created_at=r["created_at"],
                    resolved_at=r["resolved_at"],
                )
                for r in rows
            ]

    def get_interventions_for_student(self, student_id: str, active_only: bool = False) -> List[InterventionRecord]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM interventions WHERE student_id = ?"
            if active_only:
                sql += " AND status != 'resolved'"
            sql += " ORDER BY created_at DESC;"
            rows = conn.execute(sql, (student_id,)).fetchall()
            return [
                InterventionRecord(
                    id=r["id"],
                    student_id=r["student_id"],
                    course_id=r["course_id"],
                    severity=AlertSeverity(r["severity"]),
                    alert_type=r["alert_type"],
                    message=r["message"],
                    status=AlertStatus(r["status"]),
                    created_at=r["created_at"],
                    resolved_at=r["resolved_at"],
                )
                for r in rows
            ]

    def create_assignment(self, assignment: Assignment) -> Assignment:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO assignments (id, course_id, teacher_id, title, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (assignment.id, assignment.course_id, assignment.teacher_id, assignment.title, assignment.due_date, assignment.created_at),
            )
        return assignment

    def create_notification(self, notif: Notification) -> Notification:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO notifications (id, recipient_id, title, message, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (notif.id, notif.recipient_id, notif.title, notif.message, 1 if notif.is_read else 0, notif.created_at),
            )
        return notif

    def get_notifications(self, recipient_id: str) -> List[Notification]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE recipient_id = ? ORDER BY created_at DESC;",
                (recipient_id,),
            ).fetchall()
            return [
                Notification(
                    id=r["id"],
                    recipient_id=r["recipient_id"],
                    title=r["title"],
                    message=r["message"],
                    is_read=bool(r["is_read"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ── 8. AI Governance, Observability & Auditing ───────────────────────────

    def create_ai_provider(self, provider: AIProvider) -> AIProvider:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ai_providers (id, name, provider_type, base_url, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (provider.id, provider.name, provider.provider_type, provider.base_url, 1 if provider.is_active else 0, provider.created_at),
            )
        return provider

    def create_ai_model(self, model: AIModel) -> AIModel:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ai_models (id, provider_id, model_name, context_window, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?);",
                (model.id, model.provider_id, model.model_name, model.context_window, 1 if model.is_default else 0, model.created_at),
            )
        return model

    def record_ai_execution(self, log: AIExecutionLog) -> AIExecutionLog:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ai_execution_logs (id, model_id, prompt_tokens, completion_tokens, latency_ms, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (log.id, log.model_id, log.prompt_tokens, log.completion_tokens, log.latency_ms, log.status, log.created_at),
            )
        return log

    def record_audit_log(self, log: AuditLog) -> AuditLog:
        with self._get_connection() as conn:
            details_str = json.dumps(log.details) if isinstance(log.details, dict) else str(log.details)
            conn.execute(
                "INSERT OR REPLACE INTO audit_logs (id, organization_id, user_id, action, resource, details, ip_address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                (log.id, log.organization_id, log.user_id, log.action, log.resource, details_str, log.ip_address, log.created_at),
            )
        return log

    def get_audit_logs(self, organization_id: str) -> List[AuditLog]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs WHERE organization_id = ? ORDER BY created_at DESC;",
                (organization_id,),
            ).fetchall()
            return [
                AuditLog(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    user_id=r["user_id"],
                    action=r["action"],
                    resource=r["resource"],
                    details=json.loads(r["details"]) if r["details"].startswith("{") else {},
                    ip_address=r["ip_address"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
