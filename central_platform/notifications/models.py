"""Notification Domain Enums and Message Contracts (Phase 21)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRIED = "retried"


@dataclass
class ProviderDeliveryResult:
    success: bool
    provider_message_id: Optional[str] = None
    delivered: bool = False
    error_message: Optional[str] = None
    retryable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
