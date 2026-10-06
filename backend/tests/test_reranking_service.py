"""Unit tests for RerankingService and fallback mechanism."""

from unittest.mock import MagicMock, patch
from app.models.document import SearchResult
from app.services.reranking_service import RerankingService


def test_reranking_service_disabled_fallback():
    service = RerankingService(enabled=False)
    candidates = [
        SearchResult(score=0.9, document_id="d1", chunk_id="c1", page_numbers=[1], text="Text 1", token_count=5),
        SearchResult(score=0.8, document_id="d1", chunk_id="c2", page_numbers=[2], text="Text 2", token_count=5),
    ]

    results = service.rerank("query", candidates, top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "c1"


def test_reranking_service_model_load_failure_fallback():
    service = RerankingService(enabled=True)
    candidates = [
        SearchResult(score=0.9, document_id="d1", chunk_id="c1", page_numbers=[1], text="Text 1", token_count=5),
    ]

    with patch("sentence_transformers.CrossEncoder", side_effect=RuntimeError("Download failed")):
        results = service.rerank("query", candidates, top_k=5)
        assert len(results) == 1
        assert results[0].chunk_id == "c1"


def test_reranking_service_successful_rerank_mocked():
    service = RerankingService(enabled=True)
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.15, 0.95]  # Second candidate is more relevant

    service._model = mock_model
    service._device = "cpu"

    candidates = [
        SearchResult(score=0.9, document_id="d1", chunk_id="c1", page_numbers=[1], text="Text 1", token_count=5),
        SearchResult(score=0.8, document_id="d1", chunk_id="c2", page_numbers=[2], text="Text 2", token_count=5),
    ]

    results = service.rerank("query", candidates, top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c2"
    assert results[0].rerank_score == 0.95
    assert results[1].chunk_id == "c1"
    assert results[1].rerank_score == 0.15
