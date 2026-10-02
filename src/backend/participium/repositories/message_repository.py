from sqlalchemy import select

from participium.models.message import Message
from participium.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    def add(self, message: Message) -> Message:
        self.session.add(message)
        return message

    def list_for_report(self, report_id: int) -> list[Message]:
        query = select(Message).where(Message.report_id == report_id).order_by(Message.created_at.asc())
        return list(self.session.scalars(query))
