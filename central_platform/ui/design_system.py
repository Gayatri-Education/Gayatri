"""Gayatri AI Platform — Shared UI Design System Manager (Phase 24).

Provides Python backend descriptors, theme configuration contracts,
and component specifications for Student, Teacher, Parent, and Admin portals.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class UIThemeMode(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


@dataclass
class UIThemeConfig:
    """Theme configuration specification."""
    theme_mode: UIThemeMode = UIThemeMode.DARK
    primary_brand_color: str = "#D6A85F"
    font_family_ui: str = "Inter, Manrope, system-ui, sans-serif"
    font_family_mono: str = "JetBrains Mono, IBM Plex Mono, monospace"
    enable_animations: bool = True
    compact_density: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["theme_mode"] = self.theme_mode.value if isinstance(self.theme_mode, UIThemeMode) else str(self.theme_mode)
        return d


class UIComponentType(str, Enum):
    BUTTON = "button"
    INPUT = "input"
    CARD = "card"
    TABLE = "table"
    TABS = "tabs"
    MODAL = "modal"
    DRAWER = "drawer"
    TOAST = "toast"
    TOOLTIP = "tooltip"
    PROGRESS = "progress"
    TIMELINE = "timeline"
    STATUS = "status"
    SKELETON = "skeleton"
    EMPTY_STATE = "empty_state"
    ERROR_STATE = "error_state"
    CHAT_MESSAGE = "chat_message"
    SOCRATIC_HINT = "socratic_hint"
    CITATION_PILL = "citation_pill"


@dataclass
class UIComponentDescriptor:
    """Descriptor for a registered design system component."""
    component_type: UIComponentType
    class_name: str
    description: str
    props: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type.value if isinstance(self.component_type, UIComponentType) else str(self.component_type),
            "class_name": self.class_name,
            "description": self.description,
            "props": self.props,
        }


class DesignSystemRegistry:
    """Authoritative registry of Phase 24 Design System components and theme tokens."""

    SUPPORTED_COMPONENTS: List[UIComponentDescriptor] = [
        UIComponentDescriptor(UIComponentType.BUTTON, "btn", "Standard button with variants", ["variant", "size", "disabled"]),
        UIComponentDescriptor(UIComponentType.INPUT, "input", "Form text input with focus ring", ["type", "placeholder", "error"]),
        UIComponentDescriptor(UIComponentType.CARD, "card", "Container card for content grouping", ["raised"]),
        UIComponentDescriptor(UIComponentType.TABLE, "table", "Data table with striped & hover states", ["striped", "hover"]),
        UIComponentDescriptor(UIComponentType.TABS, "tab-list", "Navigational tab control", ["active_tab"]),
        UIComponentDescriptor(UIComponentType.MODAL, "modal-backdrop", "Overlay dialog modal window", ["active"]),
        UIComponentDescriptor(UIComponentType.DRAWER, "drawer-content", "Sliding side drawer", ["position"]),
        UIComponentDescriptor(UIComponentType.TOAST, "toast", "Transient alert notification", ["type", "duration"]),
        UIComponentDescriptor(UIComponentType.TOOLTIP, "data-tooltip", "Hover context tooltip", ["content"]),
        UIComponentDescriptor(UIComponentType.PROGRESS, "progress-bar", "Progress indicator & loading spinner", ["percentage"]),
        UIComponentDescriptor(UIComponentType.TIMELINE, "timeline", "Chronological event stream", ["badge_color"]),
        UIComponentDescriptor(UIComponentType.STATUS, "badge", "Status tag pill", ["variant"]),
        UIComponentDescriptor(UIComponentType.SKELETON, "skeleton", "Content loading skeleton shimmer", ["type"]),
        UIComponentDescriptor(UIComponentType.EMPTY_STATE, "empty_state", "Zero-data state placeholder", ["title", "icon"]),
        UIComponentDescriptor(UIComponentType.ERROR_STATE, "error_state", "Error feedback container", ["error_msg"]),
        UIComponentDescriptor(UIComponentType.CHAT_MESSAGE, "chat-message", "Socratic dialogue bubble", ["role"]),
        UIComponentDescriptor(UIComponentType.SOCRATIC_HINT, "socratic-hint-card", "Pedagogical hint card", ["hint"]),
        UIComponentDescriptor(UIComponentType.CITATION_PILL, "citation-pill", "Grounding source citation pill", ["citation"]),
    ]

    @classmethod
    def list_components(cls) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in cls.SUPPORTED_COMPONENTS]

    @classmethod
    def validate_theme_tokens(cls, css_content: str) -> bool:
        """Verify that CSS file contains all required semantic tokens for light and dark themes."""
        required_tokens = [
            "--bg", "--surface", "--surface-raised", "--surface-hover",
            "--border", "--border-strong", "--text", "--text-secondary",
            "--text-tertiary", "--brand", "--success", "--warning", "--error", "--info"
        ]
        return all(token in css_content for token in required_tokens)
