from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status

from app.models.conversation import SummaryRequest, SummaryResponse
from app.models.document import (
    ChunkInspectionResponse,
    DocumentChunk,
    DocumentListResponse,
    DocumentMetadata,
    ProcessedDocumentData,
    RAGQueryRequest,
    UploadDocumentResponse,
)
from app.models.error import ErrorResponse
from app.services.document_service import document_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Academic PDF Document",
    description="Validates, stores, registers, and asynchronously processes a PDF document through page extraction, chunking, and BGE-M3 embedding.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file format or empty upload."},
        409: {"model": ErrorResponse, "description": "Duplicate PDF content already uploaded."},
        413: {"model": ErrorResponse, "description": "File exceeds maximum upload size limit."},
    },
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Academic PDF document file to ingest"),
) -> UploadDocumentResponse:
    """Uploads a PDF document and queues background extraction, chunking, and BGE-M3 embedding."""
    doc_metadata = document_service.upload_document(file)

    # Queue background processing pipeline (extraction -> chunking -> BGE-M3 embedding)
    background_tasks.add_task(document_service.process_document, doc_metadata.id)

    return UploadDocumentResponse(
        message="Document uploaded successfully and queued for processing.",
        document=doc_metadata,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List All Documents",
    description="Returns a list of all registered academic documents and their processing status.",
)
async def list_documents() -> DocumentListResponse:
    """Lists all stored academic documents."""
    docs = document_service.list_documents()
    return DocumentListResponse(
        total=len(docs),
        documents=docs,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    summary="Get Document Metadata",
    description="Retrieves metadata and current processing status for a single document.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found."},
    },
)
async def get_document(document_id: str) -> DocumentMetadata:
    """Retrieves document metadata by ID."""
    return document_service.get_document(document_id)


@router.get(
    "/{document_id}/pages",
    response_model=ProcessedDocumentData,
    summary="Get Processed Document Pages",
    description="Retrieves page-level extracted and cleaned text for a processed document.",
    responses={
        404: {"model": ErrorResponse, "description": "Document or processed page data not found."},
    },
)
async def get_document_pages(document_id: str) -> ProcessedDocumentData:
    """Retrieves extracted page-level text data for a document."""
    return document_service.get_processed_data(document_id)


@router.get(
    "/{document_id}/chunks",
    response_model=ChunkInspectionResponse,
    summary="Inspect Document Chunks",
    description="Retrieves generated text chunks, page metadata, token counts, and embedding model dimension info.",
    responses={
        404: {"model": ErrorResponse, "description": "Document or chunks not found."},
    },
)
async def get_document_chunks(document_id: str) -> ChunkInspectionResponse:
    """Retrieves inspection chunk list and model metadata for a document."""
    return document_service.get_document_chunks(document_id)


@router.post(
    "/{document_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger/Re-trigger Chunking & Embedding Pipeline",
    description="Explicitly queues or forces re-processing of chunking and BGE-M3 embedding generation.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found."},
    },
)
async def process_document_pipeline(
    document_id: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
) -> Dict[str, Any]:
    """Queues document chunking and embedding generation."""
    document_service.get_document(document_id)
    background_tasks.add_task(document_service.process_document_for_embeddings, document_id, force)
    return {
        "message": "Document chunking and embedding generation queued.",
        "document_id": document_id,
        "force": force,
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description="Deletes document metadata and purges associated PDF, processed, and embedding files from disk.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found."},
    },
)
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Deletes a document and all stored filesystem artifacts."""
    document_service.delete_document(document_id)
    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
    }


@router.post(
    "/{document_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry Document Processing",
    description="Re-queues full document extraction, chunking, and embedding processing for a failed document.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found."},
    },
)
async def retry_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Re-queues document processing pipeline."""
    document_service.get_document(document_id)
    background_tasks.add_task(document_service.retry_processing, document_id)
    return {
        "message": "Document re-processing queued.",
        "document_id": document_id,
    }


@router.get(
    "/{document_id}/chunks/{chunk_id}",
    response_model=DocumentChunk,
    summary="Inspect Specific Document Chunk",
    description="Retrieves a specific chunk by document_id and chunk_id for source inspection.",
    responses={
        404: {"model": ErrorResponse, "description": "Document or chunk not found."},
    },
)
async def get_document_chunk(document_id: str, chunk_id: str) -> DocumentChunk:
    """Retrieves a single chunk for inspection by document_id and chunk_id."""
    return document_service.get_chunk(document_id=document_id, chunk_id=chunk_id)


@router.post(
    "/{document_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Document Summary",
    description="Generates a grounded research summary for a specific document using the academic RAG pipeline.",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found."},
    },
)
async def summarize_document(
    document_id: str,
    request: Optional[SummaryRequest] = None,
) -> SummaryResponse:
    """Generates a grounded document summary using the research assistant RAG pipeline."""
    document_service.get_document(document_id)  # Validate document existence
    top_k = request.top_k if request and request.top_k else 10

    rag_req = RAGQueryRequest(
        query="Summarize the core research objective, approach, main findings, conclusions, and key limitations of this paper.",
        document_id=document_id,
        mode="summary",
        top_k=top_k,
    )
    rag_res = await rag_service.query_academic_rag(rag_req)

    return SummaryResponse(
        document_id=document_id,
        summary=rag_res.answer,
        sources=rag_res.sources,
    )
