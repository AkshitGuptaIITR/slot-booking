from typing import Annotated

from fastapi import Header

from app.core.exceptions import AppException, UnauthorizedException


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    if not x_user_id or not x_user_id.strip():
        raise UnauthorizedException("Missing or empty required header 'X-User-Id'")
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
