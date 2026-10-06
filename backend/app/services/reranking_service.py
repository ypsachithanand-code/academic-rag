"""Local cross-encoder reranking service with graceful fallback."""

from typing import List, Optional
import torch

from app.core.config import settings
from app.core.logging import logger
from app.models.document import SearchResult


class RerankingService:
    """Service wrapper for CrossEncoder reranking over candidate search results."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        self.model_name = model_name or settings.RERANKER_MODEL
        self.device_setting = device or settings.RERANKER_DEVICE
        self.enabled = enabled if enabled is not None else settings.RERANKER_ENABLED
        self._model = None
        self._device = None

    def _resolve_device(self) -> str:
        if self.device_setting.lower() == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.device_setting

    def _load_model(self):
        """Lazily load SentenceTransformers CrossEncoder model."""
        if self._model is not None or not self.enabled:
            return

        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading local CrossEncoder reranker '{self.model_name}'...")
            self._device = self._resolve_device()
            logger.info(f"Using device '{self._device}' for CrossEncoder reranking.")

            self._model = CrossEncoder(
                self.model_name,
                device=self._device,
            )
            logger.info(f"Successfully loaded reranker model '{self.model_name}'.")

        except Exception as exc:
            logger.warning(
                f"Failed to load reranker model '{self.model_name}': {exc}. "
                "Reranking will be disabled for fallback."
            )
            self._model = None

    def rerank(
        self, query: str, candidates: List[SearchResult], top_k: int = settings.FINAL_TOP_K
    ) -> List[SearchResult]:
        """
        Rerank candidate search results using CrossEncoder.
        
        Falls back cleanly to candidate list order if reranking is disabled or fails.
        """
        if not candidates:
            return []

        if not self.enabled:
            logger.debug("Reranker is disabled in settings. Returning top_k candidates as-is.")
            return candidates[:top_k]

        try:
            self._load_model()
            if self._model is None:
                # Fallback if model loading failed
                return candidates[:top_k]

            # Prepare (query, text) pairs
            pairs = [[query, res.text] for res in candidates]

            # Predict cross-encoder relevance scores
            scores = self._model.predict(pairs)

            # Assign rerank scores and sort candidates by rerank_score
            reranked_results = []
            for res, score_val in zip(candidates, scores):
                res_copy = res.model_copy()
                res_copy.rerank_score = float(score_val)
                reranked_results.append(res_copy)

            reranked_results.sort(key=lambda x: x.rerank_score if x.rerank_score is not None else x.score, reverse=True)
            return reranked_results[:top_k]


        except Exception as exc:
            logger.warning(f"Error during reranking execution: {exc}. Falling back to candidate order.")
            return candidates[:top_k]


reranking_service = RerankingService()
