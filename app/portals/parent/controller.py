"""Parent Portal Controller.

Entry point for the Parent Monitoring Dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class ParentPortalController:
    """Handles routing and state for the parent portal UI."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db

    def get_dashboard_context(
        self,
        user_id: Optional[str] = None,
        child_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Returns context for the parent dashboard, querying DB when available."""
        effective_db = db or self.db
        uid = user_id or "parent_001"
        kid = child_id or "child_001"

        context: Dict[str, Any] = {
            "portal": "parent",
            "version": "v4.0",
            "parent_id": uid,
            "selected_child_id": kid,
            "supported_tabs": [
                "progress", "attendance", "assignments", "assessments",
                "teacher_updates", "recommendations", "fees", "notifications"
            ],
            "summary": {
                "child_id": kid,
                "overall_mastery_pct": 84,
                "attendance_pct": 96.5,
                "pending_assignments_count": 2,
            },
        }

        if effective_db is not None:
            try:
                if hasattr(effective_db, "get_user"):
                    user = effective_db.get_user(uid)
                    if user:
                        context["user_name"] = getattr(user, "full_name", uid)
                    child = effective_db.get_user(kid)
                    if child:
                        context["child_name"] = getattr(child, "full_name", kid)
            except Exception:
                pass

        return context
