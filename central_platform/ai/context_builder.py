"""Gayatri AI Platform — AI Context Builder (Phase 17).

Assembles authoritative execution context including pedagogical system prompt,
teacher directives, student session state, and grounded RAG knowledge.
"""
from __future__ import annotations

from typing import List, Optional


class ContextBuilder:
    """Constructs prompt and system instructions for AI model execution."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are Gayatri AI, an authoritative, pedagogical intelligent tutoring system. "
        "Your mission is to guide students towards deep conceptual understanding through Socratic "
        "scaffolding, precise explanations, and immediate misconception remediation.\n\n"
        "PEDAGOGICAL INVARIANTS:\n"
        "1. Never give away final answers directly on first attempt; provide guiding hints and breakdown steps.\n"
        "2. Ground scientific claims in authoritative knowledge and cite sources where relevant.\n"
        "3. Address student misconceptions explicitly with clarifying contrastive explanations.\n"
        "4. Comply strictly with teacher directives and instructional constraints."
    )

    @classmethod
    def build_system_prompt(
        cls,
        base_prompt: Optional[str] = None,
        teacher_directives: Optional[List[str]] = None,
        subject: Optional[str] = None,
    ) -> str:
        prompt = base_prompt or cls.DEFAULT_SYSTEM_PROMPT

        if subject:
            prompt += f"\n\nSUBJECT SCOPE: {subject}"

        if teacher_directives:
            prompt += "\n\nACTIVE TEACHER DIRECTIVES (MANDATORY COMPLIANCE):"
            for idx, d in enumerate(teacher_directives, 1):
                prompt += f"\n{idx}. {d}"

        return prompt

    @classmethod
    def build_user_prompt(
        cls,
        user_query: str,
        rag_context: Optional[str] = None,
        student_context: Optional[str] = None,
    ) -> str:
        parts = []
        if rag_context:
            parts.append(rag_context)

        if student_context:
            parts.append(f"--- STUDENT CONTEXT ---\n{student_context}\n--- END STUDENT CONTEXT ---")

        parts.append(f"Student Query: {user_query}")
        return "\n\n".join(parts)
