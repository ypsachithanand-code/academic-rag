from pathlib import Path
from typing import List, Optional, Union
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory: c:\projects\academic rag\backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Centralized Application Configuration.
    
    Loads configuration from environment variables or .env files.
    Includes Phase 2 storage, Phase 3 embeddings, and Phase 4 Qdrant vector search configuration.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core Application Settings
    APP_NAME: str = "Academic RAG"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Server Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # Phase 2 — Document Ingestion & Storage Settings
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    SQLITE_DB_PATH: str = "data/academic_rag.db"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: Union[List[str], str] = ["application/pdf"]

    # Phase 3 — Document Chunking & Embedding Settings
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "auto"
    EMBEDDING_BATCH_SIZE: int = 8
    EMBEDDING_DIR: str = "data/embeddings"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Phase 4 — Qdrant Vector Database & Search Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "academic_documents"
    QDRANT_TIMEOUT: float = 5.0
    QDRANT_UPSERT_BATCH_SIZE: int = 64
    TOP_K: int = 5
    MAX_TOP_K: int = 20

    # Phase 5 — Local LLM RAG Settings
    LLM_MODEL: str = "Qwen/Qwen2.5-3B-Instruct"
    LLM_DEVICE: str = "auto"
    LLM_MAX_NEW_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.2

    # Phase 6 — Hybrid Retrieval & Reranking Settings
    HYBRID_RETRIEVAL_ENABLED: bool = True
    DENSE_TOP_K: int = 10
    LEXICAL_TOP_K: int = 10
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_DEVICE: str = "auto"
    RERANKER_TOP_N: int = 20
    FINAL_TOP_K: int = 5
    RRF_K: float = 60.0

    # Phase 7 — Research Assistant & Conversation Settings
    MAX_CONVERSATION_MESSAGES: int = 10
    MAX_CONVERSATION_TOKENS: int = 2048
    DEFAULT_RESEARCH_MODE: str = "qa"





    def get_absolute_path(self, relative_or_abs_path: str) -> Path:
        """Resolves a file/directory path against the backend BASE_DIR if it is relative."""
        p = Path(relative_or_abs_path)
        if p.is_absolute():
            return p
        return BASE_DIR / p

    @property
    def upload_dir_path(self) -> Path:
        return self.get_absolute_path(self.UPLOAD_DIR)

    @property
    def processed_dir_path(self) -> Path:
        return self.get_absolute_path(self.PROCESSED_DIR)

    @property
    def sqlite_db_path(self) -> Path:
        return self.get_absolute_path(self.SQLITE_DB_PATH)

    @property
    def embedding_dir_path(self) -> Path:
        return self.get_absolute_path(self.EMBEDDING_DIR)

    @property
    def max_upload_size_bytes(self) -> int:
        """Returns the maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Ensures CORS_ORIGINS is always returned as a list of origin strings."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, value: Union[str, List[str]]) -> List[str]:
        """Ensures ALLOWED_FILE_TYPES is always returned as a list of MIME strings."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            return [file_type.strip() for file_type in value.split(",") if file_type.strip()]
        return value

    def ensure_directories_exist(self) -> None:
        """Ensures that required data storage directories exist on disk."""
        self.upload_dir_path.mkdir(parents=True, exist_ok=True)
        self.processed_dir_path.mkdir(parents=True, exist_ok=True)
        self.embedding_dir_path.mkdir(parents=True, exist_ok=True)
        db_parent = self.sqlite_db_path.parent
        if db_parent:
            db_parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
