# Academic RAG — Phase 7: Premium Academic Research Assistant Integration

## Overview
Academic RAG is a production-grade Retrieval-Augmented Generation application tailored for processing, indexing, and querying academic literature with grounded answers, multi-turn research conversations, research modes, multi-document retrieval, source inspection, and verified citations.

**Current Status**:
- **Phase 1**: Infrastructure, Backend Foundation, logging, and error handling (Complete ✅)
- **Phase 2**: PDF Ingestion, Validation, Text Extraction, Cleaning, and Page Preservation (Complete ✅)
- **Phase 3**: Paragraph-Aware Document Chunking & Local BGE-M3 Vector Embedding Pipeline (Complete ✅)
- **Phase 4**: Qdrant Vector Database Integration & Semantic Retrieval Pipeline (Complete ✅)
- **Phase 5**: End-to-End RAG Answer Generation with Free Local LLM & Source Citations (Complete ✅)
- **Phase 6**: Hybrid Retrieval (BGE-M3 + BM25), Reciprocal Rank Fusion (RRF), and CrossEncoder Reranking (Complete ✅)
- **Phase 7**: Research Assistant Integration (Conversations, Query Rewriting, Research Modes, Multi-Doc Filtering, Source Inspection, Streaming) (Complete ✅)

---

## Complete Architecture Pipeline

```text
                     ┌────────────────────┐
                     │    User Question   │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │ Conversation       │
                     │ History            │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │ Query Rewriting    │
                     └─────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
        Dense Retrieval                  BM25 Retrieval
          BGE-M3                           Lexical
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
                         RRF Fusion
                               │
                               ▼
                       CrossEncoder
                         Reranking
                               │
                               ▼
                    Grounded Context
                               │
                               ▼
                    Research Mode Prompt
                               │
                               ▼
                     Qwen2.5-7B Instruct
                               │
                               ▼
                  Citation-Rich Answer
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
        Follow-up Suggestions          Conversation Storage
```

---

## Technical Stack
- **Language**: Python 3.11+ / 3.14
- **API Framework**: FastAPI & Uvicorn
- **PDF Processing**: PyMuPDF (`pymupdf`)
- **Metadata & Session Storage**: SQLite (`sqlite3`) with Repository pattern & `PRAGMA foreign_keys = ON;`
- **Embedding Model**: `BAAI/bge-m3` (1024-dimensional dense vectors)
- **Vector Database**: Qdrant (running via Docker Desktop / local server)
- **Lexical Search**: Okapi BM25 (`BM25Scorer`)
- **Candidate Fusion**: Reciprocal Rank Fusion (`RRF`)
- **Reranker**: `BAAI/bge-reranker-large` / CrossEncoder
- **Local Free LLM**: `Qwen/Qwen2.5-7B-Instruct` (HF Transformers)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`

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

# Phase 4 — Qdrant Vector Database & Search Settings
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=academic_documents
QDRANT_TIMEOUT=5.0
QDRANT_UPSERT_BATCH_SIZE=64
TOP_K=5
MAX_TOP_K=20

# Phase 5 — Local LLM RAG Settings
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_DEVICE=auto
LLM_MAX_NEW_TOKENS=512
LLM_TEMPERATURE=0.2

# Phase 6 — Hybrid Search & Reranking Settings
HYBRID_RETRIEVAL_ENABLED=true
LEXICAL_TOP_K=20
RRF_K=60
RERANKER_ENABLED=true
RERANKER_MODEL=BAAI/bge-reranker-large
RERANKER_TOP_N=20
FINAL_TOP_K=5

# Phase 7 — Research Assistant & Conversation Settings
MAX_CONVERSATION_MESSAGES=10
MAX_CONVERSATION_TOKENS=2048
DEFAULT_RESEARCH_MODE=qa
```

---

## Core Research Modes
- `qa`: Direct question answering with grounded evidence and citations.
- `summary`: Structural summary covering Research Objective, Approach, Main Findings, Conclusions, and Limitations.
- `methodology`: Detailed extraction of research design, dataset/sample, preprocessing, algorithms, and evaluation setups.
- `findings`: Focus on primary/secondary empirical findings, distinguishing explicit findings from interpretations.
- `limitations`: Explicitly stated and inferred scope/methodological/dataset limitations.
- `compare`: Comparative analysis across multiple selected documents focusing on similarities, differences, and trade-offs.

---

## Core REST API Endpoints

### 1. Upload & Auto-Index Academic PDF
```powershell
curl -X POST "http://localhost:8000/api/v1/documents/upload" `
  -F "file=@C:\path\to\academic_paper.pdf"
```

### 2. Multi-Turn Research Conversations
```powershell
# Create Conversation
curl -X POST "http://localhost:8000/api/v1/conversations" `
  -H "Content-Type: application/json" `
  -d '{"title": "Transformer Attention Research"}'

# List Conversations
curl -X GET "http://localhost:8000/api/v1/conversations"

# Ask Question in Conversation
curl -X POST "http://localhost:8000/api/v1/conversations/conv_12345/messages" `
  -H "Content-Type: application/json" `
  -d '{
    "content": "Why did they choose this dataset?",
    "mode": "qa"
  }'
```

### 3. Multi-Document Research & Compare Mode
```powershell
curl -X POST "http://localhost:8000/api/v1/rag/query" `
  -H "Content-Type: application/json" `
  -d '{
    "query": "Compare the methodologies used in these two papers.",
    "document_ids": ["doc1", "doc2"],
    "mode": "compare"
  }'
```

### 4. Source & Chunk Inspection
```powershell
curl -X GET "http://localhost:8000/api/v1/documents/doc1/chunks/doc1_chunk_00000"
```

### 5. Grounded Document Summary
```powershell
curl -X POST "http://localhost:8000/api/v1/documents/doc1/summary"
```

### 6. Streaming RAG Generation
```powershell
curl -X POST "http://localhost:8000/api/v1/rag/query/stream" `
  -H "Content-Type: application/json" `
  -d '{"query": "Explain the attention mechanism."}'
```

---

## Running Test Suite

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest --basetemp=.\pytest_tmp -m "not integration" -v
```
