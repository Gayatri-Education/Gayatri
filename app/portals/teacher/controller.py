"""Teacher Portal Controller.

Entry point for the Teacher Copilot and Class Management Dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class TeacherPortalController:
    """Handles routing and state for the teacher portal UI."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db

    def get_dashboard_context(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Returns context for the teacher dashboard, querying DB when available."""
        effective_db = db or self.db
        uid = user_id or "teacher_001"
        cid = course_id or "crs-101"

        context: Dict[str, Any] = {
            "portal": "teacher",
            "version": "v4.0",
            "teacher_id": uid,
            "course_id": cid,
            "supported_tabs": [
                "class_overview", "students", "learning_health", "student_profile",
                "interventions", "assessments", "teacher_instructions", "ai_copilot"
            ],
            "overview": {
                "course_id": cid,
                "enrolled_count": 24,
                "average_mastery_pct": 76,
                "at_risk_count": 3,
                "active_interventions": 5,
            },
        }

        if effective_db is not None:
            try:
                if hasattr(effective_db, "get_user"):
                    user = effective_db.get_user(uid)
                    if user:
                        context["user_name"] = getattr(user, "full_name", uid)
                if hasattr(effective_db, "get_course"):
                    course = effective_db.get_course(cid)
                    if course:
                        context["course_title"] = getattr(course, "title", cid)
            except Exception:
                pass

        return context
