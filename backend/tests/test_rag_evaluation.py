"""Evaluation framework tests for Phase 6 Academic RAG quality."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.document import (
    RAGQueryRequest,
    SearchResult,
    SearchResponse,
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
def rag_service(mock_retriever, mock_llm):
    return RAGService(retriever=mock_retriever, llm=mock_llm)


@pytest.mark.asyncio
async def test_eval_grounded_answer_with_citations(rag_service, mock_retriever, mock_llm):
    """Evaluation Test 1: Verify grounded generation produces accurate sources and citations."""
    chunk1 = SearchResult(
        score=0.92,
        rerank_score=0.95,
        dense_score=0.88,
        lexical_score=8.5,
        document_id="paper-001",
        chunk_id="paper-001_chunk_001",
        page_numbers=[3, 4],
        text="The proposed Transformer architecture eliminates recurrence and uses multi-head attention.",
        token_count=15,
        document_title="Attention Is All You Need",
        section_heading="3 Architecture",
    )

    mock_retriever.search.return_value = SearchResponse(
        query="What architecture is proposed?",
        top_k=5,
        results=[chunk1],
    )
    mock_llm.generate_answer.return_value = (
        "The proposed Transformer architecture eliminates recurrence and relies on multi-head attention [Source 1]."
    )

    req = RAGQueryRequest(query="What architecture is proposed?")
    resp = await rag_service.query_academic_rag(req)

    assert "[Source 1]" in resp.answer or "Transformer" in resp.answer
    assert len(resp.sources) == 1
    assert resp.sources[0].chunk_id == "paper-001_chunk_001"
    assert resp.sources[0].rerank_score == 0.95
    assert resp.sources[0].dense_score == 0.88
    assert resp.sources[0].lexical_score == 8.5
    assert resp.sources[0].document_title == "Attention Is All You Need"
    assert resp.sources[0].section_heading == "3 Architecture"


@pytest.mark.asyncio
async def test_eval_unsupported_question_refusal(rag_service, mock_retriever, mock_llm):
    """Evaluation Test 2: Verify questions unsupported by Qdrant return explicit unanswerable response."""
    mock_retriever.search.return_value = SearchResponse(
        query="What is the capital of Mars?",
        top_k=5,
        results=[],
    )

    req = RAGQueryRequest(query="What is the capital of Mars?")
    resp = await rag_service.query_academic_rag(req)

    assert "do not contain enough information" in resp.answer.lower()
    assert resp.sources == []
    mock_llm.generate_answer.assert_not_called()


def test_eval_context_construction_deduplication_and_formatting():
    """Evaluation Test 3: Verify context construction formatting, header metadata, and chunk deduplication."""
    service = RAGService(retriever=MagicMock(), llm=MagicMock())

    chunk1 = SearchResult(
        score=0.91,
        rerank_score=0.91,
        document_id="doc1",
        chunk_id="chunk_1",
        page_numbers=[1],
        text="Section 1 text content.",
        token_count=5,
        document_title="Paper Title 1",
        section_heading="Introduction",
    )
    # Duplicate chunk_id
    chunk1_dup = SearchResult(
        score=0.91,
        rerank_score=0.91,
        document_id="doc1",
        chunk_id="chunk_1",
        page_numbers=[1],
        text="Section 1 text content.",
        token_count=5,
    )

    context = service.build_context([chunk1, chunk1_dup])

    # Should only include [Source 1] once due to deduplication
    assert "[Source 1]" in context
    assert "[Source 2]" not in context
    assert "Document: Paper Title 1" in context
    assert "Section: Introduction" in context
    assert "Pages: 1" in context
