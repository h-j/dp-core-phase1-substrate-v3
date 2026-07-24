"""Synthetic ground-truth world (roadmap item 0.5).

A discrete-time world of observable binary variables:
  drivers: candidate causes, each with a base activation rate
  effects: each with a spontaneous (noise) activation rate
  contexts: observable condition variables (for scope-gated rules)
  decoys: variables that MIRROR a real driver during a window, so they correlate with that driver's effects without causing anything

Ground truth is authored, windowed (regime changes = rule windows), and
exported as an answer key, so learned beliefs can be scored for
"correctness", not just formation. Generation is fully deterministic given the scenario seed.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CausalRule:
    driver: str
    effect: str
    strength: float  # P(effect fires at t+1 | driver active at t)
    start: int = 0  # rule active on [start, end)
    end: Optional[int] = None
    context: Optional[str] = None  # if set: rule fires only when context var == 1

    def active(self, t: int) -> bool:
        return t >= self.start and (self.end is None or t < self.end)


@dataclass(frozen=True)
class Decoy:
    name: str
    mirrors: str  # driver it imitates
    start: int
    end: int
    fidelity: float = 0.9  # P(copy the mirrored driver's value) in window
    base_rate: float = 0.25  # Behavior outside the window (independent)


@dataclass
class Scenario:
    name: str
    T: int
    drivers: dict[str, float]  # name -> base rate
    effects: dict[str, float]  # name -> spontaneous noise rate
    contexts: dict[str, float] = field(default_factory=dict)
    rules: list[CausalRule] = field(default_factory=list)
    decoys: list[Decoy] = field(default_factory=list)
    seed: int = 7
    description: str = ""

    def candidate_causes(self) -> list[str]:
        """What a learner may condition on (it does NOT know which are decoys)."""
        return sorted(self.drivers) + sorted(d.name for d in self.decoys) + sorted(self.contexts)

    # ------------------ answer key ------------------

    def true_pairs(self, t: int) -> set[tuple[str, str]]:
        """(cause, effect) pairs that are genuinely causal at time t."""
        return {(r.driver, r.effect) for r in self.rules if r.active(t)}

    def true_prob(self, effect: str, events: dict[str, int], t: int) -> float:
        """Ground-truth P(effect at t+1 | observed state at t) via noisy-or over active rules. This is the TrueModel floor."""
        p_not = 1.0 - self.effects[effect]
        for r in self.rules:
            if r.effect != effect or not r.active(t):
                continue
            if not events.get(r.driver, 0):
                continue
            if r.context and not events.get(r.context, 0):
                continue
            p_not *= (1.0 - r.strength)
        return 1.0 - p_not


class World:
    def __init__(self, scenario: Scenario):
        self.s = scenario

    def generate(self) -> list[dict[str, int]]:
        """Timeline of length T. events[t] holds drivers/contexts/decoys at t and effects at t (effects caused by state at t-1)."""
        s, rng = self.s, random.Random(self.s.seed)
        timeline: list[dict[str, int]] = []
        prev: dict[str, int] = {}
        for t in range(s.T):
            ev: dict[str, int] = {}
            for name, rate in s.drivers.items():
                ev[name] = int(rng.random() < rate)
            for name, rate in s.contexts.items():
                ev[name] = int(rng.random() < rate)
            for d in s.decoys:
                if d.start <= t < d.end:
                    ev[d.name] = (
                        ev[d.mirrors] if rng.random() < d.fidelity else int(rng.random() < d.base_rate)
                    )
                else:
                    ev[d.name] = int(rng.random() < d.base_rate)
            # effects at t are caused by state at t-1 (noisy-or)
            for name, noise in s.effects.items():
                p = s.true_prob(name, prev, t - 1) if t > 0 else noise
                ev[name] = int(rng.random() < p)
            timeline.append(ev)
            prev = ev
        return timeline
