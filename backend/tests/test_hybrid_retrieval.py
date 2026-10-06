"""Unit tests for Hybrid RetrievalService (RRF candidate fusion)."""

from unittest.mock import MagicMock
from app.models.document import SearchRequest, SearchResult
from app.services.retrieval_service import RetrievalService


def test_reciprocal_rank_fusion():
    retriever = RetrievalService(embedder=MagicMock(), qdrant=MagicMock(), lexical=MagicMock(), reranker=MagicMock())

    dense_results = [
        SearchResult(score=0.9, dense_score=0.9, document_id="d1", chunk_id="c1", page_numbers=[1], text="Text 1", token_count=5),
        SearchResult(score=0.8, dense_score=0.8, document_id="d1", chunk_id="c2", page_numbers=[2], text="Text 2", token_count=5),
    ]

    lexical_results = [
        SearchResult(score=10.0, lexical_score=10.0, document_id="d1", chunk_id="c2", page_numbers=[2], text="Text 2", token_count=5),
        SearchResult(score=8.0, lexical_score=8.0, document_id="d1", chunk_id="c3", page_numbers=[3], text="Text 3", token_count=5),
    ]

    fused = retriever._reciprocal_rank_fusion(dense_results, lexical_results, rrf_k=60.0)

    assert len(fused) == 3
    # c2 appears in both dense and lexical top rankings, so it should have highest RRF score
    assert fused[0].chunk_id == "c2"
    assert fused[0].dense_score == 0.8
    assert fused[0].lexical_score == 10.0


def test_hybrid_retrieval_flow():
    mock_embedder = MagicMock()
    mock_qdrant = MagicMock()
    mock_lexical = MagicMock()
    mock_reranker = MagicMock()

    mock_qdrant.search.return_value = []
    mock_lexical.search.return_value = []
    mock_reranker.rerank.side_effect = lambda query, candidates, top_k: candidates[:top_k]

    retriever = RetrievalService(
        embedder=mock_embedder,
        qdrant=mock_qdrant,
        lexical=mock_lexical,
        reranker=mock_reranker,
    )

    req = SearchRequest(query="Attention mechanism", top_k=5)
    resp = retriever.search(req)

    assert resp.query == "Attention mechanism"
    assert resp.top_k == 5
    mock_embedder.embed_query.assert_called_once()
    mock_qdrant.search.assert_called_once()
    mock_lexical.search.assert_called_once()
    mock_reranker.rerank.assert_called_once()
