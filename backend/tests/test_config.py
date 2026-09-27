from app.core.config import Settings


def test_settings_default_values():
    """Tests that default configuration values are properly loaded."""
    settings = Settings()
    assert settings.APP_NAME == "Academic RAG"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.QDRANT_PORT == 6333
    assert settings.CHUNK_SIZE == 800
    assert settings.CHUNK_OVERLAP == 120
    assert settings.TOP_K == 5


def test_cors_origins_parsing():
    """Tests CORS_ORIGINS validator parsing string format into a list."""
    settings_str = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:5173")
    assert isinstance(settings_str.CORS_ORIGINS, list)
    assert len(settings_str.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in settings_str.CORS_ORIGINS
    assert "http://localhost:5173" in settings_str.CORS_ORIGINS
