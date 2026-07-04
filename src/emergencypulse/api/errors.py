from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import SQLAlchemyError
from structlog import get_logger

from emergencypulse.services.routing import NoAmbulanceAvailableError

logger = get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NoAmbulanceAvailableError)
    async def no_ambulance_handler(_: Request, exc: NoAmbulanceAvailableError):
        return ORJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "NO_AMBULANCE_AVAILABLE", "message": str(exc)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "VALIDATION_ERROR", "details": exc.errors()},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("database_error", path=request.url.path, error=str(exc))
        return ORJSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "DATABASE_UNAVAILABLE", "message": "Database operation failed"},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("unhandled_error", path=request.url.path, error=str(exc))
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "INTERNAL_SERVER_ERROR", "message": "Unexpected server error"},
        )
