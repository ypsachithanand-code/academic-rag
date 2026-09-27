from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as top_health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import BaseAppException
from app.core.logging import logger, setup_logging
from app.models.health import RootResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    setup_logging()
    settings.ensure_directories_exist()
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} "
        f"[Env: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}]"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Academic Document RAG API Service.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(BaseAppException)
async def custom_app_exception_handler(request: Request, exc: BaseAppException):
    """Handles custom BaseAppException and formats clean JSON responses."""
    logger.warning(f"Application exception on {request.url.path}: {exc.message} (Code: {exc.code})")
    error_payload = {
        "code": exc.code,
        "message": exc.message,
    }
    if exc.details:
        error_payload["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_payload},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent raw stack traces from reaching clients."""
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            }
        },
    )


# Include Routers
app.include_router(top_health_router)
app.include_router(api_v1_router)


# Root Endpoint
@app.get(
    "/",
    response_model=RootResponse,
    tags=["Root"],
    summary="Root API Endpoint",
)
async def get_root() -> RootResponse:
    """Basic root endpoint to verify API server is operational."""
    return RootResponse(
        message="Academic RAG API",
        status="running",
    )
