"""
Unit tests for cognition/epistemics/confidence_engine.py.
"""
import pytest

from cognition.epistemics.confidence_engine import (
    ConfidenceFactor,
    ConfidenceReport,
    EpistemicConfidenceEngine,
    update_confidence,
)


class MockTheory:
    def __init__(self, theory_id: str = "TH_001", empirical_confidence: float = 0.50):
        self.id = theory_id
        class ConfState:
            def __init__(self, val):
                self.empirical_confidence = val
        self.confidence_state = ConfState(empirical_confidence)


def test_supporting_evidence_positive_delta():
    engine = EpistemicConfidenceEngine()
    theory = MockTheory(empirical_confidence=0.50)

    new_conf, report = engine.update_confidence(
        theory=theory,
        evidence=0.85,  # High evidence alignment score
        prediction_results={"validation_score": 0.80, "correct": True},
    )

    assert new_conf > 0.50
    assert report.theory_id == "TH_001"
    assert report.previous_confidence == 0.50
    assert report.new_confidence == new_conf
    assert report.confidence_delta > 0.0
    assert len(report.contributing_factors) >= 2

    factor_names = [f.factor_name for f in report.contributing_factors]
    assert "supporting_evidence" in factor_names
    assert "prediction_outcome" in factor_names
    assert "Confidence updated from 0.500 to" in report.final_justification


def test_contradictions_and_failed_prediction_negative_delta():
    theory = MockTheory(empirical_confidence=0.70)

    new_conf, report = update_confidence(
        theory=theory,
        evidence=0.20,  # Low validation alignment score
        contradictions={"active_contradictions": 2, "new_contradictions": 1, "severity": 0.60},
        prediction_results={"validation_score": 0.25, "correct": False},
    )

    assert new_conf < 0.70
    assert report.previous_confidence == 0.70
    assert report.confidence_delta < 0.0

    factor_names = [f.factor_name for f in report.contributing_factors]
    assert "contradictory_evidence" in factor_names
    assert "prediction_outcome" in factor_names


def test_theory_age_and_reuse_factors():
    engine = EpistemicConfidenceEngine()
    theory = MockTheory(empirical_confidence=0.60)

    new_conf, report = engine.update_confidence(
        theory=theory,
        theory_usefulness={"score": 0.80},
        theory_age=10,
    )

    assert new_conf > 0.60
    factor_names = [f.factor_name for f in report.contributing_factors]
    assert "theory_reuse" in factor_names
    assert "theory_age" in factor_names


def test_determinism_and_reproducibility():
    theory = MockTheory(empirical_confidence=0.55)
    
    res1, report1 = update_confidence(
        theory=theory,
        evidence=0.80,
        contradictions={"severity": 0.20},
        prediction_results={"validation_score": 0.75},
        theory_age=5,
    )

    res2, report2 = update_confidence(
        theory=theory,
        evidence=0.80,
        contradictions={"severity": 0.20},
        prediction_results={"validation_score": 0.75},
        theory_age=5,
    )

    assert res1 == res2
    assert report1.new_confidence == report2.new_confidence
    assert report1.confidence_delta == report2.confidence_delta
    assert len(report1.contributing_factors) == len(report2.contributing_factors)
    assert report1.final_justification == report2.final_justification


def test_confidence_clamping():
    engine = EpistemicConfidenceEngine(min_confidence=0.10, max_confidence=0.90)
    
    # Overly high delta
    high_theory = MockTheory(empirical_confidence=0.88)
    high_conf, high_report = engine.update_confidence(
        theory=high_theory,
        evidence=0.95,
        prediction_results={"validation_score": 0.95, "correct": True},
        theory_usefulness={"score": 0.90},
    )
    assert high_conf <= 0.90

    # Overly low delta
    low_theory = MockTheory(empirical_confidence=0.12)
    low_conf, low_report = engine.update_confidence(
        theory=low_theory,
        evidence=0.10,
        contradictions={"severity": 0.90, "active_contradictions": 3},
        prediction_results={"validation_score": 0.10, "correct": False},
    )
    assert low_conf >= 0.10
