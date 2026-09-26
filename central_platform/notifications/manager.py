"""Notification Abstraction Engine supporting multi-channel delivery and retryable queues."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRIED = "retried"


@dataclass
class NotificationMessage:
    id: str
    recipient_id: str
    channel: NotificationChannel
    title: str
    body: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotificationManager:
    """Central notification manager with channel abstraction and retry policies."""

    def __init__(self):
        self._queue: List[NotificationMessage] = []
        self._user_preferences: Dict[str, List[NotificationChannel]] = {}
        self._delivery_log: List[NotificationMessage] = []

    def set_user_channels(self, user_id: str, channels: List[NotificationChannel]) -> None:
        self._user_preferences[user_id] = channels

    def send_notification(
        self,
        recipient_id: str,
        channel: NotificationChannel,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
        simulate_failure: bool = False,
    ) -> NotificationMessage:
        # Respect user preferences if configured
        allowed_channels = self._user_preferences.get(recipient_id, [NotificationChannel.IN_APP, NotificationChannel.EMAIL])
        if channel not in allowed_channels:
            msg = NotificationMessage(
                id=f"notif-{uuid.uuid4().hex[:8]}",
                recipient_id=recipient_id,
                channel=channel,
                title=title,
                body=body,
                status=DeliveryStatus.FAILED,
                metadata={"error": "Channel disabled by user preference"},
            )
            self._delivery_log.append(msg)
            return msg

        msg = NotificationMessage(
            id=f"notif-{uuid.uuid4().hex[:8]}",
            recipient_id=recipient_id,
            channel=channel,
            title=title,
            body=body,
            metadata=metadata or {},
        )

        if simulate_failure:
            msg.status = DeliveryStatus.FAILED
            self._queue.append(msg)
        else:
            msg.status = DeliveryStatus.DELIVERED
            self._delivery_log.append(msg)

        return msg

    def process_retry_queue(self) -> List[NotificationMessage]:
        retried: List[NotificationMessage] = []
        remaining: List[NotificationMessage] = []

        for msg in self._queue:
            if msg.status == DeliveryStatus.FAILED and msg.retry_count < msg.max_retries:
                msg.retry_count += 1
                msg.status = DeliveryStatus.DELIVERED
                self._delivery_log.append(msg)
                retried.append(msg)
            else:
                remaining.append(msg)

        self._queue = remaining
        return retried

    def get_user_notifications(self, recipient_id: str) -> List[NotificationMessage]:
        return [m for m in self._delivery_log if m.recipient_id == recipient_id and m.status == DeliveryStatus.DELIVERED]
