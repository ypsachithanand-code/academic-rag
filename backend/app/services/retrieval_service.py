"""BGE-M3 query embedding and Qdrant semantic retrieval."""
from typing import Optional

from app.core.config import settings
from app.models.document import SearchRequest, SearchResponse, SearchResult
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service


class RetrievalService:
    def __init__(self, embedder=None, qdrant=None):
        self.embedder = embedder or embedding_service
        self.qdrant = qdrant or qdrant_service

    def search(self, request: SearchRequest) -> SearchResponse:
        query = request.query.strip()
        if not query:
            raise ValueError("Query string cannot be empty.")
        top_k = min(request.top_k or settings.TOP_K, settings.MAX_TOP_K)
        vector = self.embedder.embed_query(query)
        matches = self.qdrant.search(vector, top_k=top_k, document_id=request.document_id)
        results = []
        for match in matches:
            payload = match.payload or {}
            results.append(SearchResult(
                score=float(match.score), document_id=payload.get("document_id", ""),
                chunk_id=payload.get("chunk_id", str(match.id)),
                page_numbers=payload.get("page_numbers", []), text=payload.get("text", ""),
                token_count=payload.get("token_count", 0),
            ))
        return SearchResponse(query=query, top_k=top_k, results=results)


retrieval_service = RetrievalService()
