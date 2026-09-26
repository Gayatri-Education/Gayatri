"""Unit test suite for Teacher Instruction Engine (Phase 7)."""

import pytest
from central_platform.teacher.instruction import (
    TeacherInstruction,
    TeacherInstructionEngine,
)


def test_teacher_instruction_scoping_and_priority():
    engine = TeacherInstructionEngine()

    inst1 = TeacherInstruction(
        instruction_id="inst_1",
        teacher_id="t_1",
        student_id="s_1",
        course_id="c_math",
        instruction_text="Explain algebra visually.",
        priority=1,
    )
    inst2 = TeacherInstruction(
        instruction_id="inst_2",
        teacher_id="t_1",
        student_id="s_1",
        course_id="c_math",
        instruction_text="Require student to write steps.",
        priority=10,  # Higher priority
    )

    engine.add_instruction(inst1)
    engine.add_instruction(inst2)

    active_s1 = engine.get_instructions_for_student("s_1", "c_math")
    assert len(active_s1) == 2
    assert active_s1[0].instruction_id == "inst_2"  # Priority 10 first

    # Test scope isolation: Student s_2 gets zero instructions
    active_s2 = engine.get_instructions_for_student("s_2", "c_math")
    assert len(active_s2) == 0


def test_disable_teacher_instruction():
    engine = TeacherInstructionEngine()
    inst = TeacherInstruction("inst_10", "t_1", "s_1", "c_math", "Focus on mental math.")
    engine.add_instruction(inst)

    assert len(engine.get_instructions_for_student("s_1", "c_math")) == 1
    engine.disable_instruction("inst_10")
    assert len(engine.get_instructions_for_student("s_1", "c_math")) == 0
