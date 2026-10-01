"""Admin Portal Controller.

Entry point for the Institution / Organization Admin Dashboard.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class AdminPortalController:
    """Handles routing and state for the admin portal UI."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db

    def get_dashboard_context(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Returns context for the admin dashboard, querying DB when available."""
        effective_db = db or self.db
        uid = user_id or "admin_001"
        oid = organization_id or "org-default"

        context: Dict[str, Any] = {
            "portal": "admin",
            "version": "v4.0",
            "admin_id": uid,
            "organization_id": oid,
            "supported_tabs": [
                "organizations", "users", "courses", "curricula", "classes",
                "ai_models", "ai_providers", "audit_trail", "system_health"
            ],
            "stats": {
                "active_organizations": 1,
                "registered_models": 4,
                "system_status": "OPERATIONAL",
            },
        }

        if effective_db is not None:
            try:
                if hasattr(effective_db, "get_user"):
                    user = effective_db.get_user(uid)
                    if user:
                        context["user_name"] = getattr(user, "full_name", uid)
                if hasattr(effective_db, "get_organization"):
                    org = effective_db.get_organization(oid)
                    if org:
                        context["organization_name"] = getattr(org, "name", oid)
            except Exception:
                pass

        return context
