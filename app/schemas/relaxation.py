from pydantic import BaseModel, Field

from app.schemas.catalog import CarCatalogRecord
from app.schemas.normalization import HardConstraints, NormalizationResult


class RelaxationResult(BaseModel):
    applied: bool
    relaxed_normalization_result: NormalizationResult
    relaxed_hard_constraints: HardConstraints
    notes: list[str] = Field(default_factory=list)
    expanded_candidates: list[CarCatalogRecord] = Field(default_factory=list)
