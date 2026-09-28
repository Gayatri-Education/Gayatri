"""Comprehensive Verification Test Suite for Phase 21: Multi-Channel Notifications Platform.

Master Plan Section 30:
1. Multi-channel delivery abstraction: in-app, email, push, WhatsApp.
2. Asynchronous persistent queueing with worker processing.
3. State machine tracking: created -> queued -> sent -> delivered -> failed -> retried.
4. Exponential backoff retry mechanics for transient errors.
5. Max retries enforcement and terminal failure state.
6. Provider confirmation requirement before marking delivered.
7. Read/unread lifecycle, batch dispatch, and queue telemetry.
8. REST API endpoints and strict RBAC authorization boundaries.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import create_app
from central_platform.api.routes.notifications import get_notification_service
from central_platform.auth.dependencies import get_current_user, get_db
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.models.schema import Notification, Organization, User, UserRole
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


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "notifications_test.db")
    return PlatformDatabase(db_path=db_path)


@pytest.fixture
def notification_service(test_db):
    registry = ProviderRegistry()
    queue = NotificationQueueManager(test_db, registry)
    return NotificationService(db=test_db, queue_manager=queue, provider_registry=registry)


@pytest.fixture
def api_client(test_db, notification_service):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_notification_service] = lambda: notification_service
    return TestClient(app)


def _auth_header(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(
        user_id=user.id,
        role=role_str.upper(),
        organization_id=user.organization_id,
    )
    return {"Authorization": f"Bearer {token}"}


# ── 1. Multi-Channel Delivery Unit Tests ─────────────────────────────────────

@pytest.mark.anyio
async def test_all_channels_delivery(notification_service, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    student_id = f"stu_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))
    test_db.create_user(User(id=student_id, organization_id=org_id, email=f"{student_id}@test.com", role=UserRole.STUDENT, full_name="Student One"))

    channels = [
        (NotificationChannel.IN_APP, "In-App Directive", "Review first law of thermodynamics."),
        (NotificationChannel.EMAIL, "Weekly Progress Report", "Your weekly mastery score is 88%."),
        (NotificationChannel.PUSH, "Study Reminder", "Time for your 15-minute spaced review session."),
        (NotificationChannel.WHATSAPP, "Exam Alert", "Physics Midterm is scheduled for tomorrow 10:00 AM."),
    ]

    for channel, title, msg in channels:
        notif = await notification_service.send_notification(
            recipient_id=student_id,
            title=title,
            message=msg,
            channel=channel,
            sync_deliver=True,
        )

        assert notif.recipient_id == student_id
        assert notif.channel == channel.value
        assert notif.status == NotificationStatus.DELIVERED.value
        assert notif.provider_message_id is not None
        assert notif.delivered_at is not None

        # Verify persisted in database
        db_notif = notification_service.get_notification(notif.id)
        assert db_notif is not None
        assert db_notif.status == NotificationStatus.DELIVERED.value


# ── 2. Queueing and Exponential Backoff Retry ────────────────────────────────

@pytest.mark.anyio
async def test_queue_and_exponential_backoff_retry(notification_service, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    student_id = f"stu_retry_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))
    test_db.create_user(User(id=student_id, organization_id=org_id, email=f"{student_id}@test.com", role=UserRole.STUDENT, full_name="Student Retry"))

    # 1. Dispatch with simulated transient provider error (sync_deliver=False to enqueue first)
    notif = await notification_service.send_notification(
        recipient_id=student_id,
        title="Transient Alert",
        message="System checking in.",
        channel=NotificationChannel.EMAIL,
        metadata={"simulate_provider_error": True},
        sync_deliver=False,
    )
    assert notif.status == NotificationStatus.QUEUED.value

    # Process queue -> should attempt delivery and fail with RETRIED status and exponential backoff
    res = await notification_service.process_queue(limit=10)
    assert res["processed"] == 1
    assert res["retried"] == 1

    updated_notif = notification_service.get_notification(notif.id)
    assert updated_notif.status == NotificationStatus.RETRIED.value
    assert updated_notif.retry_count == 1
    assert updated_notif.next_retry_at is not None
    assert "SMTP server connection timeout" in updated_notif.error_message


@pytest.mark.anyio
async def test_max_retries_dead_letter_failure(notification_service, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    student_id = f"stu_dead_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))
    test_db.create_user(User(id=student_id, organization_id=org_id, email=f"{student_id}@test.com", role=UserRole.STUDENT, full_name="Student Dead"))

    # Create notification with retry_count already at max_retries
    notif = Notification(
        id=f"notif_max_{uuid.uuid4().hex[:6]}",
        recipient_id=student_id,
        title="Failing Alert",
        message="Will fail permanently.",
        channel="email",
        status="retried",
        retry_count=3,
        max_retries=3,
        metadata={"simulate_provider_error": True},
    )
    test_db.create_notification(notif)

    # Process queue -> should exceed max retries and transition to FAILED
    await notification_service.queue.dispatch_single(notif)

    failed_notif = notification_service.get_notification(notif.id)
    assert failed_notif.status == NotificationStatus.FAILED.value
    assert failed_notif.retry_count == 3


# ── 3. Read/Unread Lifecycle and Batch Dispatch ───────────────────────────────

@pytest.mark.anyio
async def test_batch_dispatch_and_read_lifecycle(notification_service, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="Test Org", slug=org_id))

    students = []
    for i in range(3):
        sid = f"stu_batch_{i}_{uuid.uuid4().hex[:4]}"
        test_db.create_user(User(id=sid, organization_id=org_id, email=f"{sid}@test.com", role=UserRole.STUDENT, full_name=f"Student {i}"))
        students.append(sid)

    # Batch dispatch
    batch_results = await notification_service.send_batch(
        recipient_ids=students,
        title="Class Announcement",
        message="Class session starts at 9:00 AM tomorrow.",
        channel=NotificationChannel.IN_APP,
    )

    assert len(batch_results) == 3
    for n in batch_results:
        assert n.status == NotificationStatus.DELIVERED.value
        assert n.is_read is False

    # Mark single as read
    first_notif = batch_results[0]
    marked = notification_service.mark_as_read(first_notif.id, recipient_id=students[0])
    assert marked is True

    # Check unread only query
    unread = notification_service.get_user_notifications(recipient_id=students[0], unread_only=True)
    assert len(unread) == 0

    all_notifs = notification_service.get_user_notifications(recipient_id=students[0], unread_only=False)
    assert len(all_notifs) == 1
    assert all_notifs[0].is_read is True


# ── 4. REST API & RBAC Integration Tests ──────────────────────────────────────

def test_notifications_rest_api_and_rbac(api_client, test_db):
    org_id = f"org_{uuid.uuid4().hex[:6]}"
    test_db.create_organization(Organization(id=org_id, name="API Org", slug=org_id))

    student_user = User(
        id=f"stu_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="student.notif@test.com",
        role=UserRole.STUDENT,
        full_name="Student API",
    )
    test_db.create_user(student_user)

    teacher_user = User(
        id=f"tea_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="teacher.notif@test.com",
        role=UserRole.TEACHER,
        full_name="Teacher API",
    )
    test_db.create_user(teacher_user)

    admin_user = User(
        id=f"adm_api_{uuid.uuid4().hex[:6]}",
        organization_id=org_id,
        email="admin.notif@test.com",
        role=UserRole.SUPER_ADMIN,
        full_name="Admin API",
    )
    test_db.create_user(admin_user)

    stu_headers = _auth_header(student_user)
    tea_headers = _auth_header(teacher_user)
    adm_headers = _auth_header(admin_user)

    # 1. Teacher creates a notification for student -> 200 OK
    res_create = api_client.post(
        "/api/v1/notifications",
        json={
            "recipient_id": student_user.id,
            "title": "Assignment Released",
            "message": "Thermodynamics Quiz 1 is now available.",
            "channel": "in_app",
            "sync_deliver": True,
        },
        headers=tea_headers,
    )
    assert res_create.status_code == 200
    notif_data = res_create.json()["data"]
    notif_id = notif_data["id"]
    assert notif_data["recipient_id"] == student_user.id
    assert notif_data["status"] == "delivered"

    # 2. Student lists own notifications -> 200 OK
    res_list = api_client.get("/api/v1/notifications", headers=stu_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    # 3. Student attempts to dispatch a notification -> 403 Forbidden
    res_stu_send = api_client.post(
        "/api/v1/notifications",
        json={
            "recipient_id": teacher_user.id,
            "title": "Spam",
            "message": "Unauthorized alert",
            "channel": "in_app",
        },
        headers=stu_headers,
    )
    assert res_stu_send.status_code == 403

    # 4. Student checks status of own notification -> 200 OK
    res_status = api_client.get(f"/api/v1/notifications/{notif_id}/status", headers=stu_headers)
    assert res_status.status_code == 200
    assert res_status.json()["data"]["status"] == "delivered"

    # 5. Student marks notification as read -> 200 OK
    res_read = api_client.post(f"/api/v1/notifications/{notif_id}/read", headers=stu_headers)
    assert res_read.status_code == 200
    assert res_read.json()["data"]["is_read"] is True

    # 6. Admin checks queue stats -> 200 OK
    res_stats = api_client.get("/api/v1/notifications/queue/stats", headers=adm_headers)
    assert res_stats.status_code == 200
    assert "pending_count" in res_stats.json()["data"]
