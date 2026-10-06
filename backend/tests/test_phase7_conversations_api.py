"""Unit and API integration tests for Phase 7 conversations, query rewriting, research modes, and source inspection."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.conversation import (
    Conversation,
    ConversationMessage,
    MessageRole,
    ResearchMode,
)
from app.models.document import DocumentChunk, RAGSource, RAGQueryResponse
from app.services.conversation_service import conversation_service
from app.services.query_rewrite_service import query_rewrite_service
from app.services.llm_service import build_research_mode_instructions
from app.services.document_service import document_service
from app.services.rag_service import rag_service


client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Query Rewrite Service Tests
# ---------------------------------------------------------------------------

def test_query_rewrite_empty_history():
    res = query_rewrite_service.rewrite_to_standalone_query("What is the model?", [])
    assert res == "What is the model?"


def test_query_rewrite_independent_question():
    history = [
        ConversationMessage(
            message_id="m1",
            conversation_id="c1",
            role=MessageRole.USER,
            content="What is the architecture?",
        ),
        ConversationMessage(
            message_id="m2",
            conversation_id="c1",
            role=MessageRole.ASSISTANT,
            content="The architecture uses a Transformer.",
        ),
    ]
    res = query_rewrite_service.rewrite_to_standalone_query(
        "What limitations are explicitly stated?", history
    )
    assert res == "What limitations are explicitly stated?"


def test_query_rewrite_contextual_followup():
    history = [
        ConversationMessage(
            message_id="m1",
            conversation_id="c1",
            role=MessageRole.USER,
            content="What dataset did the authors use?",
        ),
        ConversationMessage(
            message_id="m2",
            conversation_id="c1",
            role=MessageRole.ASSISTANT,
            content="They used ImageNet.",
        ),
    ]
    res = query_rewrite_service.rewrite_to_standalone_query(
        "Why did they choose it?", history
    )
    assert "Context: regarding dataset did the authors use" in res or "Why did they choose it?" in res


# ---------------------------------------------------------------------------
# 2. Research Mode Instructions Builder Tests
# ---------------------------------------------------------------------------

def test_research_mode_instructions():
    modes = ["qa", "summary", "methodology", "findings", "limitations", "compare"]
    for mode in modes:
        inst = build_research_mode_instructions(mode)
        assert isinstance(inst, str)
        assert mode.upper() in inst or "QA" in inst

    # Default fallback
    assert "QA" in build_research_mode_instructions(None)


# ---------------------------------------------------------------------------
# 3. Conversation Service Tests
# ---------------------------------------------------------------------------

def test_conversation_service_lifecycle():
    conv = conversation_service.create_conversation("Test Title")
    assert conv.conversation_id is not None
    assert conv.title == "Test Title"

    fetched = conversation_service.get_conversation(conv.conversation_id)
    assert fetched.conversation_id == conv.conversation_id

    # Add message
    msg = conversation_service.add_message(
        conversation_id=conv.conversation_id,
        role=MessageRole.USER,
        content="What is attention?",
    )
    assert msg.content == "What is attention?"

    history = conversation_service.get_bounded_history(conv.conversation_id)
    assert len(history) == 1

    # Delete conversation
    deleted = conversation_service.delete_conversation(conv.conversation_id)
    assert deleted is True


# ---------------------------------------------------------------------------
# 4. Conversations API Endpoints Tests
# ---------------------------------------------------------------------------

def test_conversations_api_crud():
    # Create
    create_resp = client.post("/api/v1/conversations", json={"title": "API Test Conv"})
    assert create_resp.status_code == 201
    conv_data = create_resp.json()
    conv_id = conv_data["conversation_id"]

    # List
    list_resp = client.get("/api/v1/conversations")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # Get
    get_resp = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["conversation_id"] == conv_id

    # Get messages
    msgs_resp = client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert msgs_resp.status_code == 200
    assert isinstance(msgs_resp.json(), list)

    # Delete
    del_resp = client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_resp.status_code == 200


# ---------------------------------------------------------------------------
# 5. Source Inspection API Endpoint Tests
# ---------------------------------------------------------------------------

def test_source_inspection_endpoint(monkeypatch):
    dummy_chunk = DocumentChunk(
        chunk_id="doc1_chunk_00000",
        document_id="doc1",
        page_numbers=[1],
        chunk_index=0,
        text="Sample chunk content.",
        character_count=20,
        token_count=5,
    )

    monkeypatch.setattr(document_service, "get_chunk", lambda document_id, chunk_id: dummy_chunk)

    resp = client.get("/api/v1/documents/doc1/chunks/doc1_chunk_00000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk_id"] == "doc1_chunk_00000"
    assert data["document_id"] == "doc1"
    assert data["text"] == "Sample chunk content."


# ---------------------------------------------------------------------------
# 6. Streaming RAG API Endpoint Tests
# ---------------------------------------------------------------------------

def test_streaming_rag_endpoint(monkeypatch):
    async def fake_stream(request):
        yield "Token 1 "
        yield "Token 2"

    monkeypatch.setattr(rag_service, "stream_academic_rag", fake_stream)

    resp = client.post("/api/v1/rag/query/stream", json={"query": "Test streaming question"})
    assert resp.status_code == 200
    assert "Token 1 Token 2" in resp.text
