"""Admin Portal Controller.

Entry point for the Institution / Organization Admin Dashboard.
"""
from typing import Dict, Any

class AdminPortalController:
    """Handles routing and state for the admin portal UI."""
    def get_dashboard_context(self) -> Dict[str, Any]:
        """Returns baseline context for the admin dashboard."""
        return {"portal": "admin", "version": "v4.0"}
