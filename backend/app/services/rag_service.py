"""Full RAG orchestrator service implementing end-to-end Academic RAG pipeline with hybrid search & reranking."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List

from app.core.config import settings
from app.core.exceptions import RAGException, BaseAppException
from app.core.logging import logger
from app.models.conversation import MessageRole
from app.models.document import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGSource,
    SearchRequest,
    SearchResponse,
)
from app.services.retrieval_service import retrieval_service, RetrievalService
from app.services.llm_service import llm_service, BaseLLMService
from app.services.conversation_service import conversation_service, ConversationService
from app.services.query_rewrite_service import query_rewrite_service, QueryRewriteService
from app.services.document_service import document_service, DocumentService


class BaseRAGService(ABC):
    """Abstract interface for end-to-end Academic RAG pipeline execution."""

    @abstractmethod
    async def query_academic_rag(
        self,
        request: RAGQueryRequest
    ) -> RAGQueryResponse:
        """Execute query pipeline: search -> retrieve context -> LLM inference -> citations."""
        raise NotImplementedError


class RAGService(BaseRAGService):
    """Concrete RAG service orchestrating hybrid retrieval, context formatting, LLM generation, and citations."""

    def __init__(
        self,
        retriever: Optional[RetrievalService] = None,
        llm: Optional[BaseLLMService] = None,
        conv_service: Optional[ConversationService] = None,
        rewrite_service: Optional[QueryRewriteService] = None,
        doc_service: Optional[DocumentService] = None,
    ):
        self.retriever = retriever or retrieval_service
        self.llm = llm or llm_service
        self.conversation_service = conv_service or conversation_service
        self.query_rewrite_service = rewrite_service or query_rewrite_service
        self.document_service = doc_service or document_service

    def build_context(self, search_results: List) -> str:
        """
        Format retrieved search chunks into structured context text for LLM prompt.
        
        Includes chunk deduplication, page numbers, document identity, section headings, and scores.
        """
        context_parts = []
        seen_chunks = set()

        idx = 1
        for result in search_results:
            cid = getattr(result, "chunk_id", None)
            if cid and cid in seen_chunks:
                continue
            if cid:
                seen_chunks.add(cid)

            pages_str = (
                ", ".join(str(p) for p in result.page_numbers)
                if getattr(result, "page_numbers", None)
                else "N/A"
            )
            doc_str = getattr(result, "document_title", None) or getattr(result, "document_id", "Unknown Document")
            heading_str = getattr(result, "section_heading", None)

            header_lines = [
                f"[Source {idx}]",
                f"Document: {doc_str}",
                f"Pages: {pages_str}",
            ]
            if heading_str:
                header_lines.append(f"Section: {heading_str}")

            score_val = getattr(result, "rerank_score", None)
            if score_val is None:
                score_val = getattr(result, "score", 0.0)
            header_lines.append(f"Relevance Score: {score_val:.3f}")
            header_lines.append(f"Content:\n{result.text.strip()}\n")

            context_parts.append("\n".join(header_lines))
            idx += 1

        return "\n".join(context_parts)

    async def query_academic_rag(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """Execute complete RAG workflow: validate -> conversation & rewriting -> hybrid search + rerank -> context -> LLM -> citations -> persistence."""
        query = request.query.strip()
        if not query:
            raise RAGException("Query string cannot be empty.")

        # 1. Document validation
        effective_document_id = request.document_id
        effective_document_ids = request.document_ids

        if effective_document_ids:
            for doc_id in effective_document_ids:
                self.document_service.get_document(doc_id)
        elif effective_document_id:
            self.document_service.get_document(effective_document_id)

        # 2. Conversation handling & query rewriting
        conversation_id = request.conversation_id
        history = []
        retrieval_query = query

        if conversation_id:
            # Ensure conversation exists (raises 404 if not found)
            self.conversation_service.get_conversation(conversation_id)
            history = self.conversation_service.get_bounded_history(conversation_id)
            if history:
                retrieval_query = self.query_rewrite_service.rewrite_to_standalone_query(query, history)
            
            # Save user's original query
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=query,
            )

        try:
            top_k = request.top_k or settings.FINAL_TOP_K
            search_req = SearchRequest(
                query=retrieval_query,
                top_k=top_k,
                document_id=effective_document_id,
                document_ids=effective_document_ids,
            )
            search_res: SearchResponse = self.retriever.search(search_req)

            mode = request.mode or settings.DEFAULT_RESEARCH_MODE
            followup_suggestions = self.conversation_service.generate_followup_suggestions(query, mode=mode)

            if not search_res.results:
                logger.info(f"No relevant documents found for query: '{query}'")
                no_info_ans = "No relevant information was found in the uploaded academic documents for your query. The provided academic documents do not contain enough information to answer this question."
                
                if conversation_id:
                    self.conversation_service.add_message(
                        conversation_id=conversation_id,
                        role=MessageRole.ASSISTANT,
                        content=no_info_ans,
                        sources=[],
                    )

                return RAGQueryResponse(
                    query=query,
                    answer=no_info_ans,
                    sources=[],
                    document_id=effective_document_id,
                    conversation_id=conversation_id,
                    mode=mode,
                    followup_suggestions=followup_suggestions,
                )

            sources = [
                RAGSource(
                    document_id=res.document_id,
                    chunk_id=res.chunk_id,
                    page_numbers=res.page_numbers,
                    score=res.score,
                    text=res.text,
                    rerank_score=res.rerank_score,
                    dense_score=res.dense_score,
                    lexical_score=res.lexical_score,
                    document_title=res.document_title,
                    section_heading=res.section_heading,
                )
                for res in search_res.results
            ]

            context = self.build_context(search_res.results)

            answer = await self.llm.generate_answer(
                prompt=query,
                context=context,
                conversation_history=history,
                research_mode=mode,
            )

            if conversation_id:
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    sources=sources,
                )

            return RAGQueryResponse(
                query=query,
                answer=answer,
                sources=sources,
                document_id=effective_document_id,
                conversation_id=conversation_id,
                mode=mode,
                followup_suggestions=followup_suggestions,
            )

        except BaseAppException:
            raise
        except Exception as e:
            logger.error(f"Error during RAG query execution: {str(e)}", exc_info=True)
            raise RAGException(
                message=f"RAG query processing failed: {str(e)}",
                details={"error": str(e)},
            )

    async def stream_academic_rag(self, request: RAGQueryRequest) -> AsyncGenerator[str, None]:
        """Stream RAG response tokens via AsyncGenerator for SSE streaming endpoint."""
        query = request.query.strip()
        if not query:
            raise RAGException("Query string cannot be empty.")

        effective_document_id = request.document_id
        effective_document_ids = request.document_ids

        if effective_document_ids:
            for doc_id in effective_document_ids:
                self.document_service.get_document(doc_id)
        elif effective_document_id:
            self.document_service.get_document(effective_document_id)

        conversation_id = request.conversation_id
        history = []
        retrieval_query = query

        if conversation_id:
            self.conversation_service.get_conversation(conversation_id)
            history = self.conversation_service.get_bounded_history(conversation_id)
            if history:
                retrieval_query = self.query_rewrite_service.rewrite_to_standalone_query(query, history)

            self.conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=query,
            )

        top_k = request.top_k or settings.FINAL_TOP_K
        search_req = SearchRequest(
            query=retrieval_query,
            top_k=top_k,
            document_id=effective_document_id,
            document_ids=effective_document_ids,
        )
        search_res: SearchResponse = self.retriever.search(search_req)

        mode = request.mode or settings.DEFAULT_RESEARCH_MODE

        if not search_res.results:
            no_info_ans = "No relevant information was found in the uploaded academic documents for your query. The provided academic documents do not contain enough information to answer this question."
            if conversation_id:
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=no_info_ans,
                    sources=[],
                )
            yield no_info_ans
            return

        sources = [
            RAGSource(
                document_id=res.document_id,
                chunk_id=res.chunk_id,
                page_numbers=res.page_numbers,
                score=res.score,
                text=res.text,
                rerank_score=res.rerank_score,
                dense_score=res.dense_score,
                lexical_score=res.lexical_score,
                document_title=res.document_title,
                section_heading=res.section_heading,
            )
            for res in search_res.results
        ]

        context = self.build_context(search_res.results)

        full_answer_chunks = []
        if hasattr(self.llm, "generate_answer_stream"):
            async for chunk in self.llm.generate_answer_stream(
                prompt=query,
                context=context,
                conversation_history=history,
                research_mode=mode,
            ):
                full_answer_chunks.append(chunk)
                yield chunk
            answer = "".join(full_answer_chunks)
        else:
            answer = await self.llm.generate_answer(
                prompt=query,
                context=context,
                conversation_history=history,
                research_mode=mode,
            )
            yield answer

        if conversation_id:
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=answer,
                sources=sources,
            )


# Global service instance
rag_service = RAGService()
