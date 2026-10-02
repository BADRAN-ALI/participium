from __future__ import annotations

from datetime import timedelta

from participium.core.exceptions import AuthenticationError, ValidationError
from participium.core.security import generate_token, hash_password, verify_password
from participium.core.utils import utcnow
from participium.models.enums import Role
from participium.models.token import EmailVerificationToken
from participium.models.user import User


class AuthService:
    def __init__(self, session, user_repository, token_repository, email_gateway):
        self.session = session
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.email_gateway = email_gateway

    def register_user(self, payload: dict, verification_base_url: str | None = None) -> tuple[User, str | None]:
        required = ["username", "first_name", "last_name", "email", "password"]
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
        if self.user_repository.get_by_username(payload["username"]):
            raise ValidationError("Username already in use.")
        if self.user_repository.get_by_email(payload["email"]):
            raise ValidationError("Email already in use.")

        user = User(
            username=payload["username"].strip(),
            first_name=payload["first_name"].strip(),
            last_name=payload["last_name"].strip(),
            email=payload["email"].strip().lower(),
            password_hash=hash_password(payload["password"]),
            role=Role.CITIZEN,
            is_active=True,
            is_email_verified=False,
            email_notifications_enabled=True,
        )
        self.user_repository.add(user)
        self.session.flush()

        token = EmailVerificationToken(
            user_id=user.id,
            token=generate_token(),
            expires_at=utcnow() + timedelta(hours=48),
            is_used=False,
        )
        self.token_repository.add(token)
        self.session.commit()

        verification_url = None
        if verification_base_url:
            verification_url = verification_base_url.rstrip("/") + f"/{token.token}"
            self.email_gateway.send(
                recipient=user.email,
                subject="Verify your Participium account",
                body=f"Open this link to verify your account: {verification_url}",
            )
        return user, verification_url

    def verify_email(self, token_value: str) -> User:
        """Verify a pending email-verification token.

        Inputs:
            token_value: verification token received by the user.

        Returns:
            The verified `User`.

        Raises:
            ValidationError: if the token does not exist.
            ValidationError: if the token was already used.
            ValidationError: if the token is expired.
        """
        token = self.token_repository.get_by_token(token_value)
        if not token or token.is_used:
            raise ValidationError("Verification token is invalid.")
        if token.expires_at < utcnow():
            raise ValidationError("Verification token has expired.")
        token.is_used = True
        token.user.is_email_verified = True
        self.session.commit()
        return token.user

    def authenticate(self, identifier: str, password: str) -> User:
        """Authenticate a user by username or email plus password.

        Inputs:
            identifier: username or email of the target user.
            password: plaintext password to verify.

        Returns:
            The authenticated `User`.

        Raises:
            AuthenticationError: if credentials are invalid.
            AuthenticationError: if the matched user exists but is inactive.
            AuthenticationError: if the matched user exists but email is not verified.
        """
        user = self.user_repository.get_by_username_or_email(identifier.strip())
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials.")
        if not user.is_email_verified:
            raise AuthenticationError("Email verification is required before login.")
        return user
