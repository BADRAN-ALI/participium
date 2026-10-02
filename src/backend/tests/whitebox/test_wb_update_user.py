from __future__ import annotations

from unittest.mock import Mock

import pytest

from participium.core.exceptions import NotFoundError, ValidationError
from participium.models.enums import Role
from participium.models.user import User
from participium.services.user_service import UserService

pytestmark = pytest.mark.whitebox


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_user(user_id: int = 1, role: Role = Role.CITIZEN) -> User:
    user = User(
        username="alice",
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        password_hash="hash",
        role=role,
    )
    user.id = user_id
    user.category_id = None
    user.is_active = True
    user.email_notifications_enabled = True
    return user


@pytest.fixture
def svc() -> dict:
    session = Mock()
    user_repo = Mock()
    category_repo = Mock()
    service = UserService(
        session=session,
        user_repository=user_repo,
        category_repository=category_repo,
    )
    return {
        "service": service,
        "session": session,
        "user_repo": user_repo,
        "category_repo": category_repo,
    }


# ---------------------------------------------------------------------------
# TC-WB-UU-01  user not found → NotFoundError raised immediately
# Covers: get_user raises (user_repository returns None)
# ---------------------------------------------------------------------------
def test_update_user_user_not_found_raises(svc: dict) -> None:
    svc["user_repo"].get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        svc["service"].update_user(999, {})


# ---------------------------------------------------------------------------
# TC-WB-UU-02  new username already used by another account → ValidationError
# Covers: C1=True (username), C2=True (different), C3=True (conflict found)
# ---------------------------------------------------------------------------
def test_update_user_duplicate_username_raises(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user
    svc["user_repo"].get_by_username.return_value = Mock()  # conflict

    with pytest.raises(ValidationError, match="Username already in use"):
        svc["service"].update_user(1, {"username": "other_name"})


# ---------------------------------------------------------------------------
# TC-WB-UU-03  new email already used by another account → ValidationError
# Covers: C4=True (email), C5=True (different), C6=True (conflict found)
# ---------------------------------------------------------------------------
def test_update_user_duplicate_email_raises(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user
    svc["user_repo"].get_by_username.return_value = None
    svc["user_repo"].get_by_email.return_value = Mock()  # conflict

    with pytest.raises(ValidationError, match="Email already in use"):
        svc["service"].update_user(1, {"email": "other@example.com"})


# ---------------------------------------------------------------------------
# TC-WB-UU-04  username in payload matches the current username → no conflict check
# Covers: C2=False (username == user.username) → get_by_username not called
# ---------------------------------------------------------------------------
def test_update_user_same_username_skips_conflict_check(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user

    result = svc["service"].update_user(1, {"username": "alice"})

    assert result is user
    svc["user_repo"].get_by_username.assert_not_called()


# ---------------------------------------------------------------------------
# TC-WB-UU-05  text fields in payload → fields updated on user object
# Covers: inner for-loop body executed for each of the four text fields
# ---------------------------------------------------------------------------
def test_update_user_text_fields_updated(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user
    svc["user_repo"].get_by_username.return_value = None
    svc["user_repo"].get_by_email.return_value = None

    result = svc["service"].update_user(1, {
        "username": "new_alice",
        "first_name": "Alicia",
        "last_name": "Brown",
        "email": "newalice@example.com",
    })

    assert result.username == "new_alice"
    assert result.first_name == "Alicia"
    assert result.last_name == "Brown"
    assert result.email == "newalice@example.com"


# ---------------------------------------------------------------------------
# TC-WB-UU-06  role changed to OPERATOR with valid category → role and category set
# Covers: C8=True (role in payload); category resolution executed
# ---------------------------------------------------------------------------
def test_update_user_role_changed_to_operator_assigns_category(svc: dict) -> None:
    user = _make_user(role=Role.CITIZEN)
    cat = Mock()
    cat.id = 3
    cat.is_active = True
    svc["user_repo"].get_by_id.return_value = user
    svc["category_repo"].get_by_id.return_value = cat

    result = svc["service"].update_user(1, {"role": "operator", "category_id": 3})

    assert result.role == Role.OPERATOR
    assert result.category_id == cat.id


# ---------------------------------------------------------------------------
# TC-WB-UU-07  only category_id in payload (no role change) → category resolved for operator
# Covers: C9=True ("category_id" in payload), role stays OPERATOR
# ---------------------------------------------------------------------------
def test_update_user_category_id_only_resolves_category(svc: dict) -> None:
    user = _make_user(role=Role.OPERATOR)
    cat = Mock()
    cat.id = 7
    cat.is_active = True
    svc["user_repo"].get_by_id.return_value = user
    svc["category_repo"].get_by_id.return_value = cat

    result = svc["service"].update_user(1, {"category_id": 7})

    assert result.category_id == cat.id


# ---------------------------------------------------------------------------
# TC-WB-UU-08  is_active updated via payload
# Covers: C10=True (is_active in payload)
# ---------------------------------------------------------------------------
def test_update_user_is_active_updated(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user

    result = svc["service"].update_user(1, {"is_active": False})

    assert result.is_active is False


# ---------------------------------------------------------------------------
# TC-WB-UU-09  email_notifications_enabled updated via payload
# Covers: C11=True (email_notifications_enabled in payload)
# ---------------------------------------------------------------------------
def test_update_user_email_notifications_enabled_updated(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user

    result = svc["service"].update_user(1, {"email_notifications_enabled": False})

    assert result.email_notifications_enabled is False


# ---------------------------------------------------------------------------
# TC-WB-UU-10  empty payload → nothing changed, commit called, user returned
# Covers: all optional branches skipped; only commit path exercised
# ---------------------------------------------------------------------------
def test_update_user_empty_payload_commits_and_returns_unchanged(svc: dict) -> None:
    user = _make_user()
    svc["user_repo"].get_by_id.return_value = user

    result = svc["service"].update_user(1, {})

    assert result is user
    svc["session"].commit.assert_called_once()
