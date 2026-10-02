from __future__ import annotations

import secrets

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Inputs:
        password: plaintext password candidate.
        password_hash: stored password hash.

    Returns:
        `True` when the password matches the hash, else `False`.

    Raises:
        No documented domain exception.
    """
    return check_password_hash(password_hash, password)


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
