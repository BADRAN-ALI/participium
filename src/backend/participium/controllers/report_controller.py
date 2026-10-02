from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from werkzeug.datastructures import FileStorage

from participium.models.message import Message
from participium.models.enums import ReportStatus
from participium.models.report import Report
from participium.models.user import User
from participium.services.messaging_service import MessagingService
from participium.services.notification_service import NotificationService
from participium.services.report_service import ReportService


@dataclass(frozen=True)
class ReportDetailContext:
    report: Report
    can_access_messages: bool


class ReportController:
    def __init__(
        self,
        report_service: ReportService,
        messaging_service: MessagingService,
        notification_service: NotificationService,
    ):
        self.report_service = report_service
        self.messaging_service = messaging_service
        self.notification_service = notification_service

    def list_public_reports(
        self,
        category_id: int | None = None,
        status: ReportStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "desc",
    ) -> list[Report]:
        return self.report_service.list_public_reports(
            category_id=category_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
        )

    def list_user_reports(self, user: User) -> list[Report]:
        return self.report_service.list_user_reports(user)

    def build_detail_context(self, report_id: int, user: User | None = None) -> ReportDetailContext:
        report = self.report_service.get_accessible_report(report_id, user)
        can_access_messages = self.messaging_service.can_access_thread(report, user)
        if can_access_messages and user is not None:
            self.notification_service.mark_report_message_notifications_as_read(user.id, report.id)
        return ReportDetailContext(report=report, can_access_messages=can_access_messages)

    def create_report(
        self,
        reporter: User,
        category_id: int | str | None,
        title: str | None,
        description: str | None,
        latitude: float | str | None,
        longitude: float | str | None,
        photos: list[FileStorage],
        is_anonymous: bool = False,
    ) -> Report:
        return self.report_service.create_report(
            reporter=reporter,
            category_id=category_id,
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            photos=photos,
            is_anonymous=is_anonymous,
        )

    def follow_report(self, report_id: int, user: User) -> Report:
        return self.report_service.follow_report(report_id, user)

    def unfollow_report(self, report_id: int, user: User) -> Report:
        return self.report_service.unfollow_report(report_id, user)

    def export_rows(
        self,
        category_id: int | None = None,
        status: ReportStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "desc",
    ) -> list[dict[str, int | float | str]]:
        return self.report_service.export_rows(
            category_id=category_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
        )

    def list_messages(self, report: Report, user: User) -> list[Message]:
        return self.messaging_service.list_messages(report, user)

    def send_message(self, report: Report, sender: User, body: str) -> Message:
        return self.messaging_service.send_message(report, sender, body)
