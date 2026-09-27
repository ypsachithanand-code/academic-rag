from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.health import HealthResponse, QdrantHealthResponse
from app.services.qdrant_service import qdrant_service

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Returns the health status of the primary FastAPI application.",
)
async def get_app_health() -> HealthResponse:
    """Returns application status, service name, and current version."""
    return HealthResponse(
        status="healthy",
        service="academic-rag",
        version=settings.APP_VERSION,
    )


@router.get(
    "/health/qdrant",
    response_model=QdrantHealthResponse,
    summary="Qdrant Service Health Check",
    description="Verifies reachability of the Qdrant vector database instance.",
    responses={
        200: {"model": QdrantHealthResponse, "description": "Qdrant is reachable and healthy."},
        503: {"model": QdrantHealthResponse, "description": "Qdrant is unreachable or unhealthy."},
    },
)
async def get_qdrant_health():
    """Checks Qdrant connectivity and returns health status without stack traces."""
    is_healthy = qdrant_service.check_health()
    qdrant_status = "healthy" if is_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={"status": qdrant_status, "service": "qdrant"},
    )
