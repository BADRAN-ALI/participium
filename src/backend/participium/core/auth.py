from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, redirect, request, session, url_for

from participium.core.exceptions import AuthenticationError, AuthorizationError


def current_user():
    return getattr(g, "current_user", None)


def login_user(user) -> None:
    session["user_id"] = user.id


def logout_user() -> None:
    session.pop("user_id", None)


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            if request.path.startswith("/api/"):
                raise AuthenticationError("Authentication required.")
            return redirect(url_for("web.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles):
    def decorator(view: Callable):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                raise AuthenticationError("Authentication required.")
            if user.role not in roles:
                raise AuthorizationError("You do not have permission to perform this action.")
            return view(*args, **kwargs)

        return wrapped

    return decorator
