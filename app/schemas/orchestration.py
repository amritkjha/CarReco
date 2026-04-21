from enum import Enum

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    FOLLOW_UP_REQUIRED = "follow_up_required"
    RECOMMENDATIONS_READY = "recommendations_ready"


class WorkflowResult(BaseModel):
    status: WorkflowStatus
    reason_codes: list[str] = Field(default_factory=list)
