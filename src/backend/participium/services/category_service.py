from __future__ import annotations

from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.category import Category


class CategoryService:
    def __init__(self, session, category_repository):
        self.session = session
        self.category_repository = category_repository

    def list_categories(self, active_only: bool = False):
        return self.category_repository.list_all(active_only=active_only)

    def get_category(self, category_id: int):
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found.")
        return category

    def create_category(self, name: str):
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValidationError("Category name is required.")
        if self.category_repository.get_by_name(cleaned_name):
            raise ValidationError("Category name already exists.")
        category = self.category_repository.add(Category(name=cleaned_name, is_active=True))
        self.session.commit()
        return category

    def update_category(self, category_id: int, *, name: str | None = None, is_active: bool | None = None):
        category = self.get_category(category_id)
        if name:
            cleaned_name = name.strip()
            duplicate = self.category_repository.get_by_name(cleaned_name)
            if duplicate and duplicate.id != category.id:
                raise ValidationError("Category name already exists.")
            category.name = cleaned_name
        if is_active is not None:
            category.is_active = is_active
        self.session.commit()
        return category
