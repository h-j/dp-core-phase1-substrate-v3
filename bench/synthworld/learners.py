"""Learner interface + reference learners.

Every method under comparison (including DP) implements Learner:
  observe(t, events)
    - see the world state at t
  predict(t, events)
    - return {effect: P(effect active at t+1)}
  beliefs()
    - return {(cause, effect): confidence in a persistent causal rule}, for discovery scoring

Learners receive IDENTICAL event streams and are scored IDENTICALLY.
They are never told which candidate causes are decoys.
"""
from __future__ import annotations
from collections import deque
from typing import Protocol
from .world import Scenario


class Learner(Protocol):
    name: str

    def observe(self, t: int, events: dict[str, int]) -> None: ...
    def predict(self, t: int, events: dict[str, int]) -> dict[str, float]: ...
    def beliefs(self) -> dict[tuple[str, str], float]: ...


# helpers

class PairEstimator:
    """Beta-style counts for P(effect_{t+1} | cause_t = 1) and (| cause_t = 0)."""

    def __init__(self, prior: float = 1.0):
        self.n1 = self.k1 = self.n0 = self.k0 = 0.0
        self.a = prior

    def update(self, cause_on: int, effect_next: int) -> None:
        if cause_on:
            self.n1 += 1
            self.k1 += effect_next
        else:
            self.n0 += 1
            self.k0 += effect_next

    def p1(self) -> float:
        return (self.k1 + self.a) / (self.n1 + 2 * self.a)

    def p0(self) -> float:
        return (self.k0 + self.a) / (self.n0 + 2 * self.a)

    def excess(self) -> float:
        """Noisy-or 'causal strength': excess risk when cause is on."""
        p1, p0 = self.p1(), self.p0()
        return max(0.0, (p1 - p0) / (1.0 - p0)) if p0 < 1.0 else 0.0

    @property
    def evidence(self) -> float:
        return self.n1


def _noisy_or(base: float, strengths: list[float]) -> float:
    p_not = 1.0 - base
    for s in strengths:
        p_not *= (1.0 - s)
    return 1.0 - p_not


# learners

class TrueModel:
    """Reads the generative rules directly: the theoretical floor.
    Every other learner's score is regret against this one.
    """

    name = "TrueModel (oracle floor)"

    def __init__(self, scenario: Scenario):
        self.s = scenario

    def observe(self, t, events):
        pass

    def predict(self, t, events):
        return {e: self.s.true_prob(e, events, t) for e in self.s.effects}

    def beliefs(self):
        return {p: 1.0 for p in self.s.true_pairs(self.s.T - 1)}


class FlatBayesian:
    """The baseline DP must beat (roadmap 0.6 / experiment E2):
    an independent lifetime Beta estimator per (candidate cause, effect), noisy-or prediction, no lifecycle, no promotion, no forgetting.
    """

    name = "FlatBayesian"

    def __init__(self, scenario: Scenario, min_evidence: int = 30, strength_threshold: float = 0.15):
        self.causes = scenario.candidate_causes()
        self.effects = list(scenario.effects)
        self.base = {e: PairEstimator() for e in self.effects}
        self.pairs = {(c, e): PairEstimator() for c in self.causes for e in self.effects}
        self.prev: dict[str, int] | None = None
        self.min_evidence, self.threshold = min_evidence, strength_threshold

    def observe(self, t, events):
        if self.prev is not None:
            for e in self.effects:
                self.base[e].update(1, events[e])
                for c in self.causes:
                    self.pairs[(c, e)].update(self.prev[c], events[e])
        self.prev = dict(events)

    def predict(self, t, events):
        out = {}
        for e in self.effects:
            strengths = [
                self.pairs[(c, e)].excess()
                for c in self.causes
                if events.get(c, 0) and self.pairs[(c, e)].excess() > 0.05
            ]
            out[e] = _noisy_or(self._noise(e), strengths)
        return out

    def _noise(self, e):
        """Estimate spontaneous rate: P(effect | no candidate active) ~ min p0."""
        return min(self.pairs[(c, e)].p0() for c in self.causes)

    def beliefs(self):
        return {
            (c, e): est.excess()
            for (c, e), est in self.pairs.items()
            if est.evidence >= self.min_evidence and est.excess() >= self.threshold
        }


class WindowedFrequency:
    """Sliding-window variant: adapts fast to regime change, pays in variance.
    The 'reactive' end of the stability-plasticity trade-off.
    """

    name = "WindowedFrequency(w=200)"

    def __init__(self, scenario: Scenario, window: int = 200):
        self.causes = scenario.candidate_causes()
        self.effects = list(scenario.effects)
        self.window = window
        self.hist: deque = deque(maxlen=window)
        self.prev: dict[str, int] | None = None

    def observe(self, t, events):
        if self.prev is not None:
            self.hist.append((self.prev, dict(events)))
        self.prev = dict(events)

    def _stats(self, c, e):
        n1 = k1 = n0 = k0 = 1.0  # +1 smoothing
        for prev, cur in self.hist:
            if prev[c]:
                n1 += 1
                k1 += cur[e]
            else:
                n0 += 1
                k0 += cur[e]
        p1, p0 = k1 / (n1 + 1), k0 / (n0 + 1)
        return p1, p0, max(0.0, (p1 - p0) / (1.0 - p0))

    def predict(self, t, events):
        out = {}
        for e in self.effects:
            noise = min(self._stats(c, e)[1] for c in self.causes)
            strengths = [
                self._stats(c, e)[2]
                for c in self.causes
                if events.get(c, 0) and self._stats(c, e)[2] > 0.05
            ]
            out[e] = _noisy_or(noise, strengths)
        return out

    def beliefs(self):
        return {
            (c, e): self._stats(c, e)[2]
            for c in self.causes
            for e in self.effects
            if self._stats(c, e)[2] >= 0.15
        }


class ContextualBayesian(FlatBayesian):
    """FlatBayesian + scope: separate estimators per observed context value.
    Exists to show that scope machinery has measurable value (DP's 'belief scope' claim, made testable).
    """

    name = "ContextualBayesian"

    def __init__(self, scenario: Scenario, **kw):
        super().__init__(scenario, **kw)
        self.ctx = sorted(scenario.contexts)
        self.cpairs = {
            (c, e, x, v): PairEstimator()
            for c in self.causes
            for e in self.effects
            for x in self.ctx
            for v in (0, 1)
        }

    def observe(self, t, events):
        if self.prev is not None and self.ctx:
            for e in self.effects:
                for c in self.causes:
                    for x in self.ctx:
                        self.cpairs[(c, e, x, self.prev[x])].update(self.prev[c], events[e])
        super().observe(t, events)

    def predict(self, t, events):
        if not self.ctx:
            return super().predict(t, events)
        out = {}
        for e in self.effects:
            strengths = []
            for c in self.causes:
                if not events.get(c, 0):
                    continue
                # use the scope-conditioned estimate when it has evidence;
                # fall back to the unconditioned (flat) estimate otherwise
                s = self.pairs[(c, e)].excess()
                for x in self.ctx:
                    est = self.cpairs[(c, e, x, events[x])]
                    if est.evidence >= 20:
                        s = est.excess()
                if s > 0.05:
                    strengths.append(s)
            out[e] = _noisy_or(self._noise(e), strengths)
        return out
