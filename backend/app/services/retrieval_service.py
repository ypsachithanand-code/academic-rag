"""Retrieval and similarity search service interface for future implementation (Phase 2+)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseRetrievalService(ABC):
    """Abstract interface for similarity search and context retrieval."""

    @abstractmethod
    async def search_similar_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform vector similarity search against Qdrant."""
        raise NotImplementedError("Similarity search will be implemented in Phase 2.")
