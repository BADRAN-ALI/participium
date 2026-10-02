from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from participium.core.exceptions import ValidationError
from participium.models.category import Category
from participium.models.report import Report
from participium.models.user import User
from participium.services.report_service import ReportService


def build_report_service(
    mock_report_repository=None,
    mock_category_repository=None,
    mock_storage_service=None,
    ):

    return ReportService(
        session=MagicMock(),
        report_repository=mock_report_repository or MagicMock(),
        category_repository=mock_category_repository or MagicMock(),
        storage_service=mock_storage_service or MagicMock(),
        notification_service=MagicMock(),
    )


def build_fake_photo(filename="photo.jpg", content_type="image/jpeg"):

    photo = MagicMock()
    photo.filename = filename
    photo.content_type = content_type

    return photo


def test_create_report_success(): #--> report01

    fake_user = User()
    fake_user.id = 1

    fake_category = Category()
    fake_category.id = 1
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    mock_storage_service = MagicMock()
    mock_storage_service.save.return_value = "/fake/path/photo.jpg"

    mock_report_repo = MagicMock()

    service = build_report_service(
        mock_report_repository=mock_report_repo,
        mock_category_repository=mock_category_repo,
        mock_storage_service=mock_storage_service,
    )

    fake_photo = build_fake_photo()

    service.get_report = MagicMock(return_value=Report())

    result = service.create_report(
        reporter=fake_user,
        category_id=1,
        title="Pothole",
        description="Large pothole in road",
        latitude=43.7696,
        longitude=11.2558,
        photos=[fake_photo],
        is_anonymous=False,
    )

    assert result is not None
    assert isinstance(result, Report)


def test_create_report_missing_category(): #--> report02

    fake_user = User()

    service = build_report_service()

    fake_photo = build_fake_photo()

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=None,
            title="Pothole",
            description="Description",
            latitude=43.7,
            longitude=11.2,
            photos=[fake_photo],
            is_anonymous=False,
        )


def test_create_report_missing_title(): #--> report03

    fake_user = User()

    fake_category = Category()
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    service = build_report_service(
        mock_category_repository=mock_category_repo
    )

    fake_photo = build_fake_photo()

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=1,
            title=None,
            description="Description",
            latitude=43.7,
            longitude=11.2,
            photos=[fake_photo],
        )


def test_create_report_missing_description(): #--> report04

    fake_user = User()

    fake_category = Category()
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    service = build_report_service(
        mock_category_repository=mock_category_repo
    )

    fake_photo = build_fake_photo()

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=1,
            title="Pothole",
            description=None,
            latitude=43.7,
            longitude=11.2,
            photos=[fake_photo],
        )


def test_create_report_invalid_latitude(): #--> report05

    fake_user = User()

    fake_category = Category()
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    service = build_report_service(
        mock_category_repository=mock_category_repo
    )

    fake_photo = build_fake_photo()

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=1,
            title="Pothole",
            description="Description",
            latitude="invalid",
            longitude=11.2,
            photos=[fake_photo],
        )


def test_create_report_without_photos(): #--> report06

    fake_user = User()

    fake_category = Category()
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    service = build_report_service(
        mock_category_repository=mock_category_repo
    )

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=1,
            title="Pothole",
            description="Description",
            latitude=43.7,
            longitude=11.2,
            photos=[],
        )


def test_create_report_more_than_three_photos(): #--> report07

    fake_user = User()

    fake_category = Category()
    fake_category.is_active = True

    mock_category_repo = MagicMock()
    mock_category_repo.get_by_id.return_value = fake_category

    service = build_report_service(
        mock_category_repository=mock_category_repo
    )

    photos = [
        build_fake_photo("1.jpg"),
        build_fake_photo("2.jpg"),
        build_fake_photo("3.jpg"),
        build_fake_photo("4.jpg"),
    ]

    with pytest.raises(ValidationError):
        service.create_report(
            reporter=fake_user,
            category_id=1,
            title="Pothole",
            description="Description",
            latitude=43.7,
            longitude=11.2,
            photos=photos,
        )
