from __future__ import annotations

from datetime import datetime

from unittest.mock import MagicMock

from participium.models.enums import ReportStatus
from participium.models.report import Report
from participium.services.report_service import ReportService


def build_report_service(mock_report_repository):

    return ReportService(
        session=MagicMock(),
        report_repository=mock_report_repository,
        category_repository=MagicMock(),
        storage_service=MagicMock(),
        notification_service=MagicMock(),
    )


def test_list_public_reports_default_descending():

    fake_reports = [Report(), Report()]

    mock_report_repo = MagicMock()
    mock_report_repo.list_reports.return_value = fake_reports

    service = build_report_service(mock_report_repo)

    result = service.list_public_reports()

    assert isinstance(result, list)
    assert result == fake_reports
    assert len(result) == 2


def test_list_public_reports_filtered_by_category():

    fake_reports = [Report()]

    mock_report_repo = MagicMock()
    mock_report_repo.list_reports.return_value = fake_reports

    service = build_report_service(mock_report_repo)

    result = service.list_public_reports(
        category_id=1,
        sort="asc",
    )

    assert result == fake_reports
    assert len(result) == 1


def test_list_public_reports_filtered_by_status():

    fake_reports = [Report()]

    mock_report_repo = MagicMock()
    mock_report_repo.list_reports.return_value = fake_reports

    service = build_report_service(mock_report_repo)

    result = service.list_public_reports(
        status=ReportStatus.RESOLVED,
    )

    assert result == fake_reports


def test_list_public_reports_filtered_by_date_range():

    fake_reports = [Report()]

    mock_report_repo = MagicMock()
    mock_report_repo.list_reports.return_value = fake_reports

    service = build_report_service(mock_report_repo)

    result = service.list_public_reports(
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 12, 31),
    )

    assert result == fake_reports


def test_list_public_reports_empty_result():

    mock_report_repo = MagicMock()
    mock_report_repo.list_reports.return_value = []

    service = build_report_service(mock_report_repo)

    result = service.list_public_reports(
        category_id=999,
    )

    assert result == []
    assert len(result) == 0
