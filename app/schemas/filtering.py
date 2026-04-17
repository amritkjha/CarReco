from pydantic import BaseModel, Field

from app.schemas.catalog import CarCatalogRecord
from app.schemas.normalization import HardConstraints


class FilterRejectionReason(BaseModel):
    make: str
    model: str
    reasons: list[str] = Field(default_factory=list)


class CandidateCountSummary(BaseModel):
    total_records: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)


class CandidateFilteringResult(BaseModel):
    hard_constraints: HardConstraints
    candidates: list[CarCatalogRecord] = Field(default_factory=list)
    rejection_reasons: list[FilterRejectionReason] = Field(default_factory=list)
    summary: CandidateCountSummary
