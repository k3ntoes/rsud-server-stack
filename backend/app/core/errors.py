"""Error response helpers with standardized code field for Android Interceptor."""

from fastapi.responses import JSONResponse


def error_response(status_code: int, detail: str, code: str) -> JSONResponse:
    """Return a structured error with both ``detail`` (human-readable) and ``code``
    (machine-readable) fields. Android Interceptor uses ``code`` for reliable
    error-type detection.

    Example response::

        HTTP 401
        { "detail": "Token expired", "code": "TOKEN_EXPIRED" }
    """
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "code": code},
    )
