"""
Phase 0 Regression Test: Verify no trade/capital feedback into cognition.

Asserts via static code analysis that:
1. DecisionPolicyEngine, CapitalSimulator, PaperTrader, ConvictionSizer outputs
   do not feed back into ConfidenceEvolutionEngine.evolve() or TheoryLineageEngine.
2. replay_engine.py does not contain the old programmatic decision feedback loop.
3. AGENTS.md explicitly documents Observer-Only Modules.
"""

import ast
import pathlib
import pytest


def test_agents_md_has_observer_only_contract():
    agents_md = pathlib.Path("AGENTS.md").read_text(encoding="utf-8")
    assert "Observer-Only Modules" in agents_md
    assert "Nothing produced by these modules" in agents_md


def test_replay_engine_no_trade_feedback_loop():
    engine_code = pathlib.Path("market/replay/replay_engine.py").read_text(encoding="utf-8")
    assert "last_rec.decision_result" not in engine_code
    assert "last_rec.pnl" not in engine_code
    assert "NOTE(charter): DecisionPolicyEngine and CapitalSimulator are downstream" in engine_code


def test_confidence_evolution_signature_no_trade_params():
    from cognition.confidence.confidence_evolution_engine import ConfidenceEvolutionEngine
    import inspect

    sig = inspect.signature(ConfidenceEvolutionEngine.evolve)
    params = set(sig.parameters.keys())

    forbidden_params = {"pnl", "conviction_score", "decision_result", "capital", "last_rec"}
    overlap = params & forbidden_params
    assert not overlap, f"ConfidenceEvolutionEngine.evolve contains forbidden trade params: {overlap}"


def test_trade_modules_do_not_import_cognition_mutators():
    trade_files = [
        pathlib.Path("market/replay/decision_policy.py"),
        pathlib.Path("market/replay/capital_simulator.py"),
        pathlib.Path("market/replay/paper_trader.py"),
        pathlib.Path("market/replay/conviction_sizer.py"),
    ]

    for tf in trade_files:
        if not tf.exists():
            continue
        code = tf.read_text(encoding="utf-8")
        assert "ConfidenceEvolutionEngine" not in code, f"{tf} must not reference ConfidenceEvolutionEngine"
        assert "TheoryLineageEngine" not in code, f"{tf} must not reference TheoryLineageEngine"
        assert "ContradictionRegistry" not in code, f"{tf} must not reference ContradictionRegistry"
