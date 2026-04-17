from app.schemas.recommendation import RecommendationRequest
from app.schemas.validation import (
    InputValidationResult,
    MissingFieldFlag,
    ValidationIssue,
)


class InputValidationService:
    """Applies business-level validation on top of transport schema checks."""

    def validate(self, request: RecommendationRequest) -> InputValidationResult:
        missing_fields: list[MissingFieldFlag] = []
        validation_errors: list[ValidationIssue] = []
        preferences = request.preferences

        if preferences.budget_range is None:
            missing_fields.append(
                MissingFieldFlag(
                    field="budget_range",
                    code="missing_budget",
                    message="Budget range is required before recommendations can be generated.",
                )
            )

        if preferences.primary_use_case is None:
            missing_fields.append(
                MissingFieldFlag(
                    field="primary_use_case",
                    code="missing_use_case",
                    message="Primary use case is required before recommendations can be generated.",
                )
            )

        if preferences.preferred_body_type is None:
            missing_fields.append(
                MissingFieldFlag(
                    field="preferred_body_type",
                    code="missing_body_type",
                    message="Preferred body type is required before recommendations can be generated.",
                )
            )

        if preferences.seating_requirement is None:
            missing_fields.append(
                MissingFieldFlag(
                    field="seating_requirement",
                    code="missing_seating_requirement",
                    message="Seating requirement is required before recommendations can be generated.",
                )
            )

        if preferences.fuel_preference is None:
            missing_fields.append(
                MissingFieldFlag(
                    field="fuel_preference",
                    code="missing_fuel_preference",
                    message="Fuel preference is required before recommendations can be generated.",
                )
            )

        overlapping_brands = sorted(
            set(brand.lower() for brand in preferences.preferred_brands)
            & set(brand.lower() for brand in preferences.excluded_brands)
        )
        if overlapping_brands:
            validation_errors.append(
                ValidationIssue(
                    field="preferred_brands",
                    code="brand_preference_conflict",
                    message=(
                        "A brand cannot be both preferred and excluded: "
                        + ", ".join(overlapping_brands)
                    ),
                )
            )

        if preferences.notes and "any car" in preferences.notes.lower():
            validation_errors.append(
                ValidationIssue(
                    field="notes",
                    code="broad_preferences",
                    message=(
                        "The request is too broad for ranking. Ask the user to pick a primary use case."
                    ),
                )
            )

        return InputValidationResult(
            validated_payload=request,
            missing_fields=missing_fields,
            validation_errors=validation_errors,
            is_valid=not missing_fields and not validation_errors,
            requires_follow_up=bool(missing_fields or validation_errors),
        )
