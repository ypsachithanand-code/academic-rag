"""API Endpoint tests for POST /api/v1/rag/query."""

from unittest.mock import AsyncMock, patch

from app.models.document import RAGQueryResponse, RAGSource


@patch("app.services.rag_service.rag_service.query_academic_rag")
def test_rag_query_api_success(mock_query_rag, client):
    """Test successful POST /api/v1/rag/query API request."""
    mock_query_rag.return_value = RAGQueryResponse(
        query="What is transformer architecture?",
        answer="Transformer architecture is based on self-attention mechanisms.",
        sources=[
            RAGSource(
                document_id="doc-111",
                chunk_id="doc-111_chunk_00001",
                page_numbers=[3],
                score=0.92,
                text="The Transformer is the first sequence transduction model based entirely on self-attention.",
            )
        ],
        document_id="doc-111",
    )

    payload = {
        "query": "What is transformer architecture?",
        "document_id": "doc-111",
        "top_k": 5,
    }
    response = client.post("/api/v1/rag/query", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What is transformer architecture?"
    assert data["answer"] == "Transformer architecture is based on self-attention mechanisms."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_id"] == "doc-111"
    assert data["sources"][0]["chunk_id"] == "doc-111_chunk_00001"
    assert data["sources"][0]["page_numbers"] == [3]
    assert data["sources"][0]["score"] == 0.92


def test_rag_query_api_invalid_empty_query(client):
    """Test POST /api/v1/rag/query with empty query string fails validation."""
    payload = {"query": ""}
    response = client.post("/api/v1/rag/query", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_rag_query_api_invalid_top_k(client):
    """Test POST /api/v1/rag/query with invalid top_k fails validation."""
    payload = {"query": "Valid query", "top_k": 0}
    response = client.post("/api/v1/rag/query", json=payload)
    assert response.status_code == 422
