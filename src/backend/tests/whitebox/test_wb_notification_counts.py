from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.models.enums import NotificationType
from participium.models.notification import Notification
from participium.services.notification_service import NotificationService

pytestmark = pytest.mark.whitebox


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _notification(report_id: int | None) -> Notification:
    n = Notification(
        user_id=1,
        type=NotificationType.MESSAGE,
        title="t",
        body="b",
        is_read=False,
        report_id=report_id,
    )
    return n


@pytest.fixture
def bundle() -> tuple[NotificationService, Mock]:
    repo = Mock()
    service = NotificationService(
        session=Mock(),
        notification_repository=repo,
        email_gateway=Mock(),
    )
    return service, repo


# ---------------------------------------------------------------------------
# TC-WB-NC-01  no notifications → empty dict (loop never entered)
# Covers: loop zero-iteration path
# ---------------------------------------------------------------------------
def test_count_unread_no_notifications_returns_empty_dict(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = []

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {}


# ---------------------------------------------------------------------------
# TC-WB-NC-02  all notifications have report_id=None → every entry skipped, empty dict
# Covers: C1=True (report_id is None) for all iterations
# ---------------------------------------------------------------------------
def test_count_unread_all_null_report_ids_returns_empty_dict(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = [
        _notification(None),
        _notification(None),
    ]

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {}


# ---------------------------------------------------------------------------
# TC-WB-NC-03  single notification with a valid report_id → {report_id: 1}
# Covers: C1=False (report_id is not None); counts.get returns default 0 → increments to 1
# ---------------------------------------------------------------------------
def test_count_unread_single_notification_returns_one(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = [_notification(report_id=10)]

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {10: 1}


# ---------------------------------------------------------------------------
# TC-WB-NC-04  multiple notifications for the same report → count incremented per iteration
# Covers: loop with multiple iterations; counter increments beyond 1
# ---------------------------------------------------------------------------
def test_count_unread_multiple_same_report_increments_correctly(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = [
        _notification(report_id=10),
        _notification(report_id=10),
        _notification(report_id=10),
    ]

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {10: 3}


# ---------------------------------------------------------------------------
# TC-WB-NC-05  notifications for different reports → correct per-report counts
# Covers: multiple distinct report_id keys accumulate independently
# ---------------------------------------------------------------------------
def test_count_unread_multiple_reports_counted_separately(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = [
        _notification(report_id=10),
        _notification(report_id=20),
        _notification(report_id=10),
    ]

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {10: 2, 20: 1}


# ---------------------------------------------------------------------------
# TC-WB-NC-06  mix of None and valid report_ids → None entries skipped, valid counted
# Covers: C1=True and C1=False in the same pass
# ---------------------------------------------------------------------------
def test_count_unread_mixed_null_and_valid_report_ids(bundle) -> None:
    service, repo = bundle
    repo.list_unread_message_notifications.return_value = [
        _notification(None),
        _notification(report_id=5),
        _notification(None),
        _notification(report_id=5),
    ]

    result = service.count_unread_message_notifications_by_report(user_id=1)

    assert result == {5: 2}
