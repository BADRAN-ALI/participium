from __future__ import annotations

import pytest

from participium.core.exceptions import ValidationError
from participium.core.status_flow import ensure_transition_allowed
from participium.models.enums import ReportStatus


def test_pending_approval_to_assigned_allowed(): #--> flow01

    result = ensure_transition_allowed(
        ReportStatus.PENDING_APPROVAL,
        ReportStatus.ASSIGNED
    )

    assert result is True


def test_pending_approval_to_rejected_allowed(): #--> flow02

    result = ensure_transition_allowed(
        ReportStatus.PENDING_APPROVAL,
        ReportStatus.REJECTED
    )

    assert result is True


def test_assigned_to_in_progress_allowed(): #--> flow03

    result = ensure_transition_allowed(
        ReportStatus.ASSIGNED,
        ReportStatus.IN_PROGRESS
    )

    assert result is True


def test_assigned_to_resolved_allowed(): #--> flow04

    result = ensure_transition_allowed(
        ReportStatus.ASSIGNED,
        ReportStatus.RESOLVED
    )

    assert result is True


def test_suspended_to_resolved_allowed(): #--> flow07

    result = ensure_transition_allowed(
        ReportStatus.SUSPENDED,
        ReportStatus.RESOLVED
    )

    assert result is True


def test_resolved_to_assigned_not_allowed(): #--> flow05

    with pytest.raises(ValidationError):
        ensure_transition_allowed(
            ReportStatus.RESOLVED,
            ReportStatus.ASSIGNED
        )


def test_rejected_to_in_progress_not_allowed(): #--> flow06

    with pytest.raises(ValidationError):
        ensure_transition_allowed(
            ReportStatus.REJECTED,
            ReportStatus.IN_PROGRESS
        )


def test_in_progress_to_pending_approval_not_allowed(): #--> flow08

    with pytest.raises(ValidationError):
        ensure_transition_allowed(
            ReportStatus.IN_PROGRESS,
            ReportStatus.PENDING_APPROVAL
        )
