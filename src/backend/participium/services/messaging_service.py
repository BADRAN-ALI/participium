from __future__ import annotations

from participium.core.exceptions import AuthorizationError, ValidationError
from participium.models.enums import Role
from participium.models.message import Message
from participium.models.report import Report
from participium.models.user import User


class MessagingService:
    def __init__(
        self,
        session=None,
        report_repository=None,
        message_repository=None,
        notification_service=None,
    ):
        self.session = session
        self.report_repository = report_repository
        self.message_repository = message_repository
        self.notification_service = notification_service

    def can_access_thread(self, report: Report, user: User | None) -> bool:
        if user is None:
            return False
        if user.role == Role.ADMIN:
            return True
        if user.role == Role.OPERATOR and user.category_id == report.category_id:
            return True
        return report.reporter_id == user.id

    def list_messages(self, report: Report, user: User) -> list[Message]:
        self._ensure_access(report, user)
        return self.message_repository.list_for_report(report.id)

    def send_message(self, report: Report, sender: User, body: str) -> Message:
        """Send a message inside a report conversation.

        Inputs:
            report: target report.
            sender: user sending the message.
            body: message body.

        Returns:
            The persisted `Message`.

        Raises:
            AuthorizationError: if `sender` cannot access the thread.
            ValidationError: if `body` is empty or blank after trimming.
            ValidationError: if no recipient can currently be resolved for the conversation.
        """
        self._ensure_access(report, sender)
        cleaned_body = body.strip()
        if not cleaned_body:
            raise ValidationError("Message body cannot be empty.")
        recipient = self._resolve_recipient(report, sender)
        if recipient is None:
            raise ValidationError("No recipient available for this conversation yet.")
        message = Message(report_id=report.id, sender_id=sender.id, recipient_id=recipient.id, body=cleaned_body)
        self.message_repository.add(message)
        self.notification_service.notify_new_message(
            recipient=recipient,
            report=report,
            sender_name=self._sender_name(sender),
            body=cleaned_body,
        )
        self.session.commit()
        return message

    def _ensure_access(self, report: Report, user: User) -> None:
        if self.can_access_thread(report, user):
            return
        raise AuthorizationError("You do not have access to the message thread for this report.")

    def _resolve_recipient(self, report: Report, sender: User) -> User | None:
        if sender.role in {Role.ADMIN, Role.OPERATOR}:
            return report.reporter
        messages = self.message_repository.list_for_report(report.id)
        for message in reversed(messages):
            if message.sender and message.sender.role in {Role.ADMIN, Role.OPERATOR}:
                return message.sender
        for status_event in reversed(report.status_history):
            if status_event.changed_by and status_event.changed_by.role in {Role.ADMIN, Role.OPERATOR}:
                return status_event.changed_by
        return None

    @staticmethod
    def _sender_name(sender: User) -> str:
        return f"{sender.first_name} {sender.last_name}".strip() or sender.username
