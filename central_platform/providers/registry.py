"""Plugin Registry for Phase 10 Plugin Architecture."""

from typing import Dict, Optional, Type
from .interfaces import CurriculumProvider, CourseProvider, ContentProvider, KnowledgeSource

class PluginRegistry:
    """Central registry for managing provider plugins."""
    
    def __init__(self):
        self._curriculum_providers: Dict[str, CurriculumProvider] = {}
        self._course_providers: Dict[str, CourseProvider] = {}
        self._content_providers: Dict[str, ContentProvider] = {}
        self._knowledge_sources: Dict[str, KnowledgeSource] = {}

    def register_curriculum_provider(self, name: str, provider: CurriculumProvider) -> None:
        self._curriculum_providers[name] = provider

    def register_course_provider(self, name: str, provider: CourseProvider) -> None:
        self._course_providers[name] = provider

    def register_content_provider(self, name: str, provider: ContentProvider) -> None:
        self._content_providers[name] = provider

    def register_knowledge_source(self, name: str, provider: KnowledgeSource) -> None:
        self._knowledge_sources[name] = provider

    def get_curriculum_provider(self, name: str) -> Optional[CurriculumProvider]:
        return self._curriculum_providers.get(name)

    def get_course_provider(self, name: str) -> Optional[CourseProvider]:
        return self._course_providers.get(name)

    def get_content_provider(self, name: str) -> Optional[ContentProvider]:
        return self._content_providers.get(name)

    def get_knowledge_source(self, name: str) -> Optional[KnowledgeSource]:
        return self._knowledge_sources.get(name)

# Global registry instance
registry = PluginRegistry()
