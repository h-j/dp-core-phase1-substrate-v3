"""Property tests: determinism, oracle floor, scenario traps working as designed."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthworld.harness import run, s1_clean, s2_spurious, s3_regime, s4_scope
from synthworld.harness_init import make_learners
from synthworld.world import World
from synthworld import metrics


def test_generation_deterministic():
    a, b = World(s2_spurious()).generate(), World(s2_spurious()).generate()
    assert a == b


def test_oracle_is_floor():
    for make in (s1_clean, s2_spurious, s3_regime, s4_scope):
        sc = make()
        r = run(sc, make_learners(sc))
        names = list(r["scores"])
        oracle = metrics.phase_brier(r["scores"][names[0]], 300, sc.T)
        for n in names[1:]:
            assert metrics.phase_brier(r["scores"][n], 300, sc.T) >= oracle - 0.003, n


def test_s2_decoy_trap_catches_lifetime_learner():
    sc = s2_spurious()
    r = run(sc, make_learners(sc))
    d = metrics.discovery(r["beliefs"]["FlatBayesian"], sc)
    assert d["decoy_claims"] >= 1, "trap failed to catch the no-forgetting learner"


def test_s3_windowed_recovers_faster_than_lifetime():
    sc = s3_regime()
    r = run(sc, make_learners(sc))
    w = metrics.recovery(r["scores"]["WindowedFrequency(w=200)"], 2000, ["E1", "E3"])

    rf = metrics.recovery(r["scores"]["FlatBayesian"], 2000, ["E1", "E3"])
    assert (w["recovery_steps"] or 10**9) < (rf["recovery_steps"] or 10**9)


def test_s4_scope_machinery_earns_its_keep():
    sc = s4_scope()
    r = run(sc, make_learners(sc))
    ctx = metrics.phase_brier(r["scores"]["ContextualBayesian"], 500, sc.T)
    flat = metrics.phase_brier(r["scores"]["FlatBayesian"], 500, sc.T)
    assert ctx < flat - 0.01, "scope conferred no measurable advantage"


if __name__ == "__main__":
    for k, t in sorted(globals().items()):
        if k.startswith("test_"):
            t()
            print(f" PASS {k}")
    print("\nall tests passed")
