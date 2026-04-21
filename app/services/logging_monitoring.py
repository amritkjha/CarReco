import json
import logging

from app.schemas.monitoring import MonitoringAlert, MonitoringEvent, MonitoringMetrics


class LoggingMonitoringService:
    """Captures structured workflow logs, simple metrics, and alert conditions."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("carreco.monitoring")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            handler.setFormatter(
                logging.Formatter("%(levelname)s:%(name)s:%(message)s")
            )
            self.logger.addHandler(handler)
        self.logger.propagate = False
        self.metrics = MonitoringMetrics()

    def record_request_started(
        self,
        *,
        request_id: str | None,
        session_id: str | None,
    ) -> None:
        self.metrics.total_requests += 1
        self._emit(
            MonitoringEvent(
                event_type="request_started",
                request_id=request_id,
                session_id=session_id,
                payload={},
            )
        )

    def record_follow_up(
        self,
        *,
        request_id: str | None,
        session_id: str | None,
        reason_codes: list[str],
    ) -> None:
        self.metrics.follow_up_responses += 1
        self._emit(
            MonitoringEvent(
                event_type="follow_up_response",
                request_id=request_id,
                session_id=session_id,
                payload={"reason_codes": reason_codes},
            )
        )

    def record_validation_failure(
        self,
        *,
        request_id: str | None,
        session_id: str | None,
        reason_codes: list[str],
    ) -> None:
        self.metrics.validation_failures += 1
        self._emit(
            MonitoringEvent(
                event_type="validation_failure",
                request_id=request_id,
                session_id=session_id,
                level="ERROR",
                payload={"reason_codes": reason_codes},
            )
        )

    def record_recommendation_completed(
        self,
        *,
        request_id: str | None,
        session_id: str | None,
        candidate_count: int,
        top_score: float | None,
        weak_match_count: int,
        relaxation_applied: bool,
        workflow_reason_codes: list[str],
    ) -> list[MonitoringAlert]:
        self.metrics.recommendation_responses += 1
        alerts: list[MonitoringAlert] = []

        if candidate_count < 3:
            self.metrics.low_result_scenarios += 1
            alerts.append(
                MonitoringAlert(
                    code="low_result_scenario",
                    message="Candidate count is below the preferred shortlist threshold.",
                )
            )

        if weak_match_count > 0:
            self.metrics.weak_match_scenarios += 1
            alerts.append(
                MonitoringAlert(
                    code="weak_matches_present",
                    message="One or more ranked candidates were flagged as weak matches.",
                )
            )

        if relaxation_applied:
            self.metrics.relaxations_applied += 1

        self._emit(
            MonitoringEvent(
                event_type="recommendation_completed",
                request_id=request_id,
                session_id=session_id,
                payload={
                    "candidate_count": candidate_count,
                    "top_score": top_score,
                    "weak_match_count": weak_match_count,
                    "relaxation_applied": relaxation_applied,
                    "workflow_reason_codes": workflow_reason_codes,
                    "alerts": [alert.model_dump() for alert in alerts],
                    "metrics_snapshot": self.metrics.model_dump(),
                },
            )
        )
        return alerts

    def _emit(self, event: MonitoringEvent) -> None:
        message = json.dumps(event.model_dump(mode="json"))
        level = event.level.upper()
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
