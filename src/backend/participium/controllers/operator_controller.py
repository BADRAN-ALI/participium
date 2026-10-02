from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from participium.models.enums import Role
from participium.models.report import Report
from participium.models.user import User
from participium.services.notification_service import NotificationService
from participium.services.report_service import ReportService


@dataclass(frozen=True)
class OperatorDashboardContext:
    pending_reports: list[Report]
    assigned_reports: list[Report]
    unread_message_counts: dict[int, int]


class OperatorController:
    def __init__(
        self,
        report_service: ReportService,
        notification_service: NotificationService,
    ):
        self.report_service = report_service
        self.notification_service = notification_service

    def build_dashboard(
        self,
        operator: User,
        filters: dict[str, Any] | None = None,
    ) -> OperatorDashboardContext:
        effective_filters = filters or {}
        pending_reports: list[Report] = []
        if operator.role == Role.ADMIN:
            pending_reports = self.report_service.list_pending_reports(effective_filters)
        elif operator.role == Role.OPERATOR:
            pending_reports = self.report_service.list_pending_reports(
                {**effective_filters, "category_id": operator.category_id}
            )
        assigned_reports = self.report_service.list_operator_reports(operator)
        unread_message_counts = self.notification_service.count_unread_message_notifications_by_report(operator.id)
        return OperatorDashboardContext(
            pending_reports=pending_reports,
            assigned_reports=assigned_reports,
            unread_message_counts=unread_message_counts,
        )

    def assign_report(self, report_id: int, operator: User) -> Report:
        return self.report_service.assign_report(report_id, operator)

    def update_status(
        self,
        report_id: int,
        operator: User,
        next_status_value: str,
        note: str | None = None,
    ) -> Report:
        return self.report_service.update_status(report_id, operator, next_status_value, note)
