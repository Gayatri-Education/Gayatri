"""Tests for Phase 25 — Application Shell.

Verifies:
- Shell CSS and JS asset existence (shell.css, shell.js)
- Responsive shell CSS rules (sidebar, topbar, user menu, portal badge, language selector)
- Shell JS controller functions (toggleSidebar, toggleUserMenu, setLanguage, navigateToPortal)
- Python backend AppShellManager and AppShellConfig functionality
"""
import pytest
from pathlib import Path

from central_platform.ui.shell import (
    AppShellConfig,
    AppShellManager,
    PortalRoute,
)


@pytest.fixture
def shell_paths():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "app" / "ui" / "design_system"
    return {
        "shell_css": ds_dir / "shell.css",
        "shell_js": ds_dir / "shell.js",
    }


def test_shell_files_exist(shell_paths):
    assert shell_paths["shell_css"].exists()
    assert shell_paths["shell_js"].exists()


def test_shell_css_rules(shell_paths):
    css = shell_paths["shell_css"].read_text(encoding="utf-8")

    # Verify key shell components in CSS
    assert ".app-shell" in css
    assert ".app-sidebar" in css
    assert ".app-topbar" in css
    assert ".user-menu-dropdown" in css
    assert ".language-selector" in css
    assert ".theme-selector" in css
    assert "@media (max-width: 768px)" in css  # Responsive breakpoint


def test_shell_js_controller(shell_paths):
    js = shell_paths["shell_js"].read_text(encoding="utf-8")

    # Verify JS controller functions
    assert "toggleSidebar" in js
    assert "toggleUserMenu" in js
    assert "setLanguage" in js
    assert "navigateToPortal" in js
    assert "supportedLanguages" in js


def test_app_shell_manager_languages():
    langs = AppShellManager.list_languages()
    assert len(langs) >= 8
    lang_codes = {l["code"] for l in langs}
    assert "en" in lang_codes
    assert "hi" in lang_codes
    assert "sa" in lang_codes


def test_app_shell_portal_routing():
    assert AppShellManager.get_portal_url(PortalRoute.STUDENT) == "/student_dashboard.html"
    assert AppShellManager.get_portal_url(PortalRoute.TEACHER) == "/teacher_portal.html"
    assert AppShellManager.get_portal_url(PortalRoute.ADMIN) == "/admin_portal.html"


def test_app_shell_config_defaults():
    cfg = AppShellConfig()
    d = cfg.to_dict()
    assert d["active_portal"] == "student"
    assert d["sidebar_collapsed"] is False
    assert d["current_language"] == "en"
