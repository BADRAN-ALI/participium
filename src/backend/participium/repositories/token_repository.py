from sqlalchemy import select

from participium.models.token import EmailVerificationToken
from participium.repositories.base import BaseRepository


class TokenRepository(BaseRepository):
    def add(self, token: EmailVerificationToken) -> None:
        self.session.add(token)
        return token

    def get_by_token(self, token: str) -> EmailVerificationToken | None:
        return self.session.scalar(
            select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        )

    def list_for_user(self, user_id: int) -> list[EmailVerificationToken]:
        return list(
            self.session.scalars(
                select(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id)
            )
        )
