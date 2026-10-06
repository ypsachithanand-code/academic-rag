"""Lexical (keyword/BM25) retrieval service for academic document chunks."""

import math
import re
from collections import Counter
from typing import List, Optional, Dict, Any

from app.core.config import settings
from app.core.logging import logger
from app.models.document import SearchResult
from app.services.qdrant_service import qdrant_service, QdrantService


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric and technical term tokens."""
    if not text:
        return []
    # Tokenize preserving hyphenated words and technical terms
    return [token.lower() for token in re.findall(r"\b[\w\-]+\b", text)]


class BM25Scorer:
    """In-memory BM25 (Okapi) ranking engine."""

    def __init__(self, corpus_documents: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus_documents  # List of payload dicts containing text, chunk_id, etc.
        self.doc_count = len(corpus_documents)
        self.doc_tokens: List[List[str]] = [tokenize_text(doc.get("text", "")) for doc in corpus_documents]
        self.doc_lens: List[int] = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len: float = sum(self.doc_lens) / max(self.doc_count, 1)

        # Calculate Document Frequencies (DF)
        self.df: Dict[str, int] = Counter()
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.df[token] += 1

    def score_query(self, query_tokens: List[str], top_k: int) -> List[tuple[Dict[str, Any], float]]:
        """Calculate BM25 scores for all documents in the corpus for the given query tokens."""
        if not query_tokens or self.doc_count == 0:
            return []

        scores: List[tuple[Dict[str, Any], float]] = []

        for idx, (doc_payload, tokens, doc_len) in enumerate(zip(self.corpus, self.doc_tokens, self.doc_lens)):
            doc_term_freqs = Counter(tokens)
            score = 0.0

            for token in query_tokens:
                if token not in doc_term_freqs:
                    continue

                freq = doc_term_freqs[token]
                n_t = self.df.get(token, 0)

                # Smooth Inverse Document Frequency (IDF)
                idf = math.log(1.0 + (self.doc_count - n_t + 0.5) / (n_t + 0.5))

                # BM25 Term Frequency component
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / max(self.avg_doc_len, 1.0)))

                score += idf * (numerator / max(denominator, 1e-6))

            if score > 0.0:
                scores.append((doc_payload, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class LexicalService:
    """Service wrapper for lexical (BM25) search against indexed Qdrant payloads."""

    def __init__(self, qdrant: Optional[QdrantService] = None):
        self.qdrant = qdrant or qdrant_service

    def _fetch_candidate_payloads(
        self,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch indexed points/payloads from Qdrant for BM25 indexing."""
        try:
            if not self.qdrant.collection_exists():
                return []

            query_filter = None
            if document_ids:
                from qdrant_client.http import models
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchAny(any=document_ids),
                        )
                    ]
                )
            elif document_id:
                from qdrant_client.http import models
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )

            points, _ = self.qdrant.client.scroll(
                collection_name=self.qdrant.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            payloads = []
            for point in points:
                p = point.payload or {}
                if "chunk_id" not in p:
                    p["chunk_id"] = str(point.id)
                payloads.append(p)
            return payloads

        except Exception as exc:
            logger.warning(f"Failed to fetch payloads from Qdrant for lexical search: {exc}")
            return []

    def search(
        self,
        query: str,
        top_k: int = settings.LEXICAL_TOP_K,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Perform lexical (BM25) search over indexed document chunks."""
        query_str = query.strip()
        if not query_str:
            return []

        query_tokens = tokenize_text(query_str)
        if not query_tokens:
            return []

        payloads = self._fetch_candidate_payloads(document_id=document_id, document_ids=document_ids)

        if not payloads:
            return []

        scorer = BM25Scorer(payloads)
        scored_docs = scorer.score_query(query_tokens, top_k=top_k)

        results = []
        for payload, score in scored_docs:
            results.append(
                SearchResult(
                    score=float(score),
                    lexical_score=float(score),
                    document_id=payload.get("document_id", ""),
                    chunk_id=payload.get("chunk_id", ""),
                    page_numbers=payload.get("page_numbers", []),
                    text=payload.get("text", ""),
                    token_count=payload.get("token_count", 0),
                    document_title=payload.get("document_title"),
                    section_heading=payload.get("section_heading"),
                )
            )
        return results


lexical_service = LexicalService()
