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
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.learning.graph import LearningGraph
from central_platform.learning.state import LearningStateManager
from central_platform.rag.service import RAGService

logger = logging.getLogger("gayatri.context_builder")


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
    ) -> AssembledContext:
        """Build clean 7-layer context while pruning irrelevant data."""
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

        # 4. Teacher Instructions Context
        teacher_instructions: List[str] = []
        if self.db and hasattr(self.db, "get_teacher_instructions_for_course"):
            records = self.db.get_teacher_instructions_for_course(course_id)
            teacher_instructions = [
                r.instruction_text for r in records if getattr(r, "is_active", True)
            ]

        # 5. Institution Policy Context
        institution_policy: Dict[str, Any] = {
            "academic_integrity": "Do not provide direct raw answers on assessment questions without pedagogical steps.",
            "safety_policy": "Strict prohibition of dangerous chemical synthesis instructions or weapons material.",
            "tone": "Socratic, encouraging, and clear.",
        }

        # 6. RAG Retrieval Context
        rag_chunks: List[Dict[str, Any]] = []
        if self.rag_service:
            try:
                query_res = self.rag_service.query(query_text=query, course_id=course_id)
                results = query_res.get("results", [])
                for item in results[:max_rag_chunks]:
                    rag_chunks.append({
                        "source_title": item.get("source_title", "Course Material"),
                        "text": item.get("text", ""),
                        "citation": item.get("citation", ""),
                    })
            except Exception as exc:
                logger.warning(f"RAG retrieval skipped during context building: {exc}")

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
            formatted_prompt_block=formatted_block,
        )

    @staticmethod
    def build_system_prompt(
        base_prompt: Optional[str] = None,
        teacher_directives: Optional[List[str]] = None,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
    ) -> str:
        """Build enriched system prompt combining base prompt, subject scope, and teacher directives."""
        prompt = base_prompt or "You are Gayatri AI, an authoritative Socratic academic and STEM tutor."
        if subject:
            prompt = f"{prompt}\n\nSUBJECT SCOPE: {subject}"
        if grade_level:
            prompt = f"{prompt}\n\nGRADE LEVEL: {grade_level}"
        if teacher_directives:
            directives_block = "\n".join(f"- {d}" for d in teacher_directives)
            prompt = f"{prompt}\n\nACTIVE TEACHER DIRECTIVES:\n{directives_block}"
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
                rag_text = "\n".join(
                    f"- [{item.get('source_title', 'Material')}] {item.get('text', str(item))}"
                    if isinstance(item, dict) else f"- {str(item)}"
                    for item in rag_context
                )
            else:
                rag_text = str(rag_context)

            if rag_text.startswith("<"):
                blocks.append(rag_text)
            else:
                blocks.append(f"[Reference Context]\n{rag_text}")

        blocks.append(f"Student Query: {user_query}")
        return "\n\n".join(blocks)
