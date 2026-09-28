"""Unified Notification Service for Gayatri AI Platform (Phase 21).

Coordinates multi-channel delivery, queueing, state tracking, and query capabilities.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Notification, User
from central_platform.notifications.models import NotificationChannel, NotificationStatus
from central_platform.notifications.providers import ProviderRegistry
from central_platform.notifications.queue import NotificationQueueManager


class NotificationService:
    """Central service managing notification lifecycle across in-app, email, push, and WhatsApp channels."""

    def __init__(
        self,
        db: Optional[PlatformDatabase] = None,
        queue_manager: Optional[NotificationQueueManager] = None,
        provider_registry: Optional[ProviderRegistry] = None,
    ):
        self.db = db or PlatformDatabase()
        self.registry = provider_registry or ProviderRegistry()
        self.queue = queue_manager or NotificationQueueManager(self.db, self.registry)

    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        message: str,
        channel: str | NotificationChannel = NotificationChannel.IN_APP,
        metadata: Optional[Dict[str, Any]] = None,
        sync_deliver: bool = True,
    ) -> Notification:
        """Create and dispatch a notification.
        
        If sync_deliver is True, attempts immediate delivery through target provider.
        If sync_deliver is False, enqueues the notification for background worker processing.
        """
        ch_str = channel.value if isinstance(channel, NotificationChannel) else str(channel).lower()
        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
        
        notif = Notification(
            id=notif_id,
            recipient_id=recipient_id,
            title=title,
            message=message,
            channel=ch_str,
            status=NotificationStatus.CREATED.value,
            metadata=metadata or {},
        )

        if sync_deliver:
            # Enqueue and immediately attempt dispatch
            await self.queue.enqueue(notif)
            return await self.queue.dispatch_single(notif)
        else:
            return await self.queue.enqueue(notif)

    async def send_batch(
        self,
        recipient_ids: List[str],
        title: str,
        message: str,
        channel: str | NotificationChannel = NotificationChannel.IN_APP,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Notification]:
        """Dispatch notifications in batch to multiple recipients."""
        results = []
        for rid in recipient_ids:
            res = await self.send_notification(
                recipient_id=rid,
                title=title,
                message=message,
                channel=channel,
                metadata=metadata,
                sync_deliver=True,
            )
            results.append(res)
        return results

    def get_user_notifications(
        self,
        recipient_id: str,
        unread_only: bool = False,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Query user notifications with unread, channel, and pagination filters."""
        return self.db.get_notifications(
            recipient_id=recipient_id,
            unread_only=unread_only,
            channel=channel,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Retrieve a specific notification record by ID."""
        return self.db.get_notification(notification_id)

    def mark_as_read(self, notification_id: str, recipient_id: Optional[str] = None) -> bool:
        """Mark a notification as read."""
        return self.db.mark_notification_read(notification_id, recipient_id)

    def mark_all_as_read(self, recipient_id: str) -> int:
        """Mark all notifications for a recipient as read."""
        return self.db.mark_all_notifications_read(recipient_id)

    async def process_queue(self, limit: int = 50) -> Dict[str, Any]:
        """Process pending items in the notification queue."""
        return await self.queue.process_queue(limit=limit)

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get summary statistics on queue depth and channel volume."""
        pending = self.db.get_pending_notifications(limit=1000)
        return {
            "pending_count": len(pending),
            "by_status": {
                "created": sum(1 for n in pending if n.status == "created"),
                "queued": sum(1 for n in pending if n.status == "queued"),
                "retried": sum(1 for n in pending if n.status == "retried"),
            },
            "by_channel": {
                "in_app": sum(1 for n in pending if n.channel == "in_app"),
                "email": sum(1 for n in pending if n.channel == "email"),
                "push": sum(1 for n in pending if n.channel == "push"),
                "whatsapp": sum(1 for n in pending if n.channel == "whatsapp"),
            },
        }
