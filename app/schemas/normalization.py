from pydantic import BaseModel, Field

from app.schemas.recommendation import (
    BodyType,
    BudgetRange,
    FeatureName,
    FuelType,
    InventoryType,
    PrimaryUseCase,
    RecommendationRequest,
    TransmissionType,
)


class NormalizedPreferenceObject(BaseModel):
    budget_range: BudgetRange
    primary_use_case: PrimaryUseCase
    preferred_body_type: BodyType | None = None
    seating_requirement: int
    fuel_preference: FuelType | None = None
    transmission_preference: TransmissionType | None = None
    inventory_type: InventoryType | None = None
    preferred_brands: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    must_have_features: list[FeatureName] = Field(default_factory=list)
    safety_priority_weight: float | None = Field(default=None, ge=0, le=1)
    efficiency_priority_weight: float | None = Field(default=None, ge=0, le=1)
    boot_space_priority_weight: float | None = Field(default=None, ge=0, le=1)
    performance_priority_weight: float | None = Field(default=None, ge=0, le=1)
    city_or_region: str | None = None
    free_text_signals: list[str] = Field(default_factory=list)


class HardConstraints(BaseModel):
    budget_min: int = Field(ge=0)
    budget_max: int = Field(gt=0)
    seating_min: int = Field(ge=1)
    body_type: BodyType | None = None
    fuel_type: FuelType | None = None
    transmission: TransmissionType | None = None
    inventory_type: InventoryType | None = None
    excluded_brands: list[str] = Field(default_factory=list)
    required_features: list[FeatureName] = Field(default_factory=list)


class SoftPreferenceWeight(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1)
    source: str


class AmbiguityFlag(BaseModel):
    field: str
    code: str
    message: str
    confidence: float = Field(ge=0, le=1)


class NormalizationResult(BaseModel):
    source_payload: RecommendationRequest
    normalized_preferences: NormalizedPreferenceObject
    hard_constraints: HardConstraints
    soft_preferences: list[SoftPreferenceWeight] = Field(default_factory=list)
    ambiguity_flags: list[AmbiguityFlag] = Field(default_factory=list)
