"""Student Portal Controller.

Entry point for the Student Learning Dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class StudentPortalController:
    """Handles routing and state for the student portal UI."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db

    def get_dashboard_context(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Returns context for the student dashboard, querying DB when available."""
        effective_db = db or self.db
        uid = user_id or "student_001"
        cid = course_id or "crs-101"

        context: Dict[str, Any] = {
            "portal": "student",
            "version": "v4.0",
            "student_id": uid,
            "course_id": cid,
            "supported_tabs": [
                "dashboard", "curriculum", "learning_graph", "progress",
                "review_queue", "assignments", "assessments", "activity", "profile", "notifications"
            ],
            "stats": {
                "mastery_pct": 74,
                "review_due_count": 5,
                "assignments_pending": 2,
                "streak_days": 12,
            },
        }

        if effective_db is not None:
            try:
                if hasattr(effective_db, "get_user"):
                    user = effective_db.get_user(uid)
                    if user:
                        context["user_name"] = getattr(user, "full_name", uid)
                if hasattr(effective_db, "get_slr"):
                    slr = effective_db.get_slr(uid, cid)
                    if slr:
                        context["slr_id"] = getattr(slr, "slr_id", "")
                        context["overall_mastery"] = getattr(slr, "overall_mastery", 0.74)
            except Exception:
                pass

        return context
