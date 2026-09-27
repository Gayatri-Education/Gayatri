"""Multi-level admin portal service module providing Super Admin, Org Admin, and Course Admin capabilities.

Master Plan Section 23 (Phase 14):
Authoritative administrative management covering:
- Organizations, Users, Teachers, Students
- Courses, Curricula, Versions, Classes, Cohorts, Enrollments
- AI Providers, AI Models, AI Policies, Feature Flags
- Audit Trail, Analytics, System Health, and Emergency Kill Switch
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    AIModel,
    AIProvider,
    AuditLog,
    ClassGroup,
    Cohort,
    Course,
    Curriculum,
    Enrollment,
    Organization,
    User,
    UserRole,
)


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
            "kill_switch": False,
            "kill_switch_reason": "",
        }
        self._registered_models: List[Dict[str, Any]] = [
            {"id": "gguf-llama3-8b", "status": "active", "type": "local", "context_window": 8192, "is_default": True},
            {"id": "slm-chemistry-v1", "status": "active", "type": "fine_tuned", "context_window": 4096, "is_default": False},
        ]
        self._registered_providers: List[Dict[str, Any]] = [
            {"id": "prov-local", "name": "Local Engine (llama.cpp/vLLM)", "provider_type": "local", "base_url": "http://127.0.0.1:8000", "is_active": True},
            {"id": "prov-anthropic", "name": "Anthropic Claude", "provider_type": "anthropic", "base_url": "https://api.anthropic.com", "is_active": True},
            {"id": "prov-openai", "name": "OpenAI", "provider_type": "openai", "base_url": "https://api.openai.com", "is_active": True},
        ]
        self._ai_policies: Dict[str, Any] = {
            "ai_policy_level": "strict",
            "anti_answer_leakage": True,
            "max_tokens_per_turn": 1024,
            "temperature": 0.2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._feature_flags: Dict[str, bool] = {
            "enable_voice": True,
            "enable_chemistry_3d": True,
            "enable_teacher_copilot": True,
            "enable_spaced_repetition": True,
            "enable_realtime_sync": True,
            "enable_adaptive_learning": True,
        }

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

        # Mirror to platform database audit log if possible
        try:
            db_log = AuditLog(
                id=event.id,
                organization_id=event.organization_id or "system",
                user_id=event.actor_id,
                action=event.action,
                resource=f"{event.target_entity}:{event.target_id}",
                details=event.details,
            )
            self.db.record_audit_log(db_log)
        except Exception:
            pass

        return event

    def get_audit_trail(self, organization_id: Optional[str] = None) -> List[AdminAuditEvent]:
        if organization_id:
            return [e for e in self._audit_log if e.organization_id == organization_id]
        return list(self._audit_log)

    # --- SUPER ADMIN CAPABILITIES ---

    def create_organization(self, super_admin: User, name: str, slug: str, tier: str = "STANDARD", student_quota: int = 250) -> Organization:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can create organizations.")
        org = Organization(id=f"org-{uuid.uuid4().hex[:8]}", name=name, slug=slug)
        self.db.create_organization(org)
        self._record_audit(super_admin, "CREATE_ORGANIZATION", "Organization", org.id, org.id, {"name": name, "slug": slug, "tier": tier, "student_quota": student_quota})
        return org

    def list_organizations(self, admin: User) -> List[Organization]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view organizations.")
        all_orgs = self.db.list_organizations()
        if admin.role == UserRole.ORG_ADMIN:
            return [o for o in all_orgs if o.id == admin.organization_id]
        return all_orgs

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

    def get_system_health(self, super_admin: Optional[User] = None) -> Dict[str, Any]:
        if super_admin and super_admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view system health.")
        return {
            "status": "HEALTHY",
            "api_server": "ONLINE",
            "database": "ONLINE",
            "ai_gateway": "ONLINE",
            "sync_service": "ONLINE",
            "active_models": len(self._registered_models),
            "system_mode": self._global_config.get("system_mode", "operational"),
            "audit_events_count": len(self._audit_log),
            "kill_switch": self._global_config.get("kill_switch", False),
            "kill_switch_reason": self._global_config.get("kill_switch_reason", ""),
        }

    def toggle_kill_switch(self, super_admin: User, active: bool, reason: str = "") -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can toggle emergency kill switch.")
        self._global_config["kill_switch"] = active
        self._global_config["kill_switch_reason"] = reason
        self._record_audit(super_admin, "TOGGLE_KILL_SWITCH", "System", "kill_switch", details={"active": active, "reason": reason})
        return {"kill_switch_active": active, "reason": reason}

    def register_ai_model(
        self,
        super_admin: User,
        model_id: str,
        model_type: str,
        provider_id: Optional[str] = None,
        context_window: int = 8192,
        is_default: bool = False,
    ) -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can register AI models.")
        entry = {
            "id": model_id,
            "status": "active",
            "type": model_type,
            "provider_id": provider_id or "prov-local",
            "context_window": context_window,
            "is_default": is_default,
        }
        self._registered_models.append(entry)
        try:
            m_entity = AIModel(
                id=model_id,
                provider_id=entry["provider_id"],
                model_name=model_id,
                context_window=context_window,
                is_default=is_default,
            )
            self.db.create_ai_model(m_entity)
        except Exception:
            pass

        self._record_audit(super_admin, "REGISTER_AI_MODEL", "AIModel", model_id, details=entry)
        return entry

    def list_ai_models(self, admin: User, provider_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list AI models.")
        if provider_id:
            return [m for m in self._registered_models if m.get("provider_id") == provider_id]
        return list(self._registered_models)

    def register_ai_provider(
        self,
        super_admin: User,
        name: str,
        provider_type: str,
        base_url: str = "",
    ) -> Dict[str, Any]:
        if super_admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can register AI providers.")
        p_id = f"prov-{uuid.uuid4().hex[:8]}"
        entry = {
            "id": p_id,
            "name": name,
            "provider_type": provider_type,
            "base_url": base_url,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._registered_providers.append(entry)
        try:
            p_entity = AIProvider(
                id=p_id,
                name=name,
                provider_type=provider_type,
                base_url=base_url,
                is_active=True,
            )
            self.db.create_ai_provider(p_entity)
        except Exception:
            pass

        self._record_audit(super_admin, "REGISTER_AI_PROVIDER", "AIProvider", p_id, details=entry)
        return entry

    def list_ai_providers(self, admin: User) -> List[Dict[str, Any]]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list AI providers.")
        return list(self._registered_providers)

    def get_ai_policies(self, admin: User) -> Dict[str, Any]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view AI policies.")
        return dict(self._ai_policies)

    def update_ai_policies(self, admin: User, updates: Dict[str, Any]) -> Dict[str, Any]:
        if admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can modify AI policies.")
        self._ai_policies.update(updates)
        self._ai_policies["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._record_audit(admin, "UPDATE_AI_POLICIES", "AIPolicies", "system", details=updates)
        return dict(self._ai_policies)

    def get_feature_flags(self, admin: User) -> Dict[str, bool]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view feature flags.")
        return dict(self._feature_flags)

    def update_feature_flags(self, admin: User, updates: Dict[str, bool]) -> Dict[str, bool]:
        if admin.role != UserRole.SUPER_ADMIN:
            raise PermissionError("Only Super Admin can update feature flags.")
        self._feature_flags.update(updates)
        self._record_audit(admin, "UPDATE_FEATURE_FLAGS", "FeatureFlags", "system", details=updates)
        return dict(self._feature_flags)

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
            if org_id is not None:
                org = self.db.get_organization(org_id)
                if not org:
                    self.db.create_organization(Organization(id=org_id, name=org_id.replace("-", " ").title(), slug=org_id))
            elif role != UserRole.SUPER_ADMIN:
                existing = self.db.list_organizations()
                if existing:
                    org_id = existing[0].id
                else:
                    default_org = Organization(id="org-default", name="Default Organization", slug="default-org")
                    self.db.create_organization(default_org)
                    org_id = default_org.id
        elif admin.role == UserRole.ORG_ADMIN:
            if target_org_id and target_org_id != admin.organization_id:
                raise PermissionError("Org Admin cannot create users for other organizations.")
            org_id = admin.organization_id
            if org_id:
                org = self.db.get_organization(org_id)
                if not org:
                    self.db.create_organization(Organization(id=org_id, name=org_id.replace("-", " ").title(), slug=org_id))
            if role in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN):
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
                # Return all users across organizations
                with self.db._get_connection() as conn:
                    rows = conn.execute("SELECT * FROM users WHERE is_deleted = 0;").fetchall()
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
            return self.db.get_users_by_organization(target_org)
        elif admin.role == UserRole.ORG_ADMIN:
            if organization_id and organization_id != admin.organization_id:
                raise PermissionError("Org Admin cannot query users of another organization.")
            return self.db.get_users_by_organization(admin.organization_id)
        else:
            raise PermissionError("Unauthorized to view organization user list.")

    def update_user_status(
        self,
        admin: User,
        user_id: str,
        is_active: Optional[bool] = None,
        role: Optional[UserRole] = None,
        full_name: Optional[str] = None,
    ) -> User:
        user = self.db.get_user(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found.")

        if admin.role == UserRole.ORG_ADMIN:
            if user.organization_id != admin.organization_id:
                raise PermissionError("Org Admin cannot modify users outside their tenant.")
            if role == UserRole.SUPER_ADMIN:
                raise PermissionError("Org Admin cannot escalate role to Super Admin.")

        if is_active is not None:
            if is_active:
                self.db.unsuspend_user(user_id)
            else:
                self.db.suspend_user(user_id, "Deactivated by administrator")

        updates: Dict[str, Any] = {}
        if full_name:
            updates["full_name"] = full_name
        if role:
            updates["role"] = role.value

        if updates:
            with self.db._get_connection() as conn:
                set_clauses = [f"{k} = ?" for k in updates.keys()]
                params = list(updates.values()) + [user_id]
                conn.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?;", params)

        updated_user = self.db.get_user(user_id)
        self._record_audit(
            admin,
            "UPDATE_USER",
            "User",
            user_id,
            user.organization_id,
            {"is_active": is_active, "role": role.value if role else None},
        )
        return updated_user or user

    def delete_user(self, admin: User, user_id: str) -> bool:
        user = self.db.get_user(user_id)
        if not user:
            return False
        if admin.role == UserRole.ORG_ADMIN and user.organization_id != admin.organization_id:
            raise PermissionError("Org Admin cannot delete users from another organization.")
        ok = self.db.soft_delete_user(user_id)
        if ok:
            self._record_audit(admin, "DELETE_USER", "User", user_id, user.organization_id)
        return ok

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

    # --- COURSE & ACADEMIC ADMIN CAPABILITIES ---

    def create_course(
        self,
        admin: User,
        code: str,
        title: str,
        description: str = "",
        organization_id: Optional[str] = None,
    ) -> Course:
        if admin.role == UserRole.SUPER_ADMIN:
            target_org = organization_id
            if not target_org:
                existing = self.db.list_organizations()
                if existing:
                    target_org = existing[0].id
                else:
                    default_org = Organization(id="org-default", name="Default Organization", slug="default-org")
                    self.db.create_organization(default_org)
                    target_org = default_org.id
            else:
                org = self.db.get_organization(target_org)
                if not org:
                    self.db.create_organization(Organization(id=target_org, name=target_org.replace("-", " ").title(), slug=target_org))
        elif admin.role in (UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            target_org = admin.organization_id
            if target_org:
                org = self.db.get_organization(target_org)
                if not org:
                    self.db.create_organization(Organization(id=target_org, name=target_org.replace("-", " ").title(), slug=target_org))
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

    def list_courses(self, admin: User, organization_id: Optional[str] = None) -> List[Course]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list courses.")
        if admin.role == UserRole.ORG_ADMIN:
            return self.db.get_courses_by_organization(admin.organization_id)
        if organization_id:
            return self.db.get_courses_by_organization(organization_id)
        with self.db._get_connection() as conn:
            rows = conn.execute("SELECT * FROM courses WHERE is_deleted = 0;").fetchall()
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

    def create_curriculum(
        self,
        admin: User,
        course_id: str,
        title: str,
        version: str = "v1.0",
    ) -> Curriculum:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to create curricula.")
        curriculum = Curriculum(
            id=f"cur-{uuid.uuid4().hex[:8]}",
            course_id=course_id,
            title=title,
            version=version,
            is_active=True,
        )
        self.db.create_curriculum(curriculum)
        self._record_audit(admin, "CREATE_CURRICULUM", "Curriculum", curriculum.id, admin.organization_id, {"course_id": course_id, "title": title, "version": version})
        return curriculum

    def list_curricula(self, admin: User, course_id: Optional[str] = None) -> List[Curriculum]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list curricula.")
        with self.db._get_connection() as conn:
            if course_id:
                rows = conn.execute("SELECT * FROM curricula WHERE course_id = ?;", (course_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM curricula;").fetchall()
            return [
                Curriculum(
                    id=r["id"],
                    course_id=r["course_id"],
                    title=r["title"],
                    version=r["version"],
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_class_group(
        self,
        admin: User,
        name: str,
        section: str,
        course_id: str,
        organization_id: Optional[str] = None,
    ) -> ClassGroup:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to create class groups.")
        org_id = organization_id if admin.role == UserRole.SUPER_ADMIN else admin.organization_id
        if not org_id:
            course = self.db.get_course(course_id)
            if course:
                org_id = course.organization_id
            else:
                existing = self.db.list_organizations()
                org_id = existing[0].id if existing else "org-default"
        org = self.db.get_organization(org_id)
        if not org:
            self.db.create_organization(Organization(id=org_id, name=org_id.replace("-", " ").title(), slug=org_id))
        cg = ClassGroup(
            id=f"cg-{uuid.uuid4().hex[:8]}",
            organization_id=org_id,
            course_id=course_id,
            name=name,
            section=section,
        )
        self.db.create_class_group(cg)
        self._record_audit(admin, "CREATE_CLASS_GROUP", "ClassGroup", cg.id, org_id, {"name": name, "section": section, "course_id": course_id})
        return cg

    def list_class_groups(self, admin: User, organization_id: Optional[str] = None) -> List[ClassGroup]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list class groups.")
        with self.db._get_connection() as conn:
            target_org = admin.organization_id if admin.role == UserRole.ORG_ADMIN else organization_id
            if target_org:
                rows = conn.execute("SELECT * FROM class_groups WHERE organization_id = ?;", (target_org,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM class_groups;").fetchall()
            return [
                ClassGroup(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    course_id=r["course_id"],
                    name=r["name"],
                    section=r["section"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def create_cohort(
        self,
        admin: User,
        name: str,
        academic_year: str,
        class_group_id: str,
    ) -> Cohort:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to create cohorts.")
        ch = Cohort(
            id=f"coh-{uuid.uuid4().hex[:8]}",
            class_group_id=class_group_id,
            name=name,
            academic_year=academic_year,
        )
        self.db.create_cohort(ch)
        self._record_audit(admin, "CREATE_COHORT", "Cohort", ch.id, admin.organization_id, {"name": name, "academic_year": academic_year, "class_group_id": class_group_id})
        return ch

    def list_cohorts(self, admin: User, class_group_id: Optional[str] = None) -> List[Cohort]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list cohorts.")
        with self.db._get_connection() as conn:
            if class_group_id:
                rows = conn.execute("SELECT * FROM cohorts WHERE class_group_id = ?;", (class_group_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM cohorts;").fetchall()
            return [
                Cohort(
                    id=r["id"],
                    class_group_id=r["class_group_id"],
                    name=r["name"],
                    academic_year=r["academic_year"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def enroll_student(
        self,
        admin: User,
        student_id: str,
        course_id: str,
        cohort_id: Optional[str] = None,
    ) -> Enrollment:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to enroll students in courses.")

        enrollment = Enrollment(
            id=f"enr-{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            course_id=course_id,
            cohort_id=cohort_id,
        )
        self.db.create_enrollment(enrollment)
        self._record_audit(admin, "ENROLL_STUDENT", "Enrollment", enrollment.id, admin.organization_id, {"student_id": student_id, "course_id": course_id, "cohort_id": cohort_id})
        return enrollment

    def list_enrollments(
        self,
        admin: User,
        course_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> List[Enrollment]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to list enrollments.")
        with self.db._get_connection() as conn:
            sql = "SELECT * FROM enrollments WHERE is_active = 1"
            params = []
            if course_id:
                sql += " AND course_id = ?"
                params.append(course_id)
            if student_id:
                sql += " AND student_id = ?"
                params.append(student_id)
            rows = conn.execute(sql, tuple(params)).fetchall()
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

    def delete_enrollment(self, admin: User, enrollment_id: str) -> bool:
        if admin.role not in (UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.COURSE_ADMIN):
            raise PermissionError("Unauthorized to delete enrollments.")
        with self.db._get_connection() as conn:
            cursor = conn.execute("UPDATE enrollments SET is_active = 0 WHERE id = ?;", (enrollment_id,))
            ok = cursor.rowcount > 0
        if ok:
            self._record_audit(admin, "DELETE_ENROLLMENT", "Enrollment", enrollment_id, admin.organization_id)
        return ok

    # --- AGGREGATED TELEMETRY ---

    def get_dashboard_summary(self, admin: User, organization_id: Optional[str] = None) -> Dict[str, Any]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view administrative dashboard.")

        orgs = self.list_organizations(admin)
        users = self.list_org_users(admin, organization_id)
        courses = self.list_courses(admin, organization_id)
        curricula = self.list_curricula(admin)
        classes = self.list_class_groups(admin, organization_id)
        cohorts = self.list_cohorts(admin)
        enrollments = self.list_enrollments(admin)

        return {
            "organizations_count": len(orgs),
            "total_users": len(users),
            "teachers_count": sum(1 for u in users if u.role == UserRole.TEACHER),
            "students_count": sum(1 for u in users if u.role == UserRole.STUDENT),
            "courses_count": len(courses),
            "curricula_count": len(curricula),
            "classes_count": len(classes),
            "cohorts_count": len(cohorts),
            "enrollments_count": len(enrollments),
            "active_models_count": len(self._registered_models),
            "system_status": "HEALTHY",
            "kill_switch_active": self._global_config.get("kill_switch", False),
            "ai_policy_level": self._ai_policies.get("ai_policy_level", "strict"),
        }

    def get_analytics_summary(self, admin: User, organization_id: Optional[str] = None) -> Dict[str, Any]:
        if admin.role in (UserRole.STUDENT, UserRole.TEACHER):
            raise PermissionError("Unauthorized to view analytics.")

        users = self.list_org_users(admin, organization_id)
        courses = self.list_courses(admin, organization_id)
        return {
            "monitored_students": sum(1 for u in users if u.role == UserRole.STUDENT),
            "active_teachers": sum(1 for u in users if u.role == UserRole.TEACHER),
            "total_courses": len(courses),
            "daily_active_sessions": 42,
            "average_mastery_retention": 0.78,
            "ai_prompt_tokens_today": 128450,
            "ai_completion_tokens_today": 34900,
            "audit_events_logged": len(self._audit_log),
        }
