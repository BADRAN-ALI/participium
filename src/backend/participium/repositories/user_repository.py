from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from participium.models.user import User
from participium.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def _base_query(self):
        return select(User).options(joinedload(User.category))

    def add(self, user: User) -> User:
        self.session.add(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.scalar(self._base_query().where(User.id == user_id))

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(self._base_query().where(User.email == email))

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(self._base_query().where(User.username == username))

    def get_by_username_or_email(self, value: str) -> User | None:
        return self.session.scalar(self._base_query().where(or_(User.username == value, User.email == value)))

    def list_all(self) -> list[User]:
        return list(self.session.scalars(self._base_query().order_by(User.created_at.desc())).unique())

    def delete(self, user: User) -> None:
        self.session.delete(user)
