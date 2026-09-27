import os
from pathlib import Path
import tempfile
import pymupdf  # PyMuPDF
import pytest
from fastapi.testclient import TestClient


from app.core.config import settings
from app.main import app
from app.repositories.sqlite_repository import SQLiteDocumentRepository
from app.services.document_service import DocumentService


@pytest.fixture
def temp_dir():
    """Provides a temporary directory for test storage."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield tmpdir



@pytest.fixture
def test_db_path(temp_dir):
    """Provides a temporary SQLite database path."""
    return str(Path(temp_dir) / "test_academic_rag.db")


@pytest.fixture
def test_repository(test_db_path):
    """Provides an isolated SQLite repository instance for testing."""
    return SQLiteDocumentRepository(db_path=test_db_path)


@pytest.fixture
def test_doc_service(temp_dir, test_repository, monkeypatch):
    """Provides an isolated DocumentService instance with overridden storage paths."""
    upload_dir = str(Path(temp_dir) / "uploads")
    processed_dir = str(Path(temp_dir) / "processed")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    Path(processed_dir).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(settings, "PROCESSED_DIR", processed_dir)

    service = DocumentService(repository=test_repository)
    return service


@pytest.fixture
def client(temp_dir, test_db_path, monkeypatch):
    """Pytest fixture providing a TestClient instance with isolated database and storage."""
    upload_dir = str(Path(temp_dir) / "api_uploads")
    processed_dir = str(Path(temp_dir) / "api_processed")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    Path(processed_dir).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "SQLITE_DB_PATH", test_db_path)
    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(settings, "PROCESSED_DIR", processed_dir)

    # Re-initialize singleton service to use overridden paths/repository
    from app.services.document_service import document_service
    document_service.repository = SQLiteDocumentRepository(db_path=test_db_path)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generates a valid 2-page PDF document in memory using PyMuPDF."""
    doc = pymupdf.open()

    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "Attention Is All You Need\nAbstract\nWe propose the Transformer, a novel neural network architecture based solely on attention mechanisms.\nThis docu-\nment demonstrates superior performance on translation tasks.",
    )

    page2 = doc.new_page()
    page2.insert_text(
        (50, 50),
        "Section 1. Introduction\nRecurrent neural networks have been established as state of the art.\nEquation: E = mc^2.",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def no_text_pdf_bytes() -> bytes:
    """Generates a 1-page PDF document containing no extractable text (blank page)."""
    doc = pymupdf.open()
    doc.new_page()  # Empty blank page
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
