import hashlib
import json
import os
from pathlib import Path
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import UploadFile
import numpy as np

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    DuplicateDocumentException,
    FileTooLargeException,
    InvalidFileException,
    ResourceNotFoundException,
)
from app.core.logging import logger
from app.models.document import (
    ChunkInspectionResponse,
    DocumentChunk,
    DocumentMetadata,
    DocumentPage,
    DocumentStatus,
    EmbeddingPipelineSummary,
    ProcessedDocumentData,
)
from app.repositories.base import BaseDocumentRepository
from app.repositories.sqlite_repository import SQLiteDocumentRepository
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.pdf_service import pdf_service


class DocumentService:
    """Service layer orchestrating PDF upload, text extraction, chunking, and BGE-M3 embedding storage."""

    def __init__(self, repository: Optional[BaseDocumentRepository] = None):
        self.repository = repository or SQLiteDocumentRepository()
        settings.ensure_directories_exist()

    def upload_document(self, file: UploadFile) -> DocumentMetadata:
        """Validates, stores, and registers a newly uploaded PDF document.

        Args:
            file: FastAPI UploadFile object.

        Returns:
            DocumentMetadata object for the created document.
        """
        if not file.filename:
            raise InvalidFileException("Upload filename must not be empty.")

        original_filename = os.path.basename(file.filename)
        if not original_filename.lower().endswith(".pdf"):
            raise InvalidFileException(f"Unsupported file format '{original_filename}'. Only PDF files (.pdf) are permitted.")

        # Read binary content
        content = file.file.read()
        file_size_bytes = len(content)

        if file_size_bytes == 0:
            raise InvalidFileException("Uploaded file is empty (0 bytes).")

        if file_size_bytes > settings.max_upload_size_bytes:
            file_size_mb = file_size_bytes / (1024 * 1024)
            raise FileTooLargeException(file_size_mb=file_size_mb, max_size_mb=settings.MAX_UPLOAD_SIZE_MB)

        # Validate PDF structure and header
        pdf_service.validate_pdf_bytes(content)

        # Calculate SHA-256 hash for duplicate detection
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Check for duplicates
        existing_doc = self.repository.get_by_sha256(sha256_hash)
        if existing_doc:
            logger.info(f"Duplicate PDF uploaded. Match found with document_id={existing_doc.id}")
            raise DuplicateDocumentException(existing_document_id=existing_doc.id)

        # Generate unique document ID and safe storage path
        doc_id = str(uuid.uuid4())
        stored_filename = f"{doc_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

        # Write uploaded file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Stored uploaded PDF to '{file_path}' (Size: {file_size_bytes} bytes, SHA-256: {sha256_hash[:8]}...)")

        now = datetime.now(timezone.utc)
        metadata = DocumentMetadata(
            id=doc_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            sha256=sha256_hash,
            file_size=file_size_bytes,
            page_count=0,
            status=DocumentStatus.UPLOADED,
            created_at=now,
            updated_at=now,
        )

        saved_metadata = self.repository.save(metadata)
        logger.info(f"Document uploaded and metadata registered: document_id={doc_id}")
        return saved_metadata

    def process_document_for_embeddings(self, document_id: str, force: bool = False) -> DocumentMetadata:
        """Executes document chunking and BGE-M3 embedding generation pipeline.

        Args:
            document_id: Unique string ID of the document.
            force: If True, forces re-chunking and re-embedding generation even if cached.

        Returns:
            Updated DocumentMetadata object.
        """
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)

        embedding_doc_dir = Path(settings.EMBEDDING_DIR) / document_id
        chunks_json_path = embedding_doc_dir / "chunks.json"
        embeddings_npy_path = embedding_doc_dir / "embeddings.npy"
        metadata_json_path = embedding_doc_dir / "metadata.json"

        # Idempotency check: skip if embeddings already exist with identical model & chunk params
        if not force and metadata_json_path.exists() and chunks_json_path.exists() and embeddings_npy_path.exists():
            try:
                with open(metadata_json_path, "r", encoding="utf-8") as f:
                    meta_content = json.load(f)
                if (
                    meta_content.get("embedding_model") == settings.EMBEDDING_MODEL
                    and meta_content.get("chunk_size") == settings.CHUNK_SIZE
                    and meta_content.get("chunk_overlap") == settings.CHUNK_OVERLAP
                ):
                    logger.info(f"Embeddings already exist for document_id={document_id} with matching configuration. Skipping generation.")
                    latest_doc = self.repository.get_by_id(document_id)
                    if latest_doc and latest_doc.status not in (DocumentStatus.COMPLETED, DocumentStatus.NO_TEXT):
                        latest_doc = self.repository.update_status(document_id=document_id, status=DocumentStatus.COMPLETED)
                    return latest_doc or doc
            except Exception:
                pass  # Re-generate if cached metadata read fails

        # Read processed page data
        processed_data = self.get_processed_data(document_id)
        if not processed_data.pages:
            logger.warning(f"Document {document_id} has no pages to chunk/embed.")
            return doc

        # Step 1: Chunking
        logger.info(f"Starting chunking for document_id={document_id}...")
        self.repository.update_status(document_id=document_id, status=DocumentStatus.CHUNKING)

        chunks = chunking_service.chunk_document_pages(
            document_id=document_id,
            pages=processed_data.pages,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        if not chunks:
            logger.warning(f"No chunks produced for document_id={document_id}")
            return doc

        # Step 2: Embedding Generation
        logger.info(f"Starting BGE-M3 embedding generation for document_id={document_id} ({len(chunks)} chunks)...")
        self.repository.update_status(document_id=document_id, status=DocumentStatus.EMBEDDING)

        chunk_texts = [c.text for c in chunks]
        vectors = embedding_service.embed_texts(chunk_texts, batch_size=settings.EMBEDDING_BATCH_SIZE)
        dimension = embedding_service.get_embedding_dimension()

        # Step 3: Persistent Storage
        embedding_doc_dir.mkdir(parents=True, exist_ok=True)

        # Save chunks.json
        chunks_data = [c.model_dump() for c in chunks]
        with open(chunks_json_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # Save embeddings.npy (binary numpy format)
        vectors_np = np.array(vectors, dtype=np.float32)
        np.save(embeddings_npy_path, vectors_np)

        # Save metadata.json
        meta_summary = EmbeddingPipelineSummary(
            document_id=document_id,
            embedding_model=settings.EMBEDDING_MODEL,
            embedding_dimension=dimension,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            chunk_count=len(chunks),
            created_at=datetime.now(timezone.utc),
        )
        with open(metadata_json_path, "w", encoding="utf-8") as f:
            f.write(meta_summary.model_dump_json(indent=2))

        completed_at = datetime.now(timezone.utc)
        updated_doc = self.repository.update_status(
            document_id=document_id,
            status=DocumentStatus.COMPLETED,
            processing_completed_at=completed_at,
        )

        logger.info(f"Successfully chunked and embedded document_id={document_id} ({len(chunks)} chunks, Dim: {dimension})")
        return updated_doc or doc

    def process_document(self, document_id: str) -> DocumentMetadata:
        """Processes an uploaded PDF document: extracts pages, cleans text, chunks, and generates embeddings."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)

        logger.info(f"Document pipeline processing started for document_id={document_id}")
        started_at = datetime.now(timezone.utc)
        self.repository.update_status(
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
            processing_started_at=started_at,
        )

        try:
            if not os.path.exists(doc.file_path):
                raise FileNotFoundError(f"Source PDF file not found at '{doc.file_path}'")

            with open(doc.file_path, "rb") as f:
                file_bytes = f.read()

            pages, total_pages, has_extractable_text = pdf_service.extract_pages(file_bytes)

            processed_dir = Path(settings.PROCESSED_DIR) / document_id
            processed_dir.mkdir(parents=True, exist_ok=True)
            pages_json_path = processed_dir / "pages.json"

            processed_data = ProcessedDocumentData(
                document_id=document_id,
                total_pages=total_pages,
                pages=pages,
            )

            with open(pages_json_path, "w", encoding="utf-8") as f:
                f.write(processed_data.model_dump_json(indent=2))

            completed_at = datetime.now(timezone.utc)

            if not has_extractable_text:
                no_text_msg = "No extractable text was found in this PDF. OCR processing is not enabled yet."
                logger.warning(f"Document {document_id} marked as NO_TEXT: {no_text_msg}")
                updated_doc = self.repository.update_status(
                    document_id=document_id,
                    status=DocumentStatus.NO_TEXT,
                    page_count=total_pages,
                    error_message=no_text_msg,
                    processing_completed_at=completed_at,
                )
                return updated_doc or doc

            self.repository.update_status(document_id=document_id, status=DocumentStatus.PROCESSING, page_count=total_pages)

            # Trigger Phase 3 Chunking & Embedding Pipeline
            return self.process_document_for_embeddings(document_id)

        except Exception as exc:
            logger.error(f"Document processing failed for document_id={document_id}: {exc}", exc_info=True)
            completed_at = datetime.now(timezone.utc)
            updated_doc = self.repository.update_status(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error_message=f"Processing failed: {str(exc)}",
                processing_completed_at=completed_at,
            )
            return updated_doc or doc

    def get_document(self, document_id: str) -> DocumentMetadata:
        """Retrieves document metadata by ID."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)
        return doc

    def get_processed_data(self, document_id: str) -> ProcessedDocumentData:
        """Retrieves structured page data for a processed document."""
        self.get_document(document_id)  # Ensures document exists
        pages_json_path = Path(settings.PROCESSED_DIR) / document_id / "pages.json"

        if not pages_json_path.exists():
            raise ResourceNotFoundException("Processed Page Data", document_id)

        try:
            with open(pages_json_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            return ProcessedDocumentData.model_validate(content)
        except Exception as exc:
            logger.error(f"Failed to read processed data for document_id={document_id}: {exc}")
            raise ResourceNotFoundException("Processed Page Data", document_id)

    def get_document_chunks(self, document_id: str) -> ChunkInspectionResponse:
        """Retrieves inspection chunk list and model metadata for a document."""
        self.get_document(document_id)  # Ensures document exists
        embedding_dir = Path(settings.EMBEDDING_DIR) / document_id
        chunks_json_path = embedding_dir / "chunks.json"
        metadata_json_path = embedding_dir / "metadata.json"

        if not chunks_json_path.exists():
            raise ResourceNotFoundException("Document Chunks", document_id)

        try:
            with open(chunks_json_path, "r", encoding="utf-8") as f:
                chunks_raw = json.load(f)
            chunks = [DocumentChunk.model_validate(c) for c in chunks_raw]

            model_name = settings.EMBEDDING_MODEL
            dimension = 1024
            if metadata_json_path.exists():
                with open(metadata_json_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    model_name = meta.get("embedding_model", model_name)
                    dimension = meta.get("embedding_dimension", dimension)

            return ChunkInspectionResponse(
                document_id=document_id,
                total_chunks=len(chunks),
                embedding_model=model_name,
                embedding_dimension=dimension,
                chunks=chunks,
            )
        except Exception as exc:
            logger.error(f"Failed to read chunks for document_id={document_id}: {exc}")
            raise ResourceNotFoundException("Document Chunks", document_id)

    def list_documents(self) -> List[DocumentMetadata]:
        """Lists all registered document metadata records."""
        return self.repository.list_all()

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document, removing metadata, uploads, processed pages, and embedding files."""
        doc = self.repository.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundException(document_id)

        # Delete upload file
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
                logger.info(f"Removed upload file: {doc.file_path}")
            except Exception as exc:
                logger.warning(f"Failed to delete upload file '{doc.file_path}': {exc}")

        # Delete processed directory
        processed_dir = Path(settings.PROCESSED_DIR) / document_id
        if processed_dir.exists():
            try:
                pages_json = processed_dir / "pages.json"
                if pages_json.exists():
                    os.remove(pages_json)
                processed_dir.rmdir()
                logger.info(f"Removed processed data dir: {processed_dir}")
            except Exception as exc:
                logger.warning(f"Failed to delete processed dir '{processed_dir}': {exc}")

        # Delete embedding directory
        embedding_dir = Path(settings.EMBEDDING_DIR) / document_id
        if embedding_dir.exists():
            try:
                for file_name in ["chunks.json", "embeddings.npy", "metadata.json"]:
                    fpath = embedding_dir / file_name
                    if fpath.exists():
                        os.remove(fpath)
                embedding_dir.rmdir()
                logger.info(f"Removed embedding dir: {embedding_dir}")
            except Exception as exc:
                logger.warning(f"Failed to delete embedding dir '{embedding_dir}': {exc}")

        # Delete metadata record
        deleted = self.repository.delete(document_id)
        logger.info(f"Deleted metadata record for document_id={document_id}")
        return deleted

    def retry_processing(self, document_id: str) -> DocumentMetadata:
        """Re-triggers full document processing pipeline."""
        doc = self.get_document(document_id)
        if not os.path.exists(doc.file_path):
            raise InvalidFileException(f"Cannot retry: PDF source file missing at '{doc.file_path}'.")

        self.repository.update_status(
            document_id=document_id,
            status=DocumentStatus.UPLOADED,
            error_message=None,
        )
        return self.process_document(document_id)


document_service = DocumentService()
