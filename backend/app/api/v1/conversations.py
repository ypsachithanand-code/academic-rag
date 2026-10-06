"""FastAPI router for research conversation sessions and message management."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status

from app.models.conversation import (
    AddMessageRequest,
    Conversation,
    ConversationListResponse,
    ConversationMessage,
    CreateConversationRequest,
)
from app.models.document import RAGQueryRequest, RAGQueryResponse
from app.models.error import ErrorResponse
from app.services.conversation_service import conversation_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
    summary="Create Research Conversation",
    description="Creates a new research conversation session.",
)
async def create_conversation(
    request: Optional[CreateConversationRequest] = None,
) -> Conversation:
    """Creates a new conversation session."""
    title = request.title if request else None
    return conversation_service.create_conversation(title=title)


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List Conversations",
    description="Lists all active research conversation sessions ordered by recent activity.",
)
async def list_conversations() -> ConversationListResponse:
    """Lists all active research conversation sessions."""
    convs = conversation_service.list_conversations()
    return ConversationListResponse(total=len(convs), conversations=convs)


@router.get(
    "/{conversation_id}",
    response_model=Conversation,
    summary="Get Conversation Session",
    description="Retrieves a research conversation session by ID with message history.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found."},
    },
)
async def get_conversation(conversation_id: str) -> Conversation:
    """Retrieves a conversation session by ID."""
    return conversation_service.get_conversation(conversation_id)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Conversation",
    description="Deletes a research conversation session and its stored message history.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found."},
    },
)
async def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """Deletes a research conversation session."""
    conversation_service.delete_conversation(conversation_id)
    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }


@router.get(
    "/{conversation_id}/messages",
    response_model=List[ConversationMessage],
    summary="Get Conversation Messages",
    description="Retrieves recent bounded message history for a conversation session.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found."},
    },
)
async def get_conversation_messages(conversation_id: str) -> List[ConversationMessage]:
    """Retrieves bounded message history for a conversation."""
    conversation_service.get_conversation(conversation_id)
    return conversation_service.get_bounded_history(conversation_id)


@router.post(
    "/{conversation_id}/messages",
    response_model=RAGQueryResponse,
    summary="Send Message / Ask Question in Conversation",
    description="Submits a user query within a research conversation session, invoking conversation-aware RAG.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation or Document not found."},
    },
)
async def add_conversation_message(
    conversation_id: str,
    request: AddMessageRequest,
) -> RAGQueryResponse:
    """Submits a question within an existing conversation session."""
    rag_req = RAGQueryRequest(
        query=request.content,
        document_id=request.document_id,
        document_ids=request.document_ids,
        conversation_id=conversation_id,
        mode=request.mode.value if request.mode else "qa",
        top_k=request.top_k,
    )
    return await rag_service.query_academic_rag(rag_req)
