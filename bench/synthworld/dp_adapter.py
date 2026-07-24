"""DP adapter STUB - the integration point for the DP/EkamNet substrate."""
from __future__ import annotations
from .world import Scenario


class DPAdapter:
    name = "DP/EkamNet"

    def __init__(self, scenario: Scenario, substrate=None):
        self.scenario = scenario
        self.substrate = substrate
        if substrate is None:
            raise NotImplementedError(
                "Wire the DP substrate here: experience ingestion in observe(), "
                "belief-consulting prediction in predict(), belief export in "
                "beliefs(). See module docstring for the lifecycle mapping."
            )

    def observe(self, t: int, events: dict[str, int]) -> None:
        raise NotImplementedError

    def predict(self, t: int, events: dict[str, int]) -> dict[str, float]:
        raise NotImplementedError

    def beliefs(self) -> dict[tuple[str, str], float]:
        raise NotImplementedError
