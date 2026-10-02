"""Gayatri AI Platform — Chemistry Domain Adapter (Phase 19).

First-class domain adapter encapsulating Chemistry-specific:
- Computational tools (ChemicalEquationBalancer, FormulaParser)
- Domain assessment evaluators (ChemistryEquationEvaluator)
- Concept keyword taxonomies and curriculum matching
- Chemical entity normalization
- Common chemical misconceptions

Enables runtime toggle and complete decoupling of generic platform operations.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gayatri.central_platform.adapters.chemistry")

DEFAULT_CHEMISTRY_MISCONCEPTIONS: List[Dict[str, Any]] = [
    {
        "code": "MISC-BOND-BREAK",
        "name": "Bond Breaking Releases Energy",
        "description": "Believing that breaking chemical bonds releases energy rather than requiring energy input.",
        "subject": "Chemistry",
        "severity": "high",
    },
    {
        "code": "MISC-TEMP-HEAT",
        "name": "Temperature and Heat Confusion",
        "description": "Confusing temperature (average kinetic energy) with thermal heat energy.",
        "subject": "Chemistry",
        "severity": "medium",
    },
    {
        "code": "MISC-EQUIL-STATIC",
        "name": "Chemical Equilibrium is Static",
        "description": "Believing that chemical reactions completely cease once dynamic equilibrium is established.",
        "subject": "Chemistry",
        "severity": "medium",
    },
    {
        "code": "MISC-COEFF-SUBSCRIPT",
        "name": "Coefficient vs Subscript Confusion",
        "description": "Confusing stoichiometric coefficients with molecular formula subscripts when balancing equations.",
        "subject": "Chemistry",
        "severity": "high",
    },
]


class ChemistryDomainAdapter:
    """First-class domain adapter for Chemistry discipline."""

    DOMAIN_NAME = "chemistry"

    def __init__(self, is_enabled: Optional[bool] = None) -> None:
        if is_enabled is not None:
            self._is_enabled = is_enabled
        else:
            env_val = os.environ.get("GAYATRI_ENABLE_CHEMISTRY_ADAPTER", "1").strip().lower()
            self._is_enabled = env_val not in ("0", "false", "no", "off", "disable", "disabled")

        self._tool_adapter: Optional[Any] = None
        self._equation_evaluator: Optional[Any] = None

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    def enable(self) -> None:
        """Enable the chemistry domain adapter."""
        self._is_enabled = True
        logger.info("ChemistryDomainAdapter: Enabled.")

    def disable(self) -> None:
        """Disable the chemistry domain adapter."""
        self._is_enabled = False
        logger.info("ChemistryDomainAdapter: Disabled.")

    def can_handle_course(self, course_id_or_subject: str) -> bool:
        """Determine if this adapter is applicable to the given course or subject."""
        if not self._is_enabled or not course_id_or_subject:
            return False
        c_lower = course_id_or_subject.lower()
        return "chem" in c_lower or "organic" in c_lower or "inorganic" in c_lower or "thermo" in c_lower

    def get_tool_adapter(self) -> Optional[Any]:
        """Return the computational tool adapter if enabled, otherwise None."""
        if not self._is_enabled:
            return None
        if self._tool_adapter is None:
            from central_platform.tools.adapters.chemistry import ChemistryToolAdapter
            self._tool_adapter = ChemistryToolAdapter()
        return self._tool_adapter

    def get_evaluators(self) -> List[Any]:
        """Return specialized assessment evaluators if enabled, otherwise empty list."""
        if not self._is_enabled:
            return []
        if self._equation_evaluator is None:
            from central_platform.assessment.evaluators.adapter_hooks import ChemistryEquationEvaluator
            self._equation_evaluator = ChemistryEquationEvaluator(self.get_tool_adapter())
        return [self._equation_evaluator]

    def get_curriculum_adapter(self) -> Optional[Any]:
        """Return the curriculum adapter if enabled, otherwise None."""
        if not self._is_enabled:
            return None
        from core.curriculum.chemistry_adapter import ChemistryCurriculumAdapter
        return ChemistryCurriculumAdapter(is_enabled=self._is_enabled)

    def get_entity_normalizer(self) -> Optional[Any]:
        """Return the entity normalizer class if enabled, otherwise None."""
        if not self._is_enabled:
            return None
        from core.learning.chemistry_entities import ChemistryEntityNormalizer
        return ChemistryEntityNormalizer

    def get_misconceptions(self) -> List[Dict[str, Any]]:
        """Return chemistry misconceptions catalog if enabled, otherwise empty list."""
        if not self._is_enabled:
            return []
        return list(DEFAULT_CHEMISTRY_MISCONCEPTIONS)

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Return metadata summary of capabilities provided by this domain adapter."""
        return {
            "domain": self.DOMAIN_NAME,
            "is_enabled": self._is_enabled,
            "tool_capabilities": [c.tool_id for c in self.get_tool_adapter().get_capabilities()] if self._is_enabled and self.get_tool_adapter() else [],
            "evaluator_types": ["EQUATION_BALANCING", "CHEMICAL_EQUATION"] if self._is_enabled else [],
            "misconception_count": len(DEFAULT_CHEMISTRY_MISCONCEPTIONS) if self._is_enabled else 0,
        }


# Global singleton instance
_GLOBAL_CHEMISTRY_ADAPTER: Optional[ChemistryDomainAdapter] = None


def get_chemistry_domain_adapter() -> ChemistryDomainAdapter:
    """Retrieve or initialize the global singleton ChemistryDomainAdapter."""
    global _GLOBAL_CHEMISTRY_ADAPTER
    if _GLOBAL_CHEMISTRY_ADAPTER is None:
        _GLOBAL_CHEMISTRY_ADAPTER = ChemistryDomainAdapter()
    return _GLOBAL_CHEMISTRY_ADAPTER


def is_chemistry_adapter_enabled() -> bool:
    """Check whether the chemistry domain adapter is globally enabled."""
    return get_chemistry_domain_adapter().is_enabled
