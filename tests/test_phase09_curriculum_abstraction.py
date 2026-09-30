"""Tests for Phase 09: Curriculum Abstraction."""
import json
import pytest
from central_platform.models.schema import Curriculum, CurriculumBoard
from central_platform.db import PlatformDatabase

@pytest.fixture
def db(tmp_path):
    """Provide a fresh isolated database for Phase 09 testing."""
    db_file = str(tmp_path / "phase09_test.db")
    return PlatformDatabase(db_file)

def test_curriculum_supports_multiple_boards(db):
    """Test that curriculum objects can be saved and retrieved with distinct board abstractions."""
    
    from central_platform.models.schema import Course, Organization
    org = Organization(id="org_test", name="Test Org", slug="test-org")
    db.create_organization(org)
    
    test_course = Course(id="course_sci_10", organization_id="org_test", title="Class 10 Science", code="SCI10")
    db.create_course(test_course)
    test_course2 = Course(id="course_chem_11", organization_id="org_test", title="Class 11 Chemistry", code="CHEM11")
    db.create_course(test_course2)
    test_course3 = Course(id="course_btech_ds", organization_id="org_test", title="B.Tech DS", code="DS01")
    db.create_course(test_course3)
    test_course4 = Course(id="course_summer_camp", organization_id="org_test", title="Summer Camp", code="CAMP")
    db.create_course(test_course4)

    # 1. Test CBSE Curriculum
    cbse_curriculum = Curriculum(
        id="curr_cbse_10",
        course_id="course_sci_10",
        title="Class 10 Science (CBSE)",
        board=CurriculumBoard.CBSE,
        metadata={"subject_code": "086", "year": "2026-27"}
    )
    saved_cbse = db.create_curriculum(cbse_curriculum)
    fetched_cbse = db.get_curriculum(cbse_curriculum.id)
    assert fetched_cbse.board == CurriculumBoard.CBSE
    assert fetched_cbse.metadata["subject_code"] == "086"
    
    # 2. Test NCERT Curriculum
    ncert_curriculum = Curriculum(
        id="curr_ncert_11",
        course_id="course_chem_11",
        title="Class 11 Chemistry (NCERT)",
        board=CurriculumBoard.NCERT,
        metadata={"edition": "2025"}
    )
    saved_ncert = db.create_curriculum(ncert_curriculum)
    fetched_ncert = db.get_curriculum(ncert_curriculum.id)
    assert fetched_ncert.board == CurriculumBoard.NCERT
    
    # 3. Test College Curriculum
    college_curriculum = Curriculum(
        id="curr_college_btech_cs",
        course_id="course_btech_ds",
        title="B.Tech Data Structures",
        board=CurriculumBoard.COLLEGE,
        metadata={"university": "VTU"}
    )
    saved_college = db.create_curriculum(college_curriculum)
    fetched_college = db.get_curriculum(college_curriculum.id)
    assert fetched_college.board == CurriculumBoard.COLLEGE

    # 4. Test Custom Default (Backwards Compatibility)
    custom_curriculum = Curriculum(
        id="curr_custom_camp",
        course_id="course_summer_camp",
        title="Summer Code Camp"
        # Omitting board defaults to CUSTOM
    )
    saved_custom = db.create_curriculum(custom_curriculum)
    fetched_custom = db.get_curriculum(custom_curriculum.id)
    assert fetched_custom.board == CurriculumBoard.CUSTOM
    assert fetched_custom.metadata == {}
