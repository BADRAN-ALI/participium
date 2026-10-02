from __future__ import annotations

from datetime import datetime

import pytest

from participium.core.utils import build_csv, parse_date, utcnow


def test_utcnow_returns_datetime():
    result = utcnow()

    assert isinstance(result, datetime)


def test_parse_date_with_none_returns_none():
    result = parse_date(None)

    assert result is None


def test_parse_date_with_empty_string_returns_none():
    result = parse_date("")

    assert result is None


def test_parse_date_with_valid_iso_string_returns_datetime():
    result = parse_date("2026-05-31T16:30:00")

    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 5
    assert result.day == 31
    assert result.hour == 16
    assert result.minute == 30


def test_parse_date_with_invalid_string_raises_value_error():
    with pytest.raises(ValueError):
        parse_date("not-a-date")


def test_build_csv_with_rows_returns_csv_string():
    rows = [
        {"id": 1, "title": "First report"},
        {"id": 2, "title": "Second report"},
    ]
    fieldnames = ["id", "title"]

    result = build_csv(rows, fieldnames)

    assert "id,title" in result
    assert "1,First report" in result
    assert "2,Second report" in result


def test_build_csv_with_empty_rows_still_writes_header():
    result = build_csv([], ["id", "title"])

    assert result.startswith("id,title")