from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.health import HealthResponse, QdrantHealthResponse
from app.services.qdrant_service import qdrant_service

router = APIRouter(prefix="/health", tags=["Health v1"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application Health Check (v1)",
)
async def get_app_health_v1() -> HealthResponse:
    """Versioned application health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="academic-rag",
        version=settings.APP_VERSION,
    )


@router.get(
    "/qdrant",
    response_model=QdrantHealthResponse,
    summary="Qdrant Service Health Check (v1)",
    responses={
        200: {"model": QdrantHealthResponse, "description": "Qdrant is reachable and healthy."},
        503: {"model": QdrantHealthResponse, "description": "Qdrant is unreachable or unhealthy."},
    },
)
async def get_qdrant_health_v1():
    """Versioned Qdrant health check endpoint."""
    is_healthy = qdrant_service.check_health()
    qdrant_status = "healthy" if is_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={"status": qdrant_status, "service": "qdrant"},
    )
