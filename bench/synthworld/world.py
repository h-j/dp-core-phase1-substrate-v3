"""
Synthworld Benchmark World Scenarios.

Scenarios:
- S1 (Clean): Cause c1 -> e1 (lag 1)
- S2 (Spurious/Decoy): Cause c1 -> e1, decoy c2 co-occurs without causality
- S3 (Regime Flip): Cause c1 -> e1 for t < 100; flips to c2 -> e1 for t >= 100
- S4 (Scoped Rule): Cause c1 -> e1 ONLY when scope condition s1 == 1 holds
"""
import random
from typing import Dict, List, Optional


class SynthWorldScenario:
    def __init__(
        self,
        scenario_id: str = "S1",
        causes: Optional[List[str]] = None,
        effects_list: Optional[List[str]] = None,
        seed: int = 42,
    ):
        self.scenario_id = scenario_id
        self._causes = causes if causes else ["c1", "c2", "c3", "c4"]
        self._effects = effects_list if effects_list else ["e1"]
        self.rng = random.Random(seed)
        self.active_regime = 1

    def candidate_causes(self) -> List[str]:
        return list(self._causes)

    def effects(self) -> List[str]:
        return list(self._effects)

    def generate_step(self, t: int, prior_events: Optional[Dict[str, int]] = None) -> Dict[str, int]:
        events = {c: 0 for c in self._causes}
        for e in self._effects:
            events[e] = 0

        if self.scenario_id == "S1":
            # Clean cause c1 fires 30% of time
            if self.rng.random() < 0.30:
                events["c1"] = 1
            # Random noise for c2, c3, c4
            for c in ["c2", "c3", "c4"]:
                if c in events and self.rng.random() < 0.20:
                    events[c] = 1

            # Effect e1 fires at t if c1 fired at t-1
            if prior_events and prior_events.get("c1", 0) == 1:
                events["e1"] = 1

        elif self.scenario_id == "S2":
            # Spurious decoy: c1 fires 30% of time; c2 co-occurs 90% of the time with c1
            if self.rng.random() < 0.30:
                events["c1"] = 1
                if self.rng.random() < 0.90:
                    events["c2"] = 1
            for c in ["c3", "c4"]:
                if c in events and self.rng.random() < 0.20:
                    events[c] = 1

            if prior_events and prior_events.get("c1", 0) == 1:
                events["e1"] = 1

        elif self.scenario_id == "S3":
            # Regime flip at t = 100
            if t >= 100:
                self.active_regime = 2
            else:
                self.active_regime = 1

            if self.rng.random() < 0.30:
                events["c1"] = 1
            if self.rng.random() < 0.30:
                events["c2"] = 1
            for c in ["c3", "c4"]:
                if c in events and self.rng.random() < 0.20:
                    events[c] = 1

            if prior_events:
                if self.active_regime == 1 and prior_events.get("c1", 0) == 1:
                    events["e1"] = 1
                elif self.active_regime == 2 and prior_events.get("c2", 0) == 1:
                    events["e1"] = 1

        elif self.scenario_id == "S4":
            # Scoped rule: c1 -> e1 ONLY when scope condition s1 == 1 holds
            if "s1" not in events:
                events["s1"] = 0
            if self.rng.random() < 0.50:
                events["s1"] = 1

            if self.rng.random() < 0.30:
                events["c1"] = 1
            for c in ["c2", "c3", "c4"]:
                if c in events and self.rng.random() < 0.20:
                    events[c] = 1

            if prior_events and prior_events.get("s1", 0) == 1 and prior_events.get("c1", 0) == 1:
                events["e1"] = 1

        return events

    def ground_truth_causes(self, t: int) -> List[str]:
        if self.scenario_id in ("S1", "S2"):
            return ["c1"]
        elif self.scenario_id == "S3":
            return ["c1"] if t < 100 else ["c2"]
        elif self.scenario_id == "S4":
            return ["c1"]
        return ["c1"]
