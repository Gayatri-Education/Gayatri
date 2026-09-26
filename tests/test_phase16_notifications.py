"""Unit and integration test suite for Phase 16: Notification Abstraction Engine."""

import pytest
from central_platform.notifications import (
    DeliveryStatus,
    NotificationChannel,
    NotificationManager,
)


@pytest.fixture
def notif_manager():
    return NotificationManager()


def test_successful_notification_dispatch(notif_manager):
    msg = notif_manager.send_notification(
        recipient_id="user-123",
        channel=NotificationChannel.IN_APP,
        title="Assignment Due",
        body="Physics Quiz 1 is due tomorrow at 5 PM.",
    )
    assert msg.status == DeliveryStatus.DELIVERED
    assert len(notif_manager.get_user_notifications("user-123")) == 1


def test_channel_preference_filtering(notif_manager):
    # Restrict user to IN_APP only
    notif_manager.set_user_channels("user-456", [NotificationChannel.IN_APP])

    # Attempt email dispatch
    msg = notif_manager.send_notification(
        recipient_id="user-456",
        channel=NotificationChannel.EMAIL,
        title="Welcome",
        body="Welcome to Gayatri Platform",
    )
    assert msg.status == DeliveryStatus.FAILED
    assert "Channel disabled" in msg.metadata.get("error", "")


def test_notification_retry_queue(notif_manager):
    # Simulate initial delivery failure
    failed_msg = notif_manager.send_notification(
        recipient_id="user-789",
        channel=NotificationChannel.IN_APP,
        title="System Alert",
        body="Maintenance scheduled",
        simulate_failure=True,
    )
    assert failed_msg.status == DeliveryStatus.FAILED

    # Process retry queue
    retried_list = notif_manager.process_retry_queue()
    assert len(retried_list) == 1
    assert retried_list[0].status == DeliveryStatus.DELIVERED
    assert retried_list[0].retry_count == 1
