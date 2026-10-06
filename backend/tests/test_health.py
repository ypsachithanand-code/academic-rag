from unittest.mock import patch


def test_root_endpoint(client):
    """Tests GET / returns message and running status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Academic RAG API"
    assert data["status"] == "running"


def test_app_health_endpoint(client):
    """Tests GET /health returns application health status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "academic-rag"
    assert "version" in data


def test_v1_health_endpoint(client):
    """Tests GET /api/v1/health returns application health status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "academic-rag"
    assert "version" in data


def test_qdrant_health_endpoint_live(client):
    """Tests GET /health/qdrant against the live Qdrant container."""
    response = client.get("/health/qdrant")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert data["service"] == "qdrant"


@patch("app.services.qdrant_service.qdrant_service.check_health", return_value=True)
def test_qdrant_health_endpoint_healthy(mock_check_health, client):
    """Tests GET /health/qdrant when Qdrant is healthy (mocked)."""
    response = client.get("/health/qdrant")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "qdrant"


@patch("app.services.qdrant_service.qdrant_service.check_health", return_value=False)
def test_qdrant_health_endpoint_unhealthy(mock_check_health, client):
    """Tests GET /health/qdrant when Qdrant is unreachable (mocked)."""
    response = client.get("/health/qdrant")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["service"] == "qdrant"


@patch("app.services.qdrant_service.qdrant_service.check_health", return_value=True)
def test_v1_qdrant_health_endpoint_healthy(mock_check_health, client):
    """Tests GET /api/v1/health/qdrant when Qdrant is healthy (mocked)."""
    response = client.get("/api/v1/health/qdrant")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "qdrant"


def test_openapi_schema_endpoint(client):
    """Tests GET /openapi.json returns 200 OK and valid OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/api/v1/conversations" in data["paths"]
    assert "/api/v1/documents/{document_id}/summary" in data["paths"]
    assert "/api/v1/rag/query/stream" in data["paths"]


def test_swagger_docs_endpoint(client):
    """Tests GET /docs returns 200 OK HTML UI page."""
    response = client.get("/docs")
    assert response.status_code == 200
