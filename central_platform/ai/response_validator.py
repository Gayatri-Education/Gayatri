"""Response Validator Engine for Phase 19.

Validates 7 critical educational response invariants:
1. Factual consistency
2. Curriculum alignment
3. Source requirements
4. Educational safety
5. Answer leakage
6. Model failure
7. Formatting
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from central_platform.ai.response_planner import PedagogicalResponsePlan
from core.tutor.intents import CHEMISTRY_SAFETY_PATTERN, PROMPT_INJECTION_PATTERN

logger = logging.getLogger("gayatri.response_validator")


@dataclass
class ValidationIssue:
    """Individual validation failure or warning."""
    category: str  # "factual", "curriculum", "source", "safety", "leakage", "model_failure", "formatting"
    message: str
    severity: str  # "ERROR", "WARNING"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Authoritative output of response validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    sanitized_response: str = ""
    retry_recommended: bool = False
    fallback_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["issues"] = [i.to_dict() for i in self.issues]
        return d


class ResponseValidatorEngine:
    """Authoritative 7-invariant AI Response Validator."""

    def __init__(self):
        pass

    def validate_response(
        self,
        generated_response: str,
        response_plan: Optional[PedagogicalResponsePlan] = None,
        target_concept: Optional[str] = None,
        rag_sources_required: bool = False,
    ) -> ValidationResult:
        """Validate generated response against all 7 educational invariants."""
        issues: List[ValidationIssue] = []
        clean_resp = generated_response.strip()

        # 1. Model Failure Check
        if not clean_resp or len(clean_resp) < 10:
            issues.append(ValidationIssue("model_failure", "Response is empty or trivially short.", "ERROR"))
        
        if "I am an AI language model" in clean_resp or "As an AI" in clean_resp or "System Prompt:" in clean_resp:
            issues.append(ValidationIssue("model_failure", "Response contains model meta-talk or prompt leakage.", "ERROR"))

        # Repetition loop check (e.g. repeated same line > 4 times)
        lines = [l.strip() for l in clean_resp.split("\n") if l.strip()]
        if len(lines) >= 5 and len(set(lines)) <= len(lines) // 2:
            issues.append(ValidationIssue("model_failure", "Response exhibits repetitive output loop.", "ERROR"))

        # 2. Educational Safety Check
        if CHEMISTRY_SAFETY_PATTERN.search(clean_resp):
            issues.append(ValidationIssue("safety", "Response contains hazardous chemical synthesis or safety violation.", "ERROR"))

        if PROMPT_INJECTION_PATTERN.search(clean_resp):
            issues.append(ValidationIssue("safety", "Response contains prompt injection artifact.", "ERROR"))

        # 3. Answer Leakage Check
        if response_plan and response_plan.anti_answer_leakage_guard:
            leakage_patterns = [
                re.compile(r"\bthe\s+(final\s+)?answer\s+is\s+([A-D]|[\d\.]+)\b", re.I),
                re.compile(r"\bcorrect\s+option\s+is\s+([A-D])\b", re.I),
            ]
            for pat in leakage_patterns:
                if pat.search(clean_resp):
                    issues.append(ValidationIssue("leakage", "Response leaks final answer during Socratic/hint turn.", "ERROR"))

        # 4. Source Requirements Check
        if rag_sources_required or (response_plan and response_plan.rag_sources_to_cite):
            # Check if any citation format or reference is present
            has_citation = any(
                c in clean_resp for c in ["[", "Reference", "Source", "NCERT", "Notes", "According to"]
            )
            if not has_citation:
                issues.append(ValidationIssue("source", "Response lacks required source citation references.", "WARNING"))

        # 5. Curriculum Alignment Check
        concept_name = target_concept or (response_plan.target_concept if response_plan else None)
        if concept_name and len(clean_resp.split()) > 30:
            c_words = [w.lower() for w in concept_name.replace("_", " ").split()]
            # If none of concept keywords appear in long response
            if not any(cw in clean_resp.lower() for cw in c_words if len(cw) > 3):
                issues.append(ValidationIssue("curriculum", f"Response may be unaligned with target concept '{concept_name}'.", "WARNING"))

        # 6. Factual Consistency (Basic Chemistry Laws Sanity Check)
        if "delta G = delta H + T delta S" in clean_resp:  # Wrong sign (+ instead of -)
            issues.append(ValidationIssue("factual", "Incorrect thermodynamic formula: delta G = delta H - T delta S.", "ERROR"))

        # 7. Formatting Check
        # Check unclosed LaTeX math delimiters $
        dollar_count = clean_resp.count("$")
        if dollar_count % 2 != 0:
            issues.append(ValidationIssue("formatting", "Unclosed LaTeX math delimiter '$'.", "WARNING"))

        has_errors = any(i.severity == "ERROR" for i in issues)
        is_valid = not has_errors

        fallback = None
        if not is_valid:
            c_name = concept_name or "this concept"
            fallback = f"Let's focus on understanding {c_name} step by step. What key principle would you like to review first?"

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            sanitized_response=clean_resp if is_valid else (fallback or clean_resp),
            retry_recommended=has_errors,
            fallback_response=fallback,
        )
