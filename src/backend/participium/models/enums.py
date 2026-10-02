from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    CITIZEN = "citizen"
    OPERATOR = "operator"
    ADMIN = "admin"


class ReportStatus(str, Enum):
    PENDING_APPROVAL = "Pending Approval"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    SUSPENDED = "Suspended"
    REJECTED = "Rejected"
    RESOLVED = "Resolved"


class NotificationType(str, Enum):
    STATUS_CHANGE = "status_change"
    MESSAGE = "message"
    SYSTEM = "system"
