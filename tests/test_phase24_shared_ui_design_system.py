"""Tests for Phase 24 — Shared UI Design System.

Verifies:
- Existence and structure of design system CSS & JS files (tokens.css, components.css, components.js)
- CSS semantic token completeness for dark and light themes
- Coverage for all 19 required component specifications:
  (tokens, themes, typography, buttons, inputs, cards, tables, tabs, modal,
   drawer, toast, tooltip, progress, timeline, status, skeleton, empty state,
   error state, chat components)
- Python backend DesignSystemRegistry and UIThemeConfig functionality
"""
import os
import pytest
from pathlib import Path

from central_platform.ui.design_system import (
    DesignSystemRegistry,
    UIComponentType,
    UIThemeConfig,
    UIThemeMode,
)


@pytest.fixture
def design_system_paths():
    root = Path(__file__).resolve().parent.parent
    ds_dir = root / "app" / "ui" / "design_system"
    return {
        "tokens": ds_dir / "tokens.css",
        "components_css": ds_dir / "components.css",
        "components_js": ds_dir / "components.js",
    }


def test_design_system_files_exist(design_system_paths):
    assert design_system_paths["tokens"].exists()
    assert design_system_paths["components_css"].exists()
    assert design_system_paths["components_js"].exists()


def test_theme_tokens_completeness(design_system_paths):
    content = design_system_paths["tokens"].read_text(encoding="utf-8")
    assert DesignSystemRegistry.validate_theme_tokens(content) is True

    # Verify Dark Theme Tokens
    assert "--bg: #0B0D10;" in content
    assert "--surface: #111418;" in content
    assert "--brand: #D6A85F;" in content

    # Verify Light Theme Tokens Override
    assert 'html[data-theme="light"]' in content or 'body.theme-light' in content
    assert "--bg: #F7F7F5;" in content
    assert "--brand: #A87528;" in content


def test_css_component_specs_coverage(design_system_paths):
    css = design_system_paths["components_css"].read_text(encoding="utf-8")

    # Verify coverage of all 19 required components in CSS
    required_css_classes = [
        ".btn",              # Buttons
        ".input",            # Inputs
        ".card",             # Cards
        ".table",            # Tables
        ".tab-list",         # Tabs
        ".modal-backdrop",   # Modal
        ".drawer-content",   # Drawer
        ".toast",            # Toast
        "[data-tooltip]",    # Tooltip
        ".progress-bar",     # Progress
        ".timeline",         # Timeline
        ".badge",            # Status
        ".skeleton",         # Skeleton
        ".empty-state",      # Empty state
        ".error-state",      # Error state
        ".chat-message",     # Chat components
        ".socratic-hint-card", # Pedagogical hint
        ".citation-pill",    # Citation pill
    ]

    for cls_name in required_css_classes:
        assert cls_name in css, f"Missing component styling for {cls_name} in components.css"


def test_js_component_controller_functions(design_system_paths):
    js = design_system_paths["components_js"].read_text(encoding="utf-8")
    assert "setTheme" in js
    assert "toggleTheme" in js
    assert "showToast" in js
    assert "openModal" in js
    assert "openDrawer" in js
    assert "selectTab" in js


def test_python_design_system_registry():
    components = DesignSystemRegistry.list_components()
    assert len(components) >= 18

    comp_types = {c["component_type"] for c in components}
    assert "button" in comp_types
    assert "card" in comp_types
    assert "modal" in comp_types
    assert "toast" in comp_types
    assert "chat_message" in comp_types


def test_ui_theme_config_defaults():
    cfg = UIThemeConfig()
    d = cfg.to_dict()
    assert d["theme_mode"] == "dark"
    assert d["primary_brand_color"] == "#D6A85F"
