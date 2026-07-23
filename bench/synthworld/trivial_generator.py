"""
Trivial Enumerating Theory Generator.

Enumerates all hypotheses (cause c, effect e, lag 1) for c in candidate_causes, e in effects.
NO LLM anywhere in the benchmark path.
"""
from typing import List, Dict, Any, Tuple
from cognition.schemas.identity import build_structural_id


class EnumerateHypothesis:
    """Deterministic structured hypothesis representing (cause c, effect e, lag 1)."""

    def __init__(self, cause: str, effect: str, day: int = 0, ordinal: int = 0):
        self.cause = cause
        self.effect = effect
        self.structural_id = build_structural_id(day, "theory", ordinal)
        self.trigger_field = cause
        self.trigger_value = 1
        self.target_field = effect
        self.target_value = 1

    def __repr__(self) -> str:
        return f"<EnumerateHypothesis {self.structural_id}: {self.cause} -> {self.effect}>"


class TrivialTheoryGenerator:
    """Enumerates hypotheses deterministically without LLM calls."""

    def __init__(self, candidate_causes: List[str], effects: List[str]):
        self.candidate_causes = list(candidate_causes)
        self.effects = list(effects)

    def generate_all(self, day: int = 0) -> List[EnumerateHypothesis]:
        hypotheses: List[EnumerateHypothesis] = []
        ordinal = 0
        for c in self.candidate_causes:
            for e in self.effects:
                hyp = EnumerateHypothesis(cause=c, effect=e, day=day, ordinal=ordinal)
                hypotheses.append(hyp)
                ordinal += 1
        return hypotheses
