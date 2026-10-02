"""Admin Portal Controller.

Authoritative entry point for the Institution / Organization Admin Dashboard.
Provides real service-backed workflows for:
- Course catalog & public/private discovery
- Course versioning & submission
- Administrative review queue
- Content approval, publishing, and archiving
- Tenant-scoped audit trail
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.app.portals.admin.controller")

from central_platform.courses.service import (
    CourseAuthorizationError,
    CourseNotFoundError,
    CourseService,
    CourseValidationError,
)
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Course,
    CourseStatus,
    CourseVisibility,
    User,
    UserRole,
)


class AdminPortalController:
    """Handles routing, workflows, and state for the admin portal UI."""

    def __init__(self, db: Optional[PlatformDatabase] = None) -> None:
        self.db = db or PlatformDatabase()
        self.course_service = CourseService(self.db)

    def get_dashboard_context(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        db: Optional[PlatformDatabase] = None,
    ) -> Dict[str, Any]:
        """Returns context for the admin dashboard, querying real DB."""
        effective_db = db or self.db
        uid = user_id or "admin_001"
        oid = organization_id or "org-default"

        courses = effective_db.get_courses_by_organization(oid)
        public_courses = effective_db.get_public_courses()
        review_queue = effective_db.get_course_versions_by_status(CourseStatus.READY_FOR_REVIEW, organization_id=oid)

        user_name = uid
        org_name = oid
        user = effective_db.get_user(uid)
        if user:
            user_name = user.full_name
        org = effective_db.get_organization(oid)
        if org:
            org_name = org.name

        return {
            "portal": "admin",
            "version": "v4.0",
            "admin_id": uid,
            "user_name": user_name,
            "organization_id": oid,
            "organization_name": org_name,
            "supported_tabs": [
                "organizations", "users", "courses", "curricula", "classes",
                "ai_models", "ai_providers", "audit_trail", "system_health",
                "review_queue",
            ],
            "stats": {
                "active_organizations": len(effective_db.list_organizations()),
                "total_org_courses": len(courses),
                "public_catalog_courses": len(public_courses),
                "review_queue_count": len(review_queue),
                "system_status": "OPERATIONAL",
            },
        }

    # ── Course Catalog Workflows ──────────────────────────────────────────────

    def list_courses(
        self,
        actor: Optional[User] = None,
        organization_id: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List courses from real DB with visibility and tenant scoping."""
        target_org = organization_id or (actor.organization_id if actor else None)
        courses_map: Dict[str, Course] = {}

        if visibility != "PRIVATE":
            for c in self.course_service.list_public_courses():
                courses_map[c.id] = c

        if target_org and visibility != "PUBLIC":
            if actor:
                try:
                    for c in self.course_service.list_courses_for_org(actor, target_org):
                        courses_map[c.id] = c
                except CourseAuthorizationError as exc:
                    logger.debug("Actor %s not authorized to list courses for org %s: %s", actor.id, target_org, exc)
            else:
                for c in self.db.get_courses_by_organization(target_org):
                    courses_map[c.id] = c

        return [
            {
                "course_id": c.id,
                "code": c.code,
                "title": c.title,
                "description": c.description or "",
                "visibility": c.visibility.value if hasattr(c.visibility, "value") else str(c.visibility),
                "organization_id": c.organization_id,
                "created_at": c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else str(c.created_at or ""),
            }
            for c in courses_map.values()
        ]

    def create_course(
        self,
        actor: User,
        code: str,
        title: str,
        description: str = "",
        visibility: str = "PRIVATE",
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new course owned by actor's organization."""
        vis = CourseVisibility.PUBLIC if visibility.upper() == "PUBLIC" else CourseVisibility.PRIVATE
        course = self.course_service.create_course(
            actor=actor,
            code=code,
            title=title,
            description=description,
            visibility=vis,
            organization_id=organization_id,
        )
        return {
            "course_id": course.id,
            "code": course.code,
            "title": course.title,
            "description": course.description or "",
            "visibility": course.visibility.value if hasattr(course.visibility, "value") else str(course.visibility),
            "organization_id": course.organization_id,
            "created_at": course.created_at.isoformat() if hasattr(course.created_at, "isoformat") else str(course.created_at or ""),
        }

    def select_course_offering(
        self,
        actor: User,
        organization_id: str,
        course_id: str,
        pinned_version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Establish an active offering for an organization pinned to a course version."""
        offering = self.course_service.select_course_for_org(
            actor=actor,
            organization_id=organization_id,
            course_id=course_id,
            pinned_version_id=pinned_version_id,
        )
        version_id = getattr(offering, "course_version_id", None) or getattr(offering, "pinned_version_id", None)
        return {
            "offering_id": offering.id,
            "organization_id": offering.organization_id,
            "course_id": offering.course_id,
            "pinned_version_id": version_id,
            "is_active": offering.is_active,
        }

    # ── Versions & Content Review Queue Workflows ─────────────────────────────

    def list_course_versions(self, course_id: str) -> List[Dict[str, Any]]:
        """List all version snapshots of a course."""
        versions = self.db.get_course_versions_by_course(course_id)
        return [
            {
                "version_id": v.id,
                "course_id": v.course_id,
                "version_number": v.version_number,
                "status": v.status.value if hasattr(v.status, "value") else str(v.status),
                "created_by": v.created_by,
                "published_by": v.published_by,
                "created_at": v.created_at.isoformat() if hasattr(v.created_at, "isoformat") else str(v.created_at or ""),
                "published_at": v.published_at.isoformat() if hasattr(v.published_at, "isoformat") and v.published_at else str(v.published_at or ""),
            }
            for v in versions
        ]

    def create_course_version(
        self,
        actor: User,
        course_id: str,
        version_number: str,
    ) -> Dict[str, Any]:
        """Create a new course version in DRAFT status."""
        version = self.course_service.create_course_version(
            actor=actor,
            course_id=course_id,
            version_number=version_number,
        )
        return {
            "version_id": version.id,
            "course_id": version.course_id,
            "version_number": version.version_number,
            "status": version.status.value if hasattr(version.status, "value") else str(version.status),
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat() if hasattr(version.created_at, "isoformat") else str(version.created_at or ""),
        }

    def submit_version_for_review(self, actor: User, version_id: str) -> Dict[str, Any]:
        """Submit version for administrative review."""
        version = self.course_service.submit_version_for_review(actor=actor, version_id=version_id)
        return {
            "version_id": version.id,
            "course_id": version.course_id,
            "version_number": version.version_number,
            "status": version.status.value if hasattr(version.status, "value") else str(version.status),
        }

    def get_review_queue(self, actor: User, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve course versions awaiting administrator review."""
        return self.course_service.get_review_queue(actor=actor, organization_id=organization_id)

    def approve_and_publish_version(self, actor: User, version_id: str) -> Dict[str, Any]:
        """Approve and publish a course version."""
        version = self.course_service.approve_and_publish_version(actor=actor, version_id=version_id)
        return {
            "version_id": version.id,
            "course_id": version.course_id,
            "version_number": version.version_number,
            "status": version.status.value if hasattr(version.status, "value") else str(version.status),
            "published_by": version.published_by,
        }

    def archive_course(self, actor: User, course_id: str) -> bool:
        """Archive a course."""
        return self.course_service.archive_course(actor=actor, course_id=course_id)

    def archive_course_version(self, actor: User, version_id: str) -> Dict[str, Any]:
        """Archive a course version."""
        version = self.course_service.archive_course_version(actor=actor, version_id=version_id)
        return {
            "version_id": version.id,
            "course_id": version.course_id,
            "version_number": version.version_number,
            "status": version.status.value if hasattr(version.status, "value") else str(version.status),
        }

    def get_audit_trail(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve authoritative audit trail from platform database."""
        with self.db._get_connection() as conn:
            if organization_id:
                rows = conn.execute(
                    "SELECT * FROM audit_logs WHERE organization_id = ? ORDER BY created_at DESC LIMIT 100;",
                    (organization_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;"
                ).fetchall()
            return [
                {
                    "id": r["id"],
                    "organization_id": r["organization_id"],
                    "user_id": r["user_id"],
                    "action": r["action"],
                    "resource": r["resource"],
                    "details": r["details"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
