from app.schemas.catalog import CarCatalogRecord
from app.schemas.filtering import (
    CandidateCountSummary,
    CandidateFilteringResult,
    FilterRejectionReason,
)
from app.schemas.normalization import HardConstraints


class CandidateFilteringService:
    """Applies hard constraints to eliminate unsuitable catalog records."""

    def filter_candidates(
        self,
        *,
        hard_constraints: HardConstraints,
        records: list[CarCatalogRecord],
    ) -> CandidateFilteringResult:
        candidates: list[CarCatalogRecord] = []
        rejection_reasons: list[FilterRejectionReason] = []

        for record in records:
            reasons = self._collect_rejection_reasons(record, hard_constraints)
            if reasons:
                rejection_reasons.append(
                    FilterRejectionReason(
                        make=record.make,
                        model=record.model,
                        reasons=reasons,
                    )
                )
            else:
                candidates.append(record)

        return CandidateFilteringResult(
            hard_constraints=hard_constraints,
            candidates=candidates,
            rejection_reasons=rejection_reasons,
            summary=CandidateCountSummary(
                total_records=len(records),
                candidate_count=len(candidates),
                rejected_count=len(rejection_reasons),
            ),
        )

    def _collect_rejection_reasons(
        self,
        record: CarCatalogRecord,
        hard_constraints: HardConstraints,
    ) -> list[str]:
        reasons: list[str] = []

        if record.price_max < hard_constraints.budget_min:
            reasons.append("Below the requested budget band.")
        if record.price_min > hard_constraints.budget_max:
            reasons.append("Above the requested budget ceiling.")
        if record.seating < hard_constraints.seating_min:
            reasons.append("Does not meet the required seating capacity.")
        if (
            hard_constraints.body_type is not None
            and record.body_type != hard_constraints.body_type
        ):
            reasons.append("Body type does not match the hard constraint.")
        if (
            hard_constraints.fuel_type is not None
            and record.fuel_type != hard_constraints.fuel_type
        ):
            reasons.append("Fuel type does not match the hard constraint.")
        if (
            hard_constraints.transmission is not None
            and record.transmission != hard_constraints.transmission
        ):
            reasons.append("Transmission does not match the hard constraint.")
        if (
            hard_constraints.inventory_type is not None
            and record.inventory_type != hard_constraints.inventory_type
        ):
            reasons.append("Inventory type does not match the hard constraint.")
        if hard_constraints.excluded_brands and record.make.lower() in {
            brand.lower() for brand in hard_constraints.excluded_brands
        }:
            reasons.append("Brand is explicitly excluded.")
        if hard_constraints.required_features:
            missing_features = [
                feature.value
                for feature in hard_constraints.required_features
                if feature not in record.available_features
            ]
            if missing_features:
                reasons.append(
                    "Missing required features: " + ", ".join(missing_features) + "."
                )

        return reasons
