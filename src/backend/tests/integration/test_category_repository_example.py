from __future__ import annotations

import pytest

from participium.database import close_connection, create_all, get_session, open_connection
from participium.models.category import Category
from participium.repositories.category_repository import CategoryRepository
from participium.services.category_service import CategoryService


@pytest.mark.integration
@pytest.mark.skip(reason="This test is a crude example.")
def test_list_categories_through_service_after_manual_database_setup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    # This is an integration test, not an end-to-end Flask test.
    # We do not call create_app(), so Flask does not run the application startup code.
    # For that reason AUTO_INIT_DB would not help here: the flag is read inside create_app().
    open_connection()

    # Since the Flask app is not bootstrapped, we must create the schema explicitly.
    # Without create_all(), the in-memory SQLite database has no tables.
    create_all()

    # The SQLAlchemy session is normally cleaned up by Flask request/app teardown hooks.
    # Here there is no Flask request context, so the test owns session/connection cleanup.
    session = get_session()

    try:
        # Arrange the database state directly, without using the service under test.
        # This keeps setup separate from the behavior we want to exercise.
        session.add(Category(name="Example Integration Category", is_active=True))
        session.commit()

        repository = CategoryRepository(session)
        service = CategoryService(session, repository)

        categories = service.list_categories(active_only=True)

        category_names = [category.name for category in categories]
        assert "Example Integration Category" in category_names
    finally:
        # close_connection() also removes scoped sessions
        close_connection()
