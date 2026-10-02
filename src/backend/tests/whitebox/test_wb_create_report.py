from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.core.exceptions import ValidationError
from participium.models.enums import ReportStatus, Role
from participium.models.report import Report
from participium.models.user import User
from participium.services.report_service import ReportService

pytestmark = pytest.mark.whitebox


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_photo(filename: str = "img.jpg", content_type: str = "image/jpeg") -> Mock:
    photo = Mock()
    photo.filename = filename
    photo.content_type = content_type
    return photo


def _make_reporter(user_id: int = 10) -> User:
    user = User(
        username="citizen1",
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        password_hash="hash",
        role=Role.CITIZEN,
    )
    user.id = user_id
    return user


def _make_active_category(category_id: int = 5) -> Mock:
    cat = Mock()
    cat.id = category_id
    cat.is_active = True
    return cat


@pytest.fixture
def svc() -> dict:
    session = Mock()
    report_repo = Mock()
    category_repo = Mock()
    storage = Mock()
    service = ReportService(
        session=session,
        report_repository=report_repo,
        category_repository=category_repo,
        storage_service=storage,
    )
    return {
        "service": service,
        "session": session,
        "report_repo": report_repo,
        "category_repo": category_repo,
        "storage": storage,
    }


def _setup_happy_path(svc: dict, num_photos: int = 1) -> tuple:
    """Wire mocks for a fully valid submission and return (category, photos, expected_report)."""
    cat = _make_active_category()
    svc["category_repo"].get_by_id.return_value = cat

    created_report = Mock(spec=Report)
    created_report.id = 99

    # Simulate DB-assigned PK after flush
    def _add_side_effect(report):
        report.id = 99

    svc["report_repo"].add.side_effect = _add_side_effect
    svc["report_repo"].get_by_id.return_value = created_report
    svc["storage"].save.return_value = "/uploads/img.jpg"

    photos = [_make_photo(f"photo_{i}.jpg") for i in range(num_photos)]
    return cat, photos, created_report


# ---------------------------------------------------------------------------
# TC-WB-CR-01  int(category_id) raises ValueError – exception branch in try block
# Covers: C2=True (conversion fails)
# ---------------------------------------------------------------------------
def test_create_report_non_parseable_category_id_raises(svc: dict) -> None:
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="valid active category"):
        svc["service"].create_report(
            reporter, "not-a-number", "T", "D", 1.0, 2.0, [_make_photo()]
        )


# ---------------------------------------------------------------------------
# TC-WB-CR-02  category_id is None → resolved to None → category not found
# Covers: C1=False (category_id is None), C4=True (not category)
# ---------------------------------------------------------------------------
def test_create_report_none_category_id_raises(svc: dict) -> None:
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="valid active category"):
        svc["service"].create_report(
            reporter, None, "T", "D", 1.0, 2.0, [_make_photo()]
        )


# ---------------------------------------------------------------------------
# TC-WB-CR-03  category_id resolves but repository returns None
# Covers: C3=True (resolved truthy), C4=True (category is None)
# ---------------------------------------------------------------------------
def test_create_report_category_not_in_repository_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = None
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="valid active category"):
        svc["service"].create_report(reporter, 7, "T", "D", 1.0, 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-04  category found but inactive
# Covers: C4=False (category exists), C5=True (not active)
# ---------------------------------------------------------------------------
def test_create_report_inactive_category_raises(svc: dict) -> None:
    cat = Mock()
    cat.id = 7
    cat.is_active = False
    svc["category_repo"].get_by_id.return_value = cat
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="valid active category"):
        svc["service"].create_report(reporter, 7, "T", "D", 1.0, 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-05  title is None
# Covers: C6=True (not title)
# ---------------------------------------------------------------------------
def test_create_report_missing_title_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="Title and description"):
        svc["service"].create_report(reporter, 5, None, "D", 1.0, 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-06  title present but description is empty
# Covers: C6=False (title ok), C7=True (not description)
# ---------------------------------------------------------------------------
def test_create_report_empty_description_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="Title and description"):
        svc["service"].create_report(reporter, 5, "Valid Title", "", 1.0, 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-07  latitude is None
# Covers: C8=True (latitude is None)
# ---------------------------------------------------------------------------
def test_create_report_missing_latitude_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="Latitude and longitude are required"):
        svc["service"].create_report(reporter, 5, "T", "D", None, 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-08  longitude is None (latitude provided)
# Covers: C8=False (latitude ok), C9=True (longitude is None)
# ---------------------------------------------------------------------------
def test_create_report_missing_longitude_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="Latitude and longitude are required"):
        svc["service"].create_report(reporter, 5, "T", "D", 1.0, None, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-09  latitude is a non-numeric string → float() raises
# Covers: C10=True (float conversion fails)
# ---------------------------------------------------------------------------
def test_create_report_non_numeric_latitude_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    with pytest.raises(ValidationError, match="must be valid numbers"):
        svc["service"].create_report(reporter, 5, "T", "D", "bad", 2.0, [_make_photo()])


# ---------------------------------------------------------------------------
# TC-WB-CR-10  all photos have no filename → valid_photos is empty
# Covers: C12=True (not valid_photos)
# ---------------------------------------------------------------------------
def test_create_report_no_valid_photos_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    empty_photo = Mock()
    empty_photo.filename = ""
    with pytest.raises(ValidationError, match="At least one photo"):
        svc["service"].create_report(reporter, 5, "T", "D", 1.0, 2.0, [empty_photo])


# ---------------------------------------------------------------------------
# TC-WB-CR-11  four valid photos → exceeds limit
# Covers: C12=False (photos exist), C13=True (len > 3)
# ---------------------------------------------------------------------------
def test_create_report_too_many_photos_raises(svc: dict) -> None:
    svc["category_repo"].get_by_id.return_value = _make_active_category()
    reporter = _make_reporter()
    photos = [_make_photo(f"p{i}.jpg") for i in range(4)]
    with pytest.raises(ValidationError, match="at most 3 photos"):
        svc["service"].create_report(reporter, 5, "T", "D", 1.0, 2.0, photos)


# ---------------------------------------------------------------------------
# TC-WB-CR-12  happy path – 1 photo, loop body executes once
# Covers: all conditions False (no error), loop entry and single iteration
# ---------------------------------------------------------------------------
def test_create_report_single_photo_success(svc: dict) -> None:
    _cat, photos, expected_report = _setup_happy_path(svc, num_photos=1)
    reporter = _make_reporter()

    result = svc["service"].create_report(
        reporter, 5, "Broken pipe", "Details here", 45.0, 9.0, photos
    )

    assert result is expected_report
    svc["report_repo"].add.assert_called_once()
    svc["session"].flush.assert_called_once()
    assert svc["report_repo"].add_photo.call_count == 1
    svc["report_repo"].add_status_entry.assert_called_once()
    svc["session"].commit.assert_called_once()


# ---------------------------------------------------------------------------
# TC-WB-CR-13  happy path – 3 photos, loop executes three times
# Covers: loop with multiple iterations
# ---------------------------------------------------------------------------
def test_create_report_three_photos_loop_coverage(svc: dict) -> None:
    _cat, photos, expected_report = _setup_happy_path(svc, num_photos=3)
    reporter = _make_reporter()

    result = svc["service"].create_report(
        reporter, 5, "Flooding", "Water on road", 45.1, 9.1, photos
    )

    assert result is expected_report
    assert svc["report_repo"].add_photo.call_count == 3
    assert svc["storage"].save.call_count == 3
