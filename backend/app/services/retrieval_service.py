"""Hybrid retrieval pipeline combining BGE-M3 Dense search, BM25 Lexical search, RRF candidate fusion, and CrossEncoder reranking."""

from typing import Optional, List, Dict

from app.core.config import settings
from app.core.logging import logger
from app.models.document import SearchRequest, SearchResponse, SearchResult
from app.services.embedding_service import embedding_service, EmbeddingService
from app.services.qdrant_service import qdrant_service, QdrantService
from app.services.lexical_service import lexical_service, LexicalService
from app.services.reranking_service import reranking_service, RerankingService


class RetrievalService:
    """Hybrid Retrieval Service orchestrating dense, lexical, RRF fusion, and cross-encoder reranking."""

    def __init__(
        self,
        embedder: Optional[EmbeddingService] = None,
        qdrant: Optional[QdrantService] = None,
        lexical: Optional[LexicalService] = None,
        reranker: Optional[RerankingService] = None,
    ):
        self.embedder = embedder or embedding_service
        self.qdrant = qdrant or qdrant_service
        self.lexical = lexical if lexical is not None else LexicalService(qdrant=self.qdrant)
        self.reranker = reranker or reranking_service


    def _reciprocal_rank_fusion(
        self,
        dense_results: List[SearchResult],
        lexical_results: List[SearchResult],
        rrf_k: float = settings.RRF_K,
    ) -> List[SearchResult]:
        """Combine dense and lexical search rankings using Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        result_map: Dict[str, SearchResult] = {}

        # Accumulate dense RRF scores
        for rank, res in enumerate(dense_results, 1):
            cid = res.chunk_id
            score = 1.0 / (rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score
            if cid not in result_map:
                result_map[cid] = res.model_copy()
            result_map[cid].dense_score = res.score

        # Accumulate lexical RRF scores
        for rank, res in enumerate(lexical_results, 1):
            cid = res.chunk_id
            score = 1.0 / (rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + score
            if cid not in result_map:
                result_map[cid] = res.model_copy()
            result_map[cid].lexical_score = res.lexical_score or res.score

        # Build fused candidate list sorted by RRF score
        fused_candidates: List[SearchResult] = []
        for cid, rrf_val in rrf_scores.items():
            res = result_map[cid]
            # Preserve original dense score as primary score if present
            if res.dense_score is not None:
                res.score = res.dense_score
            fused_candidates.append((res, rrf_val))

        fused_candidates.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in fused_candidates]


    def search(self, request: SearchRequest) -> SearchResponse:
        """Execute hybrid search pipeline: dense + lexical search -> RRF fusion -> cross-encoder rerank."""
        query = request.query.strip()
        if not query:
            raise ValueError("Query string cannot be empty.")

        target_top_k = min(request.top_k or settings.FINAL_TOP_K, settings.MAX_TOP_K)
        document_id = request.document_id
        document_ids = request.document_ids

        # Step 1: Dense Semantic Search via BGE-M3 + Qdrant
        vector = self.embedder.embed_query(query)
        dense_top_k = target_top_k if request.top_k is not None else settings.DENSE_TOP_K
        
        qdrant_kwargs = {"top_k": dense_top_k, "document_id": document_id}
        if document_ids is not None:
            qdrant_kwargs["document_ids"] = document_ids

        dense_matches = self.qdrant.search(vector, **qdrant_kwargs)

        dense_results = []
        for match in dense_matches:
            payload = match.payload or {}
            dense_results.append(
                SearchResult(
                    score=float(match.score),
                    dense_score=float(match.score),
                    document_id=payload.get("document_id", ""),
                    chunk_id=payload.get("chunk_id", str(match.id)),
                    page_numbers=payload.get("page_numbers", []),
                    text=payload.get("text", ""),
                    token_count=payload.get("token_count", 0),
                    document_title=payload.get("document_title"),
                    section_heading=payload.get("section_heading"),
                )
            )

        # Step 2: Lexical Keyword Search via BM25 (if enabled)
        if settings.HYBRID_RETRIEVAL_ENABLED:
            try:
                lexical_kwargs = {"query": query, "top_k": settings.LEXICAL_TOP_K, "document_id": document_id}
                if document_ids is not None:
                    lexical_kwargs["document_ids"] = document_ids
                lexical_results = self.lexical.search(**lexical_kwargs)
            except Exception as exc:
                logger.warning(f"Lexical search failed: {exc}. Proceeding with dense search results.")
                lexical_results = []

            # Step 3: Reciprocal Rank Fusion
            candidates = self._reciprocal_rank_fusion(dense_results, lexical_results)
        else:
            candidates = dense_results

        # Cap candidates for reranking
        candidate_pool = candidates[: settings.RERANKER_TOP_N]

        # Step 4: Cross-Encoder Reranking
        final_results = self.reranker.rerank(
            query=query, candidates=candidate_pool, top_k=target_top_k
        )

        return SearchResponse(query=query, top_k=target_top_k, results=final_results)


retrieval_service = RetrievalService()
