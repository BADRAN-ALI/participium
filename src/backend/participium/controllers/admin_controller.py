from __future__ import annotations

from typing import Any

from participium.models.category import Category
from participium.models.user import User
from participium.services.category_service import CategoryService
from participium.services.statistics_service import StatisticsService
from participium.services.user_service import UserService


class AdminController:
    def __init__(
        self,
        category_service: CategoryService,
        user_service: UserService,
        statistics_service: StatisticsService,
    ):
        self.category_service = category_service
        self.user_service = user_service
        self.statistics_service = statistics_service

    def list_categories(self, active_only: bool = False) -> list[Category]:
        return self.category_service.list_categories(active_only=active_only)

    def create_category(self, name: str) -> Category:
        return self.category_service.create_category(name)

    def update_category(self, category_id: int, payload: dict[str, Any]) -> Category:
        return self.category_service.update_category(
            category_id,
            name=payload.get("name"),
            is_active=payload.get("is_active"),
        )

    def list_users(self) -> list[User]:
        return self.user_service.list_users()

    def create_user(self, payload: dict[str, Any]) -> User:
        return self.user_service.create_user(payload)

    def update_user(self, user_id: int, payload: dict[str, Any]) -> User:
        return self.user_service.update_user(user_id, payload)

    def admin_statistics(self) -> dict[str, dict[str, int]]:
        return self.statistics_service.admin_statistics()
