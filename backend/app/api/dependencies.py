from typing import Annotated

from fastapi import HTTPException, Header, status


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Missing or invalid X-User-Id header",
                "detail": {},
            },
        )

    return x_user_id.strip()
