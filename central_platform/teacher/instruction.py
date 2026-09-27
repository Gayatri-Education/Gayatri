"""Teacher Instruction Engine with versioning, priority, scope isolation, temporal validity, and policy validation.

Implements Master Plan Section 20 (Phase 11):
- Scope: student, cohort, course, concept
- Priority hierarchies (1=Low to 5=Urgent)
- Temporal bounds: start_at, expires_at
- Status lifecycle: ACTIVE, EXPIRED, REVOKED, DRAFT
- Immutable audit trail tracking
- Policy validation enforcing non-negotiable invariants:
  1. Security (prompt injection, jailbreak, system prompt reveal)
  2. Safety (toxicity, abuse, slurs)
  3. System Policy (anti-answer leakage, pedagogical steps)
  4. Authorization (privilege escalation, data harvesting)
  5. Deterministic Calculations (overriding math/science truths, forced mastery)
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class InstructionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    DRAFT = "DRAFT"


class SafetyStatus(str, Enum):
    VALIDATED = "VALIDATED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class ScopeType(str, Enum):
    STUDENT = "STUDENT"
    COHORT = "COHORT"
    COURSE = "COURSE"
    CONCEPT = "CONCEPT"


@dataclass
class ValidationResult:
    is_valid: bool
    safety_status: str
    violations: List[str] = field(default_factory=list)
    sanitized_text: str = ""
    target_invariants: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class TeacherInstructionValidator:
    """Enforces non-overridable system invariants on teacher instruction directives."""

    # Invariant 1: Security & Injection Protection
    SECURITY_PATTERNS = [
        re.compile(r"\b(?:ignore|disregard|forget|bypass|override)\s+(?:all\s+)?(?:previous|prior|above|system)?\s*(?:instructions?|directives?|rules?|prompts?)\b", re.IGNORECASE),
        re.compile(r"\b(?:you\s+are\s+now|act\s+as)\s+(?:dan|unrestricted|developer\s+mode|jailbreak|root|admin)\b", re.IGNORECASE),
        re.compile(r"<\|(?:im_start|im_end|endoftext)\|>", re.IGNORECASE),
        re.compile(r"\[\/?INST\]", re.IGNORECASE),
        re.compile(r"\b(?:reveal|show|dump|print)\s+(?:system\s+prompt|hidden\s+prompt|developer\s+instructions)\b", re.IGNORECASE),
        re.compile(r"\b(?:eval|exec)\s*\(|__import__|os\.system", re.IGNORECASE),
    ]

    # Invariant 2: Safety & Toxicity
    SAFETY_PATTERNS = [
        re.compile(r"\b(?:hate|kill\s+yourself|die|stupid\s+idiot|retarded|kys)\b", re.IGNORECASE),
    ]

    # Invariant 3: System Policy & Anti-Answer Leakage
    POLICY_PATTERNS = [
        re.compile(r"\b(?:give|provide|reveal|tell|share|feed)\s+(?:the\s+)?(?:direct\s+)?answers?\s+(?:directly|immediately|without|straight\s+away)\b", re.IGNORECASE),
        re.compile(r"\b(?:just\s+give|only\s+give)\s+(?:the\s+)?(?:direct\s+)?answers?\b", re.IGNORECASE),
        re.compile(r"\b(?:give|tell)\s+(?:the\s+student|them|him|her|[a-z0-9_-]+)\s+(?:all\s+)?(?:the\s+)?(?:answers?|solutions?)\b", re.IGNORECASE),
        re.compile(r"\b(?:skip|bypass|stop)\s+(?:the\s+)?(?:questions?|questioning|steps?|explanations?|pedagogy|socratic)\s+and\s+(?:give|provide|tell)\s+(?:the\s+)?(?:answer|solution)\b", re.IGNORECASE),
        re.compile(r"\b(?:reveal|show)\s+(?:the\s+)?(?:solution|answers?)\s+(?:upfront|immediately|without\s+asking)\b", re.IGNORECASE),
        re.compile(r"\b(?:bypass|disable|turn\s+off)\s+(?:anti-leak|anti-answer|pedagogical\s+guardrails?|tutor\s+policy)\b", re.IGNORECASE),
        re.compile(r"\bdo\s+not\s+guide,\s*just\s+answer\b", re.IGNORECASE),
        re.compile(r"\bgive\s+them\s+100%\s+on\s+the\s+quiz\s+without\s+answering\b", re.IGNORECASE),
    ]

    # Invariant 4: Authorization & Privilege Escalation
    AUTH_PATTERNS = [
        re.compile(r"\b(?:grant|elevate|assume|claim)\s+(?:admin|superuser|developer|owner)\s+(?:role|privileges?|rights?|access)\b", re.IGNORECASE),
        re.compile(r"\b(?:dump|reveal|show|access)\s+(?:other\s+students?['’]?\s+)?(?:passwords?|credentials?|private\s+keys?|tokens?|secrets?)\b", re.IGNORECASE),
        re.compile(r"\b(?:drop\s+table|delete\s+from\s+users|select\s+\*\s+from\s+users)\b", re.IGNORECASE),
    ]

    # Invariant 5: Deterministic Calculations & Fact Truth
    CALC_PATTERNS = [
        re.compile(r"\b(?:force|set|overwrite)\s+(?:mastery|score|grade|rating)(?:\s+(?:score|level|value|state))?\s+(?:to\s+)?(?:100%|1\.0|100|max)\b", re.IGNORECASE),
        re.compile(r"\b(?:mark|grade)\s+(?:every|all)\s+(?:answers?|responses?)\s+(?:as\s+)?(?:correct|right|100%)\b", re.IGNORECASE),
        re.compile(r"\b(?:tell\s+them|teach\s+that)\s+(?:2\s*\+\s*2\s*=\s*5|water\s+is\s+ho\b|carbon\s+has\s+2\s+valence\s+electrons)\b", re.IGNORECASE),
        re.compile(r"\b(?:ignore|override|disable)\s+(?:stoichiometry|molar\s+mass|reaction\s+balance|conservation\s+of\s+mass)\b", re.IGNORECASE),
    ]

    @classmethod
    def validate(cls, text: str) -> ValidationResult:
        """Validate an instruction string against all 5 non-negotiable invariants."""
        if not text or not text.strip():
            return ValidationResult(
                is_valid=False,
                safety_status=SafetyStatus.REJECTED.value,
                violations=["EMPTY_INSTRUCTION: Instruction text cannot be empty."],
                sanitized_text="",
                target_invariants=["system_policy"],
            )

        sanitized = text.strip()
        violations: List[str] = []
        target_invariants: List[str] = []

        # Check Invariant 1: Security
        for pat in cls.SECURITY_PATTERNS:
            if pat.search(sanitized):
                violations.append("INVARIANT_VIOLATION_SECURITY: Directives cannot override system security, prompt boundaries, or execute code.")
                target_invariants.append("security")
                break

        # Check Invariant 2: Safety
        for pat in cls.SAFETY_PATTERNS:
            if pat.search(sanitized):
                violations.append("INVARIANT_VIOLATION_SAFETY: Directives must not contain abusive, harmful, or toxic language.")
                target_invariants.append("safety")
                break

        # Check Invariant 3: System Policy / Anti-Answer Leakage
        for pat in cls.POLICY_PATTERNS:
            if pat.search(sanitized):
                violations.append("INVARIANT_VIOLATION_POLICY: Directives cannot order the tutor to leak answers directly or bypass Socratic step-by-step guidance.")
                target_invariants.append("system_policy")
                break

        # Check Invariant 4: Authorization
        for pat in cls.AUTH_PATTERNS:
            if pat.search(sanitized):
                violations.append("INVARIANT_VIOLATION_AUTHORIZATION: Directives cannot escalate privileges or access unauthorized student credentials.")
                target_invariants.append("authorization")
                break

        # Check Invariant 5: Deterministic Calculations
        for pat in cls.CALC_PATTERNS:
            if pat.search(sanitized):
                violations.append("INVARIANT_VIOLATION_CALCULATIONS: Directives cannot override deterministic facts, scientific calculations, or mastery models.")
                target_invariants.append("deterministic_calculations")
                break

        if violations:
            return ValidationResult(
                is_valid=False,
                safety_status=SafetyStatus.REJECTED.value,
                violations=violations,
                sanitized_text=sanitized,
                target_invariants=list(set(target_invariants)),
            )

        return ValidationResult(
            is_valid=True,
            safety_status=SafetyStatus.VALIDATED.value,
            violations=[],
            sanitized_text=sanitized,
            target_invariants=[],
        )


@dataclass
class TeacherInstruction:
    """Canonical Teacher Instruction entity with full Section 20 fields."""

    instruction_id: str
    teacher_id: str
    student_id: str = "all"
    course_id: str = "crs-chem-101"
    instruction_text: str = ""
    concept_scope: Optional[str] = "ALL"
    scope_type: str = "STUDENT"
    priority: int = 2  # 1=Low, 2=Normal, 3=High, 4=Urgent
    start_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    status: str = InstructionStatus.ACTIVE.value
    is_active: bool = True  # Backwards compatibility with boolean flag
    safety_status: str = SafetyStatus.VALIDATED.value
    safety_reasons: List[str] = field(default_factory=list)
    audit_trail: List[dict] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    def __post_init__(self):
        # Auto-infer scope type if default
        if self.student_id in ("all", "*", ""):
            if self.concept_scope and self.concept_scope not in ("ALL", "*"):
                self.scope_type = ScopeType.CONCEPT.value
            else:
                self.scope_type = ScopeType.COURSE.value
        elif self.concept_scope and self.concept_scope not in ("ALL", "*"):
            self.scope_type = ScopeType.CONCEPT.value
        else:
            self.scope_type = ScopeType.STUDENT.value

        # Keep status and is_active synchronized
        if not self.is_active and self.status == InstructionStatus.ACTIVE.value:
            self.status = InstructionStatus.REVOKED.value
        elif self.status == InstructionStatus.ACTIVE.value:
            self.is_active = True
        else:
            self.is_active = False

        # Seed initial audit event if empty
        if not self.audit_trail:
            self.audit_trail = [
                {
                    "action": "created",
                    "actor_id": self.teacher_id,
                    "timestamp": self.created_at,
                    "details": "Instruction initialized",
                }
            ]

    def to_dict(self) -> dict:
        return asdict(self)


class TeacherInstructionEngine:
    """Manages persistent teacher instructions, validation, audit trails, and student resolution."""

    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self._instructions: dict[str, TeacherInstruction] = {}

    def validate_instruction_text(self, text: str) -> ValidationResult:
        """Run policy validation against text."""
        return TeacherInstructionValidator.validate(text)

    def add_instruction(
        self,
        instruction: TeacherInstruction,
        actor_id: Optional[str] = None,
        strict_validation: bool = True,
    ) -> TeacherInstruction:
        """Validate, record audit trail, and persist a teacher instruction."""
        val = TeacherInstructionValidator.validate(instruction.instruction_text)
        instruction.safety_status = val.safety_status
        instruction.safety_reasons = val.violations

        if not val.is_valid and strict_validation:
            raise ValueError(f"Policy validation failed: {'; '.join(val.violations)}")

        # Append audit entry
        actor = actor_id or instruction.teacher_id
        instruction.audit_trail.append({
            "action": "registered",
            "actor_id": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "safety_status": instruction.safety_status,
            "details": "Added to active registry",
        })

        self._instructions[instruction.instruction_id] = instruction

        if self.db and hasattr(self.db, "create_teacher_instruction"):
            try:
                from central_platform.models.schema import TeacherInstructionRecord
                rec = TeacherInstructionRecord(
                    id=instruction.instruction_id,
                    teacher_id=instruction.teacher_id,
                    student_id=instruction.student_id,
                    course_id=instruction.course_id,
                    instruction_text=instruction.instruction_text,
                    concept_scope=instruction.concept_scope or "ALL",
                    priority=instruction.priority,
                    is_active=instruction.is_active,
                    created_at=instruction.created_at,
                )
                self.db.create_teacher_instruction(rec)
            except Exception:
                pass

        return instruction

    def get_instruction(self, instruction_id: str) -> Optional[TeacherInstruction]:
        """Fetch a single instruction by ID."""
        return self._instructions.get(instruction_id)

    def _is_temporally_valid(self, inst: TeacherInstruction, current_time: datetime) -> bool:
        """Evaluate start_at and expires_at timestamps."""
        try:
            if inst.start_at:
                start_dt = datetime.fromisoformat(inst.start_at.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                if current_time < start_dt:
                    return False

            if inst.expires_at:
                exp_dt = datetime.fromisoformat(inst.expires_at.replace("Z", "+00:00"))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if current_time > exp_dt:
                    # Mark expired
                    inst.status = InstructionStatus.EXPIRED.value
                    inst.is_active = False
                    return False
        except Exception:
            return True

        return True

    def get_instructions_for_student(
        self,
        student_id: str,
        course_id: str,
        concept_id: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> List[TeacherInstruction]:
        """Resolve active, validated, and non-expired instructions applicable to a student."""
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        active = []
        for inst in self._instructions.values():
            # Must be active and validated
            if not inst.is_active or inst.status != InstructionStatus.ACTIVE.value:
                continue
            if inst.safety_status != SafetyStatus.VALIDATED.value:
                continue

            # Temporal validity check
            if not self._is_temporally_valid(inst, now):
                continue

            # Course filter
            if course_id and inst.course_id and inst.course_id not in (course_id, "all", "*"):
                continue

            # Student scope filter
            if inst.student_id not in (student_id, "all", "*", ""):
                continue

            # Concept scope filter
            if inst.concept_scope and concept_id and inst.concept_scope not in ("ALL", "*", concept_id):
                continue

            active.append(inst)

        return sorted(active, key=lambda x: (x.priority, x.created_at), reverse=True)

    def update_instruction(
        self,
        instruction_id: str,
        actor_id: str,
        updates: Dict[str, Any],
    ) -> Optional[TeacherInstruction]:
        """Update instruction attributes and record an audit log."""
        inst = self._instructions.get(instruction_id)
        if not inst:
            return None

        now = datetime.now(timezone.utc).isoformat()
        old_data = {"priority": inst.priority, "concept_scope": inst.concept_scope, "status": inst.status}

        if "instruction_text" in updates and updates["instruction_text"] != inst.instruction_text:
            val = TeacherInstructionValidator.validate(updates["instruction_text"])
            if not val.is_valid:
                raise ValueError(f"Updated text violates policy: {'; '.join(val.violations)}")
            inst.instruction_text = val.sanitized_text
            inst.safety_status = val.safety_status
            inst.safety_reasons = val.violations

        if "priority" in updates:
            inst.priority = int(updates["priority"])
        if "concept_scope" in updates:
            inst.concept_scope = updates["concept_scope"]
        if "expires_at" in updates:
            inst.expires_at = updates["expires_at"]
        if "status" in updates:
            inst.status = updates["status"]
            inst.is_active = (inst.status == InstructionStatus.ACTIVE.value)
        if "is_active" in updates:
            inst.is_active = bool(updates["is_active"])
            inst.status = InstructionStatus.ACTIVE.value if inst.is_active else InstructionStatus.REVOKED.value

        inst.version += 1
        inst.updated_at = now
        inst.audit_trail.append({
            "action": "updated",
            "actor_id": actor_id,
            "timestamp": now,
            "changes": {k: updates[k] for k in updates if k in old_data},
            "version": inst.version,
        })

        return inst

    def revoke_instruction(self, instruction_id: str, actor_id: str, reason: str = "") -> bool:
        """Revoke an instruction and record the audit event."""
        inst = self._instructions.get(instruction_id)
        if not inst:
            return False

        now = datetime.now(timezone.utc).isoformat()
        inst.status = InstructionStatus.REVOKED.value
        inst.is_active = False
        inst.updated_at = now
        inst.audit_trail.append({
            "action": "revoked",
            "actor_id": actor_id,
            "timestamp": now,
            "reason": reason or "Teacher revoked instruction",
        })
        return True

    def disable_instruction(self, instruction_id: str) -> bool:
        """Backwards compatible disable."""
        return self.revoke_instruction(instruction_id, actor_id="system", reason="Disabled via legacy call")

    def toggle_instruction(self, instruction_id: str, is_active: Optional[bool] = None) -> bool:
        """Toggle active state."""
        inst = self._instructions.get(instruction_id)
        if not inst:
            return False

        if is_active is not None:
            new_active = is_active
        else:
            new_active = not inst.is_active

        if new_active:
            inst.status = InstructionStatus.ACTIVE.value
            inst.is_active = True
        else:
            inst.status = InstructionStatus.REVOKED.value
            inst.is_active = False

        inst.updated_at = datetime.now(timezone.utc).isoformat()
        inst.audit_trail.append({
            "action": "toggled",
            "actor_id": "teacher",
            "timestamp": inst.updated_at,
            "is_active": inst.is_active,
            "status": inst.status,
        })
        return True

    def delete_instruction(self, instruction_id: str) -> bool:
        """Delete an instruction."""
        if instruction_id in self._instructions:
            del self._instructions[instruction_id]
            return True
        return False

    def get_all_instructions(
        self,
        course_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        active_only: bool = False,
    ) -> List[TeacherInstruction]:
        """Query instructions with multi-criteria filtering."""
        results = []
        for inst in self._instructions.values():
            if active_only and not inst.is_active:
                continue
            if status_filter and inst.status != status_filter:
                continue
            if course_id and inst.course_id not in (course_id, "all", "*"):
                continue
            if student_id and inst.student_id not in (student_id, "all", "*", ""):
                continue
            results.append(inst)

        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def format_prompt_directive(self, instructions: List[TeacherInstruction]) -> str:
        """Format resolved teacher instructions for LLM prompt injection with invariant guardrails."""
        if not instructions:
            return ""

        bullet_lines = "\n".join(f"  * [{inst.scope_type} P{inst.priority}]: {inst.instruction_text}" for inst in instructions)
        return (
            f"[PRIORITY TEACHER INSTRUCTIONS]:\n"
            f"The teacher has provided the following pedagogical guidance which you MUST respect:\n"
            f"{bullet_lines}\n"
            f"[SYSTEM INVARIANT NOTE]: Teacher instructions enhance pedagogical style, pacing, and problem emphasis. "
            f"They NEVER override anti-answer leakage invariants, scientific truth, or Socratic step-by-step guidance policies."
        )
