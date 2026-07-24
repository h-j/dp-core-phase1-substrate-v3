"""
Synthworld Learners Protocol and Baselines.

Learner Protocol (3 methods):
1. observe(t, events): Ingest experience at step t.
2. predict(t, events) -> Dict[str, float]: Return P(effect at t+1) predictions.
3. beliefs() -> Dict[Tuple[str, str], float]: Return map of (cause, effect) -> confidence.
"""
from typing import Dict, List, Tuple, Optional
from bench.synthworld.world import SynthWorldScenario


class Learner:
    """Abstract Learner protocol."""

    def observe(self, t: int, events: Dict[str, int]) -> None:
        raise NotImplementedError

    def predict(self, t: int, events: Dict[str, int]) -> Dict[str, float]:
        raise NotImplementedError

    def beliefs(self) -> Dict[Tuple[str, str], float]:
        raise NotImplementedError


class TruModalOracle(Learner):
    """Oracle floor learner with exact ground truth access."""

    def __init__(self, scenario: SynthWorldScenario):
        self.scenario = scenario
        self.last_events: Dict[str, int] = {}
        self.t = 0

    def observe(self, t: int, events: Dict[str, int]) -> None:
        self.t = t
        self.last_events = dict(events)

    def predict(self, t: int, events: Dict[str, int]) -> Dict[str, float]:
        true_causes = self.scenario.ground_truth_causes(t)
        predictions = {}
        for e in self.scenario.effects():
            prob = 0.0
            for c in true_causes:
                if events.get(c, 0) == 1:
                    prob = 1.0
                    break
            predictions[e] = prob
        return predictions

    def beliefs(self) -> Dict[Tuple[str, str], float]:
        true_causes = self.scenario.ground_truth_causes(self.t)
        res = {}
        for c in self.scenario.candidate_causes():
            for e in self.scenario.effects():
                res[(c, e)] = 1.0 if c in true_causes else 0.0
        return res


class ElatraverianLearner(Learner):
    """Empirical frequency baseline learner."""

    def __init__(self, scenario: SynthWorldScenario):
        self.scenario = scenario
        self.counts_co_occur: Dict[Tuple[str, str], int] = {}
        self.counts_cause: Dict[str, int] = {}
        self.last_events: Dict[str, int] = {}
        self.causes = scenario.candidate_causes()
        self.effects = scenario.effects()

        for c in self.causes:
            self.counts_cause[c] = 0
            for e in self.effects:
                self.counts_co_occur[(c, e)] = 0

    def observe(self, t: int, events: Dict[str, int]) -> None:
        if self.last_events:
            for c in self.causes:
                if self.last_events.get(c, 0) == 1:
                    self.counts_cause[c] += 1
                    for e in self.effects:
                        if events.get(e, 0) == 1:
                            self.counts_co_occur[(c, e)] += 1
        self.last_events = dict(events)

    def predict(self, t: int, events: Dict[str, int]) -> Dict[str, float]:
        predictions = {}
        for e in self.effects:
            prob_neg = 1.0
            for c in self.causes:
                if events.get(c, 0) == 1:
                    denom = max(1, self.counts_cause[c])
                    conf = self.counts_co_occur[(c, e)] / denom
                    prob_neg *= (1.0 - conf)
            predictions[e] = 1.0 - prob_neg
        return predictions

    def beliefs(self) -> Dict[Tuple[str, str], float]:
        res = {}
        for c in self.causes:
            for e in self.effects:
                denom = max(1, self.counts_cause[c])
                res[(c, e)] = self.counts_co_occur[(c, e)] / denom
        return res


class ContextualBayesianLearner(Learner):
    """Contextual Bayesian baseline learner."""

    def __init__(self, scenario: SynthWorldScenario):
        self.scenario = scenario
        self.causes = scenario.candidate_causes()
        self.effects = scenario.effects()
        self.alpha: Dict[Tuple[str, str], float] = {(c, e): 1.0 for c in self.causes for e in self.effects}
        self.beta: Dict[Tuple[str, str], float] = {(c, e): 1.0 for c in self.causes for e in self.effects}
        self.last_events: Dict[str, int] = {}

    def observe(self, t: int, events: Dict[str, int]) -> None:
        if self.last_events:
            for c in self.causes:
                if self.last_events.get(c, 0) == 1:
                    for e in self.effects:
                        if events.get(e, 0) == 1:
                            self.alpha[(c, e)] += 1.0
                        else:
                            self.beta[(c, e)] += 1.0
        self.last_events = dict(events)

    def predict(self, t: int, events: Dict[str, int]) -> Dict[str, float]:
        predictions = {}
        for e in self.effects:
            prob_neg = 1.0
            for c in self.causes:
                if events.get(c, 0) == 1:
                    a = self.alpha[(c, e)]
                    b = self.beta[(c, e)]
                    conf = a / (a + b)
                    prob_neg *= (1.0 - conf)
            predictions[e] = 1.0 - prob_neg
        return predictions

    def beliefs(self) -> Dict[Tuple[str, str], float]:
        res = {}
        for c in self.causes:
            for e in self.effects:
                a = self.alpha[(c, e)]
                b = self.beta[(c, e)]
                res[(c, e)] = a / (a + b)
        return res
