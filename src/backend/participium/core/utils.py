from __future__ import annotations

import csv
import io
from datetime import datetime


def utcnow() -> datetime:
    return datetime.utcnow()


def parse_date(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string.

    Inputs:
        value: ISO-8601 datetime string, or `None`.

    Returns:
        Parsed `datetime` when `value` is non-empty, otherwise `None`.

    Raises:
        ValueError: if `value` is non-empty but not a valid ISO-8601 datetime.
    """
    if not value:
        return None
    return datetime.fromisoformat(value)


def build_csv(rows: list[dict], fieldnames: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
