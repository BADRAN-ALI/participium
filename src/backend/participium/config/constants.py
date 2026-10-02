from participium.models.enums import ReportStatus, Role

APP_NAME = "Participium"

DEFAULT_CATEGORIES = [
    "Waterworks - Drinking Water",
    "Architectural Barriers",
    "Sewerage",
    "Public Lighting",
    "Waste",
    "Road Signs and Traffic Lights",
    "Roads and Urban Furniture",
    "Public Green Areas and Playgrounds",
    "Other",
]

PUBLIC_VISIBLE_STATUSES = {
    ReportStatus.ASSIGNED,
    ReportStatus.IN_PROGRESS,
    ReportStatus.SUSPENDED,
    ReportStatus.RESOLVED,
}

OPERATOR_ROLES = {Role.OPERATOR, Role.ADMIN}

DEFAULT_STATUS_TRANSITIONS = {
    ReportStatus.PENDING_APPROVAL: {ReportStatus.ASSIGNED, ReportStatus.REJECTED},
    ReportStatus.ASSIGNED: {ReportStatus.IN_PROGRESS, ReportStatus.SUSPENDED, ReportStatus.RESOLVED},
    ReportStatus.IN_PROGRESS: {ReportStatus.SUSPENDED, ReportStatus.RESOLVED},
    ReportStatus.SUSPENDED: {ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED},
    ReportStatus.REJECTED: set(),
    ReportStatus.RESOLVED: set(),
}
