from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from participium.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
)

from participium.models.enums import ReportStatus, Role
from participium.models.report import Report
from participium.models.user import User
from participium.services.report_service import ReportService


def build_report_service():

    return ReportService(
        session=MagicMock(),
        report_repository=MagicMock(),
        category_repository=MagicMock(),
        storage_service=MagicMock(),
        notification_service=MagicMock(),
    )


def build_admin_user():

    user = User()
    user.id = 1
    user.role = Role.ADMIN

    return user


def build_citizen_user():

    user = User()
    user.id = 2
    user.role = Role.CITIZEN

    return user


def build_report(status=ReportStatus.ASSIGNED):

    report = Report()
    report.id = 1
    report.status = status

    return report


def test_update_status_success(): #--> status01

    service = build_report_service()

    admin = build_admin_user()

    fake_report = build_report()

    service.get_report = MagicMock(return_value=fake_report)

    service._ensure_operator_category_access = MagicMock()

    result = service.update_status(
        report_id=1,
        operator=admin,
        next_status_value="Resolved",
        note="fixed",
    )

    assert result is not None


def test_update_status_unauthorized_user(): #--> status02

    service = build_report_service()

    citizen = build_citizen_user()

    with pytest.raises(AuthorizationError):
        service.update_status(
            report_id=1,
            operator=citizen,
            next_status_value="Resolved",
            note="fixed",
        )


def test_update_status_report_not_found(): #--> status03

    service = build_report_service()

    admin = build_admin_user()

    service.get_report = MagicMock(
        side_effect=NotFoundError("Report not found.")
    )

    with pytest.raises(NotFoundError):
        service.update_status(
            report_id=999,
            operator=admin,
            next_status_value="Resolved",
            note="fixed",
        )


def test_update_status_invalid_status_value(): #--> status04

    service = build_report_service()

    admin = build_admin_user()

    fake_report = build_report()

    service.get_report = MagicMock(return_value=fake_report)

    service._ensure_operator_category_access = MagicMock()

    with pytest.raises(ValidationError):
        service.update_status(
            report_id=1,
            operator=admin,
            next_status_value="InvalidStatus",
            note="fixed",
        )


def test_update_status_rejected_without_note(): #--> status05

    service = build_report_service()

    admin = build_admin_user()

    fake_report = build_report()

    service.get_report = MagicMock(return_value=fake_report)

    service._ensure_operator_category_access = MagicMock()

    with pytest.raises(ValidationError):
        service.update_status(
            report_id=1,
            operator=admin,
            next_status_value="Rejected",
            note=None,
        )


def test_update_status_operator_outside_category(): #--> status06

    service = build_report_service()

    admin = build_admin_user()

    fake_report = build_report()

    service.get_report = MagicMock(return_value=fake_report)

    service._ensure_operator_category_access = MagicMock(
        side_effect=AuthorizationError("Forbidden category.")
    )

    with pytest.raises(AuthorizationError):
        service.update_status(
            report_id=1,
            operator=admin,
            next_status_value="Resolved",
            note="fixed",
        )


def test_update_status_invalid_workflow_transition(): #status07

    service = build_report_service()

    admin = build_admin_user()

    fake_report = build_report(status=ReportStatus.RESOLVED)

    service.get_report = MagicMock(return_value=fake_report)

    service._ensure_operator_category_access = MagicMock()

    with pytest.raises(ValidationError):
        service.update_status(
            report_id=1,
            operator=admin,
            next_status_value="Assigned",
            note="invalid transition",
        )
