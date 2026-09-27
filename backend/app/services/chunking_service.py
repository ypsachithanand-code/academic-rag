import re
from typing import List, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentChunk, DocumentPage



class ChunkingService:
    """Service for paragraph-, section-, and page-aware document chunking."""

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        """Estimates token count based on whitespace splitting and punctuation boundaries.
        
        A standard heuristic for academic English text is ~1.3 tokens per word,
        or roughly 1 token per 4 characters. We use word splitting + punctuation sub-token heuristics.
        """
        if not text:
            return 0
        words = text.split()
        return int(len(words) * 1.25) + text.count(".") + text.count(",")

    @classmethod
    def chunk_document_pages(
        cls,
        document_id: str,
        pages: List[DocumentPage],
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> List[DocumentChunk]:
        """Splits page-level extracted document text into semantic chunks while preserving page metadata.

        Args:
            document_id: Unique identifier of the document.
            pages: List of DocumentPage objects containing page numbers and clean text.
            chunk_size: Maximum target character size per chunk.
            chunk_overlap: Overlapping character count retained between consecutive chunks.

        Returns:
            List of DocumentChunk objects with deterministic IDs and page metadata.
        """
        if not pages:
            return []

        # Step 1: Flatten pages into page-annotated text units (paragraphs)
        annotated_units: List[Tuple[int, str]] = []
        for page in pages:
            if not page.text or not page.text.strip():
                continue
            # Split text into paragraphs
            paragraphs = [p.strip() for p in re.split(r"\n\n+", page.text) if p.strip()]
            for p in paragraphs:
                annotated_units.append((page.page_number, p))

        if not annotated_units:
            return []

        chunks: List[DocumentChunk] = []
        current_unit_texts: List[str] = []
        current_page_numbers: List[int] = []
        current_char_count = 0
        chunk_index = 0

        for page_num, unit_text in annotated_units:
            unit_len = len(unit_text)

            # If single paragraph exceeds chunk_size, split by sentences
            if unit_len > chunk_size:
                sentences = [s.strip() + "." for s in re.split(r"\.\s+", unit_text) if s.strip()]
                for sentence in sentences:
                    sentence_len = len(sentence)
                    if current_char_count + sentence_len > chunk_size and current_unit_texts:
                        # Flush current chunk
                        chunk_text = "\n\n".join(current_unit_texts).strip()
                        chunk_id = f"{document_id}_chunk_{chunk_index:05d}"
                        unique_pages = sorted(list(set(current_page_numbers)))

                        chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                document_id=document_id,
                                page_numbers=unique_pages,
                                chunk_index=chunk_index,
                                text=chunk_text,
                                character_count=len(chunk_text),
                                token_count=cls._estimate_token_count(chunk_text),
                            )
                        )
                        chunk_index += 1

                        # Retain overlap tail
                        overlap_buffer: List[str] = []
                        overlap_pages: List[int] = []
                        accumulated = 0
                        for rev_text, rev_page in zip(reversed(current_unit_texts), reversed(current_page_numbers)):
                            if accumulated + len(rev_text) <= chunk_overlap:
                                overlap_buffer.insert(0, rev_text)
                                overlap_pages.insert(0, rev_page)
                                accumulated += len(rev_text)
                            else:
                                break

                        current_unit_texts = overlap_buffer
                        current_page_numbers = overlap_pages
                        current_char_count = sum(len(t) for t in current_unit_texts)

                    current_unit_texts.append(sentence)
                    current_page_numbers.append(page_num)
                    current_char_count += sentence_len
            else:
                if current_char_count + unit_len > chunk_size and current_unit_texts:
                    # Flush current chunk
                    chunk_text = "\n\n".join(current_unit_texts).strip()
                    chunk_id = f"{document_id}_chunk_{chunk_index:05d}"
                    unique_pages = sorted(list(set(current_page_numbers)))

                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            page_numbers=unique_pages,
                            chunk_index=chunk_index,
                            text=chunk_text,
                            character_count=len(chunk_text),
                            token_count=cls._estimate_token_count(chunk_text),
                        )
                    )
                    chunk_index += 1

                    # Retain overlap tail
                    overlap_buffer = []
                    overlap_pages = []
                    accumulated = 0
                    for rev_text, rev_page in zip(reversed(current_unit_texts), reversed(current_page_numbers)):
                        if accumulated + len(rev_text) <= chunk_overlap:
                            overlap_buffer.insert(0, rev_text)
                            overlap_pages.insert(0, rev_page)
                            accumulated += len(rev_text)
                        else:
                            break

                    current_unit_texts = overlap_buffer
                    current_page_numbers = overlap_pages
                    current_char_count = sum(len(t) for t in current_unit_texts)

                current_unit_texts.append(unit_text)
                current_page_numbers.append(page_num)
                current_char_count += unit_len

        # Flush remaining buffer
        if current_unit_texts:
            chunk_text = "\n\n".join(current_unit_texts).strip()
            if chunk_text:
                chunk_id = f"{document_id}_chunk_{chunk_index:05d}"
                unique_pages = sorted(list(set(current_page_numbers)))

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        page_numbers=unique_pages,
                        chunk_index=chunk_index,
                        text=chunk_text,
                        character_count=len(chunk_text),
                        token_count=cls._estimate_token_count(chunk_text),
                    )
                )

        logger.info(f"Chunked document {document_id}: created {len(chunks)} chunks (Target size: {chunk_size}, Overlap: {chunk_overlap})")
        return chunks


chunking_service = ChunkingService()
