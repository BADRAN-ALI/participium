from __future__ import annotations

from datetime import datetime

import pytest

from participium.core.utils import parse_date


def test_parse_date_valid_iso_string(): #--> date01

    result = parse_date("2000-01-01")

    assert result is not None
    assert isinstance(result, datetime)
    assert result.year == 2000
    assert result.month == 1
    assert result.day == 1



def test_parse_date_empty_string_returns_none(): #-->date02 

    result = parse_date("")

    assert result is None


def test_parse_date_invalid_format_raises_value_error(): #--> date03

    with pytest.raises(ValueError):
        parse_date("01-01-2000")
