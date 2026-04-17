from app.data.car_catalog import CAR_CATALOG
from app.schemas.catalog import (
    CarCatalogQuery,
    CarCatalogRecord,
    CatalogSearchResult,
    DatasetCoverageIndicator,
)


class CarCatalogService:
    """Provides access to the structured catalog used by the MVP."""

    def __init__(self) -> None:
        self._records = [CarCatalogRecord(**record) for record in CAR_CATALOG]

    def search(self, query: CarCatalogQuery) -> CatalogSearchResult:
        filtered_records = [
            record for record in self._records if self._matches_query(record, query)
        ]

        ranked_records = sorted(
            filtered_records,
            key=lambda record: self._sort_key(record, query),
        )

        limited_records = ranked_records[: query.limit]
        return CatalogSearchResult(
            records=limited_records,
            coverage=self._build_coverage_indicator(filtered_records),
        )

    def list_all(self) -> CatalogSearchResult:
        return CatalogSearchResult(
            records=list(self._records),
            coverage=self._build_coverage_indicator(self._records),
        )

    def _matches_query(self, record: CarCatalogRecord, query: CarCatalogQuery) -> bool:
        if query.body_type is not None and record.body_type != query.body_type:
            return False
        if query.fuel_type is not None and record.fuel_type != query.fuel_type:
            return False
        if query.transmission is not None and record.transmission != query.transmission:
            return False
        if query.inventory_type is not None and record.inventory_type != query.inventory_type:
            return False
        if query.seating_min is not None and record.seating < query.seating_min:
            return False
        if query.budget_min is not None and record.price_max < query.budget_min:
            return False
        if query.budget_max is not None and record.price_min > query.budget_max:
            return False
        if query.excluded_brands and record.make.lower() in {
            brand.lower() for brand in query.excluded_brands
        }:
            return False
        if query.required_features:
            missing_features = [
                feature
                for feature in query.required_features
                if feature not in record.available_features
            ]
            if missing_features:
                return False
        return True

    def _sort_key(
        self, record: CarCatalogRecord, query: CarCatalogQuery
    ) -> tuple[int, int, int, int]:
        preferred_brand_score = 0
        if query.preferred_brands and record.make.lower() in {
            brand.lower() for brand in query.preferred_brands
        }:
            preferred_brand_score = 1

        feature_match_count = len(record.available_features)
        safety_score = 1 if record.safety_rating is not None else 0
        price_midpoint = (record.price_min + record.price_max) // 2

        return (
            -preferred_brand_score,
            -safety_score,
            -feature_match_count,
            price_midpoint,
        )

    def _build_coverage_indicator(
        self, matched_records: list[CarCatalogRecord]
    ) -> DatasetCoverageIndicator:
        total_records = len(self._records)
        matched_count = len(matched_records)
        records_with_safety = sum(
            1 for record in matched_records if record.safety_rating is not None
        )
        records_with_features = sum(
            1 for record in matched_records if record.available_features
        )
        completeness_components = [0.0, 0.0]
        if matched_count > 0:
            completeness_components = [
                records_with_safety / matched_count,
                records_with_features / matched_count,
            ]

        return DatasetCoverageIndicator(
            total_records=total_records,
            matched_records=matched_count,
            records_with_safety_rating=records_with_safety,
            records_with_feature_metadata=records_with_features,
            completeness_ratio=round(sum(completeness_components) / 2, 2),
        )
