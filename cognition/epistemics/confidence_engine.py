"""
Epistemic Confidence Engine — Centralized, interpretable confidence evolution model for DP-Core.

All confidence evolution is calculated as an explicit, interpretable, deterministic consequence
of empirical evidence, predictions, contradictions, and meta-cognitive reflection.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ConfidenceFactor(BaseModel):
    """Represents an individual signal contribution to confidence evolution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    factor_name: str
    delta: float
    signal_value: float
    explanation: str


class ConfidenceReport(BaseModel):
    """Structured explanation report generated for every confidence update."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    theory_id: str
    previous_confidence: float
    new_confidence: float
    confidence_delta: float
    contributing_factors: List[ConfidenceFactor] = Field(default_factory=list)
    final_justification: str
    timestamp: float = Field(default_factory=time.time)


class EpistemicConfidenceEngine:
    """
    Centralized Epistemic Confidence Engine.

    Calculates confidence updates deterministically from empirical evidence and generates
    diagnostic ConfidenceReport explanations.
    """

    def __init__(
        self,
        min_confidence: float = 0.05,
        max_confidence: float = 0.99,
    ):
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence

    def update_confidence(
        self,
        theory: Any,
        evidence: Optional[Any] = None,
        contradictions: Optional[Any] = None,
        prediction_results: Optional[Any] = None,
        reflection_feedback: Optional[Any] = None,
        theory_usefulness: Optional[Dict[str, Any]] = None,
        regime_matches: Optional[List[Any]] = None,
        theory_age: int = 0,
        novelty_score: float = 1.0,
        **kwargs,
    ) -> Tuple[float, ConfidenceReport]:
        """
        Calculates updated confidence and generates an interpretable ConfidenceReport.

        Args:
            theory: Theory object or dictionary containing ID and confidence state.
            evidence: Empirical validation object or score.
            contradictions: Contradiction markers or score dict.
            prediction_results: Outcome of prior prediction probe scoring.
            reflection_feedback: Meta-cognitive reflection feedback.
            theory_usefulness: Dictionary containing theory usefulness score.
            regime_matches: List of regime historical matches.
            theory_age: Number of steps or days the theory has survived.
            novelty_score: Gating novelty score [0.0, 1.0].

        Returns:
            Tuple of (new_confidence: float, report: ConfidenceReport)
        """
        theory_id = getattr(theory, "id", None) or (
            theory.get("id") if isinstance(theory, dict) else "TH_UNKNOWN"
        )
        
        # Get previous confidence value
        prev_conf = 0.50
        if hasattr(theory, "confidence_state") and hasattr(theory.confidence_state, "empirical_confidence"):
            prev_conf = float(theory.confidence_state.empirical_confidence)
        elif isinstance(theory, dict):
            prev_conf = float(theory.get("confidence", 0.50))
        elif hasattr(theory, "confidence"):
            prev_conf = float(getattr(theory, "confidence", 0.50))

        factors: List[ConfidenceFactor] = []

        # 1. Supporting & Contradictory Evidence Signal
        if evidence is not None:
            score = float(evidence if isinstance(evidence, (int, float)) else getattr(evidence, "score", 0.5))
            if score > 0.70:
                delta = +0.07
                expl = f"Strong empirical evidence alignment ({score:.2f} > 0.70)"
            elif score > 0.40:
                delta = +0.02
                expl = f"Moderate empirical evidence alignment ({score:.2f})"
            else:
                delta = -0.08
                expl = f"Low empirical evidence alignment ({score:.2f} <= 0.40)"
            factors.append(ConfidenceFactor(factor_name="supporting_evidence", delta=delta, signal_value=score, explanation=expl))

        # 2. Contradiction Signal
        if contradictions is not None:
            if isinstance(contradictions, dict):
                new_c = int(contradictions.get("new_contradictions", 0))
                active_c = int(contradictions.get("active_contradictions", 0))
                severity = float(contradictions.get("severity", 0.0))
            else:
                new_c = 0
                active_c = int(getattr(contradictions, "count", 0))
                severity = float(getattr(contradictions, "severity", 0.0))

            if active_c > 0 or new_c > 0 or severity > 0.3:
                delta = -min(0.12, 0.04 * (active_c + new_c) + 0.05 * severity)
                expl = f"Contradictions present: active={active_c}, new={new_c}, severity={severity:.2f}"
                factors.append(ConfidenceFactor(factor_name="contradictory_evidence", delta=delta, signal_value=severity, explanation=expl))

        # 3. Prediction Success / Failure Signal
        if prediction_results is not None:
            if isinstance(prediction_results, dict):
                score = float(prediction_results.get("validation_score", 0.5))
                is_correct = bool(prediction_results.get("correct", score > 0.6))
            else:
                score = float(getattr(prediction_results, "score", 0.5))
                is_correct = bool(getattr(prediction_results, "correct", score > 0.6))

            if is_correct or score >= 0.70:
                delta = +0.06
                expl = f"Prediction successful (alignment={score:.2f})"
            elif score < 0.40:
                delta = -0.09
                expl = f"Prediction failed (alignment={score:.2f} < 0.40)"
            else:
                delta = +0.01
                expl = f"Neutral prediction outcome (alignment={score:.2f})"
            factors.append(ConfidenceFactor(factor_name="prediction_outcome", delta=delta, signal_value=score, explanation=expl))

        # 4. Reflection Feedback Signal
        if reflection_feedback is not None:
            r_score = float(reflection_feedback if isinstance(reflection_feedback, (int, float)) else getattr(reflection_feedback, "score", 0.5))
            if r_score > 0.75:
                delta = +0.04
                expl = f"High meta-cognitive reflection coherence ({r_score:.2f})"
            elif r_score < 0.35:
                delta = -0.04
                expl = f"Low reflection coherence ({r_score:.2f})"
            else:
                delta = 0.0
                expl = f"Neutral reflection feedback ({r_score:.2f})"
            if delta != 0.0:
                factors.append(ConfidenceFactor(factor_name="reflection_quality", delta=delta, signal_value=r_score, explanation=expl))

        # 5. Theory Usefulness & Reuse Signal
        if theory_usefulness:
            u_score = float(theory_usefulness.get("score", 0.0))
            if u_score > 0.60:
                delta = +0.05
                expl = f"High theory usefulness score ({u_score:.2f})"
                factors.append(ConfidenceFactor(factor_name="theory_reuse", delta=delta, signal_value=u_score, explanation=expl))
            elif u_score < 0.30:
                delta = -0.06
                expl = f"Low theory usefulness score ({u_score:.2f})"
                factors.append(ConfidenceFactor(factor_name="theory_reuse", delta=delta, signal_value=u_score, explanation=expl))

        # 6. Theory Age / Survival Stability Factor
        if theory_age > 3:
            age_delta = min(0.03, 0.005 * theory_age)
            factors.append(ConfidenceFactor(factor_name="theory_age", delta=age_delta, signal_value=float(theory_age), explanation=f"Survival stability bonus (+{age_delta:.3f} for {theory_age} steps)"))

        # Calculate Total Delta
        total_delta = sum(f.delta for f in factors)
        raw_new_conf = prev_conf + total_delta
        clamped_new_conf = max(self.min_confidence, min(self.max_confidence, raw_new_conf))

        # Build Justification Summary
        if not factors:
            justification = f"No evidence updates received. Confidence maintained at {prev_conf:.3f}."
        else:
            factor_summaries = [f"{f.factor_name}: {f.delta:+.3f}" for f in factors]
            justification = (
                f"Confidence updated from {prev_conf:.3f} to {clamped_new_conf:.3f} "
                f"({total_delta:+.3f} net delta) based on: {', '.join(factor_summaries)}."
            )

        report = ConfidenceReport(
            theory_id=theory_id,
            previous_confidence=prev_conf,
            new_confidence=clamped_new_conf,
            confidence_delta=clamped_new_conf - prev_conf,
            contributing_factors=factors,
            final_justification=justification,
        )

        logger.info("[EpistemicConfidenceEngine] %s", justification)

        return clamped_new_conf, report


# Standalone functional entry point
_DEFAULT_ENGINE = EpistemicConfidenceEngine()


def update_confidence(
    theory: Any,
    evidence: Optional[Any] = None,
    contradictions: Optional[Any] = None,
    prediction_results: Optional[Any] = None,
    reflection_feedback: Optional[Any] = None,
    **kwargs,
) -> Tuple[float, ConfidenceReport]:
    """
    Public entry point for updating theory confidence through the EpistemicConfidenceEngine.
    """
    return _DEFAULT_ENGINE.update_confidence(
        theory=theory,
        evidence=evidence,
        contradictions=contradictions,
        prediction_results=prediction_results,
        reflection_feedback=reflection_feedback,
        **kwargs,
    )
