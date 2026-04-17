from app.schemas.follow_up import FollowUpDecision
from app.schemas.normalization import AmbiguityFlag, NormalizationResult
from app.schemas.recommendation import FollowUpQuestion
from app.schemas.validation import InputValidationResult, MissingFieldFlag, ValidationIssue


class FollowUpQuestionService:
    """Decides when to ask clarifying questions instead of generating results."""

    def decide(
        self,
        *,
        validation_result: InputValidationResult,
        normalization_result: NormalizationResult | None = None,
    ) -> FollowUpDecision:
        if validation_result.missing_fields:
            missing_field = validation_result.missing_fields[0]
            return FollowUpDecision(
                should_ask=True,
                question=self._question_for_missing_field(missing_field),
                notes=self._build_missing_field_notes(validation_result),
            )

        brand_conflict = self._find_validation_issue(
            validation_result.validation_errors,
            "brand_preference_conflict",
        )
        if brand_conflict is not None:
            return FollowUpDecision(
                should_ask=True,
                question=FollowUpQuestion(
                    code="conflicting_preferences",
                    question=(
                        "You marked the same brand as both preferred and excluded. Should that brand be preferred, excluded, or ignored?"
                    ),
                ),
                notes=[
                    "The request contains conflicting brand preferences.",
                    brand_conflict.message,
                ],
            )

        broad_preference_issue = self._find_validation_issue(
            validation_result.validation_errors,
            "broad_preferences",
        )
        if broad_preference_issue is not None:
            return FollowUpDecision(
                should_ask=True,
                question=FollowUpQuestion(
                    code=broad_preference_issue.code,
                    question=(
                        "Do you want the recommendation optimized for city use, family use, highway travel, or mixed use?"
                    ),
                ),
                notes=[broad_preference_issue.message],
            )

        if normalization_result is not None:
            mixed_use_ambiguity = self._find_ambiguity_flag(
                normalization_result.ambiguity_flags,
                "mixed_use_language",
            )
            if mixed_use_ambiguity is not None:
                return FollowUpDecision(
                    should_ask=True,
                    question=FollowUpQuestion(
                        code="ambiguous_use_case",
                        question=(
                            "Your notes mention both city and highway driving. Which use case should I prioritize most?"
                        ),
                    ),
                    notes=[mixed_use_ambiguity.message],
                )

        return FollowUpDecision(should_ask=False, question=None, notes=[])

    def _question_for_missing_field(
        self, missing_field: MissingFieldFlag
    ) -> FollowUpQuestion:
        question_by_code = {
            "missing_budget": "What is your budget range for the car?",
            "missing_use_case": "What will you use the car for most often: city driving, family use, highway travel, or mixed use?",
            "missing_body_type": "Which body type do you prefer: hatchback, sedan, SUV, MUV, pickup, or no preference?",
            "missing_seating_requirement": "How many seats do you need in the car?",
            "missing_fuel_preference": "Which fuel type do you prefer: petrol, diesel, hybrid, EV, or no preference?",
        }
        return FollowUpQuestion(
            code=missing_field.code,
            question=question_by_code.get(
                missing_field.code,
                "Could you provide the missing details needed to continue?",
            ),
        )

    def _build_missing_field_notes(
        self, validation_result: InputValidationResult
    ) -> list[str]:
        notes = ["Additional input is needed before ranking cars."]
        notes.extend(flag.message for flag in validation_result.missing_fields)
        return notes

    def _find_validation_issue(
        self, issues: list[ValidationIssue], code: str
    ) -> ValidationIssue | None:
        for issue in issues:
            if issue.code == code:
                return issue
        return None

    def _find_ambiguity_flag(
        self, flags: list[AmbiguityFlag], code: str
    ) -> AmbiguityFlag | None:
        for flag in flags:
            if flag.code == code:
                return flag
        return None
