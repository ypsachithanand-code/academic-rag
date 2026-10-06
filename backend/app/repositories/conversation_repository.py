"""SQLite persistence repository for Conversation sessions and messages."""

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.conversation import Conversation, ConversationMessage, MessageRole
from app.models.document import RAGSource


class SQLiteConversationRepository:
    """SQLite implementation of Conversation Session Repository."""

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
        """Returns a configured SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes for conversations."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON conversation_messages(conversation_id);"
            )
            conn.commit()

    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Creates and persists a new conversation session."""
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        conv_title = title.strip() if (title and title.strip()) else "New Research Conversation"

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (conv_id, conv_title, now_str, now_str),
            )
            conn.commit()

        return Conversation(
            conversation_id=conv_id,
            title=conv_title,
            created_at=now,
            updated_at=now,
            messages=[],
        )

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieves a conversation by ID with its messages."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            if not row:
                return None

            messages = self.get_messages(conversation_id)
            return Conversation(
                conversation_id=row["id"],
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                messages=messages,
            )

    def list_conversations(self) -> List[Conversation]:
        """Lists all conversations ordered by updated_at DESC without message payload overhead."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            conversations = []
            for row in rows:
                conversations.append(
                    Conversation(
                        conversation_id=row["id"],
                        title=row["title"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        messages=[],
                    )
                )
            return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes a conversation and its messages."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        sources: Optional[List[RAGSource]] = None,
    ) -> ConversationMessage:
        """Persists a new message in a conversation session."""
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        sources_list = sources or []
        sources_json = json.dumps([src.model_dump() for src in sources_list])

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_messages (id, conversation_id, role, content, sources_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, conversation_id, role.value, content, sources_json, now_str),
            )
            cursor.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now_str, conversation_id),
            )
            conn.commit()

        return ConversationMessage(
            message_id=msg_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources_list,
            created_at=now,
        )

    def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Retrieves messages for a conversation ordered by created_at ASC."""
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            if limit:
                sql = (
                    "SELECT * FROM (SELECT * FROM conversation_messages "
                    "WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?) "
                    "ORDER BY created_at ASC"
                )
                cursor.execute(sql, (conversation_id, limit))
            else:
                sql = "SELECT * FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC"
                cursor.execute(sql, (conversation_id,))

            rows = cursor.fetchall()
            messages = []
            for row in rows:
                sources_raw = json.loads(row["sources_json"]) if row["sources_json"] else []
                sources = [RAGSource(**s) for s in sources_raw]
                messages.append(
                    ConversationMessage(
                        message_id=row["id"],
                        conversation_id=row["conversation_id"],
                        role=MessageRole(row["role"]),
                        content=row["content"],
                        sources=sources,
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return messages


    def update_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        """Updates the conversation title."""
        now_str = datetime.now(timezone.utc).isoformat()
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now_str, conversation_id),
            )
            conn.commit()
        return self.get_conversation(conversation_id)


conversation_repository = SQLiteConversationRepository()
