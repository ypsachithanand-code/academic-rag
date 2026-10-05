import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from qdrant_client.http import models

from app.models.document import SearchRequest
from app.services.indexing_service import IndexingService
from app.services.retrieval_service import RetrievalService


DOC_ID = "doc-1"


class FakeQdrant:
    def __init__(self, dimension=3):
        self.dimension = dimension
        self.points = {}
        self.batches = []
        self.created = []
        self.client = self

    def ensure_collection(self, vector_size, collection_name=None):
        self.created.append((vector_size, collection_name))
        if self.dimension is None:
            self.dimension = vector_size

    def get_collection(self, collection_name):
        return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(
            vectors=SimpleNamespace(size=self.dimension)
        )))

    def upsert_points(self, points, batch_size, collection_name=None):
        for start in range(0, len(points), batch_size):
            batch = points[start:start + batch_size]
            self.batches.append(batch)
            self.points.update({str(p.id): p for p in batch})

    def count_points(self, collection_name=None):
        return len(self.points)


def create_artifacts(folder: Path, vectors=None):
    folder.mkdir(parents=True)
    chunks = [{
        "chunk_id": f"{DOC_ID}_chunk_{i}", "document_id": DOC_ID,
        "page_numbers": [i + 1], "chunk_index": i,
        "text": f"chunk text {i}", "character_count": 12,
        "token_count": 3,
    } for i in range(2)]
    (folder / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    np.save(folder / "embeddings.npy", np.asarray(vectors if vectors is not None else [[1, 0, 0], [0, 1, 0]], dtype=np.float32))


def test_indexing_creates_collection_payload_batches_and_is_idempotent(tmp_path):
    create_artifacts(tmp_path / DOC_ID)
    qdrant = FakeQdrant(dimension=None)
    service = IndexingService(qdrant=qdrant, embedding_dir=tmp_path)
    result = service.index_document(DOC_ID)
    assert qdrant.created == [(3, "academic_documents")]
    assert result["point_count"] == 2
    assert len(qdrant.batches) == 1
    point = next(iter(qdrant.points.values()))
    assert point.payload == {
        "document_id": DOC_ID, "chunk_id": f"{DOC_ID}_chunk_0",
        "chunk_index": 0, "page_numbers": [1], "text": "chunk text 0",
        "token_count": 3, "character_count": 12,
    }
    assert service._point_id(point.payload["chunk_id"]) == point.id
    service.index_document(DOC_ID)
    assert len(qdrant.points) == 2


def test_indexing_rejects_existing_collection_dimension_mismatch(tmp_path):
    create_artifacts(tmp_path / DOC_ID)
    service = IndexingService(qdrant=FakeQdrant(dimension=4), embedding_dir=tmp_path)
    with pytest.raises(ValueError, match="dimension"):
        service.index_document(DOC_ID)


def test_indexing_rejects_chunk_vector_count_mismatch(tmp_path):
    create_artifacts(tmp_path / DOC_ID, vectors=[[1, 0, 0]])
    service = IndexingService(qdrant=FakeQdrant(), embedding_dir=tmp_path)
    with pytest.raises(ValueError, match="Chunk count"):
        service.index_document(DOC_ID)


def test_indexing_batches_upserts(tmp_path, monkeypatch):
    create_artifacts(tmp_path / DOC_ID)
    qdrant = FakeQdrant()
    service = IndexingService(qdrant=qdrant, embedding_dir=tmp_path)
    monkeypatch.setattr("app.services.indexing_service.settings.QDRANT_UPSERT_BATCH_SIZE", 1)
    service.index_document(DOC_ID)
    assert [len(batch) for batch in qdrant.batches] == [1, 1]


def test_search_embeds_and_filters_document():
    class Embedder:
        def embed_query(self, query):
            assert query == "attention"
            return [0.1, 0.2]

    class Qdrant:
        def search(self, vector, top_k, document_id):
            assert vector == [0.1, 0.2]
            assert top_k == 2
            assert document_id == DOC_ID
            return [SimpleNamespace(id="point", score=0.9, payload={
                "document_id": DOC_ID, "chunk_id": "chunk-a",
                "page_numbers": [2], "text": "Attention is useful.", "token_count": 4,
            })]

    response = RetrievalService(Embedder(), Qdrant()).search(
        SearchRequest(query=" attention ", top_k=2, document_id=DOC_ID)
    )
    assert response.results[0].score == 0.9
    assert response.results[0].page_numbers == [2]
    assert response.results[0].token_count == 4


def test_search_caps_top_k_and_supports_all_documents(monkeypatch):
    class Embedder:
        def embed_query(self, query): return [0.0]
    class Qdrant:
        def search(self, vector, top_k, document_id):
            assert top_k == 20
            assert document_id is None
            return []
    monkeypatch.setattr("app.services.retrieval_service.settings.MAX_TOP_K", 20)
    result = RetrievalService(Embedder(), Qdrant()).search(SearchRequest(query="x", top_k=100))
    assert result.top_k == 20
    assert result.results == []


def test_search_api_returns_results(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.retrieval_service import retrieval_service
    expected = RetrievalService(
        type("Embedder", (), {"embed_query": lambda self, query: [1.0]})(),
        type("Qdrant", (), {"search": lambda self, vector, top_k, document_id: []})(),
    ).search(SearchRequest(query="query", top_k=1))
    monkeypatch.setattr(retrieval_service, "search", lambda request: expected)
    response = TestClient(app).post("/api/v1/search", json={"query": "query", "top_k": 1})
    assert response.status_code == 200
    assert response.json() == {"query": "query", "top_k": 1, "results": []}


def test_qdrant_deletion_uses_document_filter():
    from app.services.qdrant_service import QdrantService

    class Client:
        def delete(self, **kwargs):
            self.kwargs = kwargs
    service = QdrantService()
    service._client = Client()
    service.delete_document_points(DOC_ID)
    selector = service.client.kwargs["points_selector"]
    assert selector.filter.must[0].key == "document_id"
    assert selector.filter.must[0].match.value == DOC_ID


def test_document_deletion_removes_qdrant_points_first(monkeypatch, tmp_path):
    from app.models.document import DocumentMetadata
    from app.services.document_service import DocumentService
    from datetime import datetime, timezone

    doc = DocumentMetadata(
        id=DOC_ID, original_filename="x.pdf", stored_filename="x.pdf",
        file_path=str(tmp_path / "missing.pdf"), sha256="0" * 64, file_size=0,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    class Repository:
        def get_by_id(self, document_id): return doc
        def delete(self, document_id): return True
    class Qdrant:
        def collection_exists(self): return True
        def delete_document_points(self, document_id):
            assert document_id == DOC_ID
            calls.append("vectors")
    calls = []
    monkeypatch.setattr("app.services.document_service.qdrant_service", Qdrant())
    result = DocumentService(repository=Repository()).delete_document(DOC_ID)
    assert result is True
    assert calls == ["vectors"]


def test_real_qdrant_and_bge_m3_index_and_search_existing_artifacts():
    """Exercises the local Qdrant and real configured model; skip only if unavailable."""
    from app.core.config import settings
    from app.services.embedding_service import embedding_service
    from app.services.qdrant_service import qdrant_service

    if not qdrant_service.check_health():
        pytest.skip("Local Qdrant is unavailable")
    document_id = "e3290c21-f102-42da-aadf-3718f2df8004"
    chunk_path = settings.embedding_dir_path / document_id / "chunks.json"
    vectors_path = settings.embedding_dir_path / document_id / "embeddings.npy"
    if not chunk_path.exists() or not vectors_path.exists():
        pytest.skip("Existing Phase 3 embedding artifacts are unavailable")
    service = IndexingService()
    result = service.index_document(document_id)
    chunks = json.loads(chunk_path.read_text(encoding="utf-8"))
    info = qdrant_service.get_collection_info()
    assert result["point_count"] == len(chunks)
    assert info["vector_size"] == int(np.load(vectors_path).shape[1])
    assert qdrant_service.count_points() >= len(chunks)
    from huggingface_hub import try_to_load_from_cache
    cached_files = [try_to_load_from_cache("BAAI/bge-m3", name) for name in
                    ("tokenizer_config.json", "pytorch_model.bin")]
    if not all(isinstance(path, str) for path in cached_files):
        pytest.skip("Real BGE-M3 model files are not available in the local Hugging Face cache")
    try:
        query_vector = embedding_service.embed_query("What is the main contribution of this paper?")
    except Exception as exc:
        pytest.skip(f"Real BGE-M3 model could not be loaded in this environment: {exc}")
    matches = qdrant_service.search(query_vector, top_k=1, document_id=document_id)
    assert matches and matches[0].payload["chunk_id"]
