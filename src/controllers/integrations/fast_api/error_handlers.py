from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from src.controllers.integrations.fast_api.error_response import (
    error_payload,
    http_status_for_domain,
    payload_for_exception,
)
from src.core.exceptions import DomainError, OperationalError


def handle_domain(_request: Request, exc: Exception) -> Response:
    assert isinstance(exc, DomainError)
    return JSONResponse(
        status_code=http_status_for_domain(exc),
        content=payload_for_exception(exc),
    )


def handle_operational(_request: Request, exc: Exception) -> Response:
    assert isinstance(exc, OperationalError)
    return JSONResponse(status_code=500, content=payload_for_exception(exc))


def handle_request_validation(_request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=422,
        content=error_payload(
            code="request_validation",
            message="Request validation failed",
            details=jsonable_encoder(exc.errors()),
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain)
    app.add_exception_handler(OperationalError, handle_operational)
    app.add_exception_handler(RequestValidationError, handle_request_validation)
