from __future__ import annotations

import pytest

from participium.core.exceptions import ValidationError
from participium.core.status_flow import ensure_transition_allowed
from participium.models.enums import ReportStatus


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        (ReportStatus.PENDING_APPROVAL, ReportStatus.ASSIGNED),
        (ReportStatus.PENDING_APPROVAL, ReportStatus.REJECTED),
        (ReportStatus.ASSIGNED, ReportStatus.IN_PROGRESS),
        (ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED),
        (ReportStatus.SUSPENDED, ReportStatus.IN_PROGRESS),
        (ReportStatus.RESOLVED, ReportStatus.RESOLVED),
    ],
)
def test_allowed_status_transitions_return_true(current_status, next_status):
    assert ensure_transition_allowed(current_status, next_status) is True


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        (ReportStatus.RESOLVED, ReportStatus.ASSIGNED),
        (ReportStatus.REJECTED, ReportStatus.IN_PROGRESS),
        (ReportStatus.IN_PROGRESS, ReportStatus.PENDING_APPROVAL),
    ],
)
def test_invalid_status_transitions_raise_validation_error(current_status, next_status):
    with pytest.raises(ValidationError):
        ensure_transition_allowed(current_status, next_status)