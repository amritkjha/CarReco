from pydantic import BaseModel, Field

from app.schemas.recommendation import (
    BodyType,
    FeatureName,
    FuelType,
    InventoryType,
    TransmissionType,
)


class CarCatalogRecord(BaseModel):
    make: str
    model: str
    body_type: BodyType
    fuel_type: FuelType
    transmission: TransmissionType
    inventory_type: InventoryType
    seating: int = Field(ge=1)
    price_min: int = Field(ge=0)
    price_max: int = Field(gt=0)
    mileage_or_range: str
    safety_rating: str | None = None
    available_features: list[FeatureName] = Field(default_factory=list)
    annual_running_cost_band: str | None = None


class CarCatalogQuery(BaseModel):
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    seating_min: int | None = Field(default=None, ge=1)
    body_type: BodyType | None = None
    fuel_type: FuelType | None = None
    transmission: TransmissionType | None = None
    inventory_type: InventoryType | None = None
    preferred_brands: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    required_features: list[FeatureName] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)


class DatasetCoverageIndicator(BaseModel):
    total_records: int = Field(ge=0)
    matched_records: int = Field(ge=0)
    records_with_safety_rating: int = Field(ge=0)
    records_with_feature_metadata: int = Field(ge=0)
    completeness_ratio: float = Field(ge=0, le=1)


class CatalogSearchResult(BaseModel):
    records: list[CarCatalogRecord] = Field(default_factory=list)
    coverage: DatasetCoverageIndicator

