import pytest
from app.core.exceptions import InvalidFileException
from app.services.pdf_service import pdf_service


def test_clean_text_hyphenation_and_whitespace():
    """Tests that clean_text correctly rejoins hyphenated words and normalizes whitespace."""
    raw = "This is a docu-\nment with   excessive    spaces.\n\n\nNew paragraph."
    cleaned = pdf_service.clean_text(raw)
    assert "document" in cleaned
    assert "excessive spaces" in cleaned
    assert "\n\nNew paragraph." in cleaned


def test_clean_text_preserves_equations_and_punctuation():
    """Tests that mathematical equations, formulas, and academic notation are preserved."""
    raw = "Equation (1): E = mc^2 + \\alpha_i * \\beta_j."
    cleaned = pdf_service.clean_text(raw)
    assert cleaned == raw


def test_extract_pages_valid_pdf(sample_pdf_bytes):
    """Tests page extraction from a valid 2-page PDF file."""
    pages, total_pages, has_text = pdf_service.extract_pages(sample_pdf_bytes)
    assert total_pages == 2
    assert has_text is True
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Attention Is All You Need" in pages[0].text
    assert "document" in pages[0].text  # Hyphenation rejoined ('docu-\nment')
    assert pages[1].page_number == 2
    assert "Section 1. Introduction" in pages[1].text


def test_extract_pages_no_text_pdf(no_text_pdf_bytes):
    """Tests page extraction from a blank/scanned PDF with no text."""
    pages, total_pages, has_text = pdf_service.extract_pages(no_text_pdf_bytes)
    assert total_pages == 1
    assert has_text is False


def test_validate_pdf_bytes_invalid_header():
    """Tests that non-PDF content raises InvalidFileException."""
    invalid_bytes = b"NOT_A_PDF_FILE_HEADER_CONTENT"
    with pytest.raises(InvalidFileException) as exc_info:
        pdf_service.validate_pdf_bytes(invalid_bytes)
    assert "does not match a valid PDF specification" in str(exc_info.value)


def test_validate_pdf_bytes_empty():
    """Tests that empty byte content raises InvalidFileException."""
    with pytest.raises(InvalidFileException) as exc_info:
        pdf_service.validate_pdf_bytes(b"")
    assert "empty" in str(exc_info.value)
