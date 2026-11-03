from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router as api_router
from app.core.exceptions import AppException

app = FastAPI(
    title="Slot booking backend",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = {}
    is_json_decode_error = False

    for err in exc.errors():
        err_type = err.get("type", "")
        if "json_invalid" in err_type:
            is_json_decode_error = True
            details["body"] = "Malformed JSON payload"
            continue

        loc = err.get("loc", ())
        if len(loc) > 1 and loc[0] in ("body", "query"):
            field = ".".join(str(part) for part in loc[1:])
        elif len(loc) > 1 and loc[0] == "header":
            field = "headers." + ".".join(str(part) for part in loc[1:])
        elif loc:
            field = ".".join(str(part) for part in loc)
        else:
            field = "body"

        details[field] = err.get("msg", "Invalid value")

    if request.url.path == "/slots" and "date" in details:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_DATE",
                    "message": "Query parameter 'date' must be in YYYY-MM-DD format",
                    "details": details,
                }
            },
        )

    message = (
        "Malformed JSON payload"
        if is_json_decode_error
        else "Request validation failed"
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail) if exc.detail else "An HTTP error occurred",
                "details": {},
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
