from datetime import datetime, timezone
import uuid
from app.models.document import DocumentMetadata, DocumentStatus


def test_repository_save_and_get_by_id(test_repository):
    """Tests saving and retrieving a document metadata record by ID."""
    doc_id = str(uuid.uuid4())
    doc = DocumentMetadata(
        id=doc_id,
        original_filename="paper.pdf",
        stored_filename=f"{doc_id}.pdf",
        file_path=f"data/uploads/{doc_id}.pdf",
        sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        file_size=2048,
        status=DocumentStatus.UPLOADED,
    )

    saved = test_repository.save(doc)
    assert saved.id == doc_id
    assert saved.original_filename == "paper.pdf"

    retrieved = test_repository.get_by_id(doc_id)
    assert retrieved is not None
    assert retrieved.id == doc_id
    assert retrieved.sha256 == doc.sha256


def test_repository_get_by_sha256(test_repository):
    """Tests looking up a document by its SHA-256 hash."""
    doc_id = str(uuid.uuid4())
    sha = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    doc = DocumentMetadata(
        id=doc_id,
        original_filename="unique.pdf",
        stored_filename=f"{doc_id}.pdf",
        file_path=f"data/uploads/{doc_id}.pdf",
        sha256=sha,
        file_size=4096,
        status=DocumentStatus.UPLOADED,
    )

    test_repository.save(doc)

    matched = test_repository.get_by_sha256(sha)
    assert matched is not None
    assert matched.id == doc_id

    missing = test_repository.get_by_sha256("nonexistent_sha256_hash")
    assert missing is None


def test_repository_update_status(test_repository):
    """Tests updating document status and page count in SQLite."""
    doc_id = str(uuid.uuid4())
    doc = DocumentMetadata(
        id=doc_id,
        original_filename="status_test.pdf",
        stored_filename=f"{doc_id}.pdf",
        file_path=f"data/uploads/{doc_id}.pdf",
        sha256="9999567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        file_size=1024,
        status=DocumentStatus.UPLOADED,
    )
    test_repository.save(doc)

    now = datetime.now(timezone.utc)
    updated = test_repository.update_status(
        document_id=doc_id,
        status=DocumentStatus.COMPLETED,
        page_count=5,
        processing_completed_at=now,
    )

    assert updated is not None
    assert updated.status == DocumentStatus.COMPLETED
    assert updated.page_count == 5


def test_repository_delete(test_repository):
    """Tests deleting a document metadata record from SQLite."""
    doc_id = str(uuid.uuid4())
    doc = DocumentMetadata(
        id=doc_id,
        original_filename="delete_me.pdf",
        stored_filename=f"{doc_id}.pdf",
        file_path=f"data/uploads/{doc_id}.pdf",
        sha256="8888567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        file_size=512,
        status=DocumentStatus.UPLOADED,
    )
    test_repository.save(doc)

    deleted = test_repository.delete(doc_id)
    assert deleted is True

    assert test_repository.get_by_id(doc_id) is None
