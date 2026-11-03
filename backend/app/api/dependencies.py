from typing import Annotated

from fastapi import Header

from app.core.exceptions import AppException


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    if not x_user_id or not x_user_id.strip():
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Missing required header 'X-User-Id'",
            details={"headers.x-user-id": "Header required"},
        )
    return x_user_id.strip()


def get_idempotency_key(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str:
    if not idempotency_key or not idempotency_key.strip():
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Missing required header 'Idempotency-Key'",
            details={"headers.idempotency-key": "Header required"},
        )
    return idempotency_key.strip()
