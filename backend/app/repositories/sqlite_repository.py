from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentMetadata, DocumentStatus
from app.repositories.base import BaseDocumentRepository


class SQLiteDocumentRepository(BaseDocumentRepository):
    """SQLite implementation of Document Metadata Repository."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(settings.sqlite_db_path)
        self._ensure_db_dir()
        self._init_db()


    def _ensure_db_dir(self) -> None:
        """Ensures parent directory for SQLite database exists."""
        db_parent = Path(self.db_path).parent
        if db_parent:
            db_parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes in the SQLite database."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    page_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    processing_started_at TEXT,
                    processing_completed_at TEXT,
                    error_message TEXT
                );
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);"
            )
            conn.commit()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> DocumentMetadata:
        """Converts an SQLite row to a Pydantic DocumentMetadata instance."""
        def parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str:
                return None
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        return DocumentMetadata(
            id=row["id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            file_path=row["file_path"],
            sha256=row["sha256"],
            file_size=row["file_size"],
            page_count=row["page_count"],
            status=DocumentStatus(row["status"]),
            created_at=parse_dt(row["created_at"]),
            updated_at=parse_dt(row["updated_at"]),
            processing_started_at=parse_dt(row["processing_started_at"]),
            processing_completed_at=parse_dt(row["processing_completed_at"]),
            error_message=row["error_message"],
        )

    def save(self, doc: DocumentMetadata) -> DocumentMetadata:
        """Persists a new document metadata record."""
        now_str = datetime.now(timezone.utc).isoformat()
        created_at_str = doc.created_at.isoformat() if doc.created_at else now_str
        updated_at_str = doc.updated_at.isoformat() if doc.updated_at else now_str

        proc_started_str = (
            doc.processing_started_at.isoformat() if doc.processing_started_at else None
        )
        proc_completed_str = (
            doc.processing_completed_at.isoformat()
            if doc.processing_completed_at
            else None
        )

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (
                    id, original_filename, stored_filename, file_path, sha256,
                    file_size, page_count, status, created_at, updated_at,
                    processing_started_at, processing_completed_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.id,
                    doc.original_filename,
                    doc.stored_filename,
                    doc.file_path,
                    doc.sha256,
                    doc.file_size,
                    doc.page_count,
                    doc.status.value,
                    created_at_str,
                    updated_at_str,
                    proc_started_str,
                    proc_completed_str,
                    doc.error_message,
                ),
            )
            conn.commit()

        return self.get_by_id(doc.id) or doc

    def get_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieves document metadata by document_id."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
            return None

    def get_by_sha256(self, sha256_hash: str) -> Optional[DocumentMetadata]:
        """Retrieves document metadata by file SHA-256 hash."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE sha256 = ?", (sha256_hash,))
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
            return None

    def list_all(self) -> List[DocumentMetadata]:
        """Lists all stored document metadata records ordered by created_at DESC."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        page_count: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_started_at: Optional[datetime] = None,
        processing_completed_at: Optional[datetime] = None,
    ) -> Optional[DocumentMetadata]:
        """Updates document status, timestamps, and page count."""
        now = datetime.now(timezone.utc)
        updated_at_str = now.isoformat()

        doc = self.get_by_id(document_id)
        if not doc:
            return None

        new_page_count = page_count if page_count is not None else doc.page_count
        new_started = (
            processing_started_at.isoformat()
            if processing_started_at
            else (doc.processing_started_at.isoformat() if doc.processing_started_at else None)
        )
        new_completed = (
            processing_completed_at.isoformat()
            if processing_completed_at
            else (
                doc.processing_completed_at.isoformat()
                if doc.processing_completed_at
                else None
            )
        )

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE documents
                SET status = ?, page_count = ?, error_message = ?, updated_at = ?,
                    processing_started_at = ?, processing_completed_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    new_page_count,
                    error_message,
                    updated_at_str,
                    new_started,
                    new_completed,
                    document_id,
                ),
            )
            conn.commit()

        return self.get_by_id(document_id)

    def delete(self, document_id: str) -> bool:
        """Deletes a document metadata record by ID."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            return cursor.rowcount > 0
