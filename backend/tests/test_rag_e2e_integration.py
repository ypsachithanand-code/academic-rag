"""Real end-to-end RAG query test using Qdrant vector retrieval and local Qwen LLM."""

import pytest
from app.models.document import RAGQueryRequest
from app.services.rag_service import rag_service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_rag_pipeline_end_to_end():
    """Real end-to-end integration test of search -> context -> Qwen LLM -> grounded answer."""
    req = RAGQueryRequest(query="What is attention mechanism in transformers?", top_k=3)
    response = await rag_service.query_academic_rag(req)

    print("\n--- Real RAG Query Output ---")
    print(f"Query: {response.query}")
    print(f"Answer: {response.answer}")
    print(f"Sources Count: {len(response.sources)}")
    for i, src in enumerate(response.sources, 1):
        print(f"Source [{i}] Doc: {src.document_id} | Pages: {src.page_numbers} | Score: {src.score:.3f}")

    assert response.query == "What is attention mechanism in transformers?"
    assert isinstance(response.answer, str)
    assert len(response.answer) > 0
