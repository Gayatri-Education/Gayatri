"""Multi-level admin portal service module providing Super Admin, Org Admin, and Course Admin capabilities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Course, Enrollment, Organization, User, UserRole


@dataclass
class AdminAuditEvent:
    id: str
    actor_id: str
    actor_role: UserRole
    action: str
    target_entity: str
    target_id: str
    organization_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AdminService:
    """Multi-tiered administrative portal service enforcing RBAC boundaries and tracking audit logs."""

    def __init__(self, db: PlatformDatabase):
        self.db = db
        self._audit_log: List[AdminAuditEvent] = []
        self._global_config: Dict[str, Any] = {
            "system_mode": "operational",
            "max_tenants": 100,
            "maintenance_window": False,
            "ai_policy_level": "strict",
        }
        self._registered_models: List[Dict[str, Any]] = [
            {"id": "gguf-llama3-8b", "status": "active", "type": "local"},
            {"id": "slm-chemistry-v1", "status": "active", "type": "fine_tuned"},
        ]

    def _record_audit(
        self,
        actor: User,
        action: str,
        target_entity: str,
        target_id: str,
        org_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AdminAuditEvent:
        event = AdminAuditEvent(
            id=f"audit-{uuid.uuid4().hex[:8]}",
            actor_id=actor.id,
            actor_role=actor.role,
            action=action,
            target_entity=target_entity,
            target_id=target_id,
            organization_id=org_id or actor.organization_id,
            details=details or {},
        )
        self._audit_log.append(event)
        return event

    def get_audit_trail(self, organization_id: Optional[str] = None) -> List[AdminAuditEvent]:
        if organization_id:
            return [e for e in self._audit_log if e.organization_id == organization_id]
        return list(self._audit_log)

    # --- SUPER ADMIN CAPABILITIES ---

    def create_organization(self, super_admin: User, name: str, slug: str) -> Organization:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can create organizations.")
        org = Organization(id=f"org-{uuid.uuid4().hex[:8]}", name=name, slug=slug)
        self.db.create_organization(org)
        self._record_audit(super_admin, "CREATE_ORGANIZATION", "Organization", org.id, org.id, {"name": name, "slug": slug})
        return org

    def update_global_config(self, super_admin: User, updates: Dict[str, Any]) -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can modify global configuration.")
        self._global_config.update(updates)
        self._record_audit(super_admin, "UPDATE_GLOBAL_CONFIG", "GlobalConfig", "system", details=updates)
        return dict(self._global_config)

    def get_global_config(self, user: User) -> Dict[str, Any]:
        if user.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can read full global configuration.")
        return dict(self._global_config)

    def get_system_health(self, super_admin: User) -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can access system health telemetry.")
        return {
            "status": "HEALTHY",
            "active_models": len(self._registered_models),
            "system_mode": self._global_config.get("system_mode"),
            "audit_events_count": len(self._audit_log),
        }

    def register_ai_model(self, super_admin: User, model_id: str, model_type: str) -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can register AI models.")
        entry = {"id": model_id, "status": "active", "type": model_type}
        self._registered_models.append(entry)
        self._record_audit(super_admin, "REGISTER_AI_MODEL", "AIModel", model_id, details=entry)
        return entry

    # --- ORG ADMIN CAPABILITIES ---

    def create_org_user(
        self,
        admin: User,
        email: str,
        full_name: str,
        role: UserRole,
        target_org_id: Optional[str] = None,
    ) -> User:
        if admin.role == UserRole.SUPER_ADMIN:
            org_id = target_org_id
        elif admin.role == UserRole.ORG_ADMIN:
            if target_org_id and target_org_id != admin.organization_id:
                raise PermissionError("Org Admin cannot create users for other organizations.")
            org_id = admin.organization_id
            if role in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
                # Allow Org Admin to create Teachers, Students, Course Admins
                if role == UserRole.SUPER_ADMIN:
                    raise PermissionError("Org Admin cannot assign Super Admin role.")
        else:
            raise PermissionError("Unauthorized to create users.")

        user = User(
            id=f"usr-{uuid.uuid4().hex[:8]}",
            email=email,
            full_name=full_name,
            role=role,
            organization_id=org_id,
        )
        self.db.create_user(user)
        self._record_audit(admin, "CREATE_USER", "User", user.id, org_id, {"email": email, "role": role.value})
        return user

    def list_org_users(self, admin: User, organization_id: Optional[str] = None) -> List[User]:
        if admin.role == UserRole.SUPER_ADMIN:
            target_org = organization_id or admin.organization_id
            if not target_org:
                raise ValueError("Organization ID required for listing users.")
            return self.db.get_users_by_organization(target_org)
        elif admin.role == UserRole.ORG_ADMIN:
            return self.db.get_users_by_organization(admin.organization_id)
        else:
            raise PermissionError("Unauthorized to view organization user list.")

    def generate_organization_report(self, admin: User, organization_id: Optional[str] = None) -> Dict[str, Any]:
        target_org = admin.organization_id if admin.role == UserRole.ORG_ADMIN else organization_id
        if not target_org:
            raise ValueError("Organization ID must be specified.")
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
            raise PermissionError("Unauthorized to view organization report.")
        if admin.role == UserRole.ORG_ADMIN and target_org != admin.organization_id:
            raise PermissionError("Org Admin cannot view report for another organization.")

        users = self.db.get_users_by_organization(target_org)
        courses = self.db.get_courses_by_organization(target_org)
        return {
            "organization_id": target_org,
            "total_users": len(users),
            "total_courses": len(courses),
            "teachers_count": sum(1 for u in users if u.role == UserRole.TEACHER),
            "students_count": sum(1 for u in users if u.role == UserRole.STUDENT),
        }

    # --- COURSE ADMIN CAPABILITIES ---

    def create_course(self, admin: User, code: str, title: str, description: str = "", organization_id: Optional[str] = None) -> Course:
        if admin.role == UserRole.SUPER_ADMIN:
            target_org = organization_id
            if not target_org:
                raise ValueError("Organization ID required for course creation.")
        elif admin.role in (UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            target_org = admin.organization_id
        else:
            raise PermissionError("Unauthorized to create courses.")

        course = Course(
            id=f"crs-{uuid.uuid4().hex[:8]}",
            organization_id=target_org,
            code=code,
            title=title,
            description=description,
        )
        self.db.create_course(course)
        self._record_audit(admin, "CREATE_COURSE", "Course", course.id, target_org, {"code": code, "title": title})
        return course

    def enroll_student(self, admin: User, student_id: str, course_id: str) -> Enrollment:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to enroll students in courses.")

        enrollment = Enrollment(
            id=f"enr-{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            course_id=course_id,
        )
        self.db.create_enrollment(enrollment)
        self._record_audit(admin, "ENROLL_STUDENT", "Enrollment", enrollment.id, admin.organization_id, {"student_id": student_id, "course_id": course_id})
        return enrollment
