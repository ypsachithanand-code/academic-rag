from qdrant_client import QdrantClient
from app.core.config import settings
from app.core.logging import logger


class QdrantService:
    """Service wrapper for interacting with the Qdrant Vector Database."""

    def __init__(self, url: str = settings.QDRANT_URL, timeout: float = settings.QDRANT_TIMEOUT):
        self.url = url
        self.timeout = timeout

    def check_health(self) -> bool:
        """Verifies if the Qdrant instance is reachable.

        Returns:
            bool: True if Qdrant responds successfully, False otherwise.
        """
        try:
            client = QdrantClient(url=self.url, timeout=self.timeout)
            # Make a lightweight API call to verify connection
            client.get_collections()
            return True
        except Exception as exc:
            logger.warning(f"Qdrant health check failed: {exc}")
            return False


qdrant_service = QdrantService()
