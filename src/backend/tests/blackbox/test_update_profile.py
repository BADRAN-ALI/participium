from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from participium.core.exceptions import ValidationError
from participium.models.user import User
from participium.services.user_service import UserService


def build_user_service(mock_user_repo=None):

    return UserService(
        session=MagicMock(),
        user_repository=mock_user_repo or MagicMock(),
        category_repository=MagicMock(),
        token_repository=MagicMock(),
        notification_repository=MagicMock(),
        storage_service=MagicMock(),
    )


def build_user():

    user = User()

    user.id = 1
    user.username = "olduser"
    user.first_name = "Old"
    user.last_name = "Name"
    user.email_notifications_enabled = True

    return user


def test_update_profile_success():

    mock_user_repo = MagicMock()

    #Serve per poter fare update dell'user
    mock_user_repo.get_by_username.return_value = None

    service = build_user_service(mock_user_repo)

    user = build_user()

    result = service.update_profile(
        user=user,
        username="newuser",
        first_name="Mario",
        last_name="Rossi",
        email_notifications_enabled=True,
    )

    assert result is not None
    assert result.username == "newuser"
    assert result.first_name == "Mario"
    assert result.last_name == "Rossi"
    assert result.email_notifications_enabled is True


def test_update_profile_duplicate_username():

    mock_user_repo = MagicMock()

    mock_user_repo.get_by_username.return_value = User()

    service = build_user_service(mock_user_repo)

    user = build_user()

    with pytest.raises(ValidationError):
        service.update_profile(
            user=user,
            username="existinguser",
        )


def test_update_profile_partial_update():

    mock_user_repo = MagicMock()

    mock_user_repo.get_by_username.return_value = None

    service = build_user_service(mock_user_repo)

    user = build_user()

    result = service.update_profile(
        user=user,
        first_name="Mario",
        last_name="Rossi",
        email_notifications_enabled=False,
    )

    assert result is not None
    assert result.first_name == "Mario"
    assert result.last_name == "Rossi"
    assert result.email_notifications_enabled is False


def test_update_profile_only_username():

    mock_user_repo = MagicMock()

    mock_user_repo.get_by_username.return_value = None

    service = build_user_service(mock_user_repo)

    user = build_user()

    result = service.update_profile(
        user=user,
        username="newuser",
    )

    assert result is not None
    assert result.username == "newuser"
