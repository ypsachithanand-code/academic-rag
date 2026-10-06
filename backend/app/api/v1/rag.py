"""RAG Query API Endpoint for End-to-End Academic Document Question Answering."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.document import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Academic RAG Answer Generation",
    description="Execute end-to-end RAG pipeline: vector search -> context formatting -> local LLM -> grounded answer with source citations.",
)
async def query_rag(request: RAGQueryRequest) -> RAGQueryResponse:
    """End-to-End Academic RAG question answering endpoint."""
    return await rag_service.query_academic_rag(request)


@router.post(
    "/query/stream",
    summary="Academic RAG Token Streaming Answer Generation",
    description="Execute end-to-end RAG pipeline with token streaming response.",
)
async def query_rag_stream(request: RAGQueryRequest):
    """Streaming Academic RAG question answering endpoint."""
    return StreamingResponse(
        rag_service.stream_academic_rag(request),
        media_type="text/event-stream",
    )
