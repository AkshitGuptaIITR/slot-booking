from typing import Any, Dict, Optional


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class InvalidDateException(AppException):
    def __init__(self, message: str = "Invalid date format. Expected YYYY-MM-DD."):
        super().__init__(status_code=400, code="INVALID_DATE", message=message)


class InvalidSlotException(AppException):
    def __init__(
        self,
        message: str = "The requested slot is invalid.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=400,
            code="INVALID_SLOT",
            message=message,
            details=details,
        )


class IdempotencyKeyReusedException(AppException):
    def __init__(
        self,
        message: str = "Idempotency key was previously used with a different request payload",
    ):
        super().__init__(
            status_code=422,
            code="IDEMPOTENCY_KEY_REUSED",
            message=message,
        )
