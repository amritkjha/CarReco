from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationRequest


class MissingFieldFlag(BaseModel):
    field: str
    code: str
    message: str


class ValidationIssue(BaseModel):
    field: str | None = None
    code: str
    message: str


class InputValidationResult(BaseModel):
    validated_payload: RecommendationRequest
    missing_fields: list[MissingFieldFlag] = Field(default_factory=list)
    validation_errors: list[ValidationIssue] = Field(default_factory=list)
    is_valid: bool
    requires_follow_up: bool
