from __future__ import annotations
from . import metrics
from .world import World, Scenario, CausalRule, Decoy


def run(scenario: Scenario, learners: list) -> dict:
    timeline = World(scenario).generate()
    scores = {ln.name: [] for ln in learners}
    for t in range(scenario.T - 1):
        ev, nxt = timeline[t], timeline[t + 1]
        for ln in learners:
            ln.observe(t, ev)
            preds = ln.predict(t, ev)
            scores[ln.name].append(
                {e: metrics.brier(preds[e], nxt[e]) for e in scenario.effects}
            )

    # final observe so belief extraction sees the whole stream
    for ln in learners:
        ln.observe(scenario.T - 1, timeline[-1])

    return {
        "scenario": scenario,
        "timeline": timeline,
        "scores": scores,
        "beliefs": {ln.name: ln.beliefs() for ln in learners},
    }


def s1_clean(T: int = 3000) -> Scenario:
    return Scenario(
        name="S1 clean learning",
        description="Two stable rules, moderate noise. Sanity: everyone should find them; scores measure calibration regret.",
        T=T,
        drivers={"D1": 0.30, "D2": 0.25, "D3": 0.30},
        effects={"E1": 0.05, "E2": 0.08},
        rules=[CausalRule("D1", "E1", 0.80), CausalRule("D2", "E2", 0.60)],
        seed=11,
    )


def s2_spurious(T: int = 3000) -> Scenario:
    return Scenario(
        name="S2 spurious correlation",
        description="Decoys mirror real drivers for the first 600 steps, then go independent. Tests whether beliefs demand SUSTAINED evidence: promoting (decoy->effect) as a persistent rule is the failure this scenario exists to catch.",
        T=T,
        drivers={"D1": 0.30, "D2": 0.25},
        effects={"E1": 0.05, "E2": 0.08},
        rules=[CausalRule("D1", "E1", 0.80), CausalRule("D2", "E2", 0.60)],
        decoys=[
            Decoy("X1", mirrors="D1", start=0, end=600, fidelity=0.92),
            Decoy("X2", mirrors="D2", start=0, end=600, fidelity=0.92),
        ],
    )


def s3_regime(T: int = 4000, flip: int = 2000) -> Scenario:
    return Scenario(
        name="S3 regime change",
        description=f"At t={flip}, rule D1->E1 DIES and D1->E3 is born; D2->E2 persists throughout. Measures unlearning speed (recovery) and whether revision damages the untouched rule (collateral).",
        T=T,
        drivers={"D1": 0.30, "D2": 0.25},
        effects={"E1": 0.05, "E2": 0.08, "E3": 0.05},
        rules=[
            CausalRule("D1", "E1", 0.80, start=0, end=flip),
            CausalRule("D1", "E3", 0.80, start=flip),
            CausalRule("D2", "E2", 0.60),
        ],
        seed=37,
    )


def s4_scope(T: int = 4000) -> Scenario:
    return Scenario(
        name="S4 scoped rule",
        description="D1->E1 holds ONLY when context C=1 (C is observable, active half the time). Scope-blind learners learn a diluted rule and mispredict in both contexts; scope-aware learners should approach the oracle.",
        T=T,
        drivers={"D1": 0.35, "D2": 0.25},
        effects={"E1": 0.05, "E2": 0.08},
        contexts={"C": 0.5},
        rules=[CausalRule("D1", "E1", 0.85, context="C"), CausalRule("D2", "E2", 0.60)],
        seed=51,
    )


ALL = [s1_clean, s2_spurious, s3_regime, s4_scope]
