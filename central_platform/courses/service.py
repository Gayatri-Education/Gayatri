"""Course Domain Service — Central Platform (Phase 02).

Authoritative business logic for:
- Course visibility (PUBLIC vs PRIVATE) and organization isolation
- Immutable course versioning and lifecycle status transitions
- Course offerings selection and version pinning
- Tool policy validation
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    AuditLog,
    Course,
    CourseOffering,
    CoursePolicy,
    CourseStatus,
    CourseToolPolicy,
    CourseVersion,
    CourseVisibility,
    User,
    UserRole,
)


class CourseAuthorizationError(PermissionError):
    """Raised when an actor lacks authority for a course operation."""
    pass


class CourseNotFoundError(KeyError):
    """Raised when a requested course or version cannot be found."""
    pass


class CourseValidationError(ValueError):
    """Raised when invalid course data or parameters are supplied."""
    pass


class CourseService:
    """Domain service managing course creation, versioning, offerings, and authorization."""

    def __init__(self, db: Optional[PlatformDatabase] = None) -> None:
        self.db = db or PlatformDatabase()

    def _record_audit(
        self,
        actor: User,
        action: str,
        target: str,
        org_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        try:
            self.db.record_audit_log(
                AuditLog(
                    id=f"aud_{uuid.uuid4().hex[:12]}",
                    organization_id=org_id or actor.organization_id or "system",
                    user_id=actor.id,
                    action=action,
                    resource=target,
                    details=details or {},
                )
            )
        except Exception:
            pass

    def create_course(
        self,
        actor: User,
        code: str,
        title: str,
        description: str = "",
        visibility: CourseVisibility = CourseVisibility.PRIVATE,
        organization_id: Optional[str] = None,
    ) -> Course:
        """Create a new course owned by the actor's organization."""
        org_id = organization_id or actor.organization_id
        if not org_id:
            raise CourseValidationError("Organization ID must be explicitly provided or present on actor.")

        # Authorization: Org Admin or Super Admin, or Teacher of that org
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN, UserRole.TEACHER):
            raise CourseAuthorizationError("Actor lacks permission to create courses.")
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != org_id:
            raise CourseAuthorizationError("Cannot create courses for another organization.")

        course_id = f"crs_{code.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        course = Course(
            id=course_id,
            organization_id=org_id,
            code=code,
            title=title,
            description=description,
            visibility=visibility,
        )
        self.db.create_course(course)

        # Automatically create initial Version 1.0 in DRAFT
        version_id = f"cv_{course_id}_v1_0"
        initial_checksum = hashlib.sha256(f"{course_id}:1.0:{time.time()}".encode("utf-8")).hexdigest()
        version = CourseVersion(
            id=version_id,
            course_id=course_id,
            version_number="1.0",
            status=CourseStatus.DRAFT,
            tool_policy=CourseToolPolicy(),
            tutor_policy=CoursePolicy(),
            checksum=initial_checksum,
            created_by=actor.id,
        )
        self.db.create_course_version(version)

        # Automatically create offering for owning organization
        offering = CourseOffering(
            id=f"off_{org_id}_{course_id}",
            organization_id=org_id,
            course_id=course_id,
            pinned_version_id=version_id,
        )
        self.db.create_course_offering(offering)

        self._record_audit(
            actor,
            "CREATE_COURSE",
            f"Course:{course_id}",
            org_id,
            {"code": code, "title": title, "visibility": visibility.value if hasattr(visibility, "value") else str(visibility)},
        )

        return course

    def get_course(self, actor: User, course_id: str) -> Course:
        """Retrieve course details enforcing public vs private visibility rules."""
        course = self.db.get_course(course_id)
        if not course:
            raise CourseNotFoundError(f"Course '{course_id}' not found.")

        # Super admin has global visibility
        if actor.role == UserRole.SUPER_ADMIN:
            return course

        # Public courses are visible across organizations
        if course.visibility == CourseVisibility.PUBLIC:
            return course

        # Private course: actor MUST belong to the owning organization
        if actor.organization_id != course.organization_id:
            raise CourseAuthorizationError(
                f"Access Denied: Course '{course.code}' is private to organization '{course.organization_id}'."
            )

        return course

    def list_public_courses(self) -> List[Course]:
        """Return catalog of all public courses discoverable across organizations."""
        return self.db.get_public_courses()

    def list_courses_for_org(self, actor: User, organization_id: str) -> List[Course]:
        """List all courses available to an organization (owned or selected)."""
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != organization_id:
            raise CourseAuthorizationError("Cannot view courses of another organization.")

        owned = self.db.get_courses_by_organization(organization_id)
        # Also find public courses offered to this org
        offerings = self.db.get_course_offerings_by_org(organization_id)
        offered_ids = {o.course_id for o in offerings}

        all_courses = {c.id: c for c in owned}
        for cid in offered_ids:
            if cid not in all_courses:
                c = self.db.get_course(cid)
                if c:
                    all_courses[cid] = c

        return list(all_courses.values())

    def create_course_version(
        self,
        actor: User,
        course_id: str,
        version_number: str,
        tool_policy: Optional[CourseToolPolicy] = None,
        tutor_policy: Optional[CoursePolicy] = None,
    ) -> CourseVersion:
        """Create a new immutable course version in DRAFT status."""
        course = self.get_course(actor, course_id)

        # Teachers and Admins of the owning organization can create versions
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN, UserRole.TEACHER):
            raise CourseAuthorizationError("Actor lacks authority to create course versions.")
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != course.organization_id:
            raise CourseAuthorizationError("Cannot modify course belonging to another organization.")

        version_id = f"cv_{course_id}_v{version_number.replace('.', '_')}"
        checksum = hashlib.sha256(f"{course_id}:{version_number}:{time.time()}".encode("utf-8")).hexdigest()

        version = CourseVersion(
            id=version_id,
            course_id=course_id,
            version_number=version_number,
            status=CourseStatus.DRAFT,
            tool_policy=tool_policy or CourseToolPolicy(),
            tutor_policy=tutor_policy or CoursePolicy(),
            checksum=checksum,
            created_by=actor.id,
        )
        created_ver = self.db.create_course_version(version)
        self._record_audit(
            actor,
            "CREATE_COURSE_VERSION",
            f"CourseVersion:{version.id}",
            course.organization_id,
            {"course_id": course_id, "version_number": version_number},
        )
        return created_ver

    def submit_version_for_review(self, actor: User, version_id: str) -> CourseVersion:
        """Submit a draft/processing version for administrative review."""
        version = self.db.get_course_version(version_id)
        if not version:
            raise CourseNotFoundError(f"Course version '{version_id}' not found.")

        course = self.get_course(actor, version.course_id)
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != course.organization_id:
            raise CourseAuthorizationError("Cannot submit versions for courses owned by another organization.")

        if version.status not in (CourseStatus.DRAFT, CourseStatus.PROCESSING):
            raise CourseValidationError(f"Cannot submit version in status '{version.status.value}'. Must be DRAFT or PROCESSING.")

        updated_version = CourseVersion(
            id=version.id,
            course_id=version.course_id,
            version_number=version.version_number,
            status=CourseStatus.READY_FOR_REVIEW,
            tool_policy=version.tool_policy,
            tutor_policy=version.tutor_policy,
            checksum=version.checksum,
            created_by=version.created_by,
            created_at=version.created_at,
        )
        saved_ver = self.db.create_course_version(updated_version)
        self._record_audit(
            actor,
            "SUBMIT_VERSION_FOR_REVIEW",
            f"CourseVersion:{version.id}",
            course.organization_id,
            {"course_id": version.course_id, "version_number": version.version_number},
        )
        return saved_ver

    def approve_and_publish_version(self, actor: User, version_id: str) -> CourseVersion:
        """Approve and publish a course version. Requires ORG_ADMIN or SUPER_ADMIN role."""
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN):
            raise CourseAuthorizationError("Only Organization Admins or Super Admins can approve and publish course versions.")

        version = self.db.get_course_version(version_id)
        if not version:
            raise CourseNotFoundError(f"Course version '{version_id}' not found.")

        course = self.get_course(actor, version.course_id)
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != course.organization_id:
            raise CourseAuthorizationError("Cannot approve courses belonging to another organization.")

        self.db.publish_course_version(version_id, published_by=actor.id)
        self._record_audit(
            actor,
            "APPROVE_AND_PUBLISH_VERSION",
            f"CourseVersion:{version_id}",
            course.organization_id,
            {"course_id": version.course_id, "version_number": version.version_number},
        )
        return self.db.get_course_version(version_id)

    def select_course_for_org(
        self,
        actor: User,
        organization_id: str,
        course_id: str,
        pinned_version_id: Optional[str] = None,
    ) -> CourseOffering:
        """Select a course for an organization. Enforces public vs private visibility."""
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN):
            raise CourseAuthorizationError("Only Organization Admins can select courses for an organization.")
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != organization_id:
            raise CourseAuthorizationError("Cannot configure course offerings for another organization.")

        course = self.db.get_course(course_id)
        if not course:
            raise CourseNotFoundError(f"Course '{course_id}' not found.")

        # Check access: If private and owned by another org, reject!
        if course.visibility == CourseVisibility.PRIVATE and course.organization_id != organization_id:
            raise CourseAuthorizationError(
                f"Cannot select private course '{course.code}'. It is restricted to organization '{course.organization_id}'."
            )

        # Resolve pinned version (or latest published version)
        if not pinned_version_id:
            latest = self.db.get_latest_published_course_version(course_id)
            if latest:
                pinned_version_id = latest.id

        offering_id = f"off_{organization_id}_{course_id}"
        offering = CourseOffering(
            id=offering_id,
            organization_id=organization_id,
            course_id=course_id,
            pinned_version_id=pinned_version_id,
        )
        saved_off = self.db.create_course_offering(offering)
        self._record_audit(
            actor,
            "SELECT_COURSE_OFFERING",
            f"CourseOffering:{offering_id}",
            organization_id,
            {"course_id": course_id, "pinned_version_id": pinned_version_id},
        )
        return saved_off

    def archive_course(self, actor: User, course_id: str) -> bool:
        """Archive / soft-delete a course. Requires ORG_ADMIN or SUPER_ADMIN role."""
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN):
            raise CourseAuthorizationError("Only Organization Admins or Super Admins can archive courses.")
        course = self.db.get_course(course_id)
        if not course:
            raise CourseNotFoundError(f"Course '{course_id}' not found.")
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != course.organization_id:
            raise CourseAuthorizationError("Cannot archive courses belonging to another organization.")
        ok = self.db.archive_course(course_id)
        if ok:
            self._record_audit(
                actor,
                "ARCHIVE_COURSE",
                f"Course:{course_id}",
                course.organization_id,
                {"code": course.code, "title": course.title},
            )
        return ok

    def archive_course_version(self, actor: User, version_id: str) -> CourseVersion:
        """Archive a course version. Requires ORG_ADMIN or SUPER_ADMIN role."""
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN):
            raise CourseAuthorizationError("Only Organization Admins or Super Admins can archive course versions.")
        version = self.db.get_course_version(version_id)
        if not version:
            raise CourseNotFoundError(f"Course version '{version_id}' not found.")
        course = self.get_course(actor, version.course_id)
        if actor.role != UserRole.SUPER_ADMIN and actor.organization_id != course.organization_id:
            raise CourseAuthorizationError("Cannot archive versions belonging to another organization.")
        self.db.archive_course_version(version_id, archived_by=actor.id)
        self._record_audit(
            actor,
            "ARCHIVE_COURSE_VERSION",
            f"CourseVersion:{version_id}",
            course.organization_id,
            {"course_id": version.course_id, "version_number": version.version_number},
        )
        return self.db.get_course_version(version_id)

    def get_review_queue(self, actor: User, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve course versions pending administrative review with tenant scoping."""
        if actor.role not in (UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN):
            raise CourseAuthorizationError("Only Organization Admins and Super Admins can view the review queue.")

        target_org = organization_id if actor.role == UserRole.SUPER_ADMIN else actor.organization_id
        pending_versions = self.db.get_course_versions_by_status(CourseStatus.READY_FOR_REVIEW, organization_id=target_org)

        queue: List[Dict[str, Any]] = []
        for v in pending_versions:
            course = self.db.get_course(v.course_id)
            if not course:
                continue
            created_at_str = v.created_at.isoformat() if hasattr(v.created_at, "isoformat") else str(v.created_at or "")
            queue.append({
                "version_id": v.id,
                "course_id": v.course_id,
                "course_code": course.code,
                "course_title": course.title,
                "version_number": v.version_number,
                "status": v.status.value if hasattr(v.status, "value") else str(v.status),
                "created_by": v.created_by,
                "created_at": created_at_str,
                "organization_id": course.organization_id,
                "visibility": course.visibility.value if hasattr(course.visibility, "value") else str(course.visibility),
            })
        return queue

    def get_active_course_version(self, organization_id: str, course_id: str) -> Optional[CourseVersion]:
        """Resolve the active course version pinned by the organization offering."""
        offering = self.db.get_course_offering_by_org_and_course(organization_id, course_id)
        if offering and offering.pinned_version_id:
            return self.db.get_course_version(offering.pinned_version_id)
        # Fallback to latest published version
        return self.db.get_latest_published_course_version(course_id)

    def validate_tool_access(self, course_version_id: str, tool_name: str) -> bool:
        """Server-side check verifying if a specific tool is enabled in the course version tool policy."""
        version = self.db.get_course_version(course_version_id)
        if not version or not version.tool_policy:
            return False
        return version.tool_policy.is_tool_enabled(tool_name)

