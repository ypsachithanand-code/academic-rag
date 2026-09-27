import re
from typing import List, Tuple
import pymupdf  # PyMuPDF


from app.core.exceptions import InvalidFileException
from app.core.logging import logger
from app.models.document import DocumentPage


class PDFService:
    """Service for PDF text extraction, page preservation, and text cleaning."""

    @staticmethod
    def validate_pdf_bytes(file_bytes: bytes) -> None:
        """Validates that byte content is a non-empty, valid PDF file.

        Args:
            file_bytes: Raw binary content of the uploaded file.

        Raises:
            InvalidFileException: If file is empty or corrupted.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise InvalidFileException("Uploaded file is empty (0 bytes).")

        # Verify PDF magic bytes header (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            raise InvalidFileException("File header does not match a valid PDF specification (%PDF-).")

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            if doc.is_encrypted:
                try:
                    # Attempt empty password authentication for soft encryption
                    if not doc.authenticate(""):
                        raise InvalidFileException("PDF file is password-protected and cannot be read.")
                except Exception:
                    raise InvalidFileException("PDF file is password-protected and cannot be read.")
            doc.close()
        except InvalidFileException:
            raise
        except Exception as exc:
            logger.warning(f"PyMuPDF validation failed for uploaded file: {exc}")
            raise InvalidFileException("Uploaded file is corrupted or not a valid PDF document.")

    @classmethod
    def clean_text(cls, raw_text: str) -> str:
        """Cleans extracted raw academic text without altering underlying semantic content.

        Performs:
        - Normalization of line-wrap hyphenation (e.g., 'docu-\\nments' -> 'documents')
        - Normalization of excessive tabs and horizontal spaces
        - Normalization of excessive line breaks (preserving paragraph double-line breaks)
        - Preservation of headings, math symbols, equations, and academic punctuation.

        Args:
            raw_text: Raw string extracted from a PDF page.

        Returns:
            Cleaned text string.
        """
        if not raw_text:
            return ""

        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Rejoin hyphenated words broken across line breaks (word-\nbreak -> wordbreak)
        text = re.sub(r"(\b\w+)-\n(\w+\b)", r"\1\2", text)

        # Normalize multiple horizontal whitespaces (spaces/tabs) to a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize 3 or more consecutive newlines into double newlines (paragraph boundary)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Trim leading and trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()

    @classmethod
    def extract_pages(cls, file_bytes: bytes) -> Tuple[List[DocumentPage], int, bool]:
        """Extracts page-by-page text from a PDF file.

        Args:
            file_bytes: Raw binary content of the PDF.

        Returns:
            Tuple of:
            - List of DocumentPage objects containing page numbers (1-indexed) and cleaned text.
            - Total page count.
            - Boolean flag `has_extractable_text` (True if usable text is present, False otherwise).

        Raises:
            InvalidFileException: If PDF cannot be opened or parsed.
        """
        cls.validate_pdf_bytes(file_bytes)

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            total_pages = doc.page_count
            extracted_pages: List[DocumentPage] = []
            total_text_length = 0

            for page_index in range(total_pages):
                page = doc.load_page(page_index)
                raw_page_text = page.get_text("text")
                cleaned_page_text = cls.clean_text(raw_page_text)

                total_text_length += len(cleaned_page_text)
                extracted_pages.append(
                    DocumentPage(
                        page_number=page_index + 1,
                        text=cleaned_page_text,
                    )
                )

            doc.close()

            # Determine if meaningful extractable text exists
            has_extractable_text = total_text_length >= 20

            return extracted_pages, total_pages, has_extractable_text

        except Exception as exc:
            logger.error(f"Failed to extract text from PDF document: {exc}", exc_info=True)
            raise InvalidFileException("Failed to extract text from PDF document.")


pdf_service = PDFService()
