from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from participium import create_app
from participium.database import close_connection, get_session
from participium.models.category import Category


@pytest.mark.e2e
@pytest.mark.skip(reason="This test is a crude example.")
def test_get_categories_after_inserting_category_with_flask_test_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    # This is an end-to-end Flask test: we create the real application object
    # and then call it through Flask's test client.
    # Because create_app() is executed, these startup flags are actually read.
    monkeypatch.setenv("AUTO_INIT_DB", "true")
    monkeypatch.setenv("BOOTSTRAP_REFERENCE_DATA", "false")
    monkeypatch.setenv("BOOTSTRAP_DEMO_DATA", "false")

    # create_app() opens the database connection and, because AUTO_INIT_DB=true,
    # creates the schema. This is different from a lower-level integration test,
    # where no Flask startup code runs and create_all() must be called manually.
    application = create_app()
    application.config.update(TESTING=True)
    client: FlaskClient = application.test_client()

    # We prepare a known database state directly through the SQLAlchemy session.
    # The app context is needed here because the database session is normally
    # managed while the Flask application context is active.
    with application.app_context():
        session = get_session()
        session.add(Category(name="Example E2E Category", is_active=True))
        session.commit()

    # This request is not sent over the network. Flask's test client simulates
    # an HTTP request against the application and runs the normal request hooks.
    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    category_names = [category["name"] for category in response.get_json()]
    assert "Example E2E Category" in category_names

    # The request teardown cleans up request-scoped sessions, but the global
    # test database connection opened by create_app() still has to be closed.
    close_connection()
