from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationItem


class ExplanationBundle(BaseModel):
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    alternatives: list[RecommendationItem] = Field(default_factory=list)
    alternative_notes: list[str] = Field(default_factory=list)
