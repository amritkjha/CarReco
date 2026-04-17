from app.schemas.catalog import CarCatalogRecord
from app.schemas.filtering import CandidateFilteringResult
from app.schemas.normalization import HardConstraints, NormalizationResult
from app.schemas.relaxation import RelaxationResult
from app.schemas.scoring import RankingResult
from app.services.candidate_filtering import CandidateFilteringService
from app.services.scoring_ranking import ScoringRankingService


class ConstraintRelaxationService:
    """Relaxes constraints in a controlled order when matches are too few or too weak."""

    def __init__(self) -> None:
        self.candidate_filter = CandidateFilteringService()
        self.scoring_ranking = ScoringRankingService()

    def relax(
        self,
        *,
        normalization_result: NormalizationResult,
        filtering_result: CandidateFilteringResult,
        ranking_result: RankingResult,
        catalog_records: list[CarCatalogRecord],
    ) -> RelaxationResult:
        if not self._should_relax(filtering_result, ranking_result):
            return RelaxationResult(
                applied=False,
                relaxed_normalization_result=normalization_result,
                relaxed_hard_constraints=normalization_result.hard_constraints,
                notes=[],
                expanded_candidates=[],
            )

        attempts = [
            ("required features", self._drop_required_features),
            ("body type", self._drop_body_type),
            ("fuel type", self._drop_fuel_type),
            ("transmission", self._drop_transmission),
        ]

        current_constraints = normalization_result.hard_constraints
        notes: list[str] = []

        for label, relaxer in attempts:
            relaxed_constraints = relaxer(current_constraints)
            if relaxed_constraints == current_constraints:
                continue

            relaxed_normalization = normalization_result.model_copy(
                update={"hard_constraints": relaxed_constraints}
            )
            relaxed_filtering = self.candidate_filter.filter_candidates(
                hard_constraints=relaxed_constraints,
                records=catalog_records,
            )
            relaxed_ranking = self.scoring_ranking.rank_candidates(
                normalization_result=relaxed_normalization,
                filtering_result=relaxed_filtering,
            )
            notes.append(f"Relaxed {label} to expand the candidate pool.")

            if self._is_improved(
                original_filtering=filtering_result,
                relaxed_filtering=relaxed_filtering,
                relaxed_ranking=relaxed_ranking,
            ):
                return RelaxationResult(
                    applied=True,
                    relaxed_normalization_result=relaxed_normalization,
                    relaxed_hard_constraints=relaxed_constraints,
                    notes=notes,
                    expanded_candidates=relaxed_filtering.candidates,
                )

            current_constraints = relaxed_constraints

        return RelaxationResult(
            applied=bool(notes),
            relaxed_normalization_result=normalization_result.model_copy(
                update={"hard_constraints": current_constraints}
            ),
            relaxed_hard_constraints=current_constraints,
            notes=notes,
            expanded_candidates=[],
        )

    def _should_relax(
        self,
        filtering_result: CandidateFilteringResult,
        ranking_result: RankingResult,
    ) -> bool:
        if filtering_result.summary.candidate_count == 0:
            return True
        if filtering_result.summary.candidate_count < 3:
            return True
        if ranking_result.ranked_candidates and ranking_result.ranked_candidates[0].final_score < 0.6:
            return True
        return False

    def _is_improved(
        self,
        *,
        original_filtering: CandidateFilteringResult,
        relaxed_filtering: CandidateFilteringResult,
        relaxed_ranking: RankingResult,
    ) -> bool:
        if relaxed_filtering.summary.candidate_count > original_filtering.summary.candidate_count:
            return True
        if relaxed_ranking.ranked_candidates and relaxed_ranking.ranked_candidates[0].final_score >= 0.6:
            return True
        return False

    def _drop_required_features(self, constraints: HardConstraints) -> HardConstraints:
        return constraints.model_copy(update={"required_features": []})

    def _drop_body_type(self, constraints: HardConstraints) -> HardConstraints:
        return constraints.model_copy(update={"body_type": None})

    def _drop_fuel_type(self, constraints: HardConstraints) -> HardConstraints:
        return constraints.model_copy(update={"fuel_type": None})

    def _drop_transmission(self, constraints: HardConstraints) -> HardConstraints:
        return constraints.model_copy(update={"transmission": None})
