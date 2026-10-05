from fastapi import APIRouter

from app.models.document import SearchRequest, SearchResponse
from app.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse, summary="Semantic Search")
async def semantic_search(request: SearchRequest) -> SearchResponse:
    """Embed a query with BGE-M3 and return matching indexed chunks."""
    return retrieval_service.search(request)
