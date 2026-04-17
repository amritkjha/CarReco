from app.schemas.explanation import ExplanationBundle
from app.schemas.normalization import NormalizationResult
from app.schemas.recommendation import CarSummary, PrimaryUseCase, RecommendationItem
from app.schemas.relaxation import RelaxationResult
from app.schemas.scoring import RankingResult, ScoredCandidate


class ExplanationGenerationService:
    """Generates concise recommendation explanations from ranked candidates."""

    def build_explanations(
        self,
        *,
        normalization_result: NormalizationResult,
        ranking_result: RankingResult,
        relaxation_result: RelaxationResult,
    ) -> ExplanationBundle:
        ranked_candidates = ranking_result.ranked_candidates[:5]
        recommendation_items = [
            self._to_recommendation_item(
                index=index,
                scored_candidate=scored_candidate,
                normalization_result=normalization_result,
                relaxation_result=relaxation_result,
            )
            for index, scored_candidate in enumerate(ranked_candidates)
        ]

        primary_recommendations = recommendation_items[:3]
        alternatives = recommendation_items[3:5]

        alternative_notes = self._build_alternative_notes(
            alternatives=alternatives,
            relaxation_result=relaxation_result,
            ranking_result=ranking_result,
        )

        return ExplanationBundle(
            recommendations=primary_recommendations,
            alternatives=alternatives,
            alternative_notes=alternative_notes,
        )

    def _to_recommendation_item(
        self,
        *,
        index: int,
        scored_candidate: ScoredCandidate,
        normalization_result: NormalizationResult,
        relaxation_result: RelaxationResult,
    ) -> RecommendationItem:
        record = scored_candidate.record
        return RecommendationItem(
            rank=index + 1,
            match_score=scored_candidate.final_score,
            price_range=f"{record.price_min:,} - {record.price_max:,}",
            reasons=self._build_reasons(
                normalization_result.normalized_preferences.primary_use_case,
                scored_candidate,
                relaxation_result,
            ),
            tradeoff=self._build_tradeoff(
                scored_candidate=scored_candidate,
                normalization_result=normalization_result,
                relaxation_result=relaxation_result,
            ),
            summary=CarSummary(
                make=record.make,
                model=record.model,
                body_type=record.body_type,
                fuel_type=record.fuel_type,
                transmission=record.transmission,
                seating=record.seating,
                mileage_or_range=record.mileage_or_range,
                safety_rating=record.safety_rating,
            ),
        )

    def _build_reasons(
        self,
        use_case: PrimaryUseCase,
        scored_candidate: ScoredCandidate,
        relaxation_result: RelaxationResult,
    ) -> list[str]:
        record = scored_candidate.record
        use_case_reason = {
            PrimaryUseCase.CITY_COMMUTE: "Well-suited for daily city driving and ease of use.",
            PrimaryUseCase.FAMILY_USE: "Fits family travel needs with practical cabin space.",
            PrimaryUseCase.HIGHWAY_TRAVEL: "Offers a comfortable setup for long highway trips.",
            PrimaryUseCase.OFF_ROAD: "Better aligned with rough-road and occasional off-road use.",
            PrimaryUseCase.MIXED_USE: "Balances city comfort with weekend and mixed-use practicality.",
        }[use_case]
        reasons = [
            use_case_reason,
            f"Matches the {record.body_type.value} / {record.fuel_type.value} profile available in the catalog.",
        ]
        strongest_factor = self._strongest_factor_label(scored_candidate)
        if strongest_factor is not None:
            reasons.append(f"Strongest ranking factor: {strongest_factor}.")
        if relaxation_result.applied and relaxation_result.notes:
            reasons.append("Still surfaced after controlled constraint relaxation.")
        elif record.safety_rating is not None:
            reasons.append(
                f"Safety information is available with a {record.safety_rating} rating."
            )
        else:
            reasons.append(
                "Fits the budget and practicality needs even though some metadata is incomplete."
            )
        return reasons[:4]

    def _build_tradeoff(
        self,
        *,
        scored_candidate: ScoredCandidate,
        normalization_result: NormalizationResult,
        relaxation_result: RelaxationResult,
    ) -> str:
        record = scored_candidate.record
        requested_budget_max = normalization_result.hard_constraints.budget_max
        if record.price_max > requested_budget_max:
            return "Higher variants may stretch beyond the preferred budget ceiling."
        if scored_candidate.weak_match_flags:
            return scored_candidate.weak_match_flags[0].message
        if relaxation_result.applied and relaxation_result.notes:
            return "Recommendation required relaxing some preferences to expand the shortlist."
        if record.safety_rating is None:
            return "Safety rating data is not available in the current catalog."
        if normalization_result.hard_constraints.required_features:
            return "Some desirable variants may require flexibility on feature availability."
        return "Exact trim-level suitability may vary across variants."

    def _build_alternative_notes(
        self,
        *,
        alternatives: list[RecommendationItem],
        relaxation_result: RelaxationResult,
        ranking_result: RankingResult,
    ) -> list[str]:
        notes: list[str] = []
        if alternatives:
            notes.append(
                "Alternatives are included for shortlist comparison if you want to trade off price, safety, or feature fit."
            )
        if relaxation_result.applied:
            notes.append(
                "Some alternatives may reflect a slightly broader constraint set after controlled relaxation."
            )
        weak_alternatives = sum(
            1
            for candidate in ranking_result.ranked_candidates[3:5]
            if candidate.weak_match_flags
        )
        if weak_alternatives:
            notes.append(
                f"{weak_alternatives} alternative suggestions were flagged as weaker matches."
            )
        return notes

    def _strongest_factor_label(self, scored_candidate: ScoredCandidate) -> str | None:
        if not scored_candidate.score_breakdown:
            return None
        strongest_factor = max(
            scored_candidate.score_breakdown,
            key=lambda factor: factor.weight * factor.score,
        )
        return strongest_factor.name.replace("_", " ")
