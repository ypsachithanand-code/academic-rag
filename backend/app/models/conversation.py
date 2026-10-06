"""Pydantic data models for Conversation sessions, messages, research modes, and summaries."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.document import RAGSource


class ResearchMode(str, Enum):
    """Research modes for tailoring answer focus and structure."""
    QA = "qa"
    SUMMARY = "summary"
    METHODOLOGY = "methodology"
    FINDINGS = "findings"
    LIMITATIONS = "limitations"
    COMPARE = "compare"


class MessageRole(str, Enum):
    """Role enumeration for conversation messages."""
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    """Data model representing a single message within a conversation session."""
    message_id: str = Field(..., json_schema_extra={"example": "msg_8f7c1e6a_001"})
    conversation_id: str = Field(..., json_schema_extra={"example": "conv_8f7c1e6a_100"})
    role: MessageRole = Field(..., json_schema_extra={"example": MessageRole.USER})
    content: str = Field(..., json_schema_extra={"example": "What methodology was used in the study?"})
    sources: List[RAGSource] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Conversation(BaseModel):
    """Data model representing a full conversation session with history."""
    conversation_id: str = Field(..., json_schema_extra={"example": "conv_8f7c1e6a_100"})
    title: str = Field(..., json_schema_extra={"example": "Transformer Architecture Discussion"})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[ConversationMessage] = Field(default_factory=list)


class CreateConversationRequest(BaseModel):
    """Request model for starting a new conversation session."""
    title: Optional[str] = Field(default=None, json_schema_extra={"example": "Transformer Architecture Discussion"})


class ConversationListResponse(BaseModel):
    """API response model for listing active conversation sessions."""
    total: int = Field(..., json_schema_extra={"example": 1})
    conversations: List[Conversation] = Field(default_factory=list)


class AddMessageRequest(BaseModel):
    """Request model for sending a message in a conversation session."""
    content: str = Field(..., min_length=1, max_length=10000, json_schema_extra={"example": "Why did they choose that methodology?"})
    mode: Optional[ResearchMode] = Field(default=ResearchMode.QA, json_schema_extra={"example": ResearchMode.QA})
    document_id: Optional[str] = Field(default=None, json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004"})
    document_ids: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["doc1", "doc2"]})
    top_k: Optional[int] = Field(default=None, ge=1, json_schema_extra={"example": 5})


class SummaryRequest(BaseModel):
    """Request model for generating a grounded document summary."""
    document_id: str = Field(..., json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004"})
    top_k: Optional[int] = Field(default=10, ge=1, json_schema_extra={"example": 10})


class SummaryResponse(BaseModel):
    """API response model for document-level grounded summary."""
    document_id: str = Field(..., json_schema_extra={"example": "e3290c21-f102-42da-aadf-3718f2df8004"})
    summary: str = Field(..., json_schema_extra={"example": "The paper introduces the Transformer architecture..."})
    sources: List[RAGSource] = Field(default_factory=list)
