from __future__ import annotations

from typing import Any

from werkzeug.datastructures import FileStorage

from participium.models.notification import Notification
from participium.models.user import User
from participium.services.notification_service import NotificationService
from participium.services.user_service import UserService


class UserController:
    def __init__(self, user_service: UserService, notification_service: NotificationService):
        self.user_service = user_service
        self.notification_service = notification_service

    def update_profile(
        self,
        user: User,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email_notifications_enabled: bool | None = None,
        profile_picture: FileStorage | None = None,
    ) -> User:
        return self.user_service.update_profile(
            user=user,
            username=username,
            first_name=first_name,
            last_name=last_name,
            email_notifications_enabled=email_notifications_enabled,
            profile_picture=profile_picture,
        )

    def delete_account(self, user: User) -> None:
        self.user_service.delete_account(user)

    def list_users(self) -> list[User]:
        return self.user_service.list_users()

    def create_user(self, payload: dict[str, Any]) -> User:
        return self.user_service.create_user(payload)

    def update_user(self, user_id: int, payload: dict[str, Any]) -> User:
        return self.user_service.update_user(user_id, payload)

    def list_notifications(self, user_id: int) -> list[Notification]:
        return self.notification_service.list_notifications(user_id)

    def get_notification_for_user(self, user_id: int, notification_id: int) -> Notification:
        return self.notification_service.get_user_notification(user_id, notification_id)

    def mark_notification_as_read(self, notification: Notification) -> Notification:
        return self.notification_service.mark_as_read(notification)
