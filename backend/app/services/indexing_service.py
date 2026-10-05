from pathlib import Path
from typing import Any, Dict, List
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from qdrant_client.http import models

from app.core.config import settings
from app.core.logging import logger
from app.services.qdrant_service import qdrant_service


class IndexingService:
    """Indexes persisted Phase 3 embeddings into Qdrant."""

    def __init__(self, qdrant=None, embedding_dir: Path = None) -> None:
        self.qdrant = qdrant or qdrant_service
        self.embedding_dir = embedding_dir or settings.embedding_dir_path

    def _document_embedding_dir(self, document_id: str) -> Path:
        return self.embedding_dir / document_id

    def _load_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        path = self._document_embedding_dir(document_id) / "chunks.json"

        if not path.exists():
            raise FileNotFoundError(
                f"Chunk file not found for document_id={document_id}"
            )

        import json

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("chunks.json must contain a list of chunks.")

        return data

    def _load_embeddings(self, document_id: str) -> np.ndarray:
        path = self._document_embedding_dir(document_id) / "embeddings.npy"

        if not path.exists():
            raise FileNotFoundError(
                f"Embedding file not found for document_id={document_id}"
            )

        embeddings = np.load(path)

        if embeddings.ndim != 2:
            raise ValueError(
                f"Expected a 2D embedding matrix, got shape={embeddings.shape}"
            )

        return embeddings

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        """
        Convert the deterministic chunk ID into a deterministic UUID.

        Qdrant accepts UUID point IDs. UUID5 guarantees that the same
        chunk_id always maps to the same Qdrant point ID.
        """
        return str(uuid5(NAMESPACE_URL, f"academic-rag:{chunk_id}"))

    def _build_points(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
    ) -> List[models.PointStruct]:
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk count does not match embedding count: "
                f"chunks={len(chunks)}, embeddings={len(embeddings)}"
            )

        if not chunks:
            return []

        actual_dimension = int(embeddings.shape[1])

        points: List[models.PointStruct] = []

        for chunk, vector in zip(chunks, embeddings):
            chunk_id = chunk["chunk_id"]

            if chunk.get("document_id") != document_id:
                raise ValueError(
                    f"Chunk {chunk_id} belongs to document "
                    f"{chunk.get('document_id')}, not {document_id}"
                )

            payload = {
                "document_id": document_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk["chunk_index"],
                "page_numbers": chunk["page_numbers"],
                "text": chunk["text"],
                "token_count": chunk["token_count"],
                "character_count": chunk["character_count"],
            }

            points.append(
                models.PointStruct(
                    id=self._point_id(chunk_id),
                    vector=vector.astype(np.float32).tolist(),
                    payload=payload,
                )
            )

        return points

    def index_document(self, document_id: str) -> Dict[str, Any]:
        """
        Index one document's persisted embeddings into Qdrant.

        The operation is idempotent because point IDs are deterministic.
        Re-running the operation updates the same points rather than
        creating duplicates.
        """
        logger.info(
            f"Starting Qdrant indexing for document_id={document_id}"
        )

        chunks = self._load_chunks(document_id)
        embeddings = self._load_embeddings(document_id)

        actual_dimension = int(embeddings.shape[1])

        self.qdrant.ensure_collection(
            vector_size=actual_dimension,
            collection_name=settings.QDRANT_COLLECTION,
        )

        info = self.qdrant.client.get_collection(settings.QDRANT_COLLECTION)
        collection_vectors = info.config.params.vectors
        expected_dimension = collection_vectors.size if hasattr(collection_vectors, "size") else None
        if expected_dimension != actual_dimension:
            raise ValueError(
                "Embedding dimension does not match Qdrant collection: "
                f"embedding_dimension={actual_dimension}, collection_dimension={expected_dimension}"
            )

        points = self._build_points(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        if not points:
            logger.warning(
                f"No chunks available for document_id={document_id}"
            )

            return {
                "document_id": document_id,
                "indexed": False,
                "point_count": 0,
                "embedding_dimension": actual_dimension,
            }

        self.qdrant.upsert_points(
            points=points,
            batch_size=settings.QDRANT_UPSERT_BATCH_SIZE,
            collection_name=settings.QDRANT_COLLECTION,
        )

        indexed_count = self.qdrant.count_points(
            collection_name=settings.QDRANT_COLLECTION
        )

        logger.info(
            f"Qdrant indexing completed for document_id={document_id}: "
            f"{len(points)} points upserted; "
            f"collection_total={indexed_count}"
        )

        return {
            "document_id": document_id,
            "indexed": True,
            "point_count": len(points),
            "collection_point_count": indexed_count,
            "embedding_dimension": actual_dimension,
        }


indexing_service = IndexingService()
