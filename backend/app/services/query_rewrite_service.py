"""Query Transformation Service for multi-turn academic conversation rewriting."""

import re
from typing import List

from app.core.logging import logger
from app.models.conversation import ConversationMessage, MessageRole


class QueryRewriteService:
    """Service to transform conversational follow-up questions into standalone retrieval queries."""

    def rewrite_to_standalone_query(
        self, current_query: str, history: List[ConversationMessage]
    ) -> str:
        """
        Rewrite conversational follow-up questions using prior turn context into a standalone retrieval query.
        
        Returns current_query unchanged if it is already standalone or if history is empty.
        """
        query_text = current_query.strip()
        if not query_text or not history:
            return query_text

        # Anaphoric / pronoun triggers indicating follow-up dependency
        followup_triggers = [
            r"\bit\b", r"\bthey\b", r"\bthem\b", r"\bthat\b", r"\bthis\b", r"\bthese\b",
            r"\bthose\b", r"\bthe authors?\b", r"\bthe study\b", r"\bthe paper\b",
            r"\btheir\b", r"\bits\b", r"\bsuch\b"
        ]

        is_followup = any(re.search(pattern, query_text, re.IGNORECASE) for pattern in followup_triggers)
        if not is_followup:
            return query_text

        # Extract recent user questions and assistant answers to identify focus topics
        recent_user_qs = [msg.content for msg in history if msg.role == MessageRole.USER]
        if not recent_user_qs:
            return query_text

        last_user_q = recent_user_qs[-1].strip()

        # Extract key technical nouns from the last question
        # Remove common question words from previous query
        clean_prev = re.sub(r"^(what|why|how|where|when|which|who|is|are|did|do|does)\s+(is|are|was|were|the|a|an)?\s*", "", last_user_q, flags=re.IGNORECASE)
        clean_prev = clean_prev.rstrip("?")

        # Construct a standalone contextual query
        standalone_query = f"{query_text} (Context: regarding {clean_prev})"
        logger.info(f"Transformed follow-up query '{query_text}' -> Standalone query '{standalone_query}'")
        return standalone_query


query_rewrite_service = QueryRewriteService()
