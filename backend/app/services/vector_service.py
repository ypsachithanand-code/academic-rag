"""Vector database indexing service interface for future implementation (Phase 2+)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorService(ABC):
    """Abstract interface for managing collections and vector indexing in Qdrant."""

    @abstractmethod
    async def create_collection_if_not_exists(self, collection_name: str) -> bool:
        """Ensure Qdrant vector collection exists."""
        raise NotImplementedError("Vector collection management will be implemented in Phase 2.")

    @abstractmethod
    async def index_chunks(self, collection_name: str, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> bool:
        """Upsert embedded chunks into Qdrant vector store."""
        raise NotImplementedError("Vector indexing will be implemented in Phase 2.")
