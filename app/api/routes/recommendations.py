from fastapi import APIRouter, HTTPException, status

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation_orchestrator import RecommendationOrchestrator


router = APIRouter(prefix="/recommendations", tags=["recommendations"])
orchestrator = RecommendationOrchestrator()


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
)
def create_recommendation(
    request: RecommendationRequest,
) -> RecommendationResponse:
    try:
        return orchestrator.handle(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
