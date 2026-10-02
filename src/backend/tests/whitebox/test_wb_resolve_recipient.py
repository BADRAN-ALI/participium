from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.models.enums import Role
from participium.services.messaging_service import MessagingService

pytestmark = pytest.mark.whitebox


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_user(role: Role, user_id: int = 1) -> Mock:
    user = Mock()
    user.id = user_id
    user.role = role
    return user


def _make_message(sender: Mock | None) -> Mock:
    msg = Mock()
    msg.sender = sender
    return msg


def _make_status_event(changed_by: Mock | None) -> Mock:
    event = Mock()
    event.changed_by = changed_by
    return event


@pytest.fixture
def messaging_service() -> MessagingService:
    return MessagingService(
        session=Mock(),
        report_repository=Mock(),
        message_repository=Mock(),
        notification_service=Mock(),
    )


# ---------------------------------------------------------------------------
# TC-WB-RR-01  sender is ADMIN → returns report.reporter without consulting messages
# Covers: C1=True (sender in {ADMIN, OPERATOR})
# ---------------------------------------------------------------------------
def test_resolve_recipient_admin_sender_returns_reporter(
    messaging_service: MessagingService,
) -> None:
    reporter = _make_user(Role.CITIZEN, user_id=99)
    report = Mock()
    report.reporter = reporter

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.ADMIN))

    assert result is reporter
    messaging_service.message_repository.list_for_report.assert_not_called()


# ---------------------------------------------------------------------------
# TC-WB-RR-02  sender is OPERATOR → returns report.reporter without consulting messages
# Covers: C1=True (OPERATOR branch)
# ---------------------------------------------------------------------------
def test_resolve_recipient_operator_sender_returns_reporter(
    messaging_service: MessagingService,
) -> None:
    reporter = _make_user(Role.CITIZEN, user_id=88)
    report = Mock()
    report.reporter = reporter

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.OPERATOR))

    assert result is reporter
    messaging_service.message_repository.list_for_report.assert_not_called()


# ---------------------------------------------------------------------------
# TC-WB-RR-03  sender is CITIZEN, no messages, empty status history → None
# Covers: C1=False; both loops entered but immediately exhausted
# ---------------------------------------------------------------------------
def test_resolve_recipient_citizen_no_messages_no_history_returns_none(
    messaging_service: MessagingService,
) -> None:
    report = Mock()
    report.id = 1
    report.status_history = []
    messaging_service.message_repository.list_for_report.return_value = []

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN))

    assert result is None


# ---------------------------------------------------------------------------
# TC-WB-RR-04  sender is CITIZEN, messages present but none from operator/admin → None
# Covers: C2=True (sender exists), C3=False (sender is CITIZEN)
# ---------------------------------------------------------------------------
def test_resolve_recipient_citizen_messages_no_operator_sender_returns_none(
    messaging_service: MessagingService,
) -> None:
    citizen_sender = _make_user(Role.CITIZEN, user_id=7)
    report = Mock()
    report.id = 1
    report.status_history = []
    messaging_service.message_repository.list_for_report.return_value = [
        _make_message(sender=citizen_sender),
    ]

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN, user_id=5))

    assert result is None


# ---------------------------------------------------------------------------
# TC-WB-RR-05  sender is CITIZEN, message exists but has None sender → skipped
# Covers: C2=False (message.sender is None)
# ---------------------------------------------------------------------------
def test_resolve_recipient_message_with_none_sender_is_skipped(
    messaging_service: MessagingService,
) -> None:
    report = Mock()
    report.id = 1
    report.status_history = []
    messaging_service.message_repository.list_for_report.return_value = [
        _make_message(sender=None),
    ]

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN))

    assert result is None


# ---------------------------------------------------------------------------
# TC-WB-RR-06  sender is CITIZEN, latest message is from an OPERATOR → return that sender
# Covers: C2=True, C3=True (sender is OPERATOR) → early return from first loop
# ---------------------------------------------------------------------------
def test_resolve_recipient_citizen_message_from_operator_returned(
    messaging_service: MessagingService,
) -> None:
    operator = _make_user(Role.OPERATOR, user_id=20)
    report = Mock()
    report.id = 1
    report.status_history = []
    messaging_service.message_repository.list_for_report.return_value = [
        _make_message(sender=_make_user(Role.CITIZEN, user_id=3)),
        _make_message(sender=operator),
    ]

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN, user_id=5))

    assert result is operator


# ---------------------------------------------------------------------------
# TC-WB-RR-07  no operator messages; status history entry changed by ADMIN → returned
# Covers: first loop fully exhausted; C4=True, C5=True in second loop
# ---------------------------------------------------------------------------
def test_resolve_recipient_history_entry_from_admin_returned(
    messaging_service: MessagingService,
) -> None:
    admin_changer = _make_user(Role.ADMIN, user_id=1)
    status_event = _make_status_event(changed_by=admin_changer)
    report = Mock()
    report.id = 1
    report.status_history = [status_event]
    messaging_service.message_repository.list_for_report.return_value = []

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN))

    assert result is admin_changer


# ---------------------------------------------------------------------------
# TC-WB-RR-08  status event has changed_by=None → skipped → returns None
# Covers: C4=False (changed_by is None) in second loop
# ---------------------------------------------------------------------------
def test_resolve_recipient_history_with_none_changed_by_returns_none(
    messaging_service: MessagingService,
) -> None:
    status_event = _make_status_event(changed_by=None)
    report = Mock()
    report.id = 1
    report.status_history = [status_event]
    messaging_service.message_repository.list_for_report.return_value = []

    result = messaging_service._resolve_recipient(report, sender=_make_user(Role.CITIZEN))

    assert result is None
