from __future__ import annotations

from unittest.mock import MagicMock

from participium.models.enums import NotificationType
from participium.models.report import Report
from participium.models.user import User
from participium.models.notification import Notification
from participium.services.notification_service import NotificationService


def build_notification_service():

    return NotificationService(
        session=MagicMock(),
        notification_repository=MagicMock(),
        email_gateway=MagicMock(),
    )


def build_user():

    user = User()

    user.id = 1
    user.email = "test@example.com"
    user.email_notifications_enabled = True

    return user


def build_report(): #Lo tengo per generalizzare meglio la bb

    report = Report()

    report.id = 10

    return report


def test_create_notification_success():

    service = build_notification_service()

    user = build_user()

    report = build_report()

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.SYSTEM,
        title="Report created",
        body="Your report was created",
        report=report,
    )

    assert result is not None
    assert isinstance(result, Notification)
    assert result.user_id == user.id
    assert result.report_id == report.id


def test_create_notification_without_user():

    service = build_notification_service()

    report = build_report()

    result = service.create_notification(
        user=None,
        notification_type=NotificationType.SYSTEM,
        title="Report created",
        body="Body",
        report=report,
    )

    assert result is None


def test_create_notification_without_report():

    service = build_notification_service()

    user = build_user()

    result = service.create_notification(
        user=user,
        notification_type=NotificationType.STATUS_CHANGE,
        title="Status updated",
        body="Body",
        report=None,
    )

    assert result is not None
    assert result.report_id is None
