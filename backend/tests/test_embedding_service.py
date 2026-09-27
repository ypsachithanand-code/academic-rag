from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from app.services.embedding_service import EmbeddingService, embedding_service


def test_embedding_service_device_determination():
    """Tests device selection logic (CPU vs CUDA)."""
    service = EmbeddingService(device_setting="cpu")
    assert service._determine_device() == "cpu"


@patch("app.services.embedding_service.SentenceTransformer")
def test_embed_texts_mocked(mock_transformer):
    """Tests batch embedding generation with mocked model."""
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 1024
    # Mock encode returning normalized numpy vectors
    dummy_vecs = np.random.rand(2, 1024).astype(np.float32)
    mock_model.encode.return_value = dummy_vecs
    mock_transformer.return_value = mock_model

    service = EmbeddingService(model_name="BAAI/bge-m3", device_setting="cpu")
    texts = ["Sample academic chunk 1", "Sample academic chunk 2"]

    vectors = service.embed_texts(texts, batch_size=2)
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024
    assert service.get_embedding_dimension() == 1024


@patch("app.services.embedding_service.SentenceTransformer")
def test_embed_query_mocked(mock_transformer):
    """Tests query embedding generation with mocked model."""
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 1024
    dummy_vec = np.random.rand(1024).astype(np.float32)
    mock_model.encode.return_value = dummy_vec
    mock_transformer.return_value = mock_model

    service = EmbeddingService(model_name="BAAI/bge-m3", device_setting="cpu")
    query_vector = service.embed_query("What is self-attention?")

    assert len(query_vector) == 1024


@pytest.mark.integration
def test_real_bge_m3_model_loading_and_embedding():
    """Integration Test: Loads actual BAAI/bge-m3 model locally and generates normalized embeddings."""
    dim = embedding_service.get_embedding_dimension()
    assert dim == 1024

    texts = ["Attention Is All You Need.", "Transformer models use multi-head self-attention."]
    vectors = embedding_service.embed_texts(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) == 1024

    # Verify query embedding matches dimension
    q_vector = embedding_service.embed_query("How does attention work?")
    assert len(q_vector) == 1024
