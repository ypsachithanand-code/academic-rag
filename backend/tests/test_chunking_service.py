from app.models.document import DocumentPage
from app.services.chunking_service import chunking_service


def test_chunking_empty_pages():
    """Tests that chunking an empty list of pages returns an empty list."""
    chunks = chunking_service.chunk_document_pages("doc123", [])
    assert chunks == []


def test_chunking_single_short_page():
    """Tests chunking a page with short academic text."""
    pages = [
        DocumentPage(page_number=1, text="Attention Is All You Need. Abstract text.")
    ]
    chunks = chunking_service.chunk_document_pages("doc123", pages, chunk_size=800, chunk_overlap=120)
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc123_chunk_00000"
    assert chunks[0].document_id == "doc123"
    assert chunks[0].page_numbers == [1]
    assert chunks[0].chunk_index == 0
    assert "Attention Is All You Need" in chunks[0].text
    assert chunks[0].character_count > 0
    assert chunks[0].token_count > 0


def test_chunking_multi_page_overlap_and_metadata():
    """Tests chunking long text spanning multiple pages with page metadata preservation."""
    page1_text = "Paragraph 1 on Page 1.\n\n" + ("Text unit A. " * 30)
    page2_text = "Paragraph 2 on Page 2.\n\n" + ("Text unit B. " * 30)

    pages = [
        DocumentPage(page_number=1, text=page1_text),
        DocumentPage(page_number=2, text=page2_text),
    ]

    chunks = chunking_service.chunk_document_pages("doc999", pages, chunk_size=300, chunk_overlap=50)

    assert len(chunks) > 1
    # Check deterministic chunk IDs
    for idx, c in enumerate(chunks):
        assert c.chunk_id == f"doc999_chunk_{idx:05d}"
        assert c.chunk_index == idx
        assert len(c.page_numbers) > 0
        assert c.token_count > 0

    # Verify first chunk page number
    assert 1 in chunks[0].page_numbers
    # Verify last chunk page number
    assert 2 in chunks[-1].page_numbers


def test_chunking_id_stability():
    """Tests that chunking the same input repeatedly generates identical chunk IDs."""
    pages = [DocumentPage(page_number=1, text="Consistent chunk text.")]
    chunks1 = chunking_service.chunk_document_pages("doc_stable", pages)
    chunks2 = chunking_service.chunk_document_pages("doc_stable", pages)

    assert len(chunks1) == len(chunks2) == 1
    assert chunks1[0].chunk_id == chunks2[0].chunk_id == "doc_stable_chunk_00000"
