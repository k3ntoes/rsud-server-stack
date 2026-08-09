from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.dependencies import AuthError
from app.core.errors import error_response
from app.modules.auth.api import router as auth_router
from app.modules.master.api import router as master_router
from app.modules.inspection.api import router as inspection_router
from app.modules.media.api import router as media_router
from app.modules.analytics.api import router as analytics_router

# Ensure all models are registered in SQLAlchemy metadata at startup
from app.modules.background.models import BackgroundJob  # noqa: F401

app = FastAPI(title="RSUD Ajibarang API")


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return error_response(401, exc.detail, exc.code)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Standardize schema-validation 422s to {detail, code} so Android can parse them.

    FastAPI default returns `{"detail": [...]}` (a list, no `code`), which Android's
    ApiErrorDto(detail: String, code: String) cannot deserialize. Keep the shape
    consistent with error_response(): compact "field (error_type)" list for diagnosis.
    """
    details = ", ".join(
        f"{'.'.join(str(p) for p in err.get('loc', ())) or 'body'} ({err.get('type', 'invalid')})"
        for err in exc.errors()
    )
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f"Validation error: {details}" if details else "Validation error",
        code="VALIDATION_ERROR",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(master_router)
app.include_router(inspection_router)
app.include_router(media_router)
app.include_router(analytics_router)
