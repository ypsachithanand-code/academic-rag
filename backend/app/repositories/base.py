from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from app.models.document import DocumentMetadata, DocumentStatus


class BaseDocumentRepository(ABC):
    """Abstract Repository Interface for Document Metadata persistence."""

    @abstractmethod
    def save(self, doc: DocumentMetadata) -> DocumentMetadata:
        """Persists a new document metadata record."""
        pass

    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieves document metadata by document_id."""
        pass

    @abstractmethod
    def get_by_sha256(self, sha256_hash: str) -> Optional[DocumentMetadata]:
        """Retrieves document metadata by file SHA-256 hash."""
        pass

    @abstractmethod
    def list_all(self) -> List[DocumentMetadata]:
        """Lists all stored document metadata records."""
        pass

    @abstractmethod
    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        page_count: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_started_at: Optional[datetime] = None,
        processing_completed_at: Optional[datetime] = None,
    ) -> Optional[DocumentMetadata]:
        """Updates document status, timestamps, and page count."""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """Deletes a document metadata record by ID."""
        pass
