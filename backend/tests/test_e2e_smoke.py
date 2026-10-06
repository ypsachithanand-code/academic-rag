"""End-to-end smoke test verifying PDF upload, asynchronous processing, chunking, and RAG query execution."""

import time
import pytest


@pytest.mark.integration
def test_e2e_academic_rag_smoke_pipeline(client, sample_pdf_bytes):
    """
    End-to-end smoke test validating the full real RAG workflow:
    1. Upload sample PDF -> POST /api/v1/documents/upload
    2. Verify HTTP 201 Created and extract document ID
    3. Verify metadata retrieval -> GET /api/v1/documents/{document_id}
    4. Poll until document processing status reaches 'completed'
    5. Ensure chunks exist -> GET /api/v1/documents/{document_id}/chunks
    6. Execute grounded RAG query -> POST /api/v1/rag/query
    7. Verify non-empty answer, non-empty sources, and citation matching document ID.
    """
    # Step 1: Upload sample PDF document
    files = {
        "file": ("attention_sample.pdf", sample_pdf_bytes, "application/pdf")
    }
    upload_resp = client.post("/api/v1/documents/upload", files=files)
    assert upload_resp.status_code == 201, (
        f"Upload failed with status {upload_resp.status_code}: {upload_resp.text}"
    )

    upload_data = upload_resp.json()
    assert "document" in upload_data, f"Unexpected upload response schema: {upload_data}"
    document_id = upload_data["document"]["id"]
    assert document_id, "Uploaded document ID is empty or missing"

    # Step 2: Verify metadata endpoint retrieves the document
    doc_resp = client.get(f"/api/v1/documents/{document_id}")
    assert doc_resp.status_code == 200, (
        f"Get document failed with status {doc_resp.status_code}: {doc_resp.text}"
    )
    assert doc_resp.json()["id"] == document_id

    # Step 3: Poll document processing status until 'completed'
    timeout_seconds = 60
    poll_interval_seconds = 1
    start_time = time.time()
    current_status = None
    last_doc_payload = {}

    while time.time() - start_time < timeout_seconds:
        poll_resp = client.get(f"/api/v1/documents/{document_id}")
        assert poll_resp.status_code == 200, (
            f"Poll failed with status {poll_resp.status_code}: {poll_resp.text}"
        )
        last_doc_payload = poll_resp.json()
        current_status = last_doc_payload.get("status")

        if current_status == "completed":
            break
        elif current_status == "failed":
            error_msg = last_doc_payload.get("error_message", "No error message provided")
            pytest.fail(f"Document processing failed for document_id={document_id}: {error_msg}")

        time.sleep(poll_interval_seconds)

    assert current_status == "completed", (
        f"Document processing timed out after {timeout_seconds}s for document_id={document_id}. "
        f"Last payload: {last_doc_payload}"
    )

    # Step 4: Verify generated chunks endpoint
    chunks_resp = client.get(f"/api/v1/documents/{document_id}/chunks")
    assert chunks_resp.status_code == 200, (
        f"Get chunks failed with status {chunks_resp.status_code}: {chunks_resp.text}"
    )
    chunks_data = chunks_resp.json()
    assert "chunks" in chunks_data, f"Unexpected chunks response schema: {chunks_data}"
    assert len(chunks_data["chunks"]) > 0, (
        f"Expected at least one chunk for document_id={document_id}, found 0"
    )

    # Step 5: Query RAG endpoint with text from sample_pdf_bytes
    # sample_pdf_bytes contains: "We propose the Transformer, a novel neural network architecture based solely on attention mechanisms."
    rag_query_payload = {
        "query": "What novel neural network architecture is proposed based solely on attention mechanisms?",
        "document_id": document_id,
        "mode": "qa",
        "top_k": 5,
    }
    rag_resp = client.post("/api/v1/rag/query", json=rag_query_payload)
    assert rag_resp.status_code == 200, (
        f"RAG query failed with status {rag_resp.status_code}: {rag_resp.text}"
    )

    rag_data = rag_resp.json()
    assert "answer" in rag_data, f"RAG response missing 'answer' field: {rag_data}"
    assert rag_data["answer"].strip(), "RAG response 'answer' is empty"
    assert "sources" in rag_data, f"RAG response missing 'sources' field: {rag_data}"
    assert len(rag_data["sources"]) > 0, (
        f"RAG response returned 0 sources for query payload: {rag_query_payload}"
    )

    # Verify at least one source references the uploaded document_id
    matching_sources = [
        src for src in rag_data["sources"] if src.get("document_id") == document_id
    ]
    assert len(matching_sources) > 0, (
        f"Expected at least one source with document_id={document_id}, "
        f"got sources: {rag_data['sources']}"
    )
