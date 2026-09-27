"""LLM inference service interface for future implementation (Phase 2+)."""

from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    """Abstract interface for Qwen3 model inference."""

    @abstractmethod
    async def generate_answer(self, prompt: str, context: str) -> str:
        """Generate grounded answer from context prompt using LLM."""
        raise NotImplementedError("LLM inference will be implemented in Phase 2.")
