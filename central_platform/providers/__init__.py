"""Providers module for plugin architecture (Phase 10)."""

from .interfaces import (
    CurriculumProvider,
    CourseProvider,
    ContentProvider,
    KnowledgeSource
)
from .registry import PluginRegistry, registry

__all__ = [
    "CurriculumProvider",
    "CourseProvider",
    "ContentProvider",
    "KnowledgeSource",
    "PluginRegistry",
    "registry"
]
