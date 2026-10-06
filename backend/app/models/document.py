from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Lifecycle status enumeration for academic documents."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_TEXT = "no_text"


class DocumentMetadata(BaseModel):
    """Data model representing complete metadata for an academic document."""
    id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"})
    original_filename: str = Field(..., json_schema_extra={"example": "attention_is_all_you_need.pdf"})
    stored_filename: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a.pdf"})
    file_path: str = Field(..., json_schema_extra={"example": "data/uploads/8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a.pdf"})
    sha256: str = Field(..., json_schema_extra={"example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"})
    file_size: int = Field(..., json_schema_extra={"example": 1048576})
    page_count: int = Field(default=0, json_schema_extra={"example": 15})
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, json_schema_extra={"example": DocumentStatus.UPLOADED})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_started_at: Optional[datetime] = Field(default=None)
    processing_completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, json_schema_extra={"example": None})


class DocumentPage(BaseModel):
    """Extracted text page with preserved page number for future citations."""
    page_number: int = Field(..., json_schema_extra={"example": 1})
    text: str = Field(..., json_schema_extra={"example": "Abstract. We propose a new simple network architecture..."})


class ProcessedDocumentData(BaseModel):
    """Structured container for processed page-level document contents."""
    document_id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"})
    total_pages: int = Field(..., json_schema_extra={"example": 15})
    pages: List[DocumentPage] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """Semantic text chunk with preserved page metadata and token count."""
    chunk_id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a_chunk_00000"})
    document_id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"})
    page_numbers: List[int] = Field(..., json_schema_extra={"example": [1, 2]})
    chunk_index: int = Field(..., json_schema_extra={"example": 0})
    text: str = Field(..., json_schema_extra={"example": "Attention Is All You Need. Abstract..."})
    character_count: int = Field(..., json_schema_extra={"example": 780})
    token_count: int = Field(..., json_schema_extra={"example": 165})


class ChunkInspectionResponse(BaseModel):
    """Inspection container for chunk list and embedding model metadata."""
    document_id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"})
    total_chunks: int = Field(..., json_schema_extra={"example": 12})
    embedding_model: str = Field(..., json_schema_extra={"example": "BAAI/bge-m3"})
    embedding_dimension: int = Field(..., json_schema_extra={"example": 1024})
    chunks: List[DocumentChunk] = Field(default_factory=list)


class EmbeddingPipelineSummary(BaseModel):
    """Metadata tracking how document embeddings were generated and persisted."""
    document_id: str = Field(..., json_schema_extra={"example": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"})
    embedding_model: str = Field(..., json_schema_extra={"example": "BAAI/bge-m3"})
    embedding_dimension: int = Field(..., json_schema_extra={"example": 1024})
    chunk_size: int = Field(..., json_schema_extra={"example": 800})
    chunk_overlap: int = Field(..., json_schema_extra={"example": 120})
    chunk_count: int = Field(..., json_schema_extra={"example": 12})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentListResponse(BaseModel):
    """API response model for listing documents."""
    total: int = Field(..., json_schema_extra={"example": 1})
    documents: List[DocumentMetadata] = Field(default_factory=list)


class UploadDocumentResponse(BaseModel):
    """API response model for document upload endpoint."""
    message: str = Field(..., json_schema_extra={"example": "Document uploaded successfully and queued for processing."})
    document: DocumentMetadata


class SearchRequest(BaseModel):
    """Semantic search request; top_k is bounded by application settings."""
    query: str = Field(..., min_length=1, max_length=10000)
    top_k: Optional[int] = Field(default=None, ge=1)
    document_id: Optional[str] = None
    document_ids: Optional[List[str]] = None


class SearchResult(BaseModel):
    score: float
    document_id: str
    chunk_id: str
    page_numbers: List[int]
    text: str
    token_count: int
    rerank_score: Optional[float] = None
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    document_title: Optional[str] = None
    section_heading: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: List[SearchResult]


class RAGQueryRequest(BaseModel):
    """End-to-End RAG Question Answering Request."""
    query: str = Field(..., min_length=1, max_length=10000, json_schema_extra={"example": "What methodology was used in the study?"})
    document_id: Optional[str] = Field(default=None, json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004"})
    document_ids: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["doc1", "doc2"]})
    conversation_id: Optional[str] = Field(default=None, json_schema_extra={"example": "conv_123"})
    mode: Optional[str] = Field(default="qa", json_schema_extra={"example": "qa"})
    top_k: Optional[int] = Field(default=None, ge=1, json_schema_extra={"example": 5})


class RAGSource(BaseModel):
    """Citation source retrieved from vector database & hybrid search."""
    document_id: str = Field(..., json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004"})
    chunk_id: str = Field(..., json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004_chunk_00000"})
    page_numbers: List[int] = Field(..., json_schema_extra={"example": [1, 2]})
    score: float = Field(..., json_schema_extra={"example": 0.85})
    text: str = Field(..., json_schema_extra={"example": "The study utilized a randomized controlled trial..."})
    rerank_score: Optional[float] = None
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    document_title: Optional[str] = None
    section_heading: Optional[str] = None


class RAGQueryResponse(BaseModel):
    """End-to-End RAG Question Answering Response with Grounded Answer and Sources."""
    query: str = Field(..., json_schema_extra={"example": "What methodology was used in the study?"})
    answer: str = Field(..., json_schema_extra={"example": "The study utilized a randomized controlled trial with 120 participants."})
    sources: List[RAGSource] = Field(default_factory=list)
    document_id: Optional[str] = Field(default=None)
    conversation_id: Optional[str] = Field(default=None)
    mode: Optional[str] = Field(default="qa")
    followup_suggestions: Optional[List[str]] = Field(default_factory=list)


