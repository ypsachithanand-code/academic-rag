# Academic RAG — Phase 3: Document Chunking & BGE-M3 Embedding Pipeline

## Overview
Academic RAG is a production-grade Retrieval-Augmented Generation application tailored for processing, indexing, and querying academic literature with verified citations.

**Current Status**:
- **Phase 1**: Infrastructure and Backend Foundation (Complete)
- **Phase 2**: PDF Ingestion, Validation, Text Extraction, Cleaning, and Page Preservation (Complete)
- **Phase 3**: Paragraph-Aware Document Chunking & Local BGE-M3 Vector Embedding Pipeline (Complete)

---

## Architecture Pipeline

```text
Processed PDF Pages (Phase 2)
        ↓
Paragraph/Section/Sentence-Aware Chunking (Phase 3)
        ↓
Chunk Metadata (chunk_id, document_id, page_numbers, chunk_index, token_count)
        ↓
BGE-M3 Local Embedding Model (BAAI/bge-m3, 1024-dim, L2-Normalized)
        ↓
Persistent Local Storage (data/embeddings/<document_id>/chunks.json & embeddings.npy)
```

*(Note: Qdrant Vector Collection Indexing, Semantic Search, and LLM RAG Inference will be implemented in subsequent phases.)*

---

## Technical Stack (Phase 3)
- **Language**: Python 3.11+
- **API Framework**: FastAPI & Uvicorn
- **PDF Processing**: PyMuPDF (`pymupdf`)
- **Metadata Database**: SQLite (`sqlite3`) with Repository pattern
- **Local Embedding Engine**: `sentence-transformers`, `torch`
- **Embedding Model**: `BAAI/bge-m3` (1024-dimensional dense vectors)
- **Vector Storage**: Compact binary NumPy format (`embeddings.npy`) + JSON metadata
- **Testing**: `pytest`, `httpx`

---

## Configuration (`.env`)

```env
# Phase 2 — Document Storage Settings
UPLOAD_DIR=data/uploads
PROCESSED_DIR=data/processed
SQLITE_DB_PATH=data/academic_rag.db
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=["application/pdf"]

# Phase 3 — Document Chunking & BGE-M3 Embedding Settings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=auto
EMBEDDING_BATCH_SIZE=8
EMBEDDING_DIR=data/embeddings
CHUNK_SIZE=800
CHUNK_OVERLAP=120
```

---

## Document REST API Endpoints

### 1. Upload & Auto-Process PDF Document
```powershell
curl -X POST "http://localhost:8000/api/v1/documents/upload" `
  -F "file=@C:\path\to\academic_paper.pdf"
```
*(Automatically triggers extraction -> paragraph-aware chunking -> BGE-M3 vector generation)*

### 2. Inspect Generated Document Chunks & Metadata
```powershell
curl "http://localhost:8000/api/v1/documents/8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a/chunks"
```
**Response (200 OK)**:
```json
{
  "document_id": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a",
  "total_chunks": 12,
  "embedding_model": "BAAI/bge-m3",
  "embedding_dimension": 1024,
  "chunks": [
    {
      "chunk_id": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a_chunk_00000",
      "document_id": "8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a",
      "page_numbers": [1, 2],
      "chunk_index": 0,
      "text": "Attention Is All You Need. Abstract...",
      "character_count": 780,
      "token_count": 165
    }
  ]
}
```

### 3. Trigger / Force Re-Processing for Embeddings
```powershell
curl -X POST "http://localhost:8000/api/v1/documents/8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a/process?force=true"
```

### 4. Delete Document & All Stored Artifacts
```powershell
curl -X DELETE "http://localhost:8000/api/v1/documents/8f7c1e6a-9b2c-4d5e-8f1a-2b3c4d5e6f7a"
```
*(Deletes uploaded PDF, extracted page JSON, and chunk vector files)*

---

## Running Test Suite

Run full test suite (Phase 1, Phase 2, & Phase 3):
```powershell
cd backend
python -m pytest
```

---

## Manual Verification Steps

1. Activate virtual environment and start Qdrant & FastAPI:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   docker compose up -d
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
2. Upload an academic PDF document using `POST /api/v1/documents/upload`.
3. Observe background logs: PDF text extraction -> paragraph chunking -> BGE-M3 model loading -> normalized 1024-dim vector generation.
4. Verify persisted artifacts on disk under `data/embeddings/<document_id>/`:
   - `chunks.json` (List of chunks with page numbers)
   - `embeddings.npy` (Binary NumPy matrix shape `(chunk_count, 1024)`)
   - `metadata.json` (Model summary: `BAAI/bge-m3`, dimension `1024`, chunk count)
5. Call `GET /api/v1/documents/{document_id}/chunks` to inspect chunk token counts and page numbers.
6. Re-send upload/process request for the same document to verify idempotent skip (avoiding duplicate model inference).
7. Restart the backend server and verify that `GET /api/v1/documents/{document_id}/chunks` retrieves persisted chunks cleanly.

---

## Explicit Scope Limitations (Not Implemented Yet)
- **Qdrant Vector Indexing**: Upserting embedding vectors into Qdrant collection is not implemented yet.
- **Semantic Search**: Vector similarity search and retrieval are not implemented yet.
- **LLM / RAG**: Qwen model inference and citation generation are not implemented yet.
