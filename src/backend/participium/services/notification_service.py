from __future__ import annotations

import logging
from typing import Any

from participium.core.exceptions import AuthorizationError, NotFoundError
from participium.models.enums import NotificationType
from participium.models.notification import Notification
from participium.models.report import Report
from participium.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        session: Any = None,
        notification_repository: Any = None,
        email_gateway: Any = None,
    ):
        self.session = session
        self.notification_repository = notification_repository
        self.email_gateway = email_gateway

    def create_notification(
        self,
        user: User | None,
        notification_type: NotificationType,
        title: str,
        body: str,
        report: Report | None = None,
    ) -> Notification | None:
        """Create a notification, optionally associated with a report.

        Inputs:
            user: recipient user, or `None`.
            notification_type: semantic notification kind.
            title: short notification title.
            body: notification message body.
            report: optional related report.

        Returns:
            A persisted `Notification` for a non-null user, otherwise `None`.

        Raises:
            No documented domain exception from the method contract itself.
            Email delivery failures, if any, are internally swallowed after logging.
        """
        if user is None:
            return None
        notification = Notification(
            user_id=user.id,
            report_id=report.id if report else None,
            type=notification_type,
            title=title,
            body=body,
            is_read=False,
        )
        self.notification_repository.add(notification)
        if user.email_notifications_enabled:
            try:
                self.email_gateway.send(user.email, title, body)
            except Exception:
                logger.exception("Email notification delivery failed for user_id=%s", user.id)
        return notification

    def notify_status_change(self, recipients: list[User | None], report: Report, body: str) -> None:
        seen = set()
        for recipient in recipients:
            if recipient is None or recipient.id in seen:
                continue
            seen.add(recipient.id)
            self.create_notification(
                recipient,
                NotificationType.STATUS_CHANGE,
                f"Report #{report.id} status updated",
                body,
                report=report,
            )

    def notify_new_message(self, recipient: User | None, report: Report, sender_name: str, body: str) -> None:
        self.create_notification(
            recipient,
            NotificationType.MESSAGE,
            f"New message on report #{report.id}",
            f"{sender_name}: {body}",
            report=report,
        )

    def list_notifications(self, user_id: int) -> list[Notification]:
        return self.notification_repository.list_for_user(user_id)

    def count_unread_message_notifications_by_report(self, user_id: int) -> dict[int, int]:
        notifications = self.notification_repository.list_unread_message_notifications(user_id=user_id)
        counts: dict[int, int] = {}
        for notification in notifications:
            if notification.report_id is None:
                continue
            counts[notification.report_id] = counts.get(notification.report_id, 0) + 1
        return counts

    def mark_report_message_notifications_as_read(self, user_id: int, report_id: int) -> int:
        notifications = self.notification_repository.list_unread_message_notifications(
            user_id=user_id,
            report_id=report_id,
        )
        for notification in notifications:
            notification.is_read = True
        if notifications:
            self.session.commit()
        return len(notifications)

    def get_user_notification(self, user_id: int, notification_id: int) -> Notification:
        notification = self.notification_repository.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError("Notification not found.")
        if notification.user_id != user_id:
            raise AuthorizationError("You cannot access this notification.")
        return notification

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.session.commit()
        return notification
