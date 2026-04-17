from app.schemas.catalog import CarCatalogRecord
from app.schemas.filtering import CandidateFilteringResult
from app.schemas.normalization import NormalizationResult
from app.schemas.recommendation import BodyType, FuelType, PrimaryUseCase
from app.schemas.scoring import RankingResult, ScoreFactor, ScoredCandidate, WeakMatchFlag


class ScoringRankingService:
    """Scores and ranks candidate cars using simple weighted MVP logic."""

    def rank_candidates(
        self,
        *,
        normalization_result: NormalizationResult,
        filtering_result: CandidateFilteringResult,
    ) -> RankingResult:
        scored_candidates = [
            self._score_candidate(record, normalization_result)
            for record in filtering_result.candidates
        ]
        ranked_candidates = sorted(
            scored_candidates,
            key=lambda candidate: candidate.final_score,
            reverse=True,
        )
        return RankingResult(ranked_candidates=ranked_candidates)

    def _score_candidate(
        self,
        record: CarCatalogRecord,
        normalization_result: NormalizationResult,
    ) -> ScoredCandidate:
        factors = [
            self._budget_fit(record, normalization_result),
            self._use_case_fit(record, normalization_result),
            self._safety_fit(record, normalization_result),
            self._feature_fit(record, normalization_result),
            self._brand_fit(record, normalization_result),
            self._efficiency_fit(record, normalization_result),
        ]

        weighted_sum = sum(factor.weight * factor.score for factor in factors)
        total_weight = sum(factor.weight for factor in factors)
        final_score = round(weighted_sum / total_weight, 2) if total_weight else 0.0

        weak_match_flags: list[WeakMatchFlag] = []
        if final_score < 0.6:
            weak_match_flags.append(
                WeakMatchFlag(
                    code="weak_match_score",
                    message="Overall score is below the strong-match threshold.",
                )
            )
        if record.safety_rating is None:
            weak_match_flags.append(
                WeakMatchFlag(
                    code="limited_safety_metadata",
                    message="Safety metadata is incomplete for this candidate.",
                )
            )

        return ScoredCandidate(
            record=record,
            final_score=final_score,
            score_breakdown=factors,
            weak_match_flags=weak_match_flags,
        )

    def _budget_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        budget = normalization_result.normalized_preferences.budget_range
        requested_midpoint = (budget.min_price + budget.max_price) / 2
        record_midpoint = (record.price_min + record.price_max) / 2
        distance_ratio = abs(record_midpoint - requested_midpoint) / max(requested_midpoint, 1)
        score = max(0.0, 1 - distance_ratio)
        return ScoreFactor(name="budget_fit", weight=0.25, score=round(score, 2))

    def _use_case_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        use_case = normalization_result.normalized_preferences.primary_use_case
        score = {
            PrimaryUseCase.CITY_COMMUTE: self._city_score(record),
            PrimaryUseCase.FAMILY_USE: self._family_score(record),
            PrimaryUseCase.HIGHWAY_TRAVEL: self._highway_score(record),
            PrimaryUseCase.OFF_ROAD: self._off_road_score(record),
            PrimaryUseCase.MIXED_USE: self._mixed_use_score(record),
        }[use_case]
        return ScoreFactor(name="use_case_fit", weight=0.3, score=round(score, 2))

    def _safety_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        weight = self._weight_from_soft_preferences(
            normalization_result,
            "safety_fit",
            default=0.1,
        )
        rating_map = {
            "5-star": 1.0,
            "4-star": 0.8,
            "3-star": 0.6,
        }
        score = rating_map.get(record.safety_rating or "", 0.45)
        return ScoreFactor(name="safety_fit", weight=weight, score=round(score, 2))

    def _feature_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        required = normalization_result.normalized_preferences.must_have_features
        if not required:
            return ScoreFactor(name="feature_fit", weight=0.05, score=0.7)
        matched = sum(1 for feature in required if feature in record.available_features)
        score = matched / len(required)
        return ScoreFactor(name="feature_fit", weight=0.12, score=round(score, 2))

    def _brand_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        preferred_brands = {
            brand.lower()
            for brand in normalization_result.normalized_preferences.preferred_brands
        }
        score = 1.0 if record.make.lower() in preferred_brands else 0.55
        weight = 0.1 if preferred_brands else 0.04
        return ScoreFactor(name="brand_fit", weight=weight, score=round(score, 2))

    def _efficiency_fit(
        self, record: CarCatalogRecord, normalization_result: NormalizationResult
    ) -> ScoreFactor:
        weight = self._weight_from_soft_preferences(
            normalization_result,
            "efficiency_fit",
            default=0.08,
        )
        score = 0.65
        if record.annual_running_cost_band == "low":
            score = 1.0
        elif record.annual_running_cost_band == "medium":
            score = 0.75
        elif record.annual_running_cost_band == "high":
            score = 0.5

        if record.fuel_type == FuelType.EV:
            score = min(1.0, score + 0.1)
        elif record.fuel_type == FuelType.HYBRID:
            score = min(1.0, score + 0.05)

        return ScoreFactor(name="efficiency_fit", weight=weight, score=round(score, 2))

    def _weight_from_soft_preferences(
        self,
        normalization_result: NormalizationResult,
        factor_name: str,
        *,
        default: float,
    ) -> float:
        for preference in normalization_result.soft_preferences:
            if preference.name == factor_name:
                return preference.weight
        return default

    def _city_score(self, record: CarCatalogRecord) -> float:
        if record.body_type == BodyType.HATCHBACK or record.fuel_type == FuelType.EV:
            return 1.0
        if record.body_type in {BodyType.SEDAN, BodyType.SUV}:
            return 0.78
        return 0.65

    def _family_score(self, record: CarCatalogRecord) -> float:
        if record.seating >= 7 or record.body_type in {BodyType.SUV, BodyType.MUV}:
            return 1.0
        if record.seating >= 5:
            return 0.82
        return 0.6

    def _highway_score(self, record: CarCatalogRecord) -> float:
        if record.body_type in {BodyType.SEDAN, BodyType.SUV, BodyType.MUV}:
            return 0.92
        return 0.7

    def _off_road_score(self, record: CarCatalogRecord) -> float:
        if record.body_type == BodyType.SUV and record.fuel_type in {
            FuelType.DIESEL,
            FuelType.PETROL,
        }:
            return 1.0
        if record.body_type == BodyType.MUV:
            return 0.72
        return 0.45

    def _mixed_use_score(self, record: CarCatalogRecord) -> float:
        if record.body_type in {BodyType.SUV, BodyType.SEDAN}:
            return 0.9
        if record.body_type == BodyType.HATCHBACK:
            return 0.75
        return 0.7
