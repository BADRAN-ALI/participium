from __future__ import annotations

from typing import Any

from participium.models.user import User
from participium.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def register(
        self,
        payload: dict[str, Any],
        verification_base_url: str | None = None,
    ) -> tuple[User, str | None]:
        return self.auth_service.register_user(payload, verification_base_url)

    def verify_email(self, token_value: str) -> User:
        return self.auth_service.verify_email(token_value)

    def login(self, identifier: str, password: str) -> User:
        return self.auth_service.authenticate(identifier, password)
