from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from participium.services.auth_service import AuthService
from participium.models.user import User
from participium.core.exceptions import AuthenticationError
from participium.core.security import hash_password


def build_auth_service(mock_user_repo):

    return AuthService(
        session=MagicMock(),
        user_repository=mock_user_repo,
        token_repository=MagicMock(),
        email_gateway=MagicMock(),
    )


def test_authenticate_success():  #--> auth01

    fake_user = User()
    fake_user.is_active = True
    fake_user.is_email_verified = True
    fake_user.password_hash = hash_password("correct")

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username_or_email.return_value = fake_user

    service = build_auth_service(mock_user_repo)

    result = service.authenticate(
        "valid@mail.com",
        "correct"
    )

    assert result == fake_user


def test_authenticate_wrong_password(): #--> auth02

    fake_user = User()
    fake_user.is_active = True
    fake_user.is_email_verified = True
    fake_user.password_hash = hash_password("correct")

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username_or_email.return_value = fake_user

    service = build_auth_service(mock_user_repo)

    with pytest.raises(AuthenticationError):
        service.authenticate(
            "valid@mail.com",
            "wrong"
        )


def test_authenticate_user_not_found(): #--> auth03

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username_or_email.return_value = None

    service = build_auth_service(mock_user_repo)

    with pytest.raises(AuthenticationError):
        service.authenticate(
            "missing@mail.com",
            "whatever"
        )


def test_authenticate_inactive_user(): #--> auth04

    fake_user = User()
    fake_user.is_active = False
    fake_user.is_email_verified = True
    fake_user.password_hash = hash_password("correct")

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username_or_email.return_value = fake_user

    service = build_auth_service(mock_user_repo)

    with pytest.raises(AuthenticationError):
        service.authenticate(
            "valid@mail.com",
            "correct"
        )


def test_authenticate_unverified_email(): #--> auth05

    fake_user = User()
    fake_user.is_active = True
    fake_user.is_email_verified = False
    fake_user.password_hash = hash_password("correct")

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username_or_email.return_value = fake_user

    service = build_auth_service(mock_user_repo)

    with pytest.raises(AuthenticationError):
        service.authenticate(
            "valid@mail.com",
            "correct"
        )
