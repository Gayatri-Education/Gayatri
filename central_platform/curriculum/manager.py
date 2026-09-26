"""Versioned Plug-and-Play Curriculum Management Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CurriculumStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"


@dataclass
class ConceptNode:
    concept_id: str
    title: str
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class CurriculumVersion:
    curriculum_id: str
    version: int
    title: str
    concepts: Dict[str, ConceptNode] = field(default_factory=dict)
    status: CurriculumStatus = CurriculumStatus.DRAFT


class CurriculumManager:
    """Manages authoring, versioning, publishing, and cycle prevention for curricula."""

    def __init__(self):
        self._curricula: dict[tuple[str, int], CurriculumVersion] = {}

    def create_draft(self, curriculum_id: str, version: int, title: str) -> CurriculumVersion:
        key = (curriculum_id, version)
        if key in self._curricula and self._curricula[key].status == CurriculumStatus.PUBLISHED:
            raise ValueError("Published curriculum versions are immutable.")
        c = CurriculumVersion(curriculum_id=curriculum_id, version=version, title=title)
        self._curricula[key] = c
        return c

    def add_concept(self, curriculum_id: str, version: int, concept: ConceptNode) -> None:
        c = self._curricula.get((curriculum_id, version))
        if not c:
            raise KeyError("Curriculum version not found.")
        if c.status == CurriculumStatus.PUBLISHED:
            raise ValueError("Cannot modify published curriculum.")
        c.concepts[concept.concept_id] = concept

    def publish_version(self, curriculum_id: str, version: int) -> bool:
        c = self._curricula.get((curriculum_id, version))
        if not c:
            return False
        # Validate cycle detection in prerequisites
        if self._has_cycle(c.concepts):
            raise ValueError("Curriculum contains cycle in concept prerequisites.")
        c.status = CurriculumStatus.PUBLISHED
        return True

    def _has_cycle(self, concepts: Dict[str, ConceptNode]) -> bool:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = concepts.get(node_id)
            if node:
                for prereq in node.prerequisites:
                    if prereq not in visited:
                        if dfs(prereq):
                            return True
                    elif prereq in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for cid in concepts:
            if cid not in visited:
                if dfs(cid):
                    return True
        return False
