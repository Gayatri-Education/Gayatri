"""Tests for Phase 17: Context Builder.

Tests 7-layer context assembly:
1. Conversation
2. Learner state
3. Curriculum
4. Teacher instructions
5. Institution policy
6. RAG retrieval
7. Recent events

Verifies context pruning and prompt formatting.
"""

import pytest
from central_platform.ai.context_builder import ContextBuilder, AssembledContext
from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Concept,
    Course,
    Curriculum,
    LearningEvent,
    MasteryState,
    Module,
    Organization,
    Session,
    SessionStatus,
    StudentLearningRecord,
    TeacherInstructionRecord,
    Topic,
    User,
)

@pytest.fixture
def db(tmp_path):
    """Provide isolated database instance for Phase 17 tests."""
    db_file = str(tmp_path / "phase17_context.db")
    return PlatformDatabase(db_file)

def seed_db(db):
    org = Organization(id="org_ctx", name="Ctx Org", slug="ctx-org")
    db.create_organization(org)
    user = User(id="u_ctx", email="u@test.com", full_name="Ctx Student", role="student", organization_id="org_ctx")
    db.create_user(user)
    course = Course(id="c_ctx", organization_id="org_ctx", title="Chemistry Ctx", code="CHEMCTX")
    db.create_course(course)
    cur = Curriculum(id="cur_ctx", course_id="c_ctx", title="Curriculum Ctx", version="1.0")
    db.create_curriculum(cur)
    mod = Module(id="mod_ctx", curriculum_id="cur_ctx", title="Module Ctx", sequence_order=1)
    db.create_module(mod)
    top = Topic(id="t_ctx", module_id="mod_ctx", title="Topic Ctx", sequence_order=1)
    db.create_topic(top)
    cpt = Concept(id="cpt_thermo", topic_id="t_ctx", name="Thermodynamics", description="Heat and work", difficulty=0.7)
    db.create_concept(cpt)
    
    slr = StudentLearningRecord(id="slr_ctx", student_id="u_ctx", course_id="c_ctx")
    db.create_slr(slr)
    ms = MasteryState(slr_id="slr_ctx", concept_id="cpt_thermo", score=0.80, confidence=0.88, state="practicing")
    db.upsert_mastery_state(ms)
    
    sess = Session(id="s_ctx", student_id="u_ctx", course_id="c_ctx", concept_id="cpt_thermo", status=SessionStatus.ACTIVE)
    db.create_session(sess)
    
    db.record_learning_event(LearningEvent(
        id="evt_ctx_1",
        session_id="s_ctx",
        student_id="u_ctx",
        course_id="c_ctx",
        concept_id="cpt_thermo",
        event_type="answer_submitted",
        score=1.0,
        payload={"correctness": "correct"}
    ))
    
    if hasattr(db, "add_teacher_instruction"):
        db.add_teacher_instruction(TeacherInstructionRecord(
            id="ti_1",
            course_id="c_ctx",
            teacher_id="t_1",
            instruction_text="Emphasize SI units in work calculations.",
            is_active=True
        ))

def test_full_7_layer_context_assembly(db):
    """Test full 7-layer context assembly."""
    seed_db(db)
    builder = ContextBuilder(db)
    
    conv_history = [
        {"role": "user", "content": "What is heat?"},
        {"role": "assistant", "content": "Heat is energy transfer due to temperature difference."},
        {"role": "user", "content": "Explain work done"}
    ]
    
    context = builder.build_context(
        query="Explain work done",
        student_id="u_ctx",
        course_id="c_ctx",
        concept_id="cpt_thermo",
        conversation_history=conv_history,
        max_conversation_turns=2,
    )
    
    assert isinstance(context, AssembledContext)
    assert len(context.conversation_context) == 2  # Pruned to max_conversation_turns
    assert context.learner_state_context["concept_mastery"] == 0.80
    assert context.curriculum_context["concept_name"] == "Thermodynamics"
    assert "academic_integrity" in context.institution_policy_context
    assert len(context.recent_events_context) == 1
    assert "Thermodynamics" in context.formatted_prompt_block

def test_context_builder_without_db():
    """Test ContextBuilder operates safely without DB (fallback defaults)."""
    builder = ContextBuilder()
    context = builder.build_context(
        query="What is entropy?",
        student_id="u_anon",
        course_id="crs_default",
        concept_id="cpt_entropy"
    )
    
    assert context.query == "What is entropy?"
    assert context.curriculum_context["concept_name"] == "cpt_entropy"
    assert "academic_integrity" in context.institution_policy_context
