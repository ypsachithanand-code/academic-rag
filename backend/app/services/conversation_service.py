"""Service for managing research conversation sessions, bounded memory, and follow-up suggestions."""

from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException
from app.models.conversation import Conversation, ConversationMessage, MessageRole, ResearchMode
from app.models.document import RAGSource
from app.repositories.conversation_repository import conversation_repository, SQLiteConversationRepository


class ConversationService:
    """Service wrapper for Conversation session management and memory bounded history."""

    def __init__(self, repo: Optional[SQLiteConversationRepository] = None):
        self.repo = repo or conversation_repository

    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """Creates a new conversation session."""
        return self.repo.create_conversation(title=title)

    def get_conversation(self, conversation_id: str) -> Conversation:
        """Retrieves a conversation session by ID or raises ResourceNotFoundException."""
        conv = self.repo.get_conversation(conversation_id)
        if not conv:
            raise ResourceNotFoundException(resource_name="Conversation", resource_id=conversation_id)
        return conv

    def list_conversations(self) -> List[Conversation]:
        """Lists all conversation sessions ordered by last update."""
        return self.repo.list_conversations()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes a conversation session."""
        self.get_conversation(conversation_id)  # Raises 404 if not found
        return self.repo.delete_conversation(conversation_id)

    def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        sources: Optional[List[RAGSource]] = None,
    ) -> ConversationMessage:
        """Adds and persists a new message in the conversation session."""
        conv = self.get_conversation(conversation_id)
        msg = self.repo.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )

        # Auto-update title on first user message if default
        if role == MessageRole.USER and len(conv.messages) == 0:
            new_title = content[:40].strip() + ("..." if len(content) > 40 else "")
            self.repo.update_title(conversation_id, new_title)

        return msg

    def get_bounded_history(self, conversation_id: str) -> List[ConversationMessage]:
        """
        Retrieves recent conversation messages bounded by MAX_CONVERSATION_MESSAGES settings limit.
        """
        messages = self.repo.get_messages(conversation_id)
        max_msgs = settings.MAX_CONVERSATION_MESSAGES
        if len(messages) > max_msgs:
            return messages[-max_msgs:]
        return messages

    def generate_followup_suggestions(
        self, query: str, mode: Optional[str] = "qa"
    ) -> List[str]:
        """Generate deterministic academic follow-up question suggestions."""
        mode_val = (mode or "qa").lower()
        if mode_val == ResearchMode.METHODOLOGY.value:
            return [
                "What dataset and evaluation metrics were used in the study?",
                "What were the key methodological limitations or assumptions?",
                "How does this methodology compare with baseline models?",
            ]
        elif mode_val == ResearchMode.FINDINGS.value:
            return [
                "What quantitative improvements or metric results were reported?",
                "Were there any unexpected findings or failure cases?",
                "What statistical significance or error bounds were discussed?",
            ]
        elif mode_val == ResearchMode.LIMITATIONS.value:
            return [
                "Did the authors propose any solutions or future work?",
                "How do these limitations impact practical real-world deployment?",
                "Are there threats to external validity or generalization?",
            ]
        elif mode_val == ResearchMode.COMPARE.value:
            return [
                "Which paper demonstrated superior empirical results?",
                "What are the main architectural trade-offs between the papers?",
                "Do the papers share similar experimental evaluation setups?",
            ]
        else:
            return [
                "What methodology did the authors use in the study?",
                "What were the main findings and experimental results?",
                "What stated limitations or future work did the authors propose?",
            ]


conversation_service = ConversationService()
