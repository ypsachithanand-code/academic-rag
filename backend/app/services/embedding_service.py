from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from app.core.config import settings
from app.core.exceptions import EmbeddingException
from app.core.logging import logger


class EmbeddingService:
    """Service for loading BGE-M3 embedding models and generating normalized vector embeddings."""

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL,
        device_setting: str = settings.EMBEDDING_DEVICE,
    ):
        self.model_name = model_name
        self.device_setting = device_setting
        self._model: Optional[SentenceTransformer] = None
        self._device: Optional[str] = None
        self._dimension: Optional[int] = None

    def _determine_device(self) -> str:
        """Determines the optimal available hardware device (CUDA or CPU)."""
        if self.device_setting.lower() == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            logger.warning("CUDA device was requested but is not available. Falling back to CPU.")
            return "cpu"
        elif self.device_setting.lower() == "cpu":
            return "cpu"
        else:
            # Auto mode
            if torch.cuda.is_available():
                return "cuda"
            return "cpu"

    def get_model(self) -> SentenceTransformer:
        """Lazy-loads and caches the SentenceTransformer model singleton.

        Returns:
            SentenceTransformer model instance.

        Raises:
            EmbeddingException: If model loading fails.
        """
        if self._model is not None:
            return self._model

        device = self._determine_device()
        self._device = device

        logger.info(f"Loading embedding model '{self.model_name}' on device '{self._device}'...")

        try:
            model = SentenceTransformer(self.model_name, device=self._device)
            self._dimension = model.get_sentence_embedding_dimension()
            self._model = model
            logger.info(
                f"Successfully loaded embedding model '{self.model_name}' "
                f"[Device: {self._device} | Dimension: {self._dimension}]"
            )
            return self._model
        except Exception as exc:
            logger.error(f"Failed to load embedding model '{self.model_name}': {exc}", exc_info=True)
            raise EmbeddingException(
                message=f"Failed to load embedding model '{self.model_name}'. Ensure local network or cached model exists.",
                details={"model_name": self.model_name, "error": str(exc)},
            )

    def get_embedding_dimension(self) -> int:
        """Returns the embedding vector dimension size (e.g., 1024 for BGE-M3)."""
        if self._dimension is not None:
            return self._dimension
        model = self.get_model()
        return model.get_sentence_embedding_dimension()

    def get_device_name(self) -> str:
        """Returns the active inference device name ('cuda' or 'cpu')."""
        if self._device is not None:
            return self._device
        return self._determine_device()

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ) -> List[List[float]]:
        """Generates L2-normalized dense vector embeddings for a list of input texts.

        Args:
            texts: List of string chunks to embed.
            batch_size: Batch size for model inference.

        Returns:
            List of float list vectors normalized for cosine similarity.

        Raises:
            EmbeddingException: If vector generation fails.
        """
        if not texts:
            return []

        model = self.get_model()

        try:
            logger.info(f"Generating normalized embeddings for {len(texts)} chunks in batches of {batch_size}...")
            # Generate L2-normalized embeddings for cosine similarity
            embeddings_array = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

            # Convert numpy array to Python list of float lists
            if isinstance(embeddings_array, np.ndarray):
                return embeddings_array.tolist()
            return [vec.tolist() for vec in embeddings_array]

        except Exception as exc:
            logger.error(f"Embedding generation failed: {exc}", exc_info=True)
            raise EmbeddingException(
                message="Failed to generate text embeddings.",
                details={"chunk_count": len(texts), "error": str(exc)},
            )

    def embed_query(self, query: str) -> List[float]:
        """Generates a single L2-normalized vector embedding for a search query string.

        Args:
            query: Input user query string.

        Returns:
            List of floats representing the query embedding vector.
        """
        if not query or not query.strip():
            raise EmbeddingException("Query string cannot be empty.")

        model = self.get_model()
        embedding = model.encode(
            query.strip(),
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding.tolist()


embedding_service = EmbeddingService()
