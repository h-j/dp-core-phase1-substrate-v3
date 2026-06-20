from typing import Any
from market.replay.runtime.cognition_result import CognitionResult


class PersistenceCoordinator:
    """Centralizes repository orchestration for the replay loop."""

    def __init__(self, repos: dict):
        self.repos = repos

    def save_day(self, result: CognitionResult, obs_event: Any):
        """Coordinates saving all cognitive artifacts for a day."""
        # Core Repos
        self.repos["observation"].save(obs_event)
        self.repos["abstraction"].save(result.abstraction)
        self.repos["theory"].save(result.theory)
        self.repos["validation"].save(self._create_validation_event(result))
        self.repos["reflection"].save(result.reflection)
        self.repos["confidence"].save(result.confidence)

        # Analytics Repos
        self.repos["transition_pressure"].save(
            result.transition_pressure, date=result.date, day_index=result.day_index
        )

        self.repos["prediction"].save(
            result.prediction,
            date=result.date,
            day_index=result.day_index,
            theory_id=str(getattr(result.theory, "id", "")),
            reflection_id=str(getattr(result.reflection, "id", "")),
        )

        if result.prior_prediction_result and self.repos.get("prior_prediction_id"):
            self.repos["prediction_result"].save(
                result.prior_prediction_result,
                date=result.date,
                day_index=result.day_index,
                prediction_id=self.repos["prior_prediction_id"],
            )

    def _create_validation_event(self, result: CognitionResult):
        from cognition.schemas.validation.validation_event import ValidationEvent

        return ValidationEvent(
            theory_id=result.theory.id,
            validation_summary=(
                f"Replay validation. Horizon Context: {result.horizon_view.summary()}"
            ),
            observed_behavior=result.observation.observation_text,
            expected_behavior="Market-grounded theory",
        )
