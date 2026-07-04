from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from structlog import contextvars, get_logger

from emergencypulse.api.errors import register_exception_handlers
from emergencypulse.api.routes_auth import router as auth_router
from emergencypulse.api.routes_dispatch import router as dispatch_router
from emergencypulse.api.routes_health import router as health_router
from emergencypulse.api.routes_routes import router as routes_router
from emergencypulse.core.config import get_settings
from emergencypulse.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger()


def create_app() -> FastAPI:
    tags_metadata = [
        {
            "name": "health",
            "description": (
                "Readiness and liveness endpoints for load balancers and deployment checks."
            ),
        },
        {
            "name": "auth",
            "description": "JWT token issuance for dispatch operators and system integrations.",
        },
        {
            "name": "dispatch",
            "description": "Incident intake and ambulance route assignment APIs.",
        },
        {
            "name": "routes",
            "description": "Open route calculation APIs for healthcare services.",
        },
    ]
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="Geospatial emergency ambulance routing and dispatch API.",
        description=(
            "EmergencyPulse optimizes ambulance assignment using patient criticality, "
            "ambulance capability, traffic conditions, signal timing proxies, and spatial distance."
        ),
        openapi_version="3.0.3",
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "filter": True,
            "persistAuthorization": True,
            "tryItOutEnabled": True,
        },
        openapi_tags=tags_metadata,
        servers=[
            {"url": "http://localhost:8080", "description": "Local development"},
            {"url": "https://api.staging.emergencypulse.example", "description": "Staging"},
            {"url": "https://api.emergencypulse.example", "description": "Production"},
        ],
    )

    @app.get("/swagger", include_in_schema=False)
    async def swagger_alias():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_ui_parameters={
                "displayRequestDuration": True,
                "filter": True,
                "persistAuthorization": True,
                "tryItOutEnabled": True,
            },
        )

    @app.middleware("http")
    async def request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        contextvars.bind_contextvars(request_id=request_id)
        started = perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            response.headers["x-request-id"] = request_id
            logger.info(
                "request_complete",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
            )
            return response
        finally:
            contextvars.clear_contextvars()

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(dispatch_router, prefix=settings.api_prefix)
    app.include_router(routes_router, prefix=settings.api_prefix)

    default_openapi = app.openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = default_openapi()
        openapi_schema["openapi"] = "3.0.3"
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
