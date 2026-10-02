from __future__ import annotations

from sqlalchemy import select

from participium.models.enums import NotificationType
from participium.models.notification import Notification
from participium.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def add(self, notification: Notification) -> None:
        self.session.add(notification)
        return notification

    def get_by_id(self, notification_id: int) -> Notification | None:
        return self.session.get(Notification, notification_id)

    def list_for_user(self, user_id: int) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(self.session.scalars(query))

    def list_unread_message_notifications(
        self,
        user_id: int,
        report_id: int | None = None,
    ) -> list[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.type == NotificationType.MESSAGE,
            Notification.is_read.is_(False),
        )
        if report_id is not None:
            query = query.where(Notification.report_id == report_id)
        return list(self.session.scalars(query))

    def delete_for_user(self, user_id: int) -> None:
        for item in self.list_for_user(user_id):
            self.session.delete(item)
