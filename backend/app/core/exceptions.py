from typing import Any, Dict, Optional
from fastapi import status


class BaseAppException(Exception):
    """Base exception class for all custom application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ServiceUnavailableException(BaseAppException):
    """Exception raised when an external service (e.g. Qdrant) is unreachable."""

    def __init__(self, service_name: str, message: Optional[str] = None):
        msg = message or f"The service '{service_name}' is currently unavailable."
        super().__init__(
            message=msg,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name},
        )


class ResourceNotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_name: str, resource_id: str):
        super().__init__(
            message=f"{resource_name} with id '{resource_id}' was not found.",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource_name, "id": resource_id},
        )


class DocumentNotFoundException(ResourceNotFoundException):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str):
        super().__init__(resource_name="Document", resource_id=document_id)


class InvalidFileException(BaseAppException):
    """Exception raised when an uploaded file is invalid (format, corrupt, empty)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class FileTooLargeException(BaseAppException):
    """Exception raised when an uploaded file exceeds the maximum size limit."""

    def __init__(self, file_size_mb: float, max_size_mb: int):
        super().__init__(
            message=f"Uploaded file size ({file_size_mb:.2f} MB) exceeds maximum allowed limit of {max_size_mb} MB.",
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"file_size_mb": file_size_mb, "max_size_mb": max_size_mb},
        )


class DuplicateDocumentException(BaseAppException):
    """Exception raised when a document with identical SHA-256 hash already exists."""

    def __init__(self, existing_document_id: str, message: Optional[str] = None):
        msg = message or f"A document with identical content already exists (ID: {existing_document_id})."
        super().__init__(
            message=msg,
            code="DUPLICATE_DOCUMENT",
            status_code=status.HTTP_409_CONFLICT,
            details={"existing_document_id": existing_document_id},
        )


class ChunkingException(BaseAppException):
    """Exception raised when document text chunking fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CHUNKING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class EmbeddingException(BaseAppException):
    """Exception raised when model loading or vector embedding generation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class LLMException(BaseAppException):
    """Exception raised when LLM loading or inference generation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class RAGException(BaseAppException):
    """Exception raised when RAG query orchestration fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RAG_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
