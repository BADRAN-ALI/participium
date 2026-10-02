from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from participium.models.enums import NotificationType
from participium.services.notification_service import NotificationService

pytestmark = pytest.mark.whitebox


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_recipient(user_id: int) -> Mock:
    user = Mock()
    user.id = user_id
    return user


@pytest.fixture
def notification_service() -> NotificationService:
    return NotificationService(
        session=Mock(),
        notification_repository=Mock(),
        email_gateway=Mock(),
    )


# ---------------------------------------------------------------------------
# TC-WB-NS-01  empty recipients list → loop not entered, create_notification never called
# Covers: loop zero-iteration path
# ---------------------------------------------------------------------------
def test_notify_status_change_empty_list_does_nothing(
    notification_service: NotificationService,
) -> None:
    report = Mock()
    report.id = 1

    with patch.object(notification_service, "create_notification") as mock_create:
        notification_service.notify_status_change([], report, "Status updated")

    mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# TC-WB-NS-02  single valid recipient → create_notification called once with correct args
# Covers: C1=False (not None), C2=False (id not in seen) → notification created
# ---------------------------------------------------------------------------
def test_notify_status_change_single_recipient_calls_create_notification(
    notification_service: NotificationService,
) -> None:
    recipient = _make_recipient(user_id=10)
    report = Mock()
    report.id = 42

    with patch.object(notification_service, "create_notification") as mock_create:
        notification_service.notify_status_change([recipient], report, "Assigned")

    mock_create.assert_called_once_with(
        recipient,
        NotificationType.STATUS_CHANGE,
        "Report #42 status updated",
        "Assigned",
        report=report,
    )


# ---------------------------------------------------------------------------
# TC-WB-NS-03  None in recipients list → skipped, create_notification not called
# Covers: C1=True (recipient is None) → continue
# ---------------------------------------------------------------------------
def test_notify_status_change_none_recipient_skipped(
    notification_service: NotificationService,
) -> None:
    report = Mock()
    report.id = 1

    with patch.object(notification_service, "create_notification") as mock_create:
        notification_service.notify_status_change([None], report, "Resolved")

    mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# TC-WB-NS-04  same recipient object twice → called only once (deduplication via seen set)
# Covers: C1=False, C2=True (id already in seen) on second iteration
# ---------------------------------------------------------------------------
def test_notify_status_change_duplicate_recipient_deduped(
    notification_service: NotificationService,
) -> None:
    recipient = _make_recipient(user_id=7)
    report = Mock()
    report.id = 2

    with patch.object(notification_service, "create_notification") as mock_create:
        notification_service.notify_status_change([recipient, recipient], report, "In Progress")

    mock_create.assert_called_once()


# ---------------------------------------------------------------------------
# TC-WB-NS-05  mixed list: None, duplicate, two distinct → create_notification called twice
# Covers: all three skip/proceed branches exercised in a single invocation
# ---------------------------------------------------------------------------
def test_notify_status_change_mixed_list_correct_call_count(
    notification_service: NotificationService,
) -> None:
    r1 = _make_recipient(user_id=1)
    r2 = _make_recipient(user_id=2)
    report = Mock()
    report.id = 3

    with patch.object(notification_service, "create_notification") as mock_create:
        notification_service.notify_status_change([r1, None, r1, r2], report, "Resolved")

    assert mock_create.call_count == 2
