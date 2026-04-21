from datetime import datetime, timezone

from app.schemas.explanation import ExplanationBundle
from app.schemas.follow_up import FollowUpDecision
from app.schemas.orchestration import WorkflowResult
from app.schemas.recommendation import RecommendationResponse


class ResponseFormatterService:
    """Assembles the final API response in a consistent shape."""

    def build_follow_up_response(
        self,
        *,
        follow_up_decision: FollowUpDecision,
        workflow_result: WorkflowResult,
        request_id: str | None,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            recommendations=[],
            alternatives=[],
            alternative_notes=[],
            system_notes=follow_up_decision.notes,
            follow_up_question=follow_up_decision.question,
            workflow_status=workflow_result.status,
            reason_codes=workflow_result.reason_codes,
            request_id=request_id,
            generated_at=datetime.now(timezone.utc),
        )

    def build_recommendation_response(
        self,
        *,
        explanation_bundle: ExplanationBundle,
        system_notes: list[str],
        workflow_result: WorkflowResult,
        request_id: str | None,
    ) -> RecommendationResponse:
        return RecommendationResponse(
            recommendations=explanation_bundle.recommendations,
            alternatives=explanation_bundle.alternatives,
            alternative_notes=explanation_bundle.alternative_notes,
            system_notes=system_notes,
            follow_up_question=None,
            workflow_status=workflow_result.status,
            reason_codes=workflow_result.reason_codes,
            request_id=request_id,
            generated_at=datetime.now(timezone.utc),
        )
