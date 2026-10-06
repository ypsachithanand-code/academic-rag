"""Unit tests for RAGService orchestration with mocked retrieval and LLM services."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import RAGException, LLMException, ServiceUnavailableException
from app.models.document import (
    RAGQueryRequest,
    RAGQueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.rag_service import RAGService


@pytest.fixture
def mock_retriever():
    return MagicMock()


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate_answer = AsyncMock()
    return llm


@pytest.fixture
def mock_doc_service():
    mock = MagicMock()
    return mock


@pytest.fixture
def rag_service(mock_retriever, mock_llm, mock_doc_service):
    return RAGService(retriever=mock_retriever, llm=mock_llm, doc_service=mock_doc_service)


@pytest.mark.asyncio
async def test_rag_query_success(rag_service, mock_retriever, mock_llm):
    """Test full successful RAG pipeline: query -> search -> context -> LLM -> response with citations."""
    sample_result = SearchResult(
        score=0.88,
        document_id="doc-123",
        chunk_id="doc-123_chunk_00000",
        page_numbers=[1, 2],
        text="Sample method description.",
        token_count=10,
    )
    mock_retriever.search.return_value = SearchResponse(
        query="What method was used?",
        top_k=5,
        results=[sample_result],
    )
    mock_llm.generate_answer.return_value = "The study used a sample method."

    req = RAGQueryRequest(query="What method was used?", top_k=5)
    response = await rag_service.query_academic_rag(req)

    assert isinstance(response, RAGQueryResponse)
    assert response.query == "What method was used?"
    assert response.answer == "The study used a sample method."
    assert len(response.sources) == 1
    assert response.sources[0].document_id == "doc-123"
    assert response.sources[0].chunk_id == "doc-123_chunk_00000"
    assert response.sources[0].page_numbers == [1, 2]
    assert response.sources[0].score == 0.88
    assert response.sources[0].text == "Sample method description."

    mock_retriever.search.assert_called_once()
    mock_llm.generate_answer.assert_called_once()


@pytest.mark.asyncio
async def test_rag_empty_query_rejected(rag_service):
    """Test empty query is rejected with RAGException."""
    req = RAGQueryRequest(query="   ")
    with pytest.raises(RAGException, match="Query string cannot be empty"):
        await rag_service.query_academic_rag(req)


@pytest.mark.asyncio
async def test_rag_no_search_results_safe_response(rag_service, mock_retriever, mock_llm):
    """Test safe grounded response returned without calling LLM when Qdrant returns 0 results."""
    mock_retriever.search.return_value = SearchResponse(
        query="Unknown concept",
        top_k=5,
        results=[],
    )

    req = RAGQueryRequest(query="Unknown concept")
    response = await rag_service.query_academic_rag(req)

    assert response.query == "Unknown concept"
    assert "No relevant information was found" in response.answer
    assert response.sources == []
    mock_llm.generate_answer.assert_not_called()


@pytest.mark.asyncio
async def test_rag_document_id_and_top_k_passed_to_retriever(rag_service, mock_retriever, mock_llm):
    """Test document_id and custom top_k are propagated to retrieval_service search request."""
    mock_retriever.search.return_value = SearchResponse(
        query="Specific doc question",
        top_k=3,
        results=[],
    )

    req = RAGQueryRequest(query="Specific doc question", document_id="doc-999", top_k=3)
    await rag_service.query_academic_rag(req)

    mock_retriever.search.assert_called_once()
    search_arg: SearchRequest = mock_retriever.search.call_args[0][0]
    assert search_arg.query == "Specific doc question"
    assert search_arg.document_id == "doc-999"
    assert search_arg.top_k == 3


@pytest.mark.asyncio
async def test_rag_handles_llm_failure(rag_service, mock_retriever, mock_llm):
    """Test LLM generation failure is propagated cleanly."""
    mock_retriever.search.return_value = SearchResponse(
        query="Valid query",
        top_k=5,
        results=[
            SearchResult(
                score=0.9,
                document_id="doc-1",
                chunk_id="c-1",
                page_numbers=[1],
                text="Text",
                token_count=5,
            )
        ],
    )
    mock_llm.generate_answer.side_effect = LLMException("LLM CUDA Out of Memory")

    req = RAGQueryRequest(query="Valid query")
    with pytest.raises(LLMException, match="LLM CUDA Out of Memory"):
        await rag_service.query_academic_rag(req)


@pytest.mark.asyncio
async def test_rag_handles_retrieval_failure(rag_service, mock_retriever):
    """Test retrieval failure (e.g. Qdrant unreachable) is propagated cleanly."""
    mock_retriever.search.side_effect = ServiceUnavailableException("Qdrant", "Vector database connection timed out")

    req = RAGQueryRequest(query="Query during Qdrant outage")
    with pytest.raises(ServiceUnavailableException, match="Vector database connection timed out"):
        await rag_service.query_academic_rag(req)
