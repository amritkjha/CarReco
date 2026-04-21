from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MonitoringEvent(BaseModel):
    event_type: str
    request_id: str | None = None
    session_id: str | None = None
    level: str = Field(default="INFO")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, object] = Field(default_factory=dict)


class MonitoringMetrics(BaseModel):
    total_requests: int = 0
    follow_up_responses: int = 0
    recommendation_responses: int = 0
    validation_failures: int = 0
    low_result_scenarios: int = 0
    weak_match_scenarios: int = 0
    relaxations_applied: int = 0


class MonitoringAlert(BaseModel):
    code: str
    message: str
