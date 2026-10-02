from __future__ import annotations

import pytest

from participium.database import (
    close_connection,
    create_all,
    get_session,
    open_connection,
)
from participium.models.category import Category
from participium.repositories.category_repository import CategoryRepository
from participium.services.category_service import CategoryService


@pytest.mark.integration
def test_list_active_categories_returns_only_active_categories(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    open_connection()
    create_all()

    session = get_session()

    try:
        active_category = Category(
            name="Roads",
            is_active=True,
        )

        inactive_category = Category(
            name="Old category",
            is_active=False,
        )

        session.add(active_category)
        session.add(inactive_category)

        session.commit()

        repository = CategoryRepository(session)

        service = CategoryService(
            session=session,
            category_repository=repository,
        )

        categories = service.list_categories(active_only=True)

        category_names = [category.name for category in categories]

        assert "Roads" in category_names
        assert "Old category" not in category_names
        assert len(categories) == 1

    finally:
        close_connection()