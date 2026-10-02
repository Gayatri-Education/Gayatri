"""Course Domain Management Package (Phase 02)."""

from central_platform.courses.service import CourseService, CourseAuthorizationError, CourseNotFoundError

__all__ = ["CourseService", "CourseAuthorizationError", "CourseNotFoundError"]
