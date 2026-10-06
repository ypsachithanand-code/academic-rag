"""Unit tests for LexicalService and BM25Scorer."""

from unittest.mock import MagicMock
from app.services.lexical_service import LexicalService, BM25Scorer, tokenize_text


def test_tokenize_text():
    tokens = tokenize_text("Transformer: Attention Is All You Need (2017)!")
    assert "transformer" in tokens
    assert "attention" in tokens
    assert "2017" in tokens


def test_bm25_scorer():
    corpus = [
        {"chunk_id": "c1", "text": "The Transformer uses self-attention mechanism."},
        {"chunk_id": "c2", "text": "Convolutional neural networks process images."},
        {"chunk_id": "c3", "text": "Recurrent neural networks process sequential data."},
    ]
    scorer = BM25Scorer(corpus)
    query_tokens = tokenize_text("self-attention transformer")
    results = scorer.score_query(query_tokens, top_k=2)

    assert len(results) > 0
    top_doc, top_score = results[0]
    assert top_doc["chunk_id"] == "c1"
    assert top_score > 0.0


def test_lexical_service_search_mocked():
    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True

    mock_point1 = MagicMock()
    mock_point1.id = "p1"
    mock_point1.payload = {
        "document_id": "doc1",
        "chunk_id": "c1",
        "text": "Deep learning models in natural language processing.",
        "page_numbers": [1],
        "token_count": 10,
    }

    mock_qdrant.client.scroll.return_value = ([mock_point1], None)

    service = LexicalService(qdrant=mock_qdrant)
    results = service.search(query="natural language processing", top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].lexical_score > 0.0
