"""Full RAG orchestrator service interface for future implementation (Phase 2+)."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseRAGService(ABC):
    """Abstract interface for end-to-end Academic RAG pipeline execution."""

    @abstractmethod
    async def query_academic_rag(self, query: str) -> Dict[str, Any]:
        """Execute query pipeline: search -> retrieve context -> LLM inference -> citations."""
        raise NotImplementedError("Full RAG pipeline will be implemented in Phase 2.")
