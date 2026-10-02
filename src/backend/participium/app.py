from __future__ import annotations

from flask import Flask, g, jsonify, session
from flask_cors import CORS

from participium.api import init_swagger
from participium.config import Settings
from participium.container import AppContainer
from participium.core.exceptions import DomainError
from participium.database import create_all, get_session, open_connection, remove_session
from participium.database.seed import seed_demo_data, seed_reference_data
from participium.repositories.user_repository import UserRepository
from participium.routes import register_blueprints


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(__name__, instance_path=str(settings.instance_path), instance_relative_config=True)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length
    app.config["SETTINGS"] = settings
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False

    CORS(
        app,
        resources={r"/api/*": {"origins": [settings.frontend_origin]}},
        supports_credentials=True,
    )

    open_connection()
    app.extensions["container"] = AppContainer(settings)

    if settings.auto_init_db:
        with app.app_context():
            create_all()
            if settings.bootstrap_reference_data:
                seed_reference_data(get_session())
            if settings.bootstrap_demo_data:
                seed_demo_data(get_session(), settings.media_root)

    init_swagger(app)
    register_blueprints(app)
    _register_request_hooks(app)
    _register_error_handlers(app)
    return app


def _register_request_hooks(app: Flask) -> None:
    @app.before_request
    def load_current_user():
        g.current_user = None   
        user_id = session.get("user_id")
        if user_id:
            user = UserRepository(get_session()).get_by_id(user_id)
            if user and user.is_active:
                g.current_user = user
            else:
                session.pop("user_id", None)

    @app.teardown_appcontext
    def teardown(_exception=None):
        remove_session()


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(error: DomainError):
        return jsonify({"error": str(error)}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Resource not found."}), 404
