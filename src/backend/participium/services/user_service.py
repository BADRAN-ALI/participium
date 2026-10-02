from __future__ import annotations

from sqlalchemy import or_, select
from werkzeug.datastructures import FileStorage

from participium.core.exceptions import NotFoundError, ValidationError
from participium.core.security import hash_password
from participium.models.enums import Role
from participium.models.message import Message
from participium.models.report import Report, ReportFollower, ReportStatusHistory
from participium.models.user import User


class UserService:
    def __init__(
        self,
        session=None,
        user_repository=None,
        category_repository=None,
        token_repository=None,
        notification_repository=None,
        storage_service=None,
    ):
        self.session = session
        self.user_repository = user_repository
        self.category_repository = category_repository
        self.token_repository = token_repository
        self.notification_repository = notification_repository
        self.storage_service = storage_service

    def update_profile(
        self,
        user: User,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email_notifications_enabled: bool | None = None,
        profile_picture: FileStorage | None = None,
    ) -> User:
        """Update editable fields of a user profile.

        Inputs:
            user: persisted user to update.
            username: optional new username.
            first_name: optional new first name.
            last_name: optional new last name.
            email_notifications_enabled: optional notification preference update.
            profile_picture: optional uploaded profile picture.

        Returns:
            The updated `User`.

        Raises:
            ValidationError: if `username` is already used by another account.
        """
        if username and username != user.username and self.user_repository.get_by_username(username):
            raise ValidationError("Username already in use.")
        if username:
            user.username = username.strip()
        if first_name:
            user.first_name = first_name.strip()
        if last_name:
            user.last_name = last_name.strip()
        if email_notifications_enabled is not None:
            user.email_notifications_enabled = bool(email_notifications_enabled)
        if profile_picture and profile_picture.filename:
            user.profile_picture_path = self.storage_service.save(profile_picture)
        self.session.commit()
        return user

    def delete_account(self, user: User) -> None:
        reports = list(self.session.scalars(select(Report).where(Report.reporter_id == user.id)))
        for report in reports:
            report.reporter_id = None
            report.is_anonymous = True

        followers = list(self.session.scalars(select(ReportFollower).where(ReportFollower.user_id == user.id)))
        for follower in followers:
            self.session.delete(follower)

        messages = list(
            self.session.scalars(
                select(Message).where(or_(Message.sender_id == user.id, Message.recipient_id == user.id))
            )
        )
        for message in messages:
            if message.sender_id == user.id:
                message.sender_id = None
            if message.recipient_id == user.id:
                message.recipient_id = None

        histories = list(
            self.session.scalars(select(ReportStatusHistory).where(ReportStatusHistory.changed_by_id == user.id))
        )
        for history in histories:
            history.changed_by_id = None

        for notification in self.notification_repository.list_for_user(user.id):
            self.session.delete(notification)
        for token in self.token_repository.list_for_user(user.id):
            self.session.delete(token)

        self.user_repository.delete(user)
        self.session.commit()

    def list_users(self) -> list[User]:
        return self.user_repository.list_all()

    def get_user(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def create_user(self, payload: dict) -> User:
        required = ["username", "first_name", "last_name", "email", "password", "role"]
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
        if self.user_repository.get_by_username(payload["username"]):
            raise ValidationError("Username already in use.")
        if self.user_repository.get_by_email(payload["email"]):
            raise ValidationError("Email already in use.")
        role = self._parse_role(payload["role"])
        category = self._resolve_operator_category(role, payload.get("category_id"))
        user = User(
            username=payload["username"].strip(),
            first_name=payload["first_name"].strip(),
            last_name=payload["last_name"].strip(),
            email=payload["email"].strip().lower(),
            password_hash=hash_password(payload["password"]),
            role=role,
            category_id=category.id if category else None,
            is_active=bool(payload.get("is_active", True)),
            is_email_verified=True,
            email_notifications_enabled=bool(payload.get("email_notifications_enabled", True)),
        )
        self.user_repository.add(user)
        self.session.commit()
        return user

    def update_user(self, user_id: int, payload: dict) -> User:
        user = self.get_user(user_id)
        username = payload.get("username")
        email = payload.get("email")
        if username and username != user.username and self.user_repository.get_by_username(username):
            raise ValidationError("Username already in use.")
        if email and email != user.email and self.user_repository.get_by_email(email):
            raise ValidationError("Email already in use.")
        for field in ["username", "first_name", "last_name", "email"]:
            if payload.get(field) is not None:
                value = payload[field]
                setattr(user, field, value.strip() if isinstance(value, str) else value)
        next_role = self._parse_role(payload["role"]) if payload.get("role") is not None else user.role
        if payload.get("role") is not None:
            user.role = next_role
        if "category_id" in payload or payload.get("role") is not None:
            category = self._resolve_operator_category(next_role, payload.get("category_id", user.category_id))
            user.category_id = category.id if category else None
        if payload.get("is_active") is not None:
            user.is_active = bool(payload["is_active"])
        if payload.get("email_notifications_enabled") is not None:
            user.email_notifications_enabled = bool(payload["email_notifications_enabled"])
        self.session.commit()
        return user

    @staticmethod
    def _parse_role(role_value: str) -> Role:
        try:
            return Role(role_value)
        except ValueError as exc:
            raise ValidationError("Invalid user role.") from exc

    def _resolve_operator_category(self, role: Role, category_id_value) -> object | None:
        if role != Role.OPERATOR:
            return None
        if category_id_value in {None, ""}:
            raise ValidationError("Operator category is required.")
        try:
            category_id = int(category_id_value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("A valid active category is required for operators.") from exc
        category = self.category_repository.get_by_id(category_id)
        if not category or not category.is_active:
            raise ValidationError("A valid active category is required for operators.")
        return category
