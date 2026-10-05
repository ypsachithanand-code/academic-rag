import io
import pytest
from app.services.document_service import document_service


def test_upload_valid_pdf_and_end_to_end_extraction_and_chunking(client, sample_pdf_bytes):
    """End-to-End Test: Upload PDF -> Extraction -> Chunking -> Embeddings -> Chunks API -> Delete."""
    from huggingface_hub import try_to_load_from_cache
    cached_files = [try_to_load_from_cache("BAAI/bge-m3", name) for name in
                    ("tokenizer_config.json", "pytorch_model.bin")]
    if not all(isinstance(path, str) for path in cached_files):
        pytest.skip("Real BGE-M3 model files are not available in the local Hugging Face cache")
    # 1. Upload PDF
    files = {"file": ("attention_paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    payload = response.json()
    assert "document" in payload
    doc_id = payload["document"]["id"]

    # 2. Synchronously run full pipeline (extraction -> chunking -> embeddings)
    processed_metadata = document_service.process_document(doc_id)
    assert processed_metadata.status == "completed"
    assert processed_metadata.page_count == 2

    # 3. Get Document Metadata
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_data = get_res.json()
    assert doc_data["id"] == doc_id
    assert doc_data["status"] == "completed"
    assert doc_data["page_count"] == 2

    # 4. Get Processed Pages
    pages_res = client.get(f"/api/v1/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    pages_data = pages_res.json()
    assert pages_data["total_pages"] == 2

    # 5. Inspect Generated Chunks
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks_data = chunks_res.json()
    assert chunks_data["document_id"] == doc_id
    assert chunks_data["total_chunks"] > 0
    assert chunks_data["embedding_dimension"] == 1024
    assert len(chunks_data["chunks"]) > 0
    assert chunks_data["chunks"][0]["chunk_id"].startswith(f"{doc_id}_chunk_")
    assert len(chunks_data["chunks"][0]["page_numbers"]) > 0

    # 6. Delete Document
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["document_id"] == doc_id

    # Verify document and chunks no longer exist
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404
    assert client.get(f"/api/v1/documents/{doc_id}/chunks").status_code == 404


def test_trigger_process_pipeline_endpoint(client, sample_pdf_bytes):
    """Tests POST /api/v1/documents/{id}/process endpoint."""
    files = {"file": ("process_paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    process_res = client.post(f"/api/v1/documents/{doc_id}/process?force=true")
    assert process_res.status_code == 202
    assert process_res.json()["document_id"] == doc_id


def test_duplicate_pdf_upload_detection(client, sample_pdf_bytes):
    """Tests that uploading the exact same PDF content twice returns 409 Conflict."""
    files1 = {"file": ("paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res1 = client.post("/api/v1/documents/upload", files=files1)
    assert res1.status_code == 201
    first_doc_id = res1.json()["document"]["id"]

    # Second upload with identical bytes
    files2 = {"file": ("duplicate_paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res2 = client.post("/api/v1/documents/upload", files=files2)
    assert res2.status_code == 409
    err_payload = res2.json()
    assert err_payload["error"]["code"] == "DUPLICATE_DOCUMENT"
    assert err_payload["error"]["details"]["existing_document_id"] == first_doc_id


def test_upload_non_pdf_file_rejected(client):
    """Tests uploading a text file (.txt) instead of a PDF."""
    files = {"file": ("notes.txt", io.BytesIO(b"Plain text content"), "text/plain")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_FILE"


def test_upload_empty_file_rejected(client):
    """Tests uploading an empty PDF file (0 bytes)."""
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_FILE"


def test_no_text_pdf_handling(client, no_text_pdf_bytes):
    """Tests that a blank/scanned PDF without extractable text transitions to NO_TEXT status."""
    files = {"file": ("blank_scan.pdf", io.BytesIO(no_text_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    processed = document_service.process_document(doc_id)
    assert processed.status == "no_text"
    assert "No extractable text was found" in processed.error_message


def test_retry_document_processing(client, sample_pdf_bytes):
    """Tests retrying document processing endpoint."""
    files = {"file": ("retry_paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]

    retry_res = client.post(f"/api/v1/documents/{doc_id}/retry")
    assert retry_res.status_code == 202
    assert retry_res.json()["document_id"] == doc_id
