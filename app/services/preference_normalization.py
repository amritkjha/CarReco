from app.schemas.normalization import (
    AmbiguityFlag,
    HardConstraints,
    NormalizationResult,
    NormalizedPreferenceObject,
    SoftPreferenceWeight,
)
from app.schemas.recommendation import (
    BodyType,
    FeatureName,
    FuelType,
    RecommendationRequest,
    TransmissionType,
)


class PreferenceNormalizationService:
    """Converts validated request data into a normalized internal preference model."""

    def normalize(self, request: RecommendationRequest) -> NormalizationResult:
        preferences = request.preferences
        if (
            preferences.budget_range is None
            or preferences.primary_use_case is None
            or preferences.seating_requirement is None
        ):
            raise ValueError(
                "Preference normalization requires validated critical inputs."
            )

        ambiguity_flags = self._build_ambiguity_flags(request)
        free_text_signals = self._extract_free_text_signals(preferences.notes)
        transmission_preference = self._normalize_transmission(request)
        body_type = self._normalize_body_type(request)
        fuel_type = self._normalize_fuel_type(request)

        normalized_preferences = NormalizedPreferenceObject(
            budget_range=preferences.budget_range,
            primary_use_case=preferences.primary_use_case,
            preferred_body_type=body_type,
            seating_requirement=preferences.seating_requirement,
            fuel_preference=fuel_type,
            transmission_preference=transmission_preference,
            inventory_type=self._normalize_inventory_type(request),
            preferred_brands=preferences.preferred_brands,
            excluded_brands=preferences.excluded_brands,
            must_have_features=preferences.must_have_features,
            safety_priority_weight=self._normalize_priority(preferences.safety_priority),
            efficiency_priority_weight=self._normalize_priority(
                preferences.efficiency_priority
            ),
            boot_space_priority_weight=self._normalize_priority(
                preferences.boot_space_priority
            ),
            performance_priority_weight=self._normalize_priority(
                preferences.performance_priority
            ),
            city_or_region=preferences.city_or_region,
            free_text_signals=free_text_signals,
        )

        hard_constraints = HardConstraints(
            budget_min=preferences.budget_range.min_price,
            budget_max=preferences.budget_range.max_price,
            seating_min=preferences.seating_requirement,
            body_type=body_type,
            fuel_type=fuel_type,
            transmission=transmission_preference,
            inventory_type=self._normalize_inventory_type(request),
            excluded_brands=preferences.excluded_brands,
            required_features=preferences.must_have_features,
        )

        soft_preferences = self._build_soft_preferences(
            normalized_preferences=normalized_preferences
        )

        return NormalizationResult(
            source_payload=request,
            normalized_preferences=normalized_preferences,
            hard_constraints=hard_constraints,
            soft_preferences=soft_preferences,
            ambiguity_flags=ambiguity_flags,
        )

    def _normalize_body_type(
        self, request: RecommendationRequest
    ) -> BodyType | None:
        body_type = request.preferences.preferred_body_type
        if body_type in (None, BodyType.NO_PREFERENCE):
            return None
        return body_type

    def _normalize_fuel_type(
        self, request: RecommendationRequest
    ) -> FuelType | None:
        fuel_type = request.preferences.fuel_preference
        if fuel_type in (None, FuelType.NO_PREFERENCE):
            return None
        return fuel_type

    def _normalize_inventory_type(self, request: RecommendationRequest):
        inventory_type = request.preferences.inventory_type
        if inventory_type is None or inventory_type.value == "no_preference":
            return None
        return inventory_type

    def _normalize_transmission(
        self, request: RecommendationRequest
    ) -> TransmissionType | None:
        transmission = request.preferences.transmission_preference
        if transmission is not None and transmission != TransmissionType.NO_PREFERENCE:
            return transmission

        notes = (request.preferences.notes or "").lower()
        if "automatic" in notes or "auto" in notes:
            return TransmissionType.AUTOMATIC
        if "manual" in notes:
            return TransmissionType.MANUAL
        return None

    def _normalize_priority(self, priority: int | None) -> float | None:
        if priority is None:
            return None
        return round(priority / 5, 2)

    def _extract_free_text_signals(self, notes: str | None) -> list[str]:
        if not notes:
            return []

        lowered = notes.lower()
        signals: list[str] = []
        if "mileage" in lowered or "fuel efficient" in lowered or "efficiency" in lowered:
            signals.append("efficiency_priority")
        if "safety" in lowered:
            signals.append("safety_priority")
        if "performance" in lowered or "power" in lowered:
            signals.append("performance_priority")
        if "boot" in lowered or "luggage" in lowered:
            signals.append("boot_space_priority")
        if "sunroof" in lowered:
            signals.append("feature:sunroof")
        if "adas" in lowered:
            signals.append("feature:adas")
        return signals

    def _build_soft_preferences(
        self,
        *,
        normalized_preferences: NormalizedPreferenceObject,
    ) -> list[SoftPreferenceWeight]:
        preferences: list[SoftPreferenceWeight] = [
            SoftPreferenceWeight(
                name="use_case_fit",
                weight=1.0,
                source="validated_input",
            )
        ]

        priority_mappings = [
            (
                "safety_fit",
                normalized_preferences.safety_priority_weight,
                "structured_priority",
            ),
            (
                "efficiency_fit",
                normalized_preferences.efficiency_priority_weight,
                "structured_priority",
            ),
            (
                "boot_space_fit",
                normalized_preferences.boot_space_priority_weight,
                "structured_priority",
            ),
            (
                "performance_fit",
                normalized_preferences.performance_priority_weight,
                "structured_priority",
            ),
        ]

        for name, weight, source in priority_mappings:
            if weight is not None:
                preferences.append(
                    SoftPreferenceWeight(name=name, weight=weight, source=source)
                )

        if normalized_preferences.preferred_brands:
            preferences.append(
                SoftPreferenceWeight(
                    name="preferred_brand_fit",
                    weight=0.75,
                    source="structured_input",
                )
            )

        if normalized_preferences.must_have_features:
            preferences.append(
                SoftPreferenceWeight(
                    name="feature_fit",
                    weight=0.85,
                    source="structured_input",
                )
            )

        inferred_signal_weights = {
            "efficiency_priority": 0.7,
            "safety_priority": 0.7,
            "performance_priority": 0.65,
            "boot_space_priority": 0.65,
            "feature:sunroof": 0.6,
            "feature:adas": 0.7,
        }

        for signal in normalized_preferences.free_text_signals:
            weight = inferred_signal_weights.get(signal)
            if weight is None:
                continue
            preferences.append(
                SoftPreferenceWeight(
                    name=signal,
                    weight=weight,
                    source="free_text_inference",
                )
            )

        return preferences

    def _build_ambiguity_flags(
        self, request: RecommendationRequest
    ) -> list[AmbiguityFlag]:
        notes = (request.preferences.notes or "").lower()
        flags: list[AmbiguityFlag] = []

        if "city" in notes and "highway" in notes:
            flags.append(
                AmbiguityFlag(
                    field="notes",
                    code="mixed_use_language",
                    message=(
                        "Free-text notes mention both city and highway usage. The structured primary use case remains the source of truth."
                    ),
                    confidence=0.58,
                )
            )

        if request.preferences.transmission_preference is None:
            if "automatic" in notes or "auto" in notes:
                flags.append(
                    AmbiguityFlag(
                        field="transmission_preference",
                        code="transmission_inferred_from_notes",
                        message="Transmission preference was inferred from free-text notes.",
                        confidence=0.74,
                    )
                )
            if "manual" in notes:
                flags.append(
                    AmbiguityFlag(
                        field="transmission_preference",
                        code="transmission_inferred_from_notes",
                        message="Transmission preference was inferred from free-text notes.",
                        confidence=0.74,
                    )
                )

        if (
            request.preferences.efficiency_priority is None
            and ("mileage" in notes or "fuel efficient" in notes)
        ):
            flags.append(
                AmbiguityFlag(
                    field="efficiency_priority",
                    code="priority_inferred_from_notes",
                    message="Efficiency preference was inferred from free-text notes.",
                    confidence=0.68,
                )
            )

        return flags
