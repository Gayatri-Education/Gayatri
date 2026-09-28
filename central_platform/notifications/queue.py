"""Persistent Notification Queue and Exponential Backoff Retry Engine (Phase 21).

Implements Section 30:
- Asynchronous queueing
- Precise tracking: created -> queued -> sent -> delivered -> failed -> retried
- Exponential backoff: backoff_sec = base_backoff * (2 ** retry_count)
- Strict retry limits and dead-letter failure handling
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Notification
from central_platform.notifications.models import NotificationChannel, NotificationStatus
from central_platform.notifications.providers import BaseDeliveryProvider, ProviderRegistry


class NotificationQueueManager:
    """Manages persistent dispatch queues, channel delivery, and exponential backoff retry scheduling."""

    def __init__(self, db: Optional[PlatformDatabase] = None, provider_registry: Optional[ProviderRegistry] = None):
        self.db = db or PlatformDatabase()
        self.registry = provider_registry or ProviderRegistry()

    async def enqueue(self, notification: Notification) -> Notification:
        """Persist notification with QUEUED status into database queue."""
        notification.status = NotificationStatus.QUEUED.value
        self.db.create_notification(notification)
        return notification

    async def dispatch_single(self, notification: Notification) -> Notification:
        """Attempt immediate delivery through target channel provider with state transitions."""
        provider = self.registry.get(notification.channel)
        
        # Mark as SENT before provider confirmation attempt
        notification.status = NotificationStatus.SENT.value
        
        try:
            result = await provider.deliver(notification)
            now_iso = datetime.now(timezone.utc).isoformat()
            
            if result.success:
                notification.status = NotificationStatus.DELIVERED.value
                notification.delivered_at = now_iso
                notification.provider_message_id = result.provider_message_id
                notification.error_message = None
                if result.metadata:
                    notification.metadata.update(result.metadata)
            else:
                notification.error_message = result.error_message
                if result.retryable and notification.retry_count < notification.max_retries:
                    notification.retry_count += 1
                    # Exponential backoff formula: backoff = base * (2 ** retry_count)
                    backoff_sec = notification.backoff_seconds * (2 ** (notification.retry_count - 1))
                    next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff_sec)
                    notification.status = NotificationStatus.RETRIED.value
                    notification.next_retry_at = next_retry.isoformat()
                else:
                    notification.status = NotificationStatus.FAILED.value
                    notification.next_retry_at = None

        except Exception as exc:
            notification.error_message = str(exc)
            if notification.retry_count < notification.max_retries:
                notification.retry_count += 1
                backoff_sec = notification.backoff_seconds * (2 ** (notification.retry_count - 1))
                next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff_sec)
                notification.status = NotificationStatus.RETRIED.value
                notification.next_retry_at = next_retry.isoformat()
            else:
                notification.status = NotificationStatus.FAILED.value

        self.db.update_notification(notification)
        return notification

    async def process_queue(self, limit: int = 50) -> Dict[str, Any]:
        """Process pending queued or due retry notifications."""
        now = datetime.now(timezone.utc)
        pending = self.db.get_pending_notifications(limit=limit)
        
        processed_count = 0
        delivered_count = 0
        failed_count = 0
        retried_count = 0

        for notif in pending:
            # If notification is retried, check if backoff duration has elapsed
            if notif.status == NotificationStatus.RETRIED.value and notif.next_retry_at:
                try:
                    retry_time = datetime.fromisoformat(notif.next_retry_at.replace("Z", "+00:00"))
                    if retry_time > now:
                        continue  # Not due for retry yet
                except Exception:
                    pass

            dispatched = await self.dispatch_single(notif)
            processed_count += 1

            if dispatched.status == NotificationStatus.DELIVERED.value:
                delivered_count += 1
            elif dispatched.status == NotificationStatus.FAILED.value:
                failed_count += 1
            elif dispatched.status == NotificationStatus.RETRIED.value:
                retried_count += 1

        return {
            "processed": processed_count,
            "delivered": delivered_count,
            "failed": failed_count,
            "retried": retried_count,
            "remaining_queue_depth": len(self.db.get_pending_notifications(limit=100)),
        }
