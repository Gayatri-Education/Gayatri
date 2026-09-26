"""Security Auditor, Prompt Injection Safeguards, Rate Limiter, and File Sanitizer."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SecurityAuditResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    sanitized_input: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityAuditor:
    """Centralized security auditor enforcing input validation, rate limiting, and prompt injection defense."""

    def __init__(self, rate_limit_per_minute: int = 60):
        self.rate_limit_per_minute = rate_limit_per_minute
        self._user_request_timestamps: Dict[str, List[float]] = {}
        self._injection_patterns: List[re.Pattern] = [
            re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
            re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
            re.compile(r"reveal\s+(the\s+)?secret\s+key", re.IGNORECASE),
            re.compile(r"dump\s+database", re.IGNORECASE),
            re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        ]
        self._allowed_file_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".json", ".md"}

    def check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        timestamps = self._user_request_timestamps.setdefault(user_id, [])
        # Keep timestamps within the last 60 seconds
        cutoff = now - 60.0
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._user_request_timestamps[user_id] = valid_timestamps

        if len(valid_timestamps) >= self.rate_limit_per_minute:
            return False

        valid_timestamps.append(now)
        return True

    def sanitize_prompt(self, prompt: str) -> SecurityAuditResult:
        violations: List[str] = []
        for pattern in self._injection_patterns:
            if pattern.search(prompt):
                violations.append(f"Prompt injection pattern detected: {pattern.pattern}")

        is_safe = len(violations) == 0
        # Strip potential HTML script tags as simple sanitization
        sanitized = re.sub(r"<script.*?>.*?</script>", "", prompt, flags=re.IGNORECASE | re.DOTALL)

        return SecurityAuditResult(
            is_safe=is_safe,
            violations=violations,
            sanitized_input=sanitized if is_safe else None,
        )

    def validate_file_upload(self, filename: str, file_size_bytes: int, max_bytes: int = 10 * 1024 * 1024) -> SecurityAuditResult:
        violations: List[str] = []
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in self._allowed_file_extensions:
            violations.append(f"Disallowed file extension '{ext}'. Allowed: {self._allowed_file_extensions}")

        if file_size_bytes > max_bytes:
            violations.append(f"File size {file_size_bytes} exceeds limit of {max_bytes} bytes.")

        return SecurityAuditResult(
            is_safe=len(violations) == 0,
            violations=violations,
        )

    def verify_tenant_boundary(self, user_org_id: str, target_org_id: str, is_super_admin: bool = False) -> bool:
        if is_super_admin:
            return True
        return user_org_id == target_org_id
