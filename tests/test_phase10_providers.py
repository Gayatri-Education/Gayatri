"""Tests for Phase 10: Curriculum Ingestion and Plugin Architecture."""

import pytest
from central_platform.models.schema import Curriculum, Course
from central_platform.providers import registry, CurriculumProvider, KnowledgeSource
from central_platform.db import PlatformDatabase

@pytest.fixture
def db(tmp_path):
    """Provide a fresh isolated database."""
    db_file = str(tmp_path / "phase10_test.db")
    return PlatformDatabase(db_file)

class MockKnowledgeSource(KnowledgeSource):
    def get_document(self, document_id: str) -> str:
        if document_id == "doc_123":
            return "Newton's laws of motion describe the relationship between a body and the forces acting upon it."
        return ""
        
    def get_chunks(self, document_id: str) -> list[str]:
        return [self.get_document(document_id)]

class MockCurriculumProvider(CurriculumProvider):
    def get_curriculum(self, curriculum_id: str) -> Curriculum:
        if curriculum_id == "curr_test":
            return Curriculum(
                id="curr_test",
                course_id="c1",
                title="Physics Fundamentals",
                version="1.0.0",
                metadata={
                    "modules": [
                        {
                            "id": "m1", 
                            "title": "Mechanics",
                            "topics": [
                                {
                                    "id": "t1",
                                    "title": "Kinematics",
                                    "concepts": [
                                        {"id": "c1", "title": "Velocity"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            )
        return None
        
    def list_curricula(self, filters=None) -> list[Curriculum]:
        return [self.get_curriculum("curr_test")]

def test_registry_registration():
    """Test that plugins can be registered and retrieved."""
    registry.register_knowledge_source("mock_ks", MockKnowledgeSource())
    registry.register_curriculum_provider("mock_cp", MockCurriculumProvider())
    
    assert registry.get_knowledge_source("mock_ks") is not None
    assert registry.get_curriculum_provider("mock_cp") is not None
    assert registry.get_content_provider("unknown") is None

def test_rag_ingest_from_provider(db):
    """Test that RAG service can ingest content directly from a provider."""
    from central_platform.rag.service import RAGService
    from central_platform.models.schema import Course, Organization
    
    org = Organization(id="org_test", name="Test Org", slug="test-org")
    db.create_organization(org)
    course = Course(id="c1", organization_id="org_test", title="Course 1", code="C1")
    db.create_course(course)

    service = RAGService(db)
    ks = MockKnowledgeSource()
    
    # First register a source
    source = service.register_source(
        organization_id="org_test",
        course_id="c1",
        subject="Physics",
        title="Newton's Laws"
    )
    
    # Ingest using provider
    result = service.ingest_from_provider(source.id, ks, "doc_123")
    assert result["status"] == "ingested"
    assert result["chunks_created"] > 0
    assert "checksum" in result

def test_curriculum_import_from_provider(db):
    """Test that Curriculum service can import from a provider."""
    from central_platform.curriculum.service import CurriculumService
    from central_platform.models.schema import User, UserRole, Organization
    
    # Setup dependencies
    org = Organization(id="org_test", name="Test Org", slug="test-org")
    db.create_organization(org)
    admin = User(id="u_admin", organization_id="org_test", full_name="Admin", email="a@b.com", role=UserRole.ORG_ADMIN)
    db.create_user(admin)
    db.set_user_password(admin.id, "xx")
    course = Course(id="c1", organization_id="org_test", title="Course 1", code="C1")
    db.create_course(course)
    
    service = CurriculumService(db)
    cp = MockCurriculumProvider()
    
    result = service.import_from_provider(admin, cp, "curr_test", "c1")
    assert result["version_id"] is not None
