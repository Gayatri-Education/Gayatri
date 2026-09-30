"""Tests for Phase 07: UI Interaction Boundaries for Portals."""
from app.portals.student.controller import StudentPortalController
from app.portals.teacher.controller import TeacherPortalController
from app.portals.parent.controller import ParentPortalController
from app.portals.admin.controller import AdminPortalController

def test_student_portal_baseline():
    """Verify student portal returns correct boundary context."""
    controller = StudentPortalController()
    context = controller.get_dashboard_context()
    assert context["portal"] == "student"
    assert context["version"] == "v4.0"

def test_teacher_portal_baseline():
    """Verify teacher portal returns correct boundary context."""
    controller = TeacherPortalController()
    context = controller.get_dashboard_context()
    assert context["portal"] == "teacher"
    assert context["version"] == "v4.0"

def test_parent_portal_baseline():
    """Verify parent portal returns correct boundary context."""
    controller = ParentPortalController()
    context = controller.get_dashboard_context()
    assert context["portal"] == "parent"
    assert context["version"] == "v4.0"

def test_admin_portal_baseline():
    """Verify admin portal returns correct boundary context."""
    controller = AdminPortalController()
    context = controller.get_dashboard_context()
    assert context["portal"] == "admin"
    assert context["version"] == "v4.0"
