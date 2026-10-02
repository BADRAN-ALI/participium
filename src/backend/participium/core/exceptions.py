class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str = "", status_code: int | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class ValidationError(DomainError):
    status_code = 400


class AuthenticationError(DomainError):
    status_code = 401


class AuthorizationError(DomainError):
    status_code = 403


class NotFoundError(DomainError):
    status_code = 404
