from collections.abc import Sequence
from typing import Any

from src.core.exceptions import ConflictError, DomainError, NotFoundError, OperationalError


def error_payload(
    *,
    code: str,
    message: str,
    details: Sequence[Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = list(details)
    return payload


def http_status_for_domain(exc: DomainError) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    return 400


def payload_for_exception(exc: DomainError | OperationalError) -> dict[str, Any]:
    return error_payload(code=exc.code, message=exc.message)
