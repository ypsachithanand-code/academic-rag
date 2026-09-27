from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Response model for the root API endpoint."""
    message: str = Field(..., json_schema_extra={"example": "Academic RAG API"})
    status: str = Field(..., json_schema_extra={"example": "running"})


class HealthResponse(BaseModel):
    """Response model for the application health check endpoint."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(..., json_schema_extra={"example": "academic-rag"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})


class QdrantHealthResponse(BaseModel):
    """Response model for the Qdrant service health check endpoint."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(default="qdrant", json_schema_extra={"example": "qdrant"})
