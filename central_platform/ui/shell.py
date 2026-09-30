"""Gayatri AI Platform — Application Shell Backend Manager (Phase 25).

Provides backend state contracts, portal routing descriptors, and multi-language
configurations for the desktop/web Application Shell.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PortalRoute(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


@dataclass
class LanguageOption:
    code: str
    name: str
    native_name: str


@dataclass
class AppShellConfig:
    """Application Shell state configuration."""
    active_portal: PortalRoute = PortalRoute.STUDENT
    sidebar_collapsed: bool = False
    current_language: str = "en"
    user_name: str = "Student User"
    user_role: str = "student"
    user_email: str = "student@gayatri.ai"
    theme_mode: str = "dark"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["active_portal"] = self.active_portal.value if isinstance(self.active_portal, PortalRoute) else str(self.active_portal)
        return d


class AppShellManager:
    """Authoritative Application Shell Backend Manager."""

    SUPPORTED_LANGUAGES: List[LanguageOption] = [
        LanguageOption("en", "English", "English"),
        LanguageOption("hi", "Hindi", "हिंदी"),
        LanguageOption("sa", "Sanskrit", "संस्कृतम्"),
        LanguageOption("ta", "Tamil", "தமிழ்"),
        LanguageOption("te", "Telugu", "తెలుగు"),
        LanguageOption("kn", "Kannada", "கன்னட"),
        LanguageOption("mr", "Marathi", "मराठी"),
        LanguageOption("bn", "Bengali", "বাংলা"),
    ]

    @classmethod
    def list_languages(cls) -> List[Dict[str, str]]:
        return [asdict(lang) for lang in cls.SUPPORTED_LANGUAGES]

    @classmethod
    def get_portal_url(cls, portal: PortalRoute) -> str:
        routes = {
            PortalRoute.STUDENT: "/student_dashboard.html",
            PortalRoute.TEACHER: "/teacher_portal.html",
            PortalRoute.PARENT: "/parent_dashboard.html",
            PortalRoute.ADMIN: "/admin_portal.html",
        }
        return routes.get(portal, "/index.html")
