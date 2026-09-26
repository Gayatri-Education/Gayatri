"""Teacher Instruction Engine with versioning, priority, and scope isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class TeacherInstruction:
    instruction_id: str
    teacher_id: str
    student_id: str
    course_id: str
    instruction_text: str
    concept_scope: Optional[str] = None
    priority: int = 1  # Higher priority overrides lower
    is_active: bool = True
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TeacherInstructionEngine:
    """Manages persistent teacher instructions and resolves active context per student."""

    def __init__(self):
        self._instructions: dict[str, TeacherInstruction] = {}

    def add_instruction(self, instruction: TeacherInstruction) -> TeacherInstruction:
        self._instructions[instruction.instruction_id] = instruction
        return instruction

    def get_instructions_for_student(
        self, student_id: str, course_id: str, concept_id: Optional[str] = None
    ) -> List[TeacherInstruction]:
        active = []
        for inst in self._instructions.values():
            if not inst.is_active:
                continue
            if inst.student_id != student_id or inst.course_id != course_id:
                continue
            if inst.concept_scope and concept_id and inst.concept_scope != concept_id:
                continue
            active.append(inst)

        return sorted(active, key=lambda x: x.priority, reverse=True)

    def disable_instruction(self, instruction_id: str) -> bool:
        if instruction_id in self._instructions:
            self._instructions[instruction_id].is_active = False
            return True
        return False
