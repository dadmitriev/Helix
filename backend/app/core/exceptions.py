from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


# ─── Domain exceptions ────────────────────────────────────────────────────────

class AppError(Exception):
    """Base domain exception."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "Resource not found"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"
    message = "Access denied"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"
    message = "Resource conflict"


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_ERROR"
    message = "Validation failed"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"
    message = "Authentication required"


class InvalidStatusTransitionError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "INVALID_STATUS_TRANSITION"
    message = "This status transition is not allowed"


class MLModelNotReadyError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "ML_MODEL_NOT_READY"
    message = "ML model is not loaded. Run ml_training/train.py first."


class InsufficientDataError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "INSUFFICIENT_DATA"
    message = "Insufficient lab results to run prediction"


# ─── FastAPI exception handlers ───────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "HTTP_ERROR"},
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
