"""Package init for central_platform.notifications."""

from central_platform.notifications.manager import (
    DeliveryStatus,
    NotificationChannel as LegacyNotificationChannel,
    NotificationManager,
    NotificationMessage,
)
from central_platform.notifications.models import (
    NotificationChannel,
    NotificationStatus,
    ProviderDeliveryResult,
)
from central_platform.notifications.providers import (
    BaseDeliveryProvider,
    EmailDeliveryProvider,
    InAppDeliveryProvider,
    ProviderRegistry,
    PushDeliveryProvider,
    WhatsAppDeliveryProvider,
)
from central_platform.notifications.queue import NotificationQueueManager
from central_platform.notifications.service import NotificationService

__all__ = [
    "NotificationManager",
    "NotificationChannel",
    "DeliveryStatus",
    "NotificationMessage",
    "NotificationStatus",
    "ProviderDeliveryResult",
    "BaseDeliveryProvider",
    "InAppDeliveryProvider",
    "EmailDeliveryProvider",
    "PushDeliveryProvider",
    "WhatsAppDeliveryProvider",
    "ProviderRegistry",
    "NotificationQueueManager",
    "NotificationService",
]
