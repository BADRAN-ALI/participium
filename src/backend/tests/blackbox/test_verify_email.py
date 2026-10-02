from __future__ import annotations

import pytest

from participium.core.exceptions import ValidationError
from participium.models.user import User
from participium.services.auth_service import AuthService


VALID_TOKEN = "VALID_TOKEN_FOR_MARIA_ROSSI"
INVALID_TOKEN = "INVALID_TOKEN"
EXPIRED_TOKEN = "EXPIRED_TOKEN_FOR_GIULIA_NERI"

PENDING_VERIFICATION_USER = User(
    id=101,
    username="maria.rossi",
    first_name="Maria",
    last_name="Rossi",
    email="maria.rossi@example.com",
    password_hash="HASHED_PASSWORD_101",
    is_active=True,
    is_email_verified=False,
)

USED_TOKEN_USER = User(
    id=102,
    username="luca.bianchi",
    first_name="Luca",
    last_name="Bianchi",
    email="luca.bianchi@example.com",
    password_hash="HASHED_PASSWORD_102",
    is_active=True,
    is_email_verified=True,
)

EXPIRED_TOKEN_USER = User(
    id=103,
    username="giulia.neri",
    first_name="Giulia",
    last_name="Neri",
    email="giulia.neri@example.com",
    password_hash="HASHED_PASSWORD_103",
    is_active=True,
    is_email_verified=False,
)


@pytest.fixture
def seed_verify_email_data() -> None:
    # Populate the system with the users and tokens needed by
    # `AuthService.verify_email`.
    #
    # Suggested dataset:
    # - `PENDING_VERIFICATION_USER` linked to `VALID_TOKEN`
    # - `USED_TOKEN_USER` linked to an already used token
    # - `EXPIRED_TOKEN_USER` linked to `EXPIRED_TOKEN`
    pass


@pytest.mark.skip(reason="Disabled.")
def test_verify_email_success(seed_verify_email_data: None) -> None:
    auth_service = AuthService()
    token_value = VALID_TOKEN

    verified_user = auth_service.verify_email(token_value)

    assert isinstance(verified_user, User)
    assert verified_user.id == PENDING_VERIFICATION_USER.id
    assert verified_user.username == PENDING_VERIFICATION_USER.username
    assert verified_user.first_name == PENDING_VERIFICATION_USER.first_name
    assert verified_user.last_name == PENDING_VERIFICATION_USER.last_name
    assert verified_user.email == PENDING_VERIFICATION_USER.email
    assert verified_user.is_email_verified is True


@pytest.mark.skip(reason="Disabled.")
def test_verify_email_invalid_token(seed_verify_email_data: None) -> None:
    auth_service = AuthService()
    token_value = INVALID_TOKEN

    with pytest.raises(ValidationError):
        auth_service.verify_email(token_value)


@pytest.mark.skip(reason="Disabled.")
def test_verify_email_expired_token(seed_verify_email_data: None) -> None:
    auth_service = AuthService()
    token_value = EXPIRED_TOKEN

    with pytest.raises(ValidationError):
        auth_service.verify_email(token_value)
