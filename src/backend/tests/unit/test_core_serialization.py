from __future__ import annotations

from datetime import datetime

from participium.core.serialization import (
    serialize_message,
    serialize_notification,
    serialize_user,
)
from participium.models.enums import NotificationType, Role
from participium.models.message import Message
from participium.models.notification import Notification
from participium.models.user import User


def build_user() -> User:
    user = User()

    user.id = 1
    user.username = "amin"
    user.first_name = "Amin"
    user.last_name = "Berangi"
    user.email = "amin@example.com"
    user.role = Role.CITIZEN
    user.category_id = None
    user.category = None
    user.is_active = True
    user.is_email_verified = True
    user.email_notifications_enabled = True
    user.profile_picture_path = None
    user.created_at = datetime(2026, 5, 31, 12, 0, 0)

    return user


def test_serialize_user_returns_expected_fields():
    user = build_user()

    result = serialize_user(user)

    assert result["id"] == 1
    assert result["username"] == "amin"
    assert result["email"] == "amin@example.com"
    assert result["role"] == "citizen"
    assert result["is_active"] is True
    assert result["is_email_verified"] is True


def test_serialize_notification_returns_expected_fields():
    notification = Notification()

    notification.id = 10
    notification.type = NotificationType.STATUS_CHANGE
    notification.title = "Status changed"
    notification.body = "Report status updated"
    notification.report_id = 5
    notification.is_read = False
    notification.created_at = datetime(2026, 5, 31, 13, 0, 0)

    result = serialize_notification(notification)

    assert result["id"] == 10
    assert result["type"] == NotificationType.STATUS_CHANGE.value
    assert result["title"] == "Status changed"
    assert result["report_id"] == 5
    assert result["is_read"] is False

def test_serialize_message_returns_expected_fields():
    sender = build_user()

    recipient = build_user()
    recipient.id = 2
    recipient.username = "receiver"

    message = Message()

    message.id = 100
    message.report_id = 50
    message.body = "Test message"
    message.sender = sender
    message.recipient = recipient
    message.created_at = datetime(2026, 5, 31, 14, 0, 0)

    result = serialize_message(message)

    assert result["id"] == 100
    assert result["report_id"] == 50
    assert result["body"] == "Test message"
    assert result["sender"]["id"] == 1
    assert result["recipient"]["id"] == 2