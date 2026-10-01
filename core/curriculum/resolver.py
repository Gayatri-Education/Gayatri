"""Gayatri AI - Dynamic Concept & Topic Resolver (Generic Course-Independent).

Resolves domain, chapter, topic, subtopic, and stable concept_id from student message,
active session concept state, and course curriculum manifest.
Decouples Chemistry into the ChemistryCurriculumAdapter while supporting arbitrary courses.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.curriculum.chemistry_adapter import (
    CHEMISTRY_CONCEPT_KEYWORD_MAP,
    chemistry_adapter,
)
from core.curriculum.models import GenericConcept, GenericCurriculum, format_concept_id

logger = logging.getLogger("gayatri.curriculum.resolver")


@dataclass
class ResolvedConcept:
    """Resolved active topic/concept metadata across any subject."""
    domain: str
    chapter: str
    topic: str
    subtopic: str
    concept_id: str
    confidence: float

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "chapter": self.chapter,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "concept_id": self.concept_id,
            "confidence": self.confidence,
        }


# Backwards compatibility alias for modules expecting CONCEPT_KEYWORD_MAP
CONCEPT_KEYWORD_MAP = CHEMISTRY_CONCEPT_KEYWORD_MAP


class ConceptResolver:
    """Dynamically resolves active concepts across any registered academic course."""

    _course_curricula: Dict[str, GenericCurriculum] = {}

    @classmethod
    def register_curriculum(cls, course_id: str, curriculum: GenericCurriculum) -> None:
        """Register a curriculum for course-scoped concept resolution."""
        cls._course_curricula[course_id.lower().strip()] = curriculum

    @classmethod
    def get_curriculum(cls, course_id: str) -> Optional[GenericCurriculum]:
        """Fetch registered course curriculum."""
        return cls._course_curricula.get(course_id.lower().strip())

    @classmethod
    def clear_curricula(cls) -> None:
        """Clear registered curricula."""
        cls._course_curricula.clear()

    @classmethod
    def resolve_concept(
        cls,
        user_message: str = "",
        active_concept_id: str = "",
        recent_context: list[str] | None = None,
        student_id: str = "",
        state_manager: object | None = None,
        course_id: str = "",
        **kwargs,
    ) -> ResolvedConcept:
        """Resolve domain, chapter, topic, subtopic, concept_id dynamically.

        Resolution precedence:
        1. Course-scoped resolution if course_id is provided and registered.
        2. Chemistry adapter resolution if course_id is empty or "chemistry" and adapter is enabled.
        3. Active student learning state (from state_manager for student_id).
        4. Safe unknown fallback without hardcoded active learner state.
        """
        clean_msg = (user_message or "").strip().lower()
        c_id_norm = (course_id or "").lower().strip()

        # 1. Course-Scoped Resolution (Physics, History, Programming, Custom Courses)
        if c_id_norm and c_id_norm != "chemistry" and c_id_norm in cls._course_curricula:
            curriculum = cls._course_curricula[c_id_norm]
            return cls._resolve_from_curriculum(
                curriculum=curriculum,
                clean_msg=clean_msg,
                active_concept_id=active_concept_id,
                recent_context=recent_context,
                student_id=student_id,
                state_manager=state_manager,
            )

        # 2. Chemistry Adapter Delegation (Backwards-compatible default)
        if not c_id_norm or c_id_norm == "chemistry":
            if chemistry_adapter.is_enabled:
                match = chemistry_adapter.match_concept(
                    clean_msg=clean_msg,
                    recent_context=recent_context,
                    active_concept_id=active_concept_id,
                )
                if match:
                    return ResolvedConcept(
                        domain=match["domain"],
                        chapter=match["chapter"],
                        topic=match["topic"],
                        subtopic=match["subtopic"],
                        concept_id=match["concept_id"],
                        confidence=match["confidence"],
                    )

                # Check student learning history for chemistry
                if student_id and state_manager:
                    try:
                        events = state_manager.get_learning_events(student_id)
                        if events:
                            last_event = events[-1]
                            for entry in CHEMISTRY_CONCEPT_KEYWORD_MAP:
                                if entry["concept_id"] == last_event.concept_id:
                                    logger.info(f"ConceptResolver: resolved from student learning history '{last_event.concept_id}'")
                                    return ResolvedConcept(
                                        domain=entry["domain"],
                                        chapter=entry["chapter"],
                                        topic=entry["topic"],
                                        subtopic=entry["subtopic"],
                                        concept_id=entry["concept_id"],
                                        confidence=0.6,
                                    )
                    except Exception as s_err:
                        logger.debug(f"ConceptResolver: failed reading student state: {s_err}")

                # Default Chemistry undetermined fallback (preserves test expectations)
                return ResolvedConcept(
                    domain="Undetermined",
                    chapter="Undetermined",
                    topic="General Chemistry",
                    subtopic="General",
                    concept_id="chem_general_undetermined",
                    confidence=0.3,
                )
            else:
                # Chemistry adapter explicitly disabled
                return ResolvedConcept(
                    domain="Undetermined",
                    chapter="Undetermined",
                    topic="General",
                    subtopic="General",
                    concept_id="general_undetermined",
                    confidence=0.3,
                )

        # 3. Non-Chemistry course without registered curriculum fallback
        return ResolvedConcept(
            domain="General",
            chapter="General",
            topic="General",
            subtopic="General",
            concept_id=format_concept_id(c_id_norm, "1.0", "undetermined"),
            confidence=0.3,
        )

    @classmethod
    def _resolve_from_curriculum(
        cls,
        curriculum: GenericCurriculum,
        clean_msg: str,
        active_concept_id: str,
        recent_context: Optional[List[str]],
        student_id: str,
        state_manager: Any,
    ) -> ResolvedConcept:
        """Resolve concept within an arbitrary registered course curriculum."""
        all_concepts = curriculum.all_concepts()

        # 1. Match message against concept keywords, aliases, or names
        if clean_msg:
            for c in all_concepts:
                # Check keywords
                for kw in c.keywords:
                    if kw.lower() in clean_msg:
                        return cls._to_resolved(curriculum, c, confidence=0.9)
                # Check aliases
                for al in c.aliases:
                    if al.lower() in clean_msg:
                        return cls._to_resolved(curriculum, c, confidence=0.9)
                # Check name
                if c.name.lower() in clean_msg:
                    return cls._to_resolved(curriculum, c, confidence=0.85)

        # 2. Check recent context
        if recent_context:
            for ctx_msg in reversed(recent_context):
                ctx_clean = (ctx_msg or "").strip().lower()
                if not ctx_clean:
                    continue
                for c in all_concepts:
                    for kw in c.keywords:
                        if kw.lower() in ctx_clean:
                            return cls._to_resolved(curriculum, c, confidence=0.8)
                    for al in c.aliases:
                        if al.lower() in ctx_clean:
                            return cls._to_resolved(curriculum, c, confidence=0.8)
                    if c.name.lower() in ctx_clean:
                        return cls._to_resolved(curriculum, c, confidence=0.75)

        # 3. Retain active concept ID
        if active_concept_id:
            c = curriculum.get_concept(active_concept_id)
            if c:
                return cls._to_resolved(curriculum, c, confidence=0.7)

        # 4. Fallback for course
        return ResolvedConcept(
            domain=curriculum.subject or curriculum.title or "General",
            chapter="General",
            topic="General",
            subtopic="General",
            concept_id=format_concept_id(curriculum.course_id, curriculum.version_id, "undetermined"),
            confidence=0.3,
        )

    @classmethod
    def _to_resolved(cls, curriculum: GenericCurriculum, concept: GenericConcept, confidence: float) -> ResolvedConcept:
        return ResolvedConcept(
            domain=concept.domain or curriculum.subject or "General",
            chapter=concept.chapter or "General",
            topic=concept.topic or concept.name,
            subtopic=concept.subtopic or "",
            concept_id=concept.id,
            confidence=confidence,
        )

    @classmethod
    def resolve_domain(cls, user_message: str = "", active_concept_id: str = "", **kwargs) -> str:
        return cls.resolve_concept(user_message, active_concept_id, **kwargs).domain

    @classmethod
    def resolve_chapter(cls, user_message: str = "", active_concept_id: str = "", **kwargs) -> str:
        return cls.resolve_concept(user_message, active_concept_id, **kwargs).chapter

    @classmethod
    def resolve_topic(cls, user_message: str = "", active_concept_id: str = "", **kwargs) -> str:
        return cls.resolve_concept(user_message, active_concept_id, **kwargs).topic

    @classmethod
    def resolve_subtopic(cls, user_message: str = "", active_concept_id: str = "", **kwargs) -> str:
        return cls.resolve_concept(user_message, active_concept_id, **kwargs).subtopic
