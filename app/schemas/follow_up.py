from pydantic import BaseModel, Field

from app.schemas.recommendation import FollowUpQuestion


class FollowUpDecision(BaseModel):
    should_ask: bool
    question: FollowUpQuestion | None = None
    notes: list[str] = Field(default_factory=list)

