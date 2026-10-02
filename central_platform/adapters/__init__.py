"""Gayatri AI Platform — Domain Adapters (Phase 19).

Provides pluggable, decoupled domain adapters (Chemistry, Physics, Math, etc.)
allowing domain-specific tools, evaluators, and taxonomies to be extracted
and enabled/disabled independently from the generic core platform.
"""
from __future__ import annotations

from central_platform.adapters.chemistry.adapter import (
    ChemistryDomainAdapter,
    get_chemistry_domain_adapter,
    is_chemistry_adapter_enabled,
)

__all__ = [
    "ChemistryDomainAdapter",
    "get_chemistry_domain_adapter",
    "is_chemistry_adapter_enabled",
]
