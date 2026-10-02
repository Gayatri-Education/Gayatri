"""Gayatri AI — Chemistry Curriculum Adapter.

Houses Chemistry-specific concept keywords, domain taxonomies, and resolution logic,
isolating subject-specific mappings from the generic curriculum engine.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.curriculum.chemistry_adapter")

# Authoritative Chemistry domain/topic keyword mapping
CHEMISTRY_CONCEPT_KEYWORD_MAP: List[Dict[str, Any]] = [
    # Inorganic Chemistry
    {
        "keywords": ["electronic configuration", "electronic structure", "aufbau", "valence electrons", "quantum numbers", "orbitals", "hund's rule", "pauli exclusion"],
        "domain": "Inorganic Chemistry",
        "chapter": "Structure of Atom & Periodicity",
        "topic": "Electronic Configuration",
        "subtopic": "Aufbau Principle & Orbitals",
        "concept_id": "chem_inorg_electronic",
    },
    {
        "keywords": ["ionization enthalpy", "ionization energy", "enthalpy of ionization", "ionisation", "periodicity", "periodic table", "periodic trend", "atomic radius", "electronegativity", "electron gain enthalpy"],
        "domain": "Inorganic Chemistry",
        "chapter": "Classification of Elements and Periodicity",
        "topic": "Periodic Table Trends",
        "subtopic": "Ionization Enthalpy",
        "concept_id": "chem_inorg_periodic",
    },
    {
        "keywords": [
            "vsepr", "molecular geometry", "molecular shape", "trigonal pyramidal",
            "trigonal planar", "tetrahedral", "bent", "pyramidal", "lone pair", "lone pairs",
            "bond pair", "bond pairs", "nh3", "ammonia", "bcl3", "ch4", "h2o", "water",
            "repulsion order", "lp-lp", "lp-bp", "bp-bp", "shape of nh3", "geometry of nh3",
            "bond angle", "hybridization", "hybridisation"
        ],
        "domain": "Inorganic Chemistry",
        "chapter": "Chemical Bonding and Molecular Structure",
        "topic": "VSEPR Theory & Molecular Geometry",
        "subtopic": "Molecular Geometries of NH3 and H2O",
        "concept_id": "chem_inorg_vsepr",
    },
    {
        "keywords": ["bonding", "covalent", "ionic bond", "lewis structure", "octet", "formal charge", "resonance"],
        "domain": "Inorganic Chemistry",
        "chapter": "Chemical Bonding and Molecular Structure",
        "topic": "Chemical Bonding",
        "subtopic": "Covalent & Ionic Bonding",
        "concept_id": "chem_inorg_bonding",
    },
    {
        "keywords": ["coordination", "complex", "ligand", "ligands", "coordination number", "coordination entity", "cisplatin", "chelate", "chelating", "coordination sphere"],
        "domain": "Inorganic Chemistry",
        "chapter": "Coordination Compounds",
        "topic": "Coordination Chemistry",
        "subtopic": "Ligands and Coordination Number",
        "concept_id": "chem_inorg_coordination",
    },
    {
        "keywords": ["equilibrium", "le chatelier", "le chatelier's principle", "kc", "kp", "equilibrium constant", "buffer", "solubility product", "ksp", "common ion"],
        "domain": "Physical Chemistry",
        "chapter": "Equilibrium",
        "topic": "Chemical and Ionic Equilibrium",
        "subtopic": "Le Chatelier's Principle & Buffer Solutions",
        "concept_id": "chem_equilibrium",
    },
    {
        "keywords": ["s-block", "alkali", "alkaline earth", "sodium", "potassium", "magnesium", "calcium"],
        "domain": "Inorganic Chemistry",
        "chapter": "s-Block Elements",
        "topic": "s-Block Elements",
        "subtopic": "Alkali & Alkaline Earth Metals",
        "concept_id": "chem_inorg_sblock",
    },
    {
        "keywords": ["p-block", "boron", "carbon", "nitrogen family", "oxygen family", "halogen", "noble gas"],
        "domain": "Inorganic Chemistry",
        "chapter": "p-Block Elements",
        "topic": "p-Block Elements",
        "subtopic": "Group 13-18 Elements",
        "concept_id": "chem_inorg_pblock",
    },
    {
        "keywords": ["balancing equation", "equation balancing", "balance equation", "redox balancing", "balancing"],
        "domain": "Inorganic Chemistry",
        "chapter": "Some Basic Concepts of Chemistry",
        "topic": "Equation Balancing",
        "subtopic": "Balancing Chemical Equations",
        "concept_id": "chem_balancing",
    },
    {
        "keywords": ["stoichiometry", "mole concept", "avogadro", "limiting reagent", "percentage yield"],
        "domain": "Inorganic Chemistry",
        "chapter": "Some Basic Concepts of Chemistry",
        "topic": "Stoichiometry and Mole Concept",
        "subtopic": "Equation Balancing & Moles",
        "concept_id": "chem_stoichiometry",
    },
    # Thermodynamics
    {
        "keywords": ["hess's law", "hess law", "hess", "constant heat summation", "enthalpy of reaction", "enthalpy summation"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Hess Law",
        "subtopic": "Enthalpy Summations",
        "concept_id": "chem_thermo_hess",
    },
    {
        "keywords": ["gibbs free energy", "gibbs energy", "gibbs", "free energy", "delta g", "spontaneity", "spontaneous"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Gibbs Free Energy",
        "subtopic": "Spontaneity & Equilibrium",
        "concept_id": "chem_thermo_gibbs",
    },
    {
        "keywords": ["entropy", "delta s", "second law", "disorder", "randomness"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Entropy",
        "subtopic": "Second Law & Entropy",
        "concept_id": "chem_thermo_entropy",
    },
    {
        "keywords": ["enthalpy", "delta h", "heat of reaction", "exothermic", "endothermic"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Enthalpy",
        "subtopic": "Enthalpy Changes",
        "concept_id": "chem_thermo_enthalpy",
    },
    {
        "keywords": ["first law", "internal energy", "delta u", "work", "heat (q)", "delta u = q + w"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "First Law of Thermodynamics",
        "subtopic": "Internal Energy & Work",
        "concept_id": "chem_thermo_first_law",
    },
    {
        "keywords": ["heat capacity", "specific heat", "cp", "cv", "molar heat capacity"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Heat Capacity",
        "subtopic": "Cp and Cv Relations",
        "concept_id": "chem_thermo_heat_cap",
    },
    {
        "keywords": ["calorimetry", "calorimeter", "bomb calorimeter", "heat of combustion"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Calorimetry",
        "subtopic": "Bomb Calorimeter & Measurement",
        "concept_id": "chem_thermo_calorimetry",
    },
    {
        "keywords": ["standard enthalpy of formation", "enthalpy of formation", "heat of formation", "formation enthalpy"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "Standard Enthalpy of Formation",
        "subtopic": "Formation Enthalpies",
        "concept_id": "chem_thermo_formation",
    },
    {
        "keywords": ["system", "surroundings", "isolated", "open system", "closed system", "state function"],
        "domain": "Thermodynamics",
        "chapter": "Thermodynamics",
        "topic": "System and Surroundings",
        "subtopic": "Thermodynamic Terms",
        "concept_id": "chem_thermo_system",
    },
]


class ChemistryCurriculumAdapter:
    """Dedicated Chemistry adapter decoupling Chemistry concepts from generic resolver."""

    def __init__(self, is_enabled: bool = True):
        self.is_enabled = is_enabled
        self.course_id = "chemistry"

    def match_concept(
        self,
        clean_msg: str = "",
        recent_context: Optional[List[str]] = None,
        active_concept_id: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Attempt to match a chemistry concept if the adapter is enabled."""
        if not self.is_enabled:
            return None

        # 1. Match message keywords
        if clean_msg:
            for entry in CHEMISTRY_CONCEPT_KEYWORD_MAP:
                for kw in entry["keywords"]:
                    if kw in clean_msg:
                        logger.info(f"ChemistryAdapter: matched keyword '{kw}' -> {entry['concept_id']}")
                        return {**entry, "confidence": 0.9}

        # 2. Check recent context
        if recent_context:
            for ctx_msg in reversed(recent_context):
                ctx_clean = (ctx_msg or "").strip().lower()
                if not ctx_clean:
                    continue
                for entry in CHEMISTRY_CONCEPT_KEYWORD_MAP:
                    for kw in entry["keywords"]:
                        if kw in ctx_clean:
                            logger.info(f"ChemistryAdapter: matched keyword '{kw}' in recent context -> {entry['concept_id']}")
                            return {**entry, "confidence": 0.8}

        # 3. Retain active concept ID
        if active_concept_id:
            for entry in CHEMISTRY_CONCEPT_KEYWORD_MAP:
                if entry["concept_id"] == active_concept_id:
                    return {**entry, "confidence": 0.7}

        return None


# Global singleton instance
chemistry_adapter = ChemistryCurriculumAdapter(is_enabled=True)
