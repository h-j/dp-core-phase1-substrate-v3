"""
DP Substrate Adapter for Synthworld Benchmark.

Implements 3-method Learner protocol:
1. observe(t, events): Ingest experience, evaluate predicate outcomes from step t-1, evolve ScoredConfidenceEngine.
2. predict(t, events): Return P(effect at t+1) via noisy-OR over active causes' promoted theory confidences.
3. beliefs(): Return map of (cause, effect) -> Beta posterior expectation E[Beta].

Instrumentation:
Records every belief read during predict() to ConsultationLedger with role="gate".
"""
import math
from typing import Dict, List, Tuple, Any, Optional

from bench.synthworld.learners import Learner
from bench.synthworld.trivial_generator import TrivialTheoryGenerator, EnumerateHypothesis
from bench.synthworld.world import SynthWorldScenario
from cognition.confidence.scored_confidence_engine import ScoredConfidenceEngine
from cognition.schemas.confidence.confidence_state import ConfidenceState
from dp.observability.consultation_ledger import (
    record_consultation,
    record_decision,
)


class DPAdapter(Learner):
    """
    DP Substrate Benchmark Adapter.

    Tiers:
    - Established Promotion Tier: Beta posterior expectation E[Beta] >= 0.50 (maps to ACTIVE / STABLE tier).
    Only theories at or above this promotion tier contribute to noisy-OR prediction during predict().
    """

    def __init__(self, scenario: SynthWorldScenario, promotion_threshold: float = 0.50):
        self.scenario = scenario
        self.promotion_threshold = promotion_threshold
        self.causes = scenario.candidate_causes()
        self.effects = scenario.effects()

        # Trivial enumerating generator creating exact hypothesis space
        self.generator = TrivialTheoryGenerator(self.causes, self.effects)
        self.hypotheses = self.generator.generate_all(day=0)

        # Scored Confidence Engine with substrate defaults (k_falsify=3.0, lambda=0.01)
        self.confidence_engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
        self.confidence_states: Dict[Tuple[str, str], ConfidenceState] = {
            (h.cause, h.effect): ConfidenceState(alpha=1.0, beta=1.0)
            for h in self.hypotheses
        }

        self.last_events: Optional[Dict[str, int]] = None
        self.t = 0

    @property
    def hypothesis_space(self) -> List[Tuple[str, str]]:
        """Returns exact hypothesis space tuples for comparison with baselines."""
        return [(h.cause, h.effect) for h in self.hypotheses]

    def observe(self, t: int, events: Dict[str, int]) -> None:
        self.t = t

        # Resolve predicate validation outcomes for predictions made at t-1
        if self.last_events is not None:
            for h in self.hypotheses:
                cause_fired_at_t_minus_1 = (self.last_events.get(h.cause, 0) == 1)
                effect_fired_at_t = (events.get(h.effect, 0) == 1)

                state = self.confidence_states[(h.cause, h.effect)]

                if cause_fired_at_t_minus_1:
                    if effect_fired_at_t:
                        # SUPPORTED outcome -> alpha + 1
                        state.alpha += 1.0
                        event_type = "SUPPORTED"
                    else:
                        # CONTRADICTED outcome -> beta + k_falsify (3.0)
                        state.beta += self.confidence_engine.k_falsify
                        event_type = "CONTRADICTED"

                    # Evolve through ScoredConfidenceEngine
                    self.confidence_engine.evolve(
                        confidence_state=state,
                        predicate_results=[{"status": event_type}],
                        day_idx=t,
                        lineage_id=h.structural_id,
                    )
                else:
                    # Decay step when not triggered
                    self.confidence_engine.evolve(
                        confidence_state=state,
                        predicate_results=None,
                        day_idx=t,
                        lineage_id=h.structural_id,
                    )

        self.last_events = dict(events)

    def predict(self, t: int, events: Dict[str, int]) -> Dict[str, float]:
        decision_id = f"{t}:predict:0"
        predictions: Dict[str, float] = {}

        for e in self.effects:
            prob_neg = 1.0
            for h in self.hypotheses:
                if h.effect != e:
                    continue

                state = self.confidence_states[(h.cause, h.effect)]
                conf = state.confidence  # E[Beta] = alpha / (alpha + beta)


                # Record consultation with role="gate" for every belief read during predict()
                record_consultation(
                    decision_id=decision_id,
                    object_structural_id=h.structural_id,
                    object_kind="confidence_state",
                    role="gate",
                )

                # Promotion Tier Check: Established tier requires conf >= 0.50
                if events.get(h.cause, 0) == 1 and conf >= self.promotion_threshold:
                    prob_neg *= (1.0 - conf)

            predictions[e] = 1.0 - prob_neg

        record_decision(
            decision_id=decision_id,
            output_content=str(predictions),
            day=t,
        )
        return predictions

    def beliefs(self) -> Dict[Tuple[str, str], float]:
        """Returns map of (cause, effect) -> Beta posterior expectation E[Beta]."""
        res = {}
        for (c, e), state in self.confidence_states.items():
            res[(c, e)] = state.confidence
        return res

