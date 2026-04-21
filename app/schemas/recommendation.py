from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.orchestration import WorkflowStatus


class PrimaryUseCase(str, Enum):
    CITY_COMMUTE = "city_commute"
    FAMILY_USE = "family_use"
    HIGHWAY_TRAVEL = "highway_travel"
    OFF_ROAD = "off_road"
    MIXED_USE = "mixed_use"


class BodyType(str, Enum):
    HATCHBACK = "hatchback"
    SEDAN = "sedan"
    SUV = "suv"
    MUV = "muv"
    PICKUP = "pickup"
    NO_PREFERENCE = "no_preference"


class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    EV = "ev"
    NO_PREFERENCE = "no_preference"


class TransmissionType(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    NO_PREFERENCE = "no_preference"


class InventoryType(str, Enum):
    NEW = "new"
    USED = "used"
    NO_PREFERENCE = "no_preference"


class FeatureName(str, Enum):
    ADAS = "adas"
    SUNROOF = "sunroof"
    REAR_CAMERA = "rear_camera"
    CONNECTED_FEATURES = "connected_features"
    AUTOMATIC_CLIMATE_CONTROL = "automatic_climate_control"


class BudgetRange(BaseModel):
    min_price: int = Field(ge=0, description="Minimum budget in local currency.")
    max_price: int = Field(gt=0, description="Maximum budget in local currency.")

    @model_validator(mode="after")
    def validate_budget_bounds(self) -> "BudgetRange":
        if self.min_price > self.max_price:
            raise ValueError("min_price cannot be greater than max_price")
        return self


class RequestMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    request_id: str | None = Field(default=None, min_length=1, max_length=128)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Client-side or server-generated request timestamp.",
    )


class RecommendationPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_range: BudgetRange | None = None
    primary_use_case: PrimaryUseCase | None = None
    preferred_body_type: BodyType | None = None
    seating_requirement: int | None = Field(default=None, ge=1, le=9)
    fuel_preference: FuelType | None = None
    transmission_preference: TransmissionType | None = None
    inventory_type: InventoryType | None = None
    preferred_brands: list[str] = Field(default_factory=list, max_length=10)
    excluded_brands: list[str] = Field(default_factory=list, max_length=10)
    safety_priority: int | None = Field(default=None, ge=1, le=5)
    efficiency_priority: int | None = Field(default=None, ge=1, le=5)
    boot_space_priority: int | None = Field(default=None, ge=1, le=5)
    performance_priority: int | None = Field(default=None, ge=1, le=5)
    annual_driving_distance_km: int | None = Field(default=None, ge=0, le=200000)
    city_or_region: str | None = Field(default=None, min_length=2, max_length=120)
    must_have_features: list[FeatureName] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("preferred_brands", "excluded_brands")
    @classmethod
    def normalize_brands(cls, brands: list[str]) -> list[str]:
        normalized = []
        seen: set[str] = set()
        for brand in brands:
            cleaned = brand.strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered not in seen:
                seen.add(lowered)
                normalized.append(cleaned)
        return normalized


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: RequestMetadata = Field(default_factory=RequestMetadata)
    preferences: RecommendationPreferences


class CarSummary(BaseModel):
    make: str
    model: str
    body_type: BodyType
    fuel_type: FuelType
    transmission: TransmissionType
    seating: int
    mileage_or_range: str
    safety_rating: str | None = None


class RecommendationItem(BaseModel):
    rank: int = Field(ge=1)
    match_score: float = Field(ge=0, le=1)
    price_range: str
    reasons: list[str] = Field(min_length=1, max_length=4)
    tradeoff: str
    summary: CarSummary


class FollowUpQuestion(BaseModel):
    code: str
    question: str


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem] = Field(default_factory=list, max_length=5)
    alternatives: list[RecommendationItem] = Field(default_factory=list, max_length=3)
    alternative_notes: list[str] = Field(default_factory=list)
    system_notes: list[str] = Field(default_factory=list)
    follow_up_question: FollowUpQuestion | None = None
    workflow_status: WorkflowStatus
    reason_codes: list[str] = Field(default_factory=list)
    request_id: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_response_shape(self) -> "RecommendationResponse":
        if not self.recommendations and self.follow_up_question is None:
            raise ValueError(
                "Response must include recommendations or a follow-up question"
            )
        return self
