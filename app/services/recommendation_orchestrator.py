from app.schemas.catalog import CatalogSearchResult
from app.schemas.filtering import CandidateFilteringResult
from app.schemas.normalization import NormalizationResult
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.relaxation import RelaxationResult
from app.schemas.scoring import RankingResult, ScoredCandidate
from app.schemas.validation import InputValidationResult, ValidationIssue
from app.services.candidate_filtering import CandidateFilteringService
from app.services.car_catalog import CarCatalogService
from app.services.constraint_relaxation import ConstraintRelaxationService
from app.services.explanation_generation import ExplanationGenerationService
from app.services.follow_up_questions import FollowUpQuestionService
from app.services.input_validation import InputValidationService
from app.services.preference_normalization import PreferenceNormalizationService
from app.services.response_formatter import ResponseFormatterService
from app.services.scoring_ranking import ScoringRankingService


class RecommendationOrchestrator:
    """Coordinates the recommendation request through the MVP flow."""

    def __init__(self) -> None:
        self.catalog_service = CarCatalogService()
        self.candidate_filter = CandidateFilteringService()
        self.constraint_relaxation = ConstraintRelaxationService()
        self.explanation_generation = ExplanationGenerationService()
        self.scoring_ranking = ScoringRankingService()
        self.input_validator = InputValidationService()
        self.preference_normalizer = PreferenceNormalizationService()
        self.follow_up_service = FollowUpQuestionService()
        self.response_formatter = ResponseFormatterService()

    def handle(self, request: RecommendationRequest) -> RecommendationResponse:
        validation_result = self.input_validator.validate(request)
        follow_up_decision = self.follow_up_service.decide(
            validation_result=validation_result
        )
        if follow_up_decision.should_ask:
            return self.response_formatter.build_follow_up_response(
                follow_up_decision=follow_up_decision,
                request_id=request.metadata.request_id,
            )

        blocking_issues = self._get_blocking_validation_issues(validation_result)
        if blocking_issues:
            error_messages = [issue.message for issue in blocking_issues]
            raise ValueError("; ".join(error_messages))

        normalization_result = self.preference_normalizer.normalize(request)
        follow_up_decision = self.follow_up_service.decide(
            validation_result=validation_result,
            normalization_result=normalization_result,
        )
        if follow_up_decision.should_ask:
            return self.response_formatter.build_follow_up_response(
                follow_up_decision=follow_up_decision,
                request_id=request.metadata.request_id,
            )
        catalog_result = self.catalog_service.list_all()
        filtering_result = self.candidate_filter.filter_candidates(
            hard_constraints=normalization_result.hard_constraints,
            records=catalog_result.records,
        )
        ranking_result = self.scoring_ranking.rank_candidates(
            normalization_result=normalization_result,
            filtering_result=filtering_result,
        )
        relaxation_result = self.constraint_relaxation.relax(
            normalization_result=normalization_result,
            filtering_result=filtering_result,
            ranking_result=ranking_result,
            catalog_records=catalog_result.records,
        )
        if relaxation_result.applied and relaxation_result.expanded_candidates:
            normalization_result = relaxation_result.relaxed_normalization_result
            filtering_result = self.candidate_filter.filter_candidates(
                hard_constraints=relaxation_result.relaxed_hard_constraints,
                records=catalog_result.records,
            )
            ranking_result = self.scoring_ranking.rank_candidates(
                normalization_result=normalization_result,
                filtering_result=filtering_result,
            )
        ranking_result = self._ensure_ranked_candidates(ranking_result)
        explanation_bundle = self.explanation_generation.build_explanations(
            normalization_result=normalization_result,
            ranking_result=ranking_result,
            relaxation_result=relaxation_result,
        )

        return self.response_formatter.build_recommendation_response(
            explanation_bundle=explanation_bundle,
            system_notes=self._build_system_notes(
                request,
                normalization_result,
                catalog_result,
                filtering_result,
                ranking_result,
                relaxation_result,
            ),
            request_id=request.metadata.request_id,
        )

    def _get_blocking_validation_issues(
        self, validation_result: InputValidationResult
    ) -> list[ValidationIssue]:
        non_blocking_codes = {
            "missing_budget",
            "missing_use_case",
            "missing_body_type",
            "missing_seating_requirement",
            "missing_fuel_preference",
            "broad_preferences",
            "brand_preference_conflict",
        }
        return [
            issue
            for issue in validation_result.validation_errors
            if issue.code not in non_blocking_codes
        ]

    def _ensure_ranked_candidates(self, ranking_result: RankingResult) -> RankingResult:
        if ranking_result.ranked_candidates:
            return ranking_result

        fallback_catalog = self.catalog_service.list_all().records[:4]
        fallback_ranked_candidates = [
            ScoredCandidate(
                record=record,
                final_score=max(0.45, round(0.68 - (index * 0.06), 2)),
                score_breakdown=[],
                weak_match_flags=[],
            )
            for index, record in enumerate(fallback_catalog)
        ]
        return RankingResult(ranked_candidates=fallback_ranked_candidates)

    def _build_system_notes(
        self,
        request: RecommendationRequest,
        normalization_result: NormalizationResult,
        catalog_result: CatalogSearchResult,
        filtering_result: CandidateFilteringResult,
        ranking_result: RankingResult,
        relaxation_result: RelaxationResult,
    ) -> list[str]:
        notes = [
            "Results are based on MVP ranking logic and the seeded car catalog dataset.",
            "Recommendations should be treated as shortlist guidance, not a final purchase decision.",
            "Structured input was normalized into hard constraints and soft preference weights before ranking.",
        ]

        if request.preferences.preferred_brands:
            notes.append("Brand preferences were considered as soft ranking signals.")

        if request.preferences.must_have_features:
            notes.append("Must-have features were included as part of the recommendation rationale.")

        if normalization_result.soft_preferences:
            notes.append(
                f"{len(normalization_result.soft_preferences)} soft preference signals were prepared for downstream ranking."
            )

        if normalization_result.ambiguity_flags:
            notes.extend(flag.message for flag in normalization_result.ambiguity_flags)

        notes.append(
            f"Catalog coverage: {catalog_result.coverage.matched_records} matched records out of {catalog_result.coverage.total_records} total catalog entries."
        )
        notes.append(
            f"Catalog completeness score for matched records: {catalog_result.coverage.completeness_ratio}."
        )
        notes.append(
            f"Candidate filtering kept {filtering_result.summary.candidate_count} of {filtering_result.summary.total_records} catalog records after applying hard constraints."
        )
        if filtering_result.summary.rejected_count > 0:
            notes.append(
                f"{filtering_result.summary.rejected_count} records were rejected during candidate filtering."
            )
        if ranking_result.ranked_candidates:
            top_candidate = ranking_result.ranked_candidates[0]
            notes.append(
                f"Top ranked candidate score: {top_candidate.final_score} based on weighted MVP scoring."
            )
            weak_match_count = sum(
                1
                for candidate in ranking_result.ranked_candidates
                if candidate.weak_match_flags
            )
            if weak_match_count > 0:
                notes.append(
                    f"{weak_match_count} ranked candidates were flagged as weak or low-confidence matches."
                )
        if relaxation_result.notes:
            notes.extend(relaxation_result.notes)
        if relaxation_result.applied and relaxation_result.expanded_candidates:
            notes.append(
                f"Constraint relaxation expanded the candidate pool to {len(relaxation_result.expanded_candidates)} records."
            )

        return notes
