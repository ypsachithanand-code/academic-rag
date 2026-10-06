"""Unit tests for Multi-Document and Single-Document retrieval filtering."""

from unittest.mock import MagicMock
from app.models.document import SearchRequest
from app.services.retrieval_service import RetrievalService


def test_single_document_filtering():
    mock_qdrant = MagicMock()
    mock_embedder = MagicMock()
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

    req = SearchRequest(query="Question", document_id="doc-123", top_k=5)
    retriever.search(req)

    mock_qdrant.search.assert_called_once()
    assert mock_qdrant.search.call_args[1]["document_id"] == "doc-123"

    mock_lexical.search.assert_called_once()
    assert mock_lexical.search.call_args[1]["document_id"] == "doc-123"


def test_multi_document_retrieval_all_documents():
    mock_qdrant = MagicMock()
    mock_embedder = MagicMock()
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

    req = SearchRequest(query="Cross-document academic question", document_id=None, top_k=5)
    retriever.search(req)

    mock_qdrant.search.assert_called_once()
    assert mock_qdrant.search.call_args[1]["document_id"] is None

    mock_lexical.search.assert_called_once()
    assert mock_lexical.search.call_args[1]["document_id"] is None
