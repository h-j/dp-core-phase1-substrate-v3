"""
Phase 4: Tests for ContradictionDetector.

Uses MagicMock theories to exercise detection logic. LLM dependency is mocked.
No external services required.
"""
from unittest.mock import MagicMock, patch
import pytest


def _make_detector(debug=False):
    with patch(
        "cognition.contradiction.contradiction_detector.LLMContradictionAuditor"
    ) as MockAuditor:
        MockAuditor.return_value.audit_contradiction = MagicMock(
            return_value={"is_contradiction": False, "reasoning": "test"}
        )
        from cognition.contradiction.contradiction_detector import ContradictionDetector
        d = ContradictionDetector(debug=debug)
        d.llm_auditor.audit_contradiction = MagicMock(
            return_value={"is_contradiction": False, "reasoning": "test"}
        )
        return d


def _theory_mock(claim: str, direction: str = "bullish", theory_id: str = "t1"):
    """Mock theory with structured summary as a MagicMock."""
    structured = MagicMock()
    structured.claim = claim
    structured.direction = direction
    structured.horizon = "5d"
    structured.mechanism = "test mechanism"
    structured.falsified_if = "price drops 2%"
    structured.unless = ""
    structured.forbidden_state = ""
    structured.if_branch = MagicMock()
    structured.if_branch.condition = "if FII buys"
    structured.if_branch.action = "price rises"
    structured.else_branch = MagicMock()
    structured.else_branch.condition = "else"
    structured.else_branch.action = "neutral"
    structured.mechanism_components = []
    structured.falsification_conditions = []

    t = MagicMock()
    t.id = theory_id
    t.thesis = claim
    t.summary = claim
    t.summary_structured = structured
    return t


def test_no_history_gives_zero_score():
    detector = _make_detector()
    curr = _theory_mock("Market will rally", "bullish", "t1")
    result = detector.detect(curr, [], [], [])
    assert result["score"] == 0.0, "No historical theories → score must be 0"


def test_result_has_required_keys():
    detector = _make_detector()
    curr = _theory_mock("Any theory", "bullish", "t1")
    result = detector.detect(curr, [], [], [])
    assert "score" in result
    assert "indicators" in result
    assert "summary" in result


def test_score_is_bounded():
    detector = _make_detector()
    curr = _theory_mock("Bull case", "bullish", "t1")
    hist = _theory_mock("Bear case", "bearish", "t2")
    result = detector.detect(curr, [hist], [], [])
    assert 0.0 <= result["score"] <= 1.0


def test_debug_false_produces_no_stdout(capsys):
    detector = _make_detector(debug=False)
    curr = _theory_mock("Theory A", "bullish", "t1")
    hist = _theory_mock("Theory B", "bearish", "t2")
    detector.detect(curr, [hist], [], [])
    captured = capsys.readouterr()
    assert captured.out == "", "debug=False must produce no stdout"
