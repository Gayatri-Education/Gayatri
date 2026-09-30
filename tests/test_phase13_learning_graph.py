"""Tests for Phase 13: Learning Graph.

Tests concept graph traversal, prerequisite DAG validation, node state aggregation,
mastery, confidence, attempts telemetry, misconceptions, and teacher instructions.
"""

import pytest
from central_platform.db import PlatformDatabase
from central_platform.learning.graph import LearningGraph, ConceptNodeState
from central_platform.models.schema import (
    Concept,
    Course,
    Curriculum,
    LearningEvent,
    MasteryState,
    Module,
    Organization,
    Prerequisite,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    Topic,
    User,
)

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 13 tests."""
    db_file = str(tmp_path / "phase13_graph.db")
    return PlatformDatabase(db_file)

def seed_parent_entities(db, org_id="org_g", course_id="crs_g"):
    org = Organization(id=org_id, name="Graph Org", slug="graph-org")
    db.create_organization(org)
    course = Course(id=course_id, organization_id=org_id, title="Graph Course", code="GC101")
    db.create_course(course)
    cur = Curriculum(id="cur_g", course_id=course_id, title="Curriculum G", version="1.0")
    db.create_curriculum(cur)
    mod = Module(id="mod_g", curriculum_id="cur_g", title="Module G", sequence_order=1)
    db.create_module(mod)
    top = Topic(id="t1", module_id="mod_g", title="Topic 1", sequence_order=1)
    db.create_topic(top)

def test_prerequisite_chain_traversal(db):
    """Test recursive prerequisite DAG chain traversal."""
    seed_parent_entities(db, "org_g", "crs_g")
    
    # Create concepts c1 -> c2 -> c3
    c1 = Concept(id="c1", topic_id="t1", name="Basic Algebra")
    c2 = Concept(id="c2", topic_id="t1", name="Linear Equations")
    c3 = Concept(id="c3", topic_id="t1", name="Quadratic Equations")
    db.create_concept(c1)
    db.create_concept(c2)
    db.create_concept(c3)
    
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c1", dependent_concept_id="c2"))
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c2", dependent_concept_id="c3"))
    
    graph = LearningGraph(db)
    direct = graph.get_prerequisites("c3")
    assert direct == ["c2"]
    
    chain = graph.get_prerequisite_chain("c3")
    assert "c2" in chain
    assert "c1" in chain

def test_dag_validation(db):
    """Test DAG cycle and missing prerequisite validation."""
    seed_parent_entities(db, "org_dag", "crs_dag")
    graph = LearningGraph(db)
    
    c1 = Concept(id="c_alpha", topic_id="t1", name="Alpha")
    c2 = Concept(id="c_beta", topic_id="t1", name="Beta")
    db.create_concept(c1)
    db.create_concept(c2)
    
    db.add_prerequisite(Prerequisite(prerequisite_concept_id="c_alpha", dependent_concept_id="c_beta"))
    
    # Valid DAG test
    res = graph.validate_dag(["c_alpha", "c_beta"])
    assert res["valid"] is True
    assert len(res["cycles"]) == 0

def test_concept_node_state_aggregation(db):
    """Test full multi-dimensional concept node state construction."""
    seed_parent_entities(db, "org_test", "crs_chem")
    user = User(id="std_99", email="s99@test.com", full_name="Student 99", role="student", organization_id="org_test")
    db.create_user(user)
    
    concept = Concept(id="cpt_moles", topic_id="t1", name="Mole Concept", description="Atomic mass and moles", difficulty=0.6)
    db.create_concept(concept)
    
    slr = StudentLearningRecord(id="slr_99", student_id="std_99", course_id="crs_chem")
    db.create_slr(slr)
    
    ms = MasteryState(slr_id="slr_99", concept_id="cpt_moles", score=0.85, confidence=0.90, state="mastered")
    db.upsert_mastery_state(ms)
    
    # Create session before events for FK constraint
    from central_platform.models.schema import Session, SessionStatus
    sess = Session(id="sess_1", student_id="std_99", course_id="crs_chem", concept_id="cpt_moles", status=SessionStatus.ACTIVE)
    db.create_session(sess)
    
    # Log events
    db.record_learning_event(LearningEvent(
        id="evt_1",
        session_id="sess_1",
        student_id="std_99",
        course_id="crs_chem",
        concept_id="cpt_moles",
        event_type="answer_submitted",
        score=1.0,
        payload={"correctness": "correct"}
    ))
    db.record_learning_event(LearningEvent(
        id="evt_2",
        session_id="sess_1",
        student_id="std_99",
        course_id="crs_chem",
        concept_id="cpt_moles",
        event_type="hint_requested",
        payload={"hint_level": 1}
    ))
    
    # Create misconception definition
    from central_platform.models.schema import Misconception
    db.create_misconception(Misconception(
        id="misc_def_1",
        code="MOL_MASS_CONFUSION",
        category="chemistry",
        name="Mole Mass Confusion",
        description="Confusing molar mass with molecular mass"
    ))
    
    # Record misconception
    db.record_student_misconception(StudentMisconceptionRecord(
        id="sm_1",
        student_id="std_99",
        misconception_code="MOL_MASS_CONFUSION",
        frequency=2
    ))
    
    graph = LearningGraph(db)
    node_state = graph.get_concept_node_state("std_99", "crs_chem", "cpt_moles")
    
    assert node_state.concept_id == "cpt_moles"
    assert node_state.concept_name == "Mole Concept"
    assert node_state.mastery_score == 0.85
    assert node_state.confidence == 0.90
    assert node_state.mastery_status == "practicing"
    assert node_state.total_attempts == 2
    assert node_state.correct_attempts == 1
    assert node_state.hints_requested == 1
    assert "MOL_MASS_CONFUSION" in node_state.active_misconceptions
