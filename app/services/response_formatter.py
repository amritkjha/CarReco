from datetime import datetime, timezone

from app.schemas.explanation import ExplanationBundle
from app.schemas.follow_up import FollowUpDecision
from app.schemas.recommendation import RecommendationResponse


class ResponseFormatterService:
    """Assembles the final API response in a consistent shape."""

    def build_follow_up_response(
        self,
        *,
        follow_up_decision: FollowUpDecision,
        request_id: str | None,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            recommendations=[],
            alternatives=[],
            alternative_notes=[],
            system_notes=follow_up_decision.notes,
            follow_up_question=follow_up_decision.question,
            request_id=request_id,
            generated_at=datetime.now(timezone.utc),
        )

    def build_recommendation_response(
        self,
        *,
        explanation_bundle: ExplanationBundle,
        system_notes: list[str],
        request_id: str | None,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            recommendations=explanation_bundle.recommendations,
            alternatives=explanation_bundle.alternatives,
            alternative_notes=explanation_bundle.alternative_notes,
            system_notes=system_notes,
            follow_up_question=None,
            request_id=request_id,
            generated_at=datetime.now(timezone.utc),
        )
