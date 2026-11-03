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
            status_code=422,
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


class SlotTakenException(AppException):

    def __init__(self, message: str = "This slot is already booked"):
        super().__init__(
            status_code=409,
            code="SLOT_TAKEN",
            message=message,
        )


class BookingLimitReachedException(AppException):

    def __init__(
        self,
        message: str = (
            "User cannot have more than 2 active upcoming bookings at any time"
        ),
    ):
        super().__init__(
            status_code=409,
            code="BOOKING_LIMIT_REACHED",
            message=message,
        )


class BookingNotFoundException(AppException):

    def __init__(self, message: str = "Booking not found"):
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=message,
        )


class BookingAlreadyCancelledException(AppException):

    def __init__(self, message: str = "Booking is already cancelled"):
        super().__init__(
            status_code=400,
            code="ALREADY_CANCELLED",
            message=message,
        )
