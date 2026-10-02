from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from participium.core.exceptions import (
    AuthorizationError,
    ValidationError,
)

from participium.models.message import Message
from participium.models.report import Report
from participium.models.user import User
from participium.services.messaging_service import MessagingService


def build_messaging_service():

    return MessagingService(
        session=MagicMock(),
        report_repository=MagicMock(),
        message_repository=MagicMock(),
        notification_service=MagicMock(),
    )


def build_user(user_id=1):

    user = User()
    user.id = user_id

    return user


def build_report(report_id=1):

    report = Report()
    report.id = report_id

    return report


def test_send_message_success():

    service = build_messaging_service()

    report = build_report()

    sender = build_user(1)

    recipient = build_user(2)

    service._ensure_access = MagicMock()

    service._resolve_recipient = MagicMock(
        return_value=recipient
    )

    result = service.send_message(
        report=report,
        sender=sender,
        body="Hello"
    )

    assert result is not None
    assert isinstance(result, Message)
    assert result.body == "Hello"


def test_send_message_unauthorized_user():

    service = build_messaging_service()

    report = build_report()

    sender = build_user()

    service._ensure_access = MagicMock(
        side_effect=AuthorizationError("Forbidden")
    )

    with pytest.raises(AuthorizationError):
        service.send_message(
            report=report,
            sender=sender,
            body="Hello"
        )


def test_send_message_empty_body():

    service = build_messaging_service()

    report = build_report()

    sender = build_user()

    service._ensure_access = MagicMock()

    with pytest.raises(ValidationError):
        service.send_message(
            report=report,
            sender=sender,
            body=""
        )


def test_send_message_blank_body():

    service = build_messaging_service()

    report = build_report()

    sender = build_user()

    service._ensure_access = MagicMock()

    with pytest.raises(ValidationError):
        service.send_message(
            report=report,
            sender=sender,
            body="   "
        )


def test_send_message_without_recipient():

    service = build_messaging_service()

    report = build_report()

    sender = build_user()

    service._ensure_access = MagicMock()

    service._resolve_recipient = MagicMock(
        return_value=None
    )

    with pytest.raises(ValidationError):
        service.send_message(
            report=report,
            sender=sender,
            body="Hello"
        )
