"""Unit test suite for Plug & Play Curriculum Platform (Phase 12)."""

import pytest
from central_platform.curriculum.manager import (
    ConceptNode,
    CurriculumManager,
    CurriculumStatus,
)


def test_curriculum_versioning_lifecycle_and_immutability():
    mgr = CurriculumManager()
    c = mgr.create_draft("curr_math", 1, "K-12 Math")
    mgr.add_concept("curr_math", 1, ConceptNode("c1", "Numbers", []))
    mgr.add_concept("curr_math", 1, ConceptNode("c2", "Addition", ["c1"]))

    assert mgr.publish_version("curr_math", 1) is True
    assert c.status == CurriculumStatus.PUBLISHED

    # Cannot add concept to published version
    with pytest.raises(ValueError):
        mgr.add_concept("curr_math", 1, ConceptNode("c3", "Subtraction", ["c1"]))


def test_curriculum_cycle_prevention():
    mgr = CurriculumManager()
    mgr.create_draft("curr_physics", 1, "Physics")

    # Create cycle: A -> B -> A
    mgr.add_concept("curr_physics", 1, ConceptNode("A", "Concept A", ["B"]))
    mgr.add_concept("curr_physics", 1, ConceptNode("B", "Concept B", ["A"]))

    with pytest.raises(ValueError, match="cycle"):
        mgr.publish_version("curr_physics", 1)
