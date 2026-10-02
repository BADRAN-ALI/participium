from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from participium import create_app
from participium.database import close_connection, get_session
from participium.models.category import Category


@pytest.mark.e2e
def test_get_categories_returns_inserted_category(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+pysqlite:///:memory:",
    )

    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    application = create_app()

    application.config.update(TESTING=True)

    client: FlaskClient = application.test_client()

    with application.app_context():
        session = get_session()

        session.add(
            Category(
                name="E2E Test Category",
                is_active=True,
            )
        )

        session.commit()

    response = client.get("/api/v1/categories")

    assert response.status_code == 200

    categories = response.get_json()

    category_names = [
        category["name"]
        for category in categories
    ]

    assert "E2E Test Category" in category_names

    close_connection()