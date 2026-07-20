"""
Phase 4: Tests for telemetry/logging_config.py.
"""
import logging
import pytest
from unittest.mock import MagicMock, patch


def test_configure_logging_runs_without_error():
    from telemetry.logging_config import configure_logging
    configure_logging(level=logging.WARNING)


def test_configure_logging_idempotent():
    from telemetry.logging_config import configure_logging
    root = logging.getLogger()
    configure_logging(level=logging.WARNING)
    h_count = len(root.handlers)
    configure_logging(level=logging.WARNING)
    assert len(root.handlers) <= h_count + 1


def test_contradiction_detector_no_stdout_by_default(capsys):
    """Integration: ContradictionDetector debug=False must produce no stdout."""
    with patch(
        "cognition.contradiction.contradiction_detector.LLMContradictionAuditor"
    ) as M:
        M.return_value.audit_contradiction = MagicMock(
            return_value={"is_contradiction": False, "reasoning": "test"}
        )
        from cognition.contradiction.contradiction_detector import ContradictionDetector
        detector = ContradictionDetector(debug=False)
        detector.llm_auditor.audit_contradiction = M.return_value.audit_contradiction

        def _theory(claim, direction, tid):
            s = MagicMock()
            s.claim = claim; s.direction = direction; s.horizon = "5d"
            s.mechanism = "test"; s.falsified_if = "drops"
            s.unless = ""; s.forbidden_state = ""
            s.if_branch = MagicMock(); s.if_branch.condition = "if"; s.if_branch.action = "rise"
            s.else_branch = MagicMock(); s.else_branch.condition = "else"; s.else_branch.action = "flat"
            s.mechanism_components = []; s.falsification_conditions = []
            t = MagicMock(); t.id = tid; t.thesis = claim; t.summary = claim; t.summary_structured = s
            return t

        detector.detect(_theory("bull", "bullish", "t1"), [_theory("bear", "bearish", "t2")], [], [])
        captured = capsys.readouterr()
        assert captured.out == "", "ContradictionDetector debug=False must not write to stdout"
