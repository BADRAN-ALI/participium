from sqlalchemy import select

from participium.models.category import Category
from participium.repositories.base import BaseRepository


class CategoryRepository(BaseRepository):
    def add(self, category: Category) -> Category:
        self.session.add(category)
        return category

    def get_by_id(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def get_by_name(self, name: str) -> Category | None:
        return self.session.scalar(select(Category).where(Category.name == name))

    def list_all(self, active_only: bool = False) -> list[Category]:
        query = select(Category).order_by(Category.name.asc())
        if active_only:
            query = query.where(Category.is_active.is_(True))
        return list(self.session.scalars(query))
