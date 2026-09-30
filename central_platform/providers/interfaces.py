"""Plugin architecture interfaces for Phase 10.

Defines the core provider protocols for Curriculum, Content, Courses, and Knowledge.
"""
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from central_platform.models.schema import Curriculum, Course

@runtime_checkable
class CurriculumProvider(Protocol):
    """Interface for systems that provide curriculum definitions."""
    
    def get_curriculum(self, curriculum_id: str) -> Optional[Curriculum]:
        """Fetch a specific curriculum by ID."""
        ...
        
    def list_curricula(self, filters: Optional[Dict[str, Any]] = None) -> List[Curriculum]:
        """List curricula matching optional filters."""
        ...

@runtime_checkable
class CourseProvider(Protocol):
    """Interface for systems that provide course metadata and enrollment data."""
    
    def get_course(self, course_id: str) -> Optional[Course]:
        """Fetch a specific course by ID."""
        ...
        
    def list_courses(self, organization_id: str) -> List[Course]:
        """List all courses for an organization."""
        ...

@runtime_checkable
class ContentProvider(Protocol):
    """Interface for fetching educational content blocks."""
    
    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Fetch raw content block by ID."""
        ...
        
    def search_content(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search available content."""
        ...

@runtime_checkable
class KnowledgeSource(Protocol):
    """Interface for RAG knowledge sources."""
    
    def get_document(self, document_id: str) -> Optional[str]:
        """Fetch full document text by ID."""
        ...
        
    def get_chunks(self, document_id: str) -> List[str]:
        """Fetch pre-chunked text for a document."""
        ...
