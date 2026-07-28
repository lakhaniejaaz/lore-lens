import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_server_error"
    message = "An unexpected error occurred."

    def __init__(self, fields: dict | None = None):
        self.fields = fields


class DuplicateEmailError(AppError):
    status_code = 409
    code = "duplicate_email"
    message = "An account with this email already exists."


class DuplicateUsernameError(AppError):
    status_code = 409
    code = "duplicate_username"
    message = "This username is already in use."


class InternalServerError(AppError):
    pass


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"
    message = "Username or password is incorrect."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        body = {"error": {"code": exc.code, "message": exc.message}}
        if exc.fields:
            body["error"]["fields"] = exc.fields
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = {}
        for err in exc.errors():
            loc = err["loc"]
            field = str(loc[-1]) if loc else "body"
            msg = err["msg"].removeprefix("Value error, ")
            fields[field] = msg
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "One or more fields are invalid.",
                    "fields": fields,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error in %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )
