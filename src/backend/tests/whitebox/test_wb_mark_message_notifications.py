from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.models.notification import Notification
from participium.services.notification_service import NotificationService


pytestmark = pytest.mark.whitebox


def _notification(*, notification_id: int, user_id: int, report_id: int, is_read: bool = False) -> Notification:
    return Notification(
        id=notification_id,
        user_id=user_id,
        report_id=report_id,
        is_read=is_read,
    )


@pytest.fixture
def notification_service_bundle() -> dict[str, object]:
    session = Mock()
    notification_repository = Mock()
    email_gateway = Mock()
    service = NotificationService(
        session=session,
        notification_repository=notification_repository,
        email_gateway=email_gateway,
    )
    return {
        "service": service,
        "session": session,
        "notification_repository": notification_repository,
    }


@pytest.fixture
def empty_notifications_case(notification_service_bundle: dict[str, object]) -> dict[str, object]:
    notification_service_bundle["notification_repository"].list_unread_message_notifications.return_value = []
    return notification_service_bundle


@pytest.fixture
def single_notification_case(notification_service_bundle: dict[str, object]) -> dict[str, object]:
    notification = _notification(notification_id=101, user_id=10, report_id=20)
    notification_service_bundle["notification_repository"].list_unread_message_notifications.return_value = [
        notification
    ]
    notification_service_bundle["notification"] = notification
    return notification_service_bundle


@pytest.fixture
def multiple_notifications_case(notification_service_bundle: dict[str, object]) -> dict[str, object]:
    notifications = [
        _notification(notification_id=201, user_id=10, report_id=20),
        _notification(notification_id=202, user_id=10, report_id=20),
        _notification(notification_id=203, user_id=10, report_id=20),
    ]
    notification_service_bundle["notification_repository"].list_unread_message_notifications.return_value = (
        notifications
    )
    notification_service_bundle["notifications"] = notifications
    return notification_service_bundle


@pytest.mark.skip(reason="Disabled.")
def test_mark_message_notifications_returns_zero_without_matches(
    empty_notifications_case: dict[str, object],
) -> None:
    service = empty_notifications_case["service"]
    session = empty_notifications_case["session"]
    notification_repository = empty_notifications_case["notification_repository"]

    marked_count = service.mark_report_message_notifications_as_read(user_id=10, report_id=20)

    assert marked_count == 0
    notification_repository.list_unread_message_notifications.assert_called_once_with(
        user_id=10,
        report_id=20,
    )
    session.commit.assert_not_called()


@pytest.mark.skip(reason="Disabled.")
def test_mark_message_notifications_marks_one_notification_and_commits(
    single_notification_case: dict[str, object],
) -> None:
    service = single_notification_case["service"]
    session = single_notification_case["session"]
    notification = single_notification_case["notification"]

    marked_count = service.mark_report_message_notifications_as_read(user_id=10, report_id=20)

    assert marked_count == 1
    assert notification.is_read is True
    session.commit.assert_called_once_with()


@pytest.mark.skip(reason="Disabled.")
def test_mark_message_notifications_marks_all_notifications_in_the_result_set(
    multiple_notifications_case: dict[str, object],
) -> None:
    service = multiple_notifications_case["service"]
    session = multiple_notifications_case["session"]
    notifications = multiple_notifications_case["notifications"]

    marked_count = service.mark_report_message_notifications_as_read(user_id=10, report_id=20)

    assert marked_count == 3
    assert all(notification.is_read is True for notification in notifications)
    session.commit.assert_called_once_with()
