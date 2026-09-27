from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    """Inner error payload containing error code and human-readable message."""
    code: str = Field(..., json_schema_extra={"example": "INTERNAL_SERVER_ERROR"})
    message: str = Field(..., json_schema_extra={"example": "An unexpected error occurred."})
    details: Optional[Dict[str, Any]] = Field(default=None, json_schema_extra={"example": {"field": "value"}})


class ErrorResponse(BaseModel):
    """Standardized top-level JSON error response container."""
    error: ErrorDetails
