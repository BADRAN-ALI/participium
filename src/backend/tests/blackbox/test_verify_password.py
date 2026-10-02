from __future__ import annotations

from participium.core.security import (
    hash_password,
    verify_password,
)


def test_verify_password_success():

    real_hash = hash_password("correctpass")

    result = verify_password(
        "correctpass",
        real_hash,
    )

    assert result is True


def test_verify_password_wrong_password():

    real_hash = hash_password("correctpass")

    result = verify_password(
        "wrongpass",
        real_hash,
    )

    assert result is False


def test_verify_password_empty_password():

    real_hash = hash_password("correctpass")

    result = verify_password(
        "",
        real_hash,
    )

    assert result is False


def test_verify_password_invalid_hash():

    result = verify_password(
        "correctpass",
        "invalidhash",
    )

    assert result is False

