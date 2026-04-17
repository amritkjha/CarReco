from pydantic import BaseModel, Field

from app.schemas.catalog import CarCatalogRecord


class ScoreFactor(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)


class WeakMatchFlag(BaseModel):
    code: str
    message: str


class ScoredCandidate(BaseModel):
    record: CarCatalogRecord
    final_score: float = Field(ge=0, le=1)
    score_breakdown: list[ScoreFactor] = Field(default_factory=list)
    weak_match_flags: list[WeakMatchFlag] = Field(default_factory=list)


class RankingResult(BaseModel):
    ranked_candidates: list[ScoredCandidate] = Field(default_factory=list)
