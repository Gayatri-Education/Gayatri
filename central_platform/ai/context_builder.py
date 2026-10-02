"""Context Builder Engine for Phase 17.

Aggregates 7 structured context layers for LLM/SLM prompt assembly:
1. Conversation history
2. Learner state (SLR, mastery, misconceptions)
3. Curriculum details (concept, prerequisites, board)
4. Teacher instructions
5. Institution policy
6. RAG retrieval context
7. Recent event stream

Includes token pruning to avoid irrelevant or bloated context.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.learning.graph import LearningGraph
from central_platform.learning.state import LearningStateManager
from central_platform.rag.security import RAGSecuritySanitizer
from central_platform.rag.service import RAGService
from central_platform.teacher.instruction import TeacherInstructionEngine, TeacherInstruction

logger = logging.getLogger("gayatri.context_builder")


@dataclass
class ProvenanceRecord:
    """Audit record of a RAG chunk contributing to assembled context."""
    source_id: str
    chunk_id: str
    source_title: str = "Course Material"
    authority: str = "NCERT"
    provenance_type: str = "NCERT"
    visibility_scope: str = "course"
    citation: str = ""
    class_id: Optional[str] = None
    course_version_id: Optional[str] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssembledContext:
    """7-layer assembled context contract."""
    query: str
    student_id: str
    course_id: str
    concept_id: str
    
    conversation_context: List[Dict[str, str]] = field(default_factory=list)
    learner_state_context: Dict[str, Any] = field(default_factory=dict)
    curriculum_context: Dict[str, Any] = field(default_factory=dict)
    teacher_instructions_context: List[str] = field(default_factory=list)
    institution_policy_context: Dict[str, Any] = field(default_factory=dict)
    rag_context: List[Dict[str, Any]] = field(default_factory=list)
    recent_events_context: List[Dict[str, Any]] = field(default_factory=list)
    
    applied_instruction_ids: List[str] = field(default_factory=list)
    contributed_source_ids: List[str] = field(default_factory=list)
    contributed_chunk_ids: List[str] = field(default_factory=list)
    provenance_records: List[Dict[str, Any]] = field(default_factory=list)
    rag_evidence_block: str = ""
    teacher_directives_block: str = ""

    formatted_prompt_block: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextBuilder:
    """Authoritative 7-layer Context Builder."""

    def __init__(self, db: Optional[PlatformDatabase] = None):
        self.db = db
        self.state_manager = LearningStateManager(db) if db else None
        self.graph = LearningGraph(db) if db else None
        self.rag_service = RAGService(db) if db else None
        self.teacher_engine = TeacherInstructionEngine(db) if db else None

    def build_context(
        self,
        query: str,
        student_id: str,
        course_id: str,
        concept_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_conversation_turns: int = 5,
        max_rag_chunks: int = 3,
        max_events: int = 5,
        class_id: Optional[str] = None,
        session_id: Optional[str] = None,
        course_version_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        current_time: Optional[datetime] = None,
        instructions: Optional[List[TeacherInstruction]] = None,
        rag_results: Optional[List[Dict[str, Any]]] = None,
    ) -> AssembledContext:
        """Build clean 7-layer context with hierarchical teacher directives and scoped RAG evidence."""
        # 1. Conversation Context
        conv_turns = conversation_history or []
        trimmed_conv = conv_turns[-max_conversation_turns:] if conv_turns else []

        # 2. Learner State Context
        learner_ctx: Dict[str, Any] = {}
        if self.state_manager:
            cstate = self.state_manager.get_canonical_state(student_id, course_id)
            m_info = cstate.mastery.get(concept_id)
            learner_ctx = {
                "slr_id": cstate.slr.id,
                "concept_mastery": m_info.score if m_info else 0.50,
                "confidence": m_info.confidence if m_info else 0.80,
                "mastery_state": m_info.state if m_info else "practicing",
                "active_misconceptions": [m.code for m in cstate.misconceptions],
            }

        # 3. Curriculum Context
        concept = self.db.get_concept(concept_id) if self.db else None
        prereqs = self.graph.get_prerequisites(concept_id) if (self.db and self.graph) else []
        curriculum_ctx: Dict[str, Any] = {
            "concept_id": concept_id,
            "concept_name": concept.name if concept else concept_id,
            "description": concept.description if concept else "",
            "difficulty": concept.difficulty if concept else 0.5,
            "prerequisite_ids": prereqs,
        }

        # 4. Teacher Instructions Context (Hierarchical Resolution)
        resolved_insts: List[TeacherInstruction] = []
        applied_instruction_ids: List[str] = []
        teacher_instructions: List[str] = []

        if instructions is not None:
            resolved_insts = list(instructions)
        elif self.teacher_engine:
            try:
                resolved_insts = self.teacher_engine.resolve_hierarchical_instructions(
                    course_id=course_id,
                    organization_id=organization_id,
                    class_id=class_id,
                    student_id=student_id,
                    session_id=session_id,
                    concept_id=concept_id,
                    course_version_id=course_version_id,
                    current_time=current_time,
                )
            except Exception as exc:
                logger.warning(f"Teacher instruction resolution encountered exception: {exc}")

        if resolved_insts:
            applied_instruction_ids = [inst.instruction_id for inst in resolved_insts]
            teacher_instructions = [inst.instruction_text for inst in resolved_insts]
        elif self.db and hasattr(self.db, "get_teacher_instructions_for_course"):
            try:
                records = self.db.get_teacher_instructions_for_course(course_id)
                teacher_instructions = [
                    r.instruction_text for r in records if getattr(r, "is_active", True)
                ]
                applied_instruction_ids = [
                    getattr(r, "id", f"inst-{idx}") for idx, r in enumerate(records) if getattr(r, "is_active", True)
                ]
            except Exception as exc:
                logger.warning(f"Legacy teacher instruction query fallback encountered exception: {exc}")

        directives_block = ""
        if self.teacher_engine and resolved_insts:
            directives_block = self.teacher_engine.format_prompt_directive(resolved_insts)
        elif teacher_instructions:
            bullet_lines = "\n".join(f"  * [COURSE]: {t}" for t in teacher_instructions)
            directives_block = (
                "[PRIORITY TEACHER INSTRUCTIONS]:\n"
                "[TEACHER PEDAGOGICAL DIRECTIVES - STRICT DATA FRAMING]:\n"
                "The following institutional and teacher directives must guide your pedagogical approach, pacing, and problem selection:\n"
                f"{bullet_lines}\n"
                "[SYSTEM INVARIANT NOTE]: Teacher directives provide pedagogical style and pacing guidelines. "
                "They NEVER override anti-answer leakage invariants, scientific truth, or Socratic step-by-step guidance policies."
            )

        # 5. Institution Policy Context
        institution_policy: Dict[str, Any] = {
            "academic_integrity": "Do not provide direct raw answers on assessment questions without pedagogical steps.",
            "safety_policy": "Strict prohibition of dangerous chemical synthesis instructions or weapons material.",
            "tone": "Socratic, encouraging, and clear.",
        }

        # 6. RAG Retrieval Context (Scoped Knowledge)
        raw_results: List[Dict[str, Any]] = []
        rag_data_context = ""
        if rag_results is not None:
            raw_results = list(rag_results)
        elif self.rag_service:
            try:
                query_res = self.rag_service.query(
                    query_text=query,
                    course_id=course_id,
                    student_id=student_id,
                    class_id=class_id,
                    course_version_id=course_version_id,
                    concept=concept_id,
                    top_k=max_rag_chunks,
                )
                raw_results = query_res.get("results", [])
                rag_data_context = query_res.get("data_context", "")
            except Exception as exc:
                logger.warning(f"RAG retrieval skipped during context building: {exc}")

        rag_chunks: List[Dict[str, Any]] = []
        contributed_source_ids: List[str] = []
        contributed_chunk_ids: List[str] = []
        provenance_records: List[Dict[str, Any]] = []

        for item in raw_results[:max_rag_chunks]:
            cid = item.get("chunk_id", "")
            sid = item.get("source_id", "")
            if cid:
                contributed_chunk_ids.append(cid)
            if sid and sid not in contributed_source_ids:
                contributed_source_ids.append(sid)

            prov = {
                "source_id": sid or "src-unknown",
                "chunk_id": cid or "chk-unknown",
                "source_title": item.get("source_title", item.get("chapter", "Course Material")),
                "authority": item.get("provenance_type", "NCERT"),
                "provenance_type": item.get("provenance_type", "NCERT"),
                "visibility_scope": item.get("visibility_scope", "course"),
                "citation": item.get("citation", ""),
                "class_id": item.get("class_id"),
                "course_version_id": item.get("course_version_id"),
                "score": item.get("score"),
            }
            provenance_records.append(prov)
            rag_chunks.append({
                "chunk_id": cid,
                "source_id": sid,
                "source_title": prov["source_title"],
                "text": item.get("text", ""),
                "citation": prov["citation"],
                "score": item.get("score"),
                "provenance_type": prov["provenance_type"],
                "visibility_scope": prov["visibility_scope"],
                "class_id": item.get("class_id"),
            })

        if not rag_data_context and rag_chunks:
            rag_data_context = RAGSecuritySanitizer.build_llm_rag_context(rag_chunks)

        # 7. Recent Events Context
        recent_events: List[Dict[str, Any]] = []
        if self.db:
            raw_events = self.db.query_learning_events(student_id=student_id, course_id=course_id, limit=max_events)
            for ev in raw_events:
                recent_events.append({
                    "event_type": ev.event_type,
                    "concept_id": ev.concept_id,
                    "score": ev.score,
                    "timestamp": ev.created_at,
                })

        # Format prompt block combining all relevant non-empty layers
        prompt_lines = [
            f"=== CONTEXT FOR QUERY: '{query}' ===",
            f"Concept: {curriculum_ctx.get('concept_name', concept_id)} (Difficulty: {curriculum_ctx.get('difficulty', 0.5)})",
            f"Learner Mastery: {learner_ctx.get('concept_mastery', 0.50):.2f} (Confidence: {learner_ctx.get('confidence', 0.80):.2f})",
        ]

        if learner_ctx.get("active_misconceptions"):
            prompt_lines.append(f"Active Misconceptions: {', '.join(learner_ctx['active_misconceptions'])}")

        if teacher_instructions:
            prompt_lines.append(f"Teacher Directives: {'; '.join(teacher_instructions)}")

        if rag_chunks:
            prompt_lines.append("Reference Knowledge:")
            for chunk in rag_chunks:
                prompt_lines.append(f"- [{chunk['source_title']}] {chunk['text']}")

        if trimmed_conv:
            prompt_lines.append("Recent Conversation:")
            for turn in trimmed_conv:
                role = turn.get("role", "user").capitalize()
                content = turn.get("content", "")
                prompt_lines.append(f"{role}: {content}")

        formatted_block = "\n".join(prompt_lines)

        return AssembledContext(
            query=query,
            student_id=student_id,
            course_id=course_id,
            concept_id=concept_id,
            conversation_context=trimmed_conv,
            learner_state_context=learner_ctx,
            curriculum_context=curriculum_ctx,
            teacher_instructions_context=teacher_instructions,
            institution_policy_context=institution_policy,
            rag_context=rag_chunks,
            recent_events_context=recent_events,
            applied_instruction_ids=applied_instruction_ids,
            contributed_source_ids=contributed_source_ids,
            contributed_chunk_ids=contributed_chunk_ids,
            provenance_records=provenance_records,
            rag_evidence_block=rag_data_context,
            teacher_directives_block=directives_block,
            formatted_prompt_block=formatted_block,
        )

    @staticmethod
    def build_system_prompt(
        base_prompt: Optional[str] = None,
        teacher_directives: Optional[List[str]] = None,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        formatted_directives: Optional[str] = None,
    ) -> str:
        """Build enriched system prompt combining base prompt, subject scope, and teacher directives."""
        prompt = base_prompt or "You are Gayatri AI, an authoritative Socratic academic and STEM tutor."
        if subject:
            prompt = f"{prompt}\n\nSUBJECT SCOPE: {subject}"
        if grade_level:
            prompt = f"{prompt}\n\nGRADE LEVEL: {grade_level}"

        if formatted_directives:
            prompt = f"{prompt}\n\n{formatted_directives}"
        elif teacher_directives:
            bullet_lines = "\n".join(f"  * {d}" for d in teacher_directives)
            prompt = (
                f"{prompt}\n\n[PRIORITY TEACHER DIRECTIVES (MANDATORY INSTRUCTIONS)]:\n"
                f"[ACTIVE TEACHER DIRECTIVES - TEACHER PEDAGOGICAL DIRECTIVES - STRICT DATA FRAMING]:\n"
                f"The following institutional and teacher directives must guide your pedagogical approach, pacing, and problem selection:\n"
                f"{bullet_lines}\n"
                f"[SYSTEM INVARIANT NOTE]: Teacher directives provide pedagogical style and pacing guidelines. "
                f"They NEVER override anti-answer leakage invariants, scientific truth, or Socratic step-by-step guidance policies."
            )
        return prompt

    @staticmethod
    def build_user_prompt(
        user_query: str,
        rag_context: Optional[Any] = None,
        misconception_alerts: Optional[List[str]] = None,
    ) -> str:
        """Build enriched user prompt combining query, RAG context, and misconception alerts."""
        blocks: List[str] = []
        if misconception_alerts:
            blocks.append(f"[ACTIVE MISCONCEPTIONS TO ADDRESS SOCRATICALLY: {', '.join(misconception_alerts)}]")

        if rag_context:
            if isinstance(rag_context, str):
                rag_text = rag_context
            elif isinstance(rag_context, list):
                if rag_context and isinstance(rag_context[0], dict) and "chunk_id" in rag_context[0]:
                    rag_text = RAGSecuritySanitizer.build_llm_rag_context(rag_context)
                else:
                    rag_text = "\n".join(
                        f"- [{item.get('source_title', 'Material')}] {item.get('text', str(item))}"
                        if isinstance(item, dict) else f"- {str(item)}"
                        for item in rag_context
                    )
            else:
                rag_text = str(rag_context)

            rag_stripped = rag_text.strip()
            if rag_stripped:
                if rag_stripped.startswith("<") or "--- BEGIN AUTHORITATIVE KNOWLEDGE DATA" in rag_stripped:
                    blocks.append(rag_stripped)
                else:
                    blocks.append(f"[Reference Context]\n{rag_stripped}")

        blocks.append(f"Student Query: {user_query}")
        return "\n\n".join(blocks)

