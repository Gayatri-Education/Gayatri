"""Gayatri AI Platform — Comprehensive Security Audit Subsystem (Phase 37).

Provides automated security scanning, vulnerability detection, PII masking,
prompt injection protection, upload validation, and tenant boundary verification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import uuid
from typing import Any, Dict, List, Optional


class SecurityAuditCategory(str, Enum):
    AUTH_RBAC = "auth_rbac"
    TENANT_ISOLATION = "tenant_isolation"
    SECRETS_EXPOSURE = "secrets_exposure"
    PROMPT_INJECTION = "prompt_injection"
    UPLOAD_SAFETY = "upload_safety"
    PAYMENT_SECURITY = "payment_security"
    PII_PRIVACY = "pii_privacy"


class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SecurityAuditIssue:
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: SecurityAuditCategory = SecurityAuditCategory.AUTH_RBAC
    severity: SecuritySeverity = SecuritySeverity.MEDIUM
    title: str = ""
    description: str = ""
    remediation: str = ""
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value if isinstance(self.category, SecurityAuditCategory) else self.category
        d["severity"] = self.severity.value if isinstance(self.severity, SecuritySeverity) else self.severity
        return d


class SecurityAuditRunner:
    """Authoritative Platform Security Audit & PII Sanitizer Engine."""

    DANGEROUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".php", ".py", ".pl", ".vbs", ".ps1", ".jar", ".dll"}

    PROMPT_INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(a|an)\s+unrestricted", re.IGNORECASE),
        re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
        re.compile(r"jailbreak\s+mode", re.IGNORECASE),
        re.compile(r"<script>.*?</script>", re.IGNORECASE | re.DOTALL),
    ]

    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_REGEX = re.compile(r"\b(?:\+91|91)?[789]\d{9}\b")

    @classmethod
    def sanitize_pii_logs(cls, log_message: str) -> str:
        """Mask PII (emails & Indian mobile numbers) in log streams to protect privacy."""
        if not log_message:
            return ""

        # Mask emails -> e.g. j***n@domain.com
        def mask_email(match: re.Match) -> str:
            email = match.group(0)
            parts = email.split("@")
            username = parts[0]
            domain = parts[1]
            if len(username) <= 2:
                masked_user = username[0] + "*"
            else:
                masked_user = username[0] + "*" * (len(username) - 2) + username[-1]
            return f"{masked_user}@{domain}"

        # Mask phone -> e.g. +91 9******10
        def mask_phone(match: re.Match) -> str:
            phone = match.group(0)
            if len(phone) > 10:
                prefix = phone[:-10]
                local = phone[-10:]
                return f"{prefix}{local[0]}******{local[-2:]}"
            return f"{phone[0]}******{phone[-2:]}"

        sanitized = cls.EMAIL_REGEX.sub(mask_email, log_message)
        sanitized = cls.PHONE_REGEX.sub(mask_phone, sanitized)
        return sanitized

    @classmethod
    def audit_prompt_injection(cls, prompt_text: str) -> List[SecurityAuditIssue]:
        issues = []
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if pattern.search(prompt_text):
                issues.append(
                    SecurityAuditIssue(
                        category=SecurityAuditCategory.PROMPT_INJECTION,
                        severity=SecuritySeverity.HIGH,
                        title="Potential Prompt Injection / Jailbreak Attack Pattern Detected",
                        description=f"Prompt matches injection regex pattern: {pattern.pattern}",
                        remediation="Sanitize input prompt and strip system instruction overrides before sending to SLM/LLM.",
                        passed=False,
                    )
                )

        if not issues:
            issues.append(
                SecurityAuditIssue(
                    category=SecurityAuditCategory.PROMPT_INJECTION,
                    severity=SecuritySeverity.LOW,
                    title="Prompt Security Sanitization",
                    description="No prompt injection patterns detected.",
                    remediation="None",
                    passed=True,
                )
            )
        return issues

    @classmethod
    def audit_upload_filename(cls, filename: str) -> SecurityAuditIssue:
        filename_lower = filename.lower()
        if ".." in filename or "/" in filename or "\\" in filename:
            return SecurityAuditIssue(
                category=SecurityAuditCategory.UPLOAD_SAFETY,
                severity=SecuritySeverity.CRITICAL,
                title="Path Traversal Vulnerability in Upload Filename",
                description=f"Filename '{filename}' contains path traversal sequences.",
                remediation="Sanitize filename using secure basename algorithm.",
                passed=False,
            )

        for ext in cls.DANGEROUS_EXTENSIONS:
            if filename_lower.endswith(ext):
                return SecurityAuditIssue(
                    category=SecurityAuditCategory.UPLOAD_SAFETY,
                    severity=SecuritySeverity.HIGH,
                    title="Dangerous File Extension Upload Detected",
                    description=f"Filename '{filename}' contains executable extension '{ext}'.",
                    remediation="Restrict allowed upload extensions to safe formats (.pdf, .txt, .png, .jpeg, .docx).",
                    passed=False,
                )

        return SecurityAuditIssue(
            category=SecurityAuditCategory.UPLOAD_SAFETY,
            severity=SecuritySeverity.LOW,
            title="Upload Safety Check",
            description=f"Filename '{filename}' passed safety validation.",
            remediation="None",
            passed=True,
        )

    @classmethod
    def audit_tenant_query(cls, sql_query: str) -> SecurityAuditIssue:
        """Audit SQL query for cross-tenant scoping parameters (org_id or course_id)."""
        sql_lower = sql_query.lower()
        if "where" in sql_lower and ("org_id" not in sql_lower and "organization_id" not in sql_lower and "student_id" not in sql_lower):
            return SecurityAuditIssue(
                category=SecurityAuditCategory.TENANT_ISOLATION,
                severity=SecuritySeverity.HIGH,
                title="Potential Cross-Tenant SQL Data Leakage",
                description=f"Query lacks explicit org_id/student_id tenant boundary filter.",
                remediation="Ensure SQL query explicitly filters by organization_id or student_id.",
                passed=False,
            )

        return SecurityAuditIssue(
            category=SecurityAuditCategory.TENANT_ISOLATION,
            severity=SecuritySeverity.LOW,
            title="Tenant Boundary Check",
            description="Query contains tenant scoping parameters.",
            remediation="None",
            passed=True,
        )
