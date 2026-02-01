from typing import Any


class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class ValidationError(AppException):
    status_code = 400
    code = "VALIDATION_ERROR"


class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"


class PaymentRequiredError(AppException):
    status_code = 402
    code = "PAYMENT_REQUIRED"


class UnauthorizedError(AppException):
    status_code = 401
    code = "UNAUTHORIZED"
