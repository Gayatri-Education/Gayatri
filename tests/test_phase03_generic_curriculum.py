"""Tests for Phase 03: Generic Curriculum & Versioned Learning Graph (Section 12.3).

Verifies:
1. Data-driven ingestion of 4 canonical courses: Chemistry, Physics, History, Programming.
2. Zero-Chemistry dependency: All non-chemistry courses function with the Chemistry adapter completely disabled.
3. Cross-course concept ID collision resistance through canonical namespacing.
4. Multi-hop prerequisite DAG traversal scoped by course and version.
5. Cycle detection and missing prerequisite detection across diverse subject domains.
6. Backward compatibility for existing Chemistry concept resolution.
"""

from pathlib import Path
import pytest

from core.curriculum.chemistry_adapter import chemistry_adapter
from core.curriculum.loader import load_generic_curriculum
from core.curriculum.models import (
    GenericConcept,
    GenericCurriculum,
    format_concept_id,
    parse_concept_id,
)
from core.curriculum.resolver import ConceptResolver
from core.curriculum.validator import CurriculumValidator
from central_platform.learning.graph import LearningGraph


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "curriculum"


def test_four_course_generic_ingestion():
    """Verify that Chemistry, Physics, History, and Programming load via the exact same generic engine."""
    chem_path = DATA_DIR / "chemistry" / "ncert_class11_12.json"
    phys_path = DATA_DIR / "physics" / "mechanics_grade11.json"
    hist_path = DATA_DIR / "history" / "world_history.json"
    prog_path = DATA_DIR / "programming" / "intro_cs.json"

    for p in [chem_path, phys_path, hist_path, prog_path]:
        assert p.exists(), f"Curriculum fixture file does not exist: {p}"

    curr_chem = load_generic_curriculum(chem_path, course_id="chemistry", version_id="1.0")
    curr_phys = load_generic_curriculum(phys_path, course_id="physics", version_id="1.0")
    curr_hist = load_generic_curriculum(hist_path, course_id="history", version_id="1.0")
    curr_prog = load_generic_curriculum(prog_path, course_id="programming", version_id="1.0")

    assert curr_chem.subject.lower() == "chemistry"
    assert len(curr_chem.all_concepts()) >= 20

    assert "Physics" in curr_phys.subject
    assert len(curr_phys.all_concepts()) >= 5

    assert "History" in curr_hist.subject
    assert len(curr_hist.all_concepts()) >= 5

    assert "Computer Science" in curr_prog.subject or "Programming" in curr_prog.subject
    assert len(curr_prog.all_concepts()) >= 5


def test_cross_course_concept_resolution():
    """Verify that ConceptResolver accurately resolves concepts across Physics, History, Programming, and Chemistry."""
    phys_curr = load_generic_curriculum(DATA_DIR / "physics" / "mechanics_grade11.json", course_id="physics")
    hist_curr = load_generic_curriculum(DATA_DIR / "history" / "world_history.json", course_id="history")
    prog_curr = load_generic_curriculum(DATA_DIR / "programming" / "intro_cs.json", course_id="programming")

    ConceptResolver.register_curriculum("physics", phys_curr)
    ConceptResolver.register_curriculum("history", hist_curr)
    ConceptResolver.register_curriculum("programming", prog_curr)

    # 1. Physics resolution
    res_phys = ConceptResolver.resolve_concept(
        user_message="Can you explain the trajectory and range in projectile motion?",
        course_id="physics",
    )
    assert res_phys.concept_id == "phys_projectile"
    assert "Mechanics" in res_phys.domain
    assert res_phys.confidence >= 0.8

    # 2. History resolution
    res_hist = ConceptResolver.resolve_concept(
        user_message="How did the Code of Hammurabi establish Babylonian legal principles?",
        course_id="history",
    )
    assert res_hist.concept_id == "hist_hammurabi_code"
    assert "Ancient History" in res_hist.domain
    assert res_hist.confidence >= 0.8

    # 3. Programming resolution
    res_prog = ConceptResolver.resolve_concept(
        user_message="Explain recursion and the base case in divide-and-conquer algorithms",
        course_id="programming",
    )
    assert res_prog.concept_id == "cs_recursion"
    assert "Algorithms" in res_prog.domain or "Software" in res_prog.domain
    assert res_prog.confidence >= 0.8

    # 4. Chemistry resolution (backward-compatible)
    res_chem = ConceptResolver.resolve_concept(
        user_message="What is Hess's law of constant heat summation?",
    )
    assert res_chem.concept_id == "chem_thermo_hess"
    assert res_chem.domain == "Thermodynamics"


def test_phase_gate_chemistry_adapter_disabled():
    """Mandatory Phase Gate: Prove that the generic platform functions completely when the Chemistry adapter is disabled."""
    # Temporarily disable chemistry adapter
    original_state = chemistry_adapter.is_enabled
    chemistry_adapter.is_enabled = False

    try:
        # Load non-chemistry curriculum
        phys_curr = load_generic_curriculum(DATA_DIR / "physics" / "mechanics_grade11.json", course_id="physics")
        ConceptResolver.register_curriculum("physics", phys_curr)

        # Physics resolution must succeed without Chemistry adapter
        res = ConceptResolver.resolve_concept(
            user_message="Tell me about Newton's laws of motion and inertia",
            course_id="physics",
        )
        assert res.concept_id == "phys_newton_laws"
        assert res.domain == "Classical Mechanics"
        assert res.confidence >= 0.8

        # Unspecified query with chemistry adapter disabled must return generic neutral undetermined, not chemistry
        res_neutral = ConceptResolver.resolve_concept(user_message="Hello, can you help me?")
        assert res_neutral.concept_id == "general_undetermined"
        assert res_neutral.topic == "General"
        assert "chem" not in res_neutral.concept_id
        assert "Chemistry" not in res_neutral.topic

    finally:
        # Always restore original state to preserve backward compatibility for other test suites
        chemistry_adapter.is_enabled = original_state


def test_concept_namespacing_and_collision_resistance():
    """Verify that concepts with identical local names/keys across distinct courses do not collide."""
    cid_chem = format_concept_id("chemistry", "1.0", "thermo")
    cid_phys = format_concept_id("physics", "1.0", "thermo")

    assert cid_chem == "course:chemistry:version:1.0:concept:thermo"
    assert cid_phys == "course:physics:version:1.0:concept:thermo"
    assert cid_chem != cid_phys, "Concepts from different courses must have distinct canonical IDs"

    parsed_chem = parse_concept_id(cid_chem)
    assert parsed_chem["course_id"] == "chemistry"
    assert parsed_chem["version_id"] == "1.0"
    assert parsed_chem["concept_key"] == "thermo"

    # Verify legacy identifier parsing
    parsed_legacy = parse_concept_id("chem_thermo_hess")
    assert parsed_legacy["concept_key"] == "chem_thermo_hess"


def test_curriculum_dag_cycle_and_missing_prereq_detection():
    """Verify strict DAG cycle and missing prerequisite detection across diverse curricula."""
    # 1. Clean valid Physics curriculum
    phys_curr = load_generic_curriculum(DATA_DIR / "physics" / "mechanics_grade11.json", course_id="physics")
    val_clean = LearningGraph.validate_curriculum_dag(phys_curr)
    assert val_clean["valid"] is True
    assert len(val_clean["cycles"]) == 0
    assert len(val_clean["missing_prerequisites"]) == 0

    # 2. Cycle injection: C1 -> C2 -> C3 -> C1
    cyclic_curr = GenericCurriculum(
        id="curr_cycle_test",
        course_id="history",
        concepts=[
            GenericConcept(id="c1", name="C1", prerequisites=["c2"]),
            GenericConcept(id="c2", name="C2", prerequisites=["c3"]),
            GenericConcept(id="c3", name="C3", prerequisites=["c1"]),
        ],
    )
    val_cycle = LearningGraph.validate_curriculum_dag(cyclic_curr)
    assert val_cycle["valid"] is False
    assert len(val_cycle["cycles"]) > 0

    # 3. Missing prerequisite injection
    missing_curr = GenericCurriculum(
        id="curr_missing_test",
        course_id="programming",
        concepts=[
            GenericConcept(id="c_valid", name="Valid", prerequisites=["c_nonexistent"]),
        ],
    )
    val_missing = LearningGraph.validate_curriculum_dag(missing_curr)
    assert val_missing["valid"] is False
    assert len(val_missing["missing_prerequisites"]) == 1
    assert val_missing["missing_prerequisites"][0]["missing_prerequisite"] == "c_nonexistent"


def test_multi_hop_prerequisite_traversal_history_and_physics():
    """Verify multi-hop prerequisite dependencies for non-chemistry subjects."""
    hist_curr = load_generic_curriculum(DATA_DIR / "history" / "world_history.json", course_id="history")
    
    # Trace history dependencies: Pax Romana -> Roman Republic -> Code of Hammurabi -> Fertile Crescent
    empire = hist_curr.get_concept("hist_roman_empire")
    assert empire is not None
    assert "hist_roman_republic" in empire.prerequisites

    republic = hist_curr.get_concept("hist_roman_republic")
    assert republic is not None
    assert "hist_hammurabi_code" in republic.prerequisites

    code = hist_curr.get_concept("hist_hammurabi_code")
    assert code is not None
    assert "hist_fertile_crescent" in code.prerequisites
