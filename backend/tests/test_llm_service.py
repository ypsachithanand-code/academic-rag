"""Unit tests for LocalLLMService with mocked model weights."""

import pytest
from unittest.mock import MagicMock, patch
import torch

from app.core.exceptions import LLMException
from app.services.llm_service import LocalLLMService, SYSTEM_PROMPT


def test_llm_lazy_loading_init():
    """Verify LLM service does not load model or tokenizer during instantiation."""
    service = LocalLLMService(model_name="test-model", device="cpu")
    assert service._model is None
    assert service._tokenizer is None


@pytest.mark.asyncio
async def test_llm_empty_prompt_rejected():
    """Verify empty or whitespace query is rejected with LLMException."""
    service = LocalLLMService()
    with pytest.raises(LLMException, match="Prompt cannot be empty"):
        await service.generate_answer(prompt="   ", context="Some context")


@pytest.mark.asyncio
async def test_llm_model_load_failure_raises_exception():
    """Verify failure during transformers model loading raises LLMException."""
    service = LocalLLMService(model_name="invalid-nonexistent-model")
    with patch("transformers.AutoTokenizer.from_pretrained", side_effect=RuntimeError("Model not found")):
        with pytest.raises(LLMException, match="Failed to load LLM model"):
            await service.generate_answer(prompt="What is X?", context="Context X")


@pytest.mark.asyncio
async def test_llm_successful_generation_mocked():
    """Verify successful generation pipeline with mocked transformers model and tokenizer."""
    service = LocalLLMService(model_name="mock-model", device="cpu")

    mock_tokenizer = MagicMock()
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.apply_chat_template.return_value = "Formatted Chat Prompt"
    
    # Mock tokenizer call returning dictionary with tensors
    dummy_input_ids = torch.tensor([[1, 2, 3, 4]])
    mock_tokenizer.return_value = {"input_ids": dummy_input_ids}

    # Mock output tokens from model generate
    dummy_output_tokens = torch.tensor([[1, 2, 3, 4, 10, 11, 12]])
    mock_model = MagicMock()
    mock_model.generate.return_value = dummy_output_tokens

    mock_tokenizer.decode.return_value = "The study used a randomized trial."

    service._tokenizer = mock_tokenizer
    service._model = mock_model
    service._device = "cpu"

    answer = await service.generate_answer(prompt="What method was used?", context="Randomized trial.")

    assert answer == "The study used a randomized trial."
    mock_model.generate.assert_called_once()
    mock_tokenizer.decode.assert_called_once()
