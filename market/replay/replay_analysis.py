"""
Replay analysis engine for longitudinal cognition study.

Analyzes:
- confidence ceiling detection
- contradiction persistence
- theory rigidity
- coherence decay
- regime transition adaptation
- narrative repetition
"""

import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Union

from market.replay.prediction_probe import PredictionDirection
from market.replay.replay_analysis_reporting import \
    ReplayAnalysisReportingMixin


def extract_usefulness_score(value):
    """Normalizes theory_usefulness to a float score. Supports dict or numeric."""
    if isinstance(value, dict):
        return float(value.get("score", 0.0))
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


class ReplayAnalysisEngine(ReplayAnalysisReportingMixin):
    """
    Analyzes cognition behavior over replay execution.
    """

    def __init__(self, market_name: str = "UNKNOWN"):
        """Initialize analysis state."""
        self.market_name = market_name
        self.days = []
        self.confidence_history = []
        self.contradiction_history = []
        self.theory_themes = defaultdict(int)
        self.reflection_patterns = defaultdict(int)
        self.regime_transitions = []
        self.epistemic_quality_history = []
        self.prediction_history = []
        self.transition_pressure_history = []
        self.capital_simulation_logs = []
        self.decisions_history = []
        self.config_snapshot = {}
        self.transition_memory_hits = 0
        self.miss_analysis = []  # v2.1 Miss Audit
        self.theory_metrics_history = []

    def set_config_snapshot(self, config: dict):
        """Record the configuration used for this replay."""
        self.config_snapshot = config

    def record_day(
        self,
        day_index: int,
        date: str,
        confidence_state: dict,
        contradiction_result: dict,
        theory_summary: str,
        reflection_summary: str,
        market_regime: str,
        epistemic_quality: Union[dict, None] = None,
        prediction: Union[dict, None] = None,
        prior_prediction_result: Union[dict, None] = None,
        regime_matches: Union[list, None] = None,
        theory_usefulness: Union[dict, None] = None,
        transition_pressure: Union[dict, None] = None,
        decisions: Union[dict, None] = None,
        candle_type: Union[str, None] = None,
        participation_strength: Union[str, None] = None,
        participation_confirmation: Union[str, None] = None,
        market_name: Union[str, None] = None,
        # v2.0 enriched dimensions
        volume_state: Union[str, None] = None,
        volatility_regime: Union[str, None] = None,
        momentum_regime: Union[str, None] = None,
        # v3.0 Regime Fields
        regime_subtype: Union[str, None] = "neutral",
        falsifiability_conditions: Union[list, None] = None,
        analog_divergence_claim: Union[str, None] = "",
        regime_history: Union[dict, None] = None,
        transition_memory_hit: bool = False,
        branches_generated: int = 0,
        branch_stats: dict = None,
        intelligence_data: dict = None,
        # NEW Learning Effectiveness Audit fields
        components_failed: Union[list, None] = None,
        reused_lessons: Union[list, None] = None,
        lessons_retired: int = 0,
        components_tested: Union[list, None] = None,
        theory_id: Union[str, None] = None,
        principles_consulted: Union[list, None] = None,
        principles_accepted: Union[list, None] = None,
        principles_rejected: Union[list, None] = None,
        world_model_applied: bool = False,
        confidence_delta: float = 0.0,
        prediction_override_applied: bool = False,
        novelty_decision: Union[str, None] = None,
        novelty_score: float = 1.0,
        theory_metrics: Union[dict, None] = None,
    ):
        """Record cognition state for a day."""
        # v2.4 Persistence fallback
        if not theory_usefulness:
            theory_usefulness = {"score": 0.0, "label": "unknown"}

        self.days.append(
            {
                "day_index": day_index,
                "date": date,
                "confidence_state": confidence_state,
                "contradiction_result": contradiction_result,
                "theory_summary": theory_summary,
                "reflection_summary": reflection_summary,
                "market_regime": market_regime,
                "epistemic_quality": epistemic_quality or {},
                "prediction": prediction or {},
                "prior_prediction_result": prior_prediction_result or {},
                "regime_matches": regime_matches or [],
                "theory_usefulness": theory_usefulness,
                "transition_pressure": transition_pressure or {},
                "decisions": decisions or {},
                "candle_type": candle_type,
                "participation_strength": participation_strength,
                "participation_confirmation": participation_confirmation,
                # v2.0 dimensions
                "volume_state": volume_state,
                "volatility_regime": volatility_regime,
                "momentum_regime": momentum_regime,
                # v3.0 dimensions
                "regime_subtype": regime_subtype,
                "falsifiability_conditions": falsifiability_conditions or [],
                "analog_divergence_claim": analog_divergence_claim,
                "regime_history": regime_history,
                "branches_generated": branches_generated,
                "branch_stats": branch_stats or {},  # Store branch stats
                "intelligence": intelligence_data or {},
                "components_failed": components_failed or [],
                "reused_lessons": reused_lessons or [],
                "lessons_retired": lessons_retired,
                "components_tested": components_tested or [],
                "theory_id": theory_id or "",
                "principles_consulted": principles_consulted or [],
                "principles_accepted": principles_accepted or [],
                "principles_rejected": principles_rejected or [],
                "world_model_applied": world_model_applied,
                "confidence_delta": confidence_delta,
                "prediction_override_applied": prediction_override_applied,
                "novelty_decision": novelty_decision,
                "novelty_score": novelty_score,
                "theory_metrics": theory_metrics or {},
            }
        )

        if transition_memory_hit:
            self.transition_memory_hits += 1

        self.theory_metrics_history.append(theory_metrics or {})

        # Track confidence
        self.confidence_history.append(
            {
                "date": date,
                "empirical": confidence_state.get("empirical_confidence", 0),
                "regime": confidence_state.get("regime_confidence", 0),
                "reflection": confidence_state.get("reflection_confidence", 0),
                "coherence": confidence_state.get("theoretical_coherence", 0),
                "contradiction": confidence_state.get("contradiction_pressure", 0),
            }
        )

        # Track contradictions
        self.contradiction_history.append(
            {
                "date": date,
                "score": contradiction_result.get("score", 0),
                "count": len(
                    contradiction_result.get("contradictions")
                    or contradiction_result.get("indicators", [])
                ),
            }
        )

        # Track theory themes
        if theory_summary:
            self._extract_theme(theory_summary)

        # Track reflection patterns
        if reflection_summary:
            self._extract_reflection_pattern(reflection_summary)

        if epistemic_quality:
            self.epistemic_quality_history.append(epistemic_quality)

        if prediction or prior_prediction_result:
            # capture richer context for prediction auditing
            regime_sim = 0.0
            if regime_matches:
                try:
                    regime_sim = max(
                        (
                            m.get("similarity")
                            if isinstance(m, dict)
                            else getattr(m, "similarity", 0)
                        )
                        for m in regime_matches
                    )
                except Exception:
                    regime_sim = 0.0

            theory_usefulness_score = 0.0
            if theory_usefulness and isinstance(theory_usefulness, dict):
                theory_usefulness_score = theory_usefulness.get("score", 0.0)

            self.prediction_history.append(
                {
                    "date": date,
                    "market_name": market_name or self.market_name,
                    "prediction": prediction or {},
                    "prior_prediction_result": prior_prediction_result or {},
                    "regime_matches": regime_matches or [],
                    "contradiction_score": float(contradiction_result.get("score", 0)),
                    "regime_similarity": float(regime_sim),
                    "theory_usefulness": theory_usefulness,  # Store the full dict
                    "theory_summary": theory_summary,
                    "transition_pressure_score": (
                        float(transition_pressure.get("pressure_score", 0.0))
                        if transition_pressure
                        else 0.0
                    ),
                    "transition_breakout_risk": (
                        bool(transition_pressure.get("breakout_risk", False))
                        if transition_pressure
                        else False
                    ),
                    "participation_confirmation": participation_confirmation,
                    # v2.0 dimensions
                    "volume_state": volume_state,
                    "volatility_regime": volatility_regime,
                    "momentum_regime": momentum_regime,
                    "regime_subtype": regime_subtype,
                    "analog_divergence_claim": analog_divergence_claim,
                    "regime_history": regime_history,
                    "branches_generated": branches_generated,
                    "intelligence": intelligence_data or {},
                    "components_failed": components_failed or [],
                    "reused_lessons": reused_lessons or [],
                    "lessons_retired": lessons_retired,
                    "components_tested": components_tested or [],
                    "theory_id": theory_id or "",
                }
            )

        if transition_pressure:
            self.transition_pressure_history.append(
                {
                    "date": date,
                    "day_index": day_index,
                    "direction_bias": transition_pressure.get(
                        "direction_bias", "neutral"
                    ),
                    "pressure_score": float(
                        transition_pressure.get("pressure_score", 0.0)
                    ),
                    "stability_score": float(
                        transition_pressure.get("stability_score", 0.7)
                    ),
                    "breakout_risk": bool(
                        transition_pressure.get("breakout_risk", False)
                    ),
                    "drivers": transition_pressure.get("drivers", []),
                    "contradiction_score": float(contradiction_result.get("score", 0)),
                    "prediction_direction": (
                        prediction.get("direction", "uncertain")
                        if prediction
                        else "uncertain"
                    ),
                }
            )

        if decisions:
            self.decisions_history.append({"date": date, "decisions": decisions})

    def _extract_theme(self, theory_text: str):
        """Extract recurring themes from theory text."""
        keywords = [
            "momentum",
            "breadth",
            "volatility",
            "liquidity",
            "regime",
            "participation",
            "coherence",
            "structure",
            "trend",
            "reversal",
        ]

        lower_text = theory_text.lower()
        for keyword in keywords:
            if keyword in lower_text:
                self.theory_themes[keyword] += 1

    def _extract_reflection_pattern(self, reflection_text: str):
        """Extract reflection patterns."""
        patterns = [
            "uncertainty",
            "weakness",
            "divergence",
            "strength",
            "coherence",
            "instability",
            "structure",
            "support",
            "resistance",
        ]

        lower_text = reflection_text.lower()
        for pattern in patterns:
            if pattern in lower_text:
                self.reflection_patterns[pattern] += 1

    def analyze(self) -> Dict:
        """Run comprehensive analysis."""
        if not self.days:
            return {"status": "no_data", "message": "No replay days recorded"}

        analysis = {
            "market_name": self.market_name,
            "total_days": len(self.days),
            "date_range": (self.days[0]["date"], self.days[-1]["date"]),
            "confidence_analysis": self._analyze_confidence(),
            "contradiction_analysis": self._analyze_contradictions(),
            "theory_analysis": self._analyze_theories(),
            "epistemic_quality_analysis": self._analyze_epistemic_quality(),
            "coherence_analysis": self._analyze_coherence(),
            "transition_pressure_analysis": self._analyze_transition_pressure(),
            "capital_simulation_analysis": self._analyze_capital_simulation(),
            "prediction_analysis": self._analyze_predictions(),
            "prediction_intelligence": self._analyze_prediction_intelligence(),
            "transition_memory_analysis": self._analyze_transition_memory(),
            "prediction_history": self.prediction_history,
            "transition_pressure_history": self.transition_pressure_history,
            "config": self.config_snapshot,
            "risks": self._detect_cognition_risks(),
            "theory_mutation_metrics": self._analyze_theory_mutation_metrics(),
            "mechanism_metrics": self._analyze_mechanisms(),
        }

        return analysis

    def _analyze_theory_mutation_metrics(self) -> Dict:
        """Analyze theory complexity and mutation metrics."""
        if not self.theory_metrics_history:
            return {}

        from statistics import mean

        def safe_mean(values, default=0.0):
            val_list = [v for v in values if v is not None]
            return round(mean(val_list), 3) if val_list else default

        def safe_sum(values):
            return sum(v for v in values if v is not None)

        word_counts = [
            item.get("theory_word_count") for item in self.theory_metrics_history
        ]
        mech_counts = [
            item.get("mechanism_count") for item in self.theory_metrics_history
        ]
        clauses = [
            item.get("conditional_clauses_count")
            for item in self.theory_metrics_history
        ]
        exceptions = [
            item.get("exceptions_added") for item in self.theory_metrics_history
        ]
        retired = [
            item.get("mechanisms_retired") for item in self.theory_metrics_history
        ]
        added = [item.get("mechanisms_added") for item in self.theory_metrics_history]
        modified = [
            item.get("mechanisms_modified") for item in self.theory_metrics_history
        ]
        stability = [
            item.get("mechanism_stability") for item in self.theory_metrics_history
        ]

        words_before = safe_sum(
            [item.get("words_before_mutation") for item in self.theory_metrics_history]
        )
        words_after = safe_sum(
            [item.get("words_after_mutation") for item in self.theory_metrics_history]
        )
        mechs_before = safe_sum(
            [
                item.get("mechanisms_before_mutation")
                for item in self.theory_metrics_history
            ]
        )
        mechs_after = safe_sum(
            [
                item.get("mechanisms_after_mutation")
                for item in self.theory_metrics_history
            ]
        )

        # Compression achieved percentages
        word_comp_pct = (
            round(((words_before - words_after) / words_before * 100.0), 1)
            if words_before > 0
            else 0.0
        )
        mech_comp_pct = (
            round(((mechs_before - mechs_after) / mechs_before * 100.0), 1)
            if mechs_before > 0
            else 0.0
        )

        return {
            "avg_theory_word_count": safe_mean(word_counts),
            "avg_mechanism_count": safe_mean(mech_counts),
            "avg_conditional_clauses": safe_mean(clauses),
            "total_exceptions_added": safe_sum(exceptions),
            "total_mechanisms_retired": safe_sum(retired),
            "total_mechanisms_added": safe_sum(added),
            "total_mechanisms_modified": safe_sum(modified),
            "avg_mechanism_stability": safe_mean(stability, default=1.0),
            "words_before_mutation": words_before,
            "words_after_mutation": words_after,
            "word_compression_pct": word_comp_pct,
            "mechanisms_before_mutation": mechs_before,
            "mechanisms_after_mutation": mechs_after,
            "mechanism_compression_pct": mech_comp_pct,
        }

    def _analyze_confidence(self) -> Dict:
        """Analyze confidence evolution."""
        if not self.confidence_history:
            return {}

        empirical_conf = [c["empirical"] for c in self.confidence_history]
        regime_conf = [c["regime"] for c in self.confidence_history]
        coherence = [c["coherence"] for c in self.confidence_history]
        contradiction_pressure = [c["contradiction"] for c in self.confidence_history]

        return {
            "empirical_confidence": {
                "initial": empirical_conf[0] if empirical_conf else 0,
                "final": empirical_conf[-1] if empirical_conf else 0,
                "max": max(empirical_conf) if empirical_conf else 0,
                "min": min(empirical_conf) if empirical_conf else 0,
                "mean": mean(empirical_conf) if empirical_conf else 0,
                "trajectory": (
                    "rising"
                    if empirical_conf[-1] > empirical_conf[0]
                    else (
                        "declining"
                        if empirical_conf[-1] < empirical_conf[0]
                        else "stable"
                    )
                ),
            },
            "regime_confidence": {
                "initial": regime_conf[0] if regime_conf else 0,
                "final": regime_conf[-1] if regime_conf else 0,
                "mean": mean(regime_conf) if regime_conf else 0,
            },
            "theoretical_coherence": {
                "initial": coherence[0] if coherence else 0,
                "final": coherence[-1] if coherence else 0,
                "mean": mean(coherence) if coherence else 0,
                "trend": (
                    "degrading"
                    if coherence[-1] < coherence[0]
                    else (
                        "stable"
                        if abs(coherence[-1] - coherence[0]) < 0.1
                        else "improving"
                    )
                ),
            },
            "contradiction_pressure": {
                "initial": contradiction_pressure[0] if contradiction_pressure else 0,
                "final": contradiction_pressure[-1] if contradiction_pressure else 0,
                "mean": (mean(contradiction_pressure) if contradiction_pressure else 0),
                "increasing": contradiction_pressure[-1] > contradiction_pressure[0],
            },
        }

    def _analyze_contradictions(self) -> Dict:
        """Analyze contradiction dynamics."""
        if not self.contradiction_history:
            return {}

        scores = [c["score"] for c in self.contradiction_history]
        counts = [c["count"] for c in self.contradiction_history]

        # Detect persistent contradictions
        persistent = sum(1 for c in self.contradiction_history if c["count"] > 0)
        persistence_ratio = persistent / len(self.contradiction_history)

        return {
            "total_days_with_contradictions": persistent,
            "persistence_ratio": persistence_ratio,
            "score_trend": (
                "increasing"
                if scores[-1] > scores[0]
                else "decreasing" if scores[-1] < scores[0] else "stable"
            ),
            "mean_contradiction_score": mean(scores) if scores else 0,
            "max_contradiction_score": max(scores) if scores else 0,
            "observations": [
                (
                    "High contradiction persistence detected"
                    if persistence_ratio > 0.7
                    else "Moderate contradiction dynamics"
                ),
                (
                    "Contradiction pressure increasing"
                    if scores[-1] > scores[0]
                    else "Contradiction pressure decreasing"
                ),
            ],
        }

    def _analyze_theories(self) -> Dict:
        """Analyze theory evolution patterns."""
        return {
            "top_themes": sorted(
                self.theory_themes.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "theme_diversity": len(self.theory_themes),
            "theme_repetition_risk": (
                "high"
                if len(self.theory_themes) < 5
                else "moderate" if len(self.theory_themes) < 10 else "low"
            ),
        }

    def _analyze_coherence(self) -> Dict:
        """Analyze theoretical coherence dynamics."""
        coherence_vals = [c["coherence"] for c in self.confidence_history]

        if not coherence_vals:
            return {}

        # Detect coherence ceiling
        recent_coherence = (
            coherence_vals[-20:] if len(coherence_vals) > 20 else coherence_vals
        )
        coherence_ceiling = max(recent_coherence)
        coherence_mean = mean(recent_coherence)

        coherence_stagnation = (
            max(coherence_vals) - min(coherence_vals) < 0.1 if coherence_vals else False
        )

        return {
            "coherence_ceiling": coherence_ceiling,
            "coherence_mean": coherence_mean,
            "coherence_stagnation": coherence_stagnation,
            "coherence_trend": (
                "declining"
                if coherence_vals[-1] < coherence_vals[0]
                else (
                    "stable"
                    if abs(coherence_vals[-1] - coherence_vals[0]) < 0.1
                    else "improving"
                )
            ),
            "risk_assessment": (
                "High coherence stagnation risk"
                if coherence_stagnation
                else "Moderate coherence dynamics"
            ),
        }

    def _analyze_epistemic_quality(self) -> Dict:
        """Analyze compression and epistemic posture metrics."""
        if not self.epistemic_quality_history:
            return {}

        theory_metrics = [
            item.get("theory", {})
            for item in self.epistemic_quality_history
            if item.get("theory")
        ]
        reflection_metrics = [
            item.get("reflection", {})
            for item in self.epistemic_quality_history
            if item.get("reflection")
        ]

        return {
            "theory": self._mean_quality_metrics(theory_metrics),
            "reflection": self._mean_quality_metrics(reflection_metrics),
        }

    def _mean_quality_metrics(self, metric_rows: List[dict]) -> Dict:
        if not metric_rows:
            return {}

        metric_names = [
            "narrative_density",
            "uncertainty_presence",
            "contradiction_acknowledgment",
            "abstraction_sharpness",
            "causal_inflation",
            "semantic_repetition",
            "compression_score",
        ]
        return {
            name: round(
                mean(row.get(name, 0) for row in metric_rows),
                3,
            )
            for name in metric_names
        }

    def _analyze_transition_pressure(self) -> Dict:
        """Analyze transition pressure patterns with detailed calibration metrics."""
        if not self.transition_pressure_history:
            return {
                "status": "no_data",
                "message": "No transition pressure data recorded",
            }

        tp_data = self.transition_pressure_history

        # Basic metrics
        pressure_scores = [d["pressure_score"] for d in tp_data]
        stability_scores = [d["stability_score"] for d in tp_data]

        # TUNED METRICS: New breakpoints for calibration audit
        high_pressure_gt_0_5 = [d for d in tp_data if d["pressure_score"] > 0.5]
        high_pressure_gt_0_7 = [d for d in tp_data if d["pressure_score"] > 0.7]
        breakout_risk_count = sum(1 for d in tp_data if d["breakout_risk"])

        # Previous threshold (0.6) for backward compatibility
        high_pressure_days = [d for d in tp_data if d["pressure_score"] > 0.6]

        # Accuracy analysis when pressure > 0.5
        accuracy_when_pressure_gt_0_5 = 0.0
        if high_pressure_gt_0_5:
            correct = sum(
                1
                for d in high_pressure_gt_0_5
                if "prior_prediction_result" in d
                and d.get("prior_prediction_result", {}).get("direction_score", 0)
                >= 0.5
            )
            accuracy_when_pressure_gt_0_5 = correct / len(high_pressure_gt_0_5)

        # Accuracy when pressure > 0.7
        accuracy_when_pressure_gt_0_7 = 0.0
        if high_pressure_gt_0_7:
            correct = sum(
                1
                for d in high_pressure_gt_0_7
                if "prior_prediction_result" in d
                and d.get("prior_prediction_result", {}).get("direction_score", 0)
                >= 0.5
            )
            accuracy_when_pressure_gt_0_7 = correct / len(high_pressure_gt_0_7)

        # Accuracy analysis when pressure > 0.6 (legacy)
        accuracy_when_high_pressure = 0.0
        if high_pressure_days:
            correct_high_pressure = sum(
                1
                for d in high_pressure_days
                if "prior_prediction_result" in d
                and d.get("prior_prediction_result", {}).get("direction_score", 0)
                >= 0.5
            )
            accuracy_when_high_pressure = correct_high_pressure / len(
                high_pressure_days
            )

        # Accuracy when breakout_risk=True
        breakout_risk_days = [d for d in tp_data if d["breakout_risk"]]
        accuracy_when_breakout_risk = 0.0
        if breakout_risk_days:
            correct_breakout = sum(
                1
                for d in breakout_risk_days
                if "prior_prediction_result" in d
                and d.get("prior_prediction_result", {}).get("direction_score", 0)
                >= 0.5
            )
            accuracy_when_breakout_risk = correct_breakout / len(breakout_risk_days)

        # Transition capture rate: pressure > 0.5 AND directional move
        transition_attempts = sum(
            1 for d in tp_data if d["direction_bias"] in ["higher", "lower"]
        )
        transition_hits = sum(
            1
            for d in tp_data
            if d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") in ["higher", "lower"]
        )
        transition_hit_rate = (
            transition_hits / transition_attempts if transition_attempts > 0 else 0.0
        )

        # TUNED: High-pressure transition capture (when pressure > 0.5 + directional bias)
        high_pressure_directional = sum(
            1
            for d in high_pressure_gt_0_5
            if d["direction_bias"] in ["higher", "lower"]
        )
        high_pressure_transitions_captured = sum(
            1
            for d in high_pressure_gt_0_5
            if d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") in ["higher", "lower"]
        )
        transition_capture_under_high_pressure = (
            high_pressure_transitions_captured / high_pressure_directional
            if high_pressure_directional > 0
            else 0.0
        )

        # False positives: high pressure but direction missed
        false_positives = sum(
            1
            for d in high_pressure_gt_0_5
            if d.get("prediction_direction") == "uncertain"
        )

        # False negatives: low pressure but missed actual move (proxy: low stability + move happened)
        false_negatives = sum(
            1
            for d in tp_data
            if d["stability_score"] < 0.4
            and d.get("prediction_direction") in ["higher", "lower"]
        )

        # TUNED: Missed transitions analysis with pressure context
        missed_high_pressure = [
            d
            for d in tp_data
            if d["pressure_score"] > 0.5
            and d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") == "uncertain"
        ]
        missed_high_pressure_avg_score = (
            mean([d["pressure_score"] for d in missed_high_pressure])
            if missed_high_pressure
            else 0.0
        )

        # Direction bias distribution
        direction_counts = {"higher": 0, "lower": 0, "neutral": 0}
        for d in tp_data:
            direction = d.get("direction_bias", "neutral")
            if direction in direction_counts:
                direction_counts[direction] += 1

        # Driver frequency
        driver_frequency = defaultdict(int)
        for d in tp_data:
            for driver in d.get("drivers", []):
                driver_frequency[driver] += 1

        return {
            "total_days": len(tp_data),
            "avg_pressure": float(mean(pressure_scores)) if pressure_scores else 0.0,
            "avg_stability": float(mean(stability_scores)) if stability_scores else 0.7,
            "pressure_distribution": {
                "gt_0_5": len(high_pressure_gt_0_5),
                "gt_0_6": len(high_pressure_days),
                "gt_0_7": len(high_pressure_gt_0_7),
            },
            "high_pressure_rate_0_5": (
                len(high_pressure_gt_0_5) / len(tp_data) if tp_data else 0.0
            ),
            "high_pressure_rate_0_7": (
                len(high_pressure_gt_0_7) / len(tp_data) if tp_data else 0.0
            ),
            "accuracy_when_pressure_gt_0_5": round(accuracy_when_pressure_gt_0_5, 3),
            "accuracy_when_pressure_gt_0_6": round(accuracy_when_high_pressure, 3),
            "accuracy_when_pressure_gt_0_7": round(accuracy_when_pressure_gt_0_7, 3),
            "breakout_risk_count": breakout_risk_count,
            "breakout_risk_rate": (
                breakout_risk_count / len(tp_data) if tp_data else 0.0
            ),
            "accuracy_when_breakout_risk": round(accuracy_when_breakout_risk, 3),
            "transition_hit_rate": round(transition_hit_rate, 3),
            "transition_capture_under_high_pressure": round(
                transition_capture_under_high_pressure, 3
            ),
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "missed_high_pressure_count": len(missed_high_pressure),
            "missed_high_pressure_avg_score": round(missed_high_pressure_avg_score, 3),
            "direction_bias_distribution": direction_counts,
            "top_drivers": sorted(
                driver_frequency.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def _analyze_predictions(self) -> Dict:
        """Analyze prediction probe performance."""
        if not self.prediction_history:
            return {}

        aligned_predictions = []
        for i in range(1, len(self.prediction_history)):
            current_day_record = self.prediction_history[i]
            previous_day_prediction_record = self.prediction_history[i - 1]

            if current_day_record.get(
                "prior_prediction_result"
            ) and previous_day_prediction_record.get("prediction"):
                aligned_predictions.append(
                    {
                        "date": current_day_record["date"],
                        "prediction": previous_day_prediction_record["prediction"],
                        "prior_prediction_result": current_day_record[
                            "prior_prediction_result"
                        ],
                        "contradiction_score": previous_day_prediction_record.get(
                            "contradiction_score", 0.0
                        ),
                        "regime_similarity": previous_day_prediction_record.get(
                            "regime_similarity", 0.0
                        ),
                        "theory_usefulness": previous_day_prediction_record.get(
                            "theory_usefulness"
                        ),
                        "theory_summary": previous_day_prediction_record.get(
                            "theory_summary", ""
                        ),
                        "transition_pressure_score": previous_day_prediction_record.get(
                            "transition_pressure_score", 0.0
                        ),
                        "transition_breakout_risk": previous_day_prediction_record.get(
                            "transition_breakout_risk", False
                        ),
                        "components_failed": previous_day_prediction_record.get(
                            "components_failed", []
                        ),
                        "reused_lessons": previous_day_prediction_record.get(
                            "reused_lessons", []
                        ),
                        "lessons_retired": previous_day_prediction_record.get(
                            "lessons_retired", 0
                        ),
                        "regime_matches": previous_day_prediction_record.get(
                            "regime_matches", []
                        ),
                    }
                )

        total = len(self.prediction_history)
        scored_count = len(aligned_predictions)

        def is_correct(row):
            return row["prior_prediction_result"].get("direction_score", 0) == 1.0

        def is_partial(row):
            return row["prior_prediction_result"].get("direction_score", 0) == 0.5

        correct = sum(1 for r in aligned_predictions if is_correct(r))
        partial = sum(1 for r in aligned_predictions if is_partial(r))
        mean_conf = (
            mean([r["prediction"].get("confidence", 0) for r in aligned_predictions])
            if aligned_predictions
            else 0.0
        )

        # Task 2.1: Median Confidence
        conf_list = [r["prediction"].get("confidence", 0) for r in aligned_predictions]
        median_conf = median(conf_list) if conf_list else 0.0

        # By direction
        directions = ["higher", "lower", "range_bound"]
        accuracy_by_direction = {}
        for d in directions:
            rows = [
                r
                for r in aligned_predictions
                if r.get("prediction", {}).get("direction") == d
            ]
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0

            # Task 2.2: Extended direction metrics
            partial_acc = (
                (
                    sum(1 for r in rows if is_correct(r))
                    + sum(1 for r in rows if is_partial(r))
                )
                / cnt
                if cnt
                else 0.0
            )
            avg_conf_dir = (
                statistics.mean([r["prediction"].get("confidence", 0) for r in rows])
                if cnt
                else 0.0
            )
            accuracy_by_direction[d] = {
                "count": cnt,
                "accuracy": acc,
                "partial_accuracy": partial_acc,
                "avg_confidence": avg_conf_dir,
            }

        # Contradiction buckets
        def bucket(score: float) -> str:
            if score >= 0.66:
                return "high"
            if score >= 0.33:
                return "medium"
            return "low"

        buckets = {"low": [], "medium": [], "high": []}
        for r in aligned_predictions:
            b = bucket(r.get("contradiction_score", 0.0))
            buckets[b].append(r)

        accuracy_by_contradiction = {}
        for bname, rows in buckets.items():
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0
            accuracy_by_contradiction[bname] = {"count": cnt, "accuracy": acc}

        # v1.5 Confidence Calibration Buckets (0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
        cal_buckets = {
            "0.0-0.2": [],
            "0.2-0.4": [],
            "0.4-0.6": [],
            "0.6-0.8": [],
            "0.8-1.0": [],
        }
        for r in aligned_predictions:
            c = r["prediction"].get("confidence", 0.0)
            if c < 0.2:
                cal_buckets["0.0-0.2"].append(r)
            elif c < 0.4:
                cal_buckets["0.2-0.4"].append(r)
            elif c < 0.6:
                cal_buckets["0.4-0.6"].append(r)
            elif c < 0.8:
                cal_buckets["0.6-0.8"].append(r)
            else:
                cal_buckets["0.8-1.0"].append(r)

        accuracy_by_confidence_bucket = {}
        gaps = []
        for bname, rows in cal_buckets.items():
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0
            p_acc = (
                (
                    sum(1 for r in rows if is_correct(r))
                    + sum(1 for r in rows if is_partial(r))
                )
                / cnt
                if cnt
                else 0.0
            )
            avg_c = (
                statistics.mean([r["prediction"].get("confidence", 0) for r in rows])
                if cnt
                else 0.0
            )

            gap = avg_c - acc if cnt else 0.0
            if cnt > 0:
                gaps.append(abs(gap))

            accuracy_by_confidence_bucket[bname] = {
                "count": cnt,
                "actual_accuracy": acc,
                "partial_accuracy": p_acc,
                "avg_confidence": avg_c,
                "gap": gap,
            }

        calibration_score = statistics.mean(gaps) if gaps else 0.0

        # Usefulness Bands
        useful_buckets = {"0-0.3": [], "0.3-0.5": [], "0.5-0.7": [], "0.7+": []}
        for r in aligned_predictions:
            v = extract_usefulness_score(r.get("theory_usefulness", 0.0))
            if v < 0.3:
                useful_buckets["0-0.3"].append(r)
            elif v < 0.5:
                useful_buckets["0.3-0.5"].append(r)
            elif v < 0.7:
                useful_buckets["0.5-0.7"].append(r)
            else:
                useful_buckets["0.7+"].append(r)

        accuracy_by_usefulness = {
            b: {
                "count": len(rs),
                "accuracy": (
                    sum(1 for r in rs if is_correct(r)) / len(rs) if rs else 0.0
                ),
            }
            for b, rs in useful_buckets.items()
        }

        # Contradiction Bands
        contra_buckets = {"0-0.2": [], "0.2-0.5": [], "0.5+": []}
        for r in aligned_predictions:
            v = r.get("contradiction_score", 0.0)
            if v < 0.2:
                contra_buckets["0-0.2"].append(r)
            elif v < 0.5:
                contra_buckets["0.2-0.5"].append(r)
            else:
                contra_buckets["0.5+"].append(r)

        accuracy_by_contradiction_severity = {
            b: {
                "count": len(rs),
                "accuracy": (
                    sum(1 for r in rs if is_correct(r)) / len(rs) if rs else 0.0
                ),
            }
            for b, rs in contra_buckets.items()
        }

        # Theory Usefulness Analysis
        usefulness_scores = []
        missing_usefulness_count = 0
        for r in aligned_predictions:
            tu = r.get("theory_usefulness")
            # Ensure it's a dict and has 'score' and 'label'
            if tu and isinstance(tu, dict) and "score" in tu and "label" in tu:
                usefulness_scores.append(tu["score"])
            else:
                missing_usefulness_count += 1

        avg_theory_usefulness = mean(usefulness_scores) if usefulness_scores else 0.0
        high_usefulness_days = sum(1 for s in usefulness_scores if s > 0.7)

        # Accuracy when usefulness > 0.7
        high_usefulness_predictions = [
            r
            for r in aligned_predictions
            if r.get("theory_usefulness", {}).get("score", 0.0) > 0.7
        ]
        accuracy_when_high_usefulness = (
            sum(1 for r in high_usefulness_predictions if is_correct(r))
            / len(high_usefulness_predictions)
            if high_usefulness_predictions
            else 0.0
        )

        # Prediction Drift
        change_count = 0
        if len(self.prediction_history) > 1:
            for i in range(1, len(self.prediction_history)):
                if self.prediction_history[i - 1]["prediction"].get(
                    "direction"
                ) != self.prediction_history[i]["prediction"].get("direction"):
                    change_count += 1
        prediction_drift = (
            change_count / (len(self.prediction_history) - 1)
            if len(self.prediction_history) > 1
            else 0.0
        )

        # Rolling Confidence Drift
        conf_vals = [
            r["prediction"].get("confidence", 0) for r in self.prediction_history
        ]
        rolling_drift = {
            "7d": statistics.mean(conf_vals[-7:]) if len(conf_vals) >= 7 else 0.0,
            "15d": statistics.mean(conf_vals[-15:]) if len(conf_vals) >= 15 else 0.0,
        }

        # Task 2.2: Add 'uncertain'
        uncertain_rows = [
            r
            for r in aligned_predictions
            if r.get("prediction", {}).get("direction")
            == PredictionDirection.uncertain.value
        ]
        avg_conf_uncertain = (
            mean([r["prediction"].get("confidence", 0) for r in uncertain_rows])
            if uncertain_rows
            else 0.0
        )
        accuracy_by_direction["uncertain"] = {
            "count": len(uncertain_rows),
            "accuracy": 0.0,
            "partial_accuracy": 0.0,
            "avg_confidence": avg_conf_uncertain,
        }

        # Regime similarity > 0.9
        high_regime = [
            r for r in aligned_predictions if r.get("regime_similarity", 0.0) > 0.9
        ]
        regime_acc = (
            sum(1 for r in high_regime if is_correct(r)) / len(high_regime)
            if high_regime
            else 0.0
        )

        # Theory usefulness > 0.5
        useful = [
            r
            for r in aligned_predictions
            if extract_usefulness_score(r.get("theory_usefulness", 0.0)) > 0.5
        ]
        useful_acc = (
            sum(1 for r in useful if is_correct(r)) / len(useful) if useful else 0.0
        )

        # Task 2.4: Prediction slices by pressure
        pressure_gt_0_5 = [
            r
            for r in aligned_predictions
            if r.get("transition_pressure_score", 0.0) > 0.5
        ]
        acc_pressure_gt_0_5 = (
            sum(1 for r in pressure_gt_0_5 if is_correct(r)) / len(pressure_gt_0_5)
            if pressure_gt_0_5
            else 0.0
        )

        pressure_gt_0_7 = [
            r
            for r in aligned_predictions
            if r.get("transition_pressure_score", 0.0) > 0.7
        ]
        acc_pressure_gt_0_7 = (
            sum(1 for r in pressure_gt_0_7 if is_correct(r)) / len(pressure_gt_0_7)
            if pressure_gt_0_7
            else 0.0
        )

        # Task 2.5: False breakout
        false_breakouts = [
            r
            for r in aligned_predictions
            if r.get("transition_breakout_risk") and not is_correct(r)
        ]

        # Task 2.6: Best breakout capture
        best_breakout_captures = [
            r
            for r in aligned_predictions
            if r.get("transition_breakout_risk")
            and is_correct(r)
            and r["prediction"].get("direction")
            in [PredictionDirection.higher.value, PredictionDirection.lower.value]
        ]

        # Missed transition cases: range_bound -> higher / lower
        missed_range_to_higher = [
            r
            for r in aligned_predictions
            if r.get("prediction", {}).get("direction") == "range_bound"
            and r.get("prior_prediction_result", {}).get("actual_direction") == "higher"
            and not is_correct(r)
        ]
        missed_range_to_lower = [
            r
            for r in aligned_predictions
            if r.get("prediction", {}).get("direction") == "range_bound"
            and r.get("prior_prediction_result", {}).get("actual_direction") == "lower"
            and not is_correct(r)
        ]

        def sample_top(rows, n=5):
            return [
                {
                    "date": r.get("date"),
                    "theory_summary": r.get("theory_summary", ""),
                    "confidence": r.get("prediction", {}).get("confidence"),
                }
                for r in rows[:n]
            ]

        correlation_coeff = 0.0
        confidences = [
            r["prediction"].get("confidence", 0)
            for r in aligned_predictions
            if r.get("prediction")
        ]
        scores = [
            r["prior_prediction_result"].get("direction_score", 0)
            for r in aligned_predictions
        ]
        if len(confidences) > 1 and len(scores) > 1:
            try:
                correlation_val = statistics.correlation(confidences, scores)
                correlation_coeff = correlation_val
            except Exception:
                correlation_coeff = 0.0

        return {
            "total_predictions": total,
            "scored_predictions": scored_count,
            "accuracy": correct / scored_count if scored_count else 0.0,
            "partial_accuracy": (
                (correct + partial) / scored_count if scored_count else 0.0
            ),
            "uncertain_rate": (
                sum(
                    1
                    for r in self.prediction_history
                    if r.get("prediction", {}).get("direction") == "uncertain"
                )
                / total
                if total
                else 0.0
            ),
            "invalidation_rate": (
                sum(
                    1
                    for r in aligned_predictions
                    if r.get("prior_prediction_result", {}).get(
                        "invalidation_triggered"
                    )
                )
                / scored_count
                if scored_count
                else 0.0
            ),
            "mean_confidence": mean_conf,
            "median_confidence": median_conf,
            "confidence_accuracy_correlation": round(correlation_coeff, 3),
            "accuracy_by_direction": accuracy_by_direction,
            "accuracy_by_contradiction_bucket": accuracy_by_contradiction,
            "accuracy_by_confidence_bucket": accuracy_by_confidence_bucket,
            "calibration_score": round(calibration_score, 3),
            "prediction_drift": round(prediction_drift, 3),
            "rolling_drift": rolling_drift,
            "accuracy_when_pressure_gt_0_5": round(acc_pressure_gt_0_5, 3),
            "accuracy_when_pressure_gt_0_7": round(acc_pressure_gt_0_7, 3),
            "accuracy_regime_similarity_gt_0_9": regime_acc,
            "accuracy_theory_usefulness_gt_0_5": useful_acc,
            "accuracy_by_usefulness": accuracy_by_usefulness,
            "accuracy_by_contradiction_severity": accuracy_by_contradiction_severity,
            "missed_range_to_higher": {
                "count": len(missed_range_to_higher),
                "samples": sample_top(missed_range_to_higher),
            },
            "missed_range_to_lower": {
                "count": len(missed_range_to_lower),
                "samples": sample_top(missed_range_to_lower),
            },
            "false_breakouts": {
                "count": len(false_breakouts),
                "samples": sample_top(false_breakouts),
            },
            "best_breakout_captures": {
                "count": len(best_breakout_captures),
                "samples": sample_top(best_breakout_captures),
            },
            "avg_theory_usefulness": avg_theory_usefulness,
            "high_usefulness_days": high_usefulness_days,
            "accuracy_when_high_usefulness": accuracy_when_high_usefulness,
            "missing_usefulness_values": missing_usefulness_count,
        }

    def _analyze_prediction_intelligence(self) -> Dict:
        """Analyze longitudinal prediction intelligence and learning effectiveness."""
        if not self.prediction_history:
            return {}

        # Create a temporally aligned list of predictions and their outcomes
        # Each entry in prediction_history[i] contains:
        #   - "prediction": The prediction made ON day_i for day_i+1
        #   - "prior_prediction_result": The evaluation of the prediction made ON day_i-1 for day_i
        # To correctly analyze, we need to pair prediction_history[i-1]["prediction"] with
        # prediction_history[i]["prior_prediction_result"].

        aligned_predictions = []
        for i in range(1, len(self.prediction_history)):
            current_day_record = self.prediction_history[i]
            previous_day_prediction_record = self.prediction_history[i - 1]

            if current_day_record.get(
                "prior_prediction_result"
            ) and previous_day_prediction_record.get("prediction"):
                aligned_predictions.append(
                    {
                        "date": current_day_record["date"],
                        "theory_family": previous_day_prediction_record.get(
                            "regime_subtype", "neutral"
                        ),
                        "predicted_direction": previous_day_prediction_record[
                            "prediction"
                        ].get("direction"),
                        "actual_direction": current_day_record[
                            "prior_prediction_result"
                        ].get("actual_direction"),
                        "direction_score": current_day_record[
                            "prior_prediction_result"
                        ].get("direction_score"),
                        "intelligence": previous_day_prediction_record.get(
                            "intelligence", {}
                        ),
                        "volatility_regime": previous_day_prediction_record.get(
                            "volatility_regime", "normal"
                        ),
                        "volume_state": previous_day_prediction_record.get(
                            "volume_state", "normal"
                        ),
                    }
                )

        if not aligned_predictions:
            return {}

        # 1. Theory Family Accuracy
        family_stats = defaultdict(list)
        for r in aligned_predictions:
            family_stats[r["theory_family"]].append(r["direction_score"])

        # Trend Persistence Intelligence (Phase 5)
        persistence_stats = defaultdict(list)
        blindness_violations = 0
        alignment_hits = 0
        alignment_total = 0

        for r in aligned_predictions:
            p_intel = r["intelligence"].get("directional_persistence", {})
            p_regime = p_intel.get("regime", "Mixed")
            p_score_5d = p_intel.get("5d", 0.0)

            persistence_stats[p_regime].append(r["direction_score"])

            # Blindness Audit: Strong trend but predicted Range
            if (
                p_regime in ["Persistent Higher", "Persistent Lower"]
                and r["predicted_direction"] == "range_bound"
            ):
                blindness_violations += 1

            if r["predicted_direction"] != "uncertain":
                alignment_total += 1
                p_sign = 1 if p_score_5d > 0.3 else -1 if p_score_5d < -0.3 else 0
                pred_sign = (
                    1
                    if r["predicted_direction"] == "higher"
                    else -1 if r["predicted_direction"] == "lower" else 0
                )
                if p_sign == pred_sign:
                    alignment_hits += 1

        theory_family_accuracy = {
            fam: {"accuracy": mean(scores), "count": len(scores)}
            for fam, scores in family_stats.items()
        }

        # 2. Mutation Effectiveness (Depth)
        mutation_buckets = defaultdict(list)
        for r in aligned_predictions:
            depth = r["intelligence"].get("theory_mutation_count", 0)
            mutation_buckets[depth].append(r["direction_score"])

        mutation_effectiveness = {
            depth: {"accuracy": mean(scores), "count": len(scores)}
            for depth, scores in mutation_buckets.items()
        }

        # 3. Regime Accuracy
        direction_regime = defaultdict(list)
        volatility_regime = defaultdict(list)
        volume_regime = defaultdict(list)

        for r in aligned_predictions:
            direction_regime[r["actual_direction"]].append(r["direction_score"])
            volatility_regime[r["volatility_regime"]].append(r["direction_score"])
            volume_regime[r["volume_state"]].append(r["direction_score"])

        regime_accuracy = {
            "direction": {
                k: {"accuracy": mean(v), "count": len(v)}
                for k, v in direction_regime.items()
            },
            "volatility": {
                k: {"accuracy": mean(v), "count": len(v)}
                for k, v in volatility_regime.items()
            },
            "volume": {
                k: {"accuracy": mean(v), "count": len(v)}
                for k, v in volume_regime.items()
            },
        }

        # 4. Contradiction Intelligence (Aligned)
        contra_buckets = {"0": [], "1-3": [], "3-5": [], "5+": []}
        for r in aligned_predictions:
            c = r["intelligence"].get("contradiction_count", 0)
            if c == 0:
                contra_buckets["0"].append(r["direction_score"])
            elif c <= 3:
                contra_buckets["1-3"].append(r["direction_score"])
            elif c <= 5:
                contra_buckets["3-5"].append(r["direction_score"])
            else:
                contra_buckets["5+"].append(r["direction_score"])

        contradiction_intelligence = {
            k: {"accuracy": mean(v) if v else 0.0, "count": len(v)}
            for k, v in contra_buckets.items()
        }

        # 5. Confusion Matrix (Aligned)
        dirs = ["higher", "lower", "range_bound", "uncertain"]
        matrix = {d: {act: 0 for act in dirs} for d in dirs}
        for r in aligned_predictions:
            pred = r["predicted_direction"]
            act = r["actual_direction"]
            if pred in matrix and act in matrix[pred]:
                matrix[pred][act] += 1

        # 6. Learning Trend (Thirds)
        n_aligned = len(aligned_predictions)
        segments = {
            "first": aligned_predictions[: n_aligned // 3],
            "middle": aligned_predictions[n_aligned // 3 : 2 * n_aligned // 3],
            "final": aligned_predictions[2 * n_aligned // 3 :],
        }
        learning_trend = {
            k: mean([r["direction_score"] for r in v]) if v else 0.0
            for k, v in segments.items()
        }

        # 7. Drift and Convergence
        # Best/Worst Family
        sorted_fams = sorted(
            theory_family_accuracy.items(), key=lambda x: x[1]["accuracy"], reverse=True
        )
        best_family = sorted_fams[0][0] if sorted_fams else "N/A"
        worst_family = sorted_fams[-1][0] if sorted_fams else "N/A"

        # Mutation Insight
        depths = sorted(mutation_effectiveness.keys())
        base_acc = mutation_effectiveness.get(0, {}).get("accuracy", 0.0)
        max_depth = depths[-1] if depths else 0
        final_acc = mutation_effectiveness.get(max_depth, {}).get("accuracy", 0.0)
        mutation_trend = (
            "Improving"
            if final_acc > base_acc
            else "Degrading" if final_acc < base_acc else "Stable"
        )

        # Drift
        pred_changes = 0
        for i in range(1, len(self.prediction_history)):
            if self.prediction_history[i]["prediction"].get(
                "direction"
            ) != self.prediction_history[i - 1]["prediction"].get("direction"):
                pred_changes += 1

        prediction_drift = (
            pred_changes / (len(self.prediction_history) - 1)
            if len(self.prediction_history) > 1
            else 0.0
        )

        mutations = sum(
            1
            for r in self.prediction_history
            if r.get("intelligence", {}).get("mutation_count", 0) > 0
        )
        theory_drift = (
            mutations / len(self.prediction_history) if self.prediction_history else 0.0
        )
        accuracy_drift = learning_trend["final"] - learning_trend["first"]

        # Audit
        audit = []
        for r in self.prediction_history:
            res = r.get("prior_prediction_result", {})
            audit.append(
                {
                    "date": r["date"],
                    "actual": res.get("actual_direction", "N/A"),
                    "predicted": r["prediction"].get("direction", "N/A"),
                    "persistence": r.get("intelligence", {})
                    .get("directional_persistence", {})
                    .get("10d", 0.0),
                    "result": (
                        "PASS"
                        if res.get("direction_score", 0) == 1.0
                        else (
                            "FAIL"
                            if res.get("direction_score", 0) == 0.0
                            else "PARTIAL"
                        )
                    ),
                }
            )

        return {
            "theory_family_accuracy": theory_family_accuracy,
            "mutation_effectiveness": mutation_effectiveness,
            "regime_accuracy": regime_accuracy,
            "contradiction_intelligence": contradiction_intelligence,
            "directional_bias": matrix,
            "learning_trend": learning_trend,
            "best_family": best_family,
            "worst_family": worst_family,
            "mutation_trend_label": mutation_trend,
            "persistence_intelligence": {
                "accuracy_by_regime": {
                    k: {"accuracy": mean(v), "count": len(v)}
                    for k, v in persistence_stats.items()
                },
                "blindness_violations": blindness_violations,
                "alignment_score": (
                    alignment_hits / alignment_total if alignment_total > 0 else 0.0
                ),
            },
            "convergence": {
                "prediction_drift": prediction_drift,
                "theory_drift": theory_drift,
                "accuracy_drift": accuracy_drift,
            },
            "trend_audit": audit,
        }

    def _detect_cognition_risks(self) -> List:
        """Detect potential cognition dysfunctions."""
        risks = []

        if not self.confidence_history or not self.contradiction_history:
            return risks

        # Overconfidence drift
        empirical_conf = [c["empirical"] for c in self.confidence_history]
        if len(empirical_conf) > 10:
            recent_mean = mean(empirical_conf[-10:])
            early_mean = mean(empirical_conf[:10])
            if recent_mean > early_mean + 0.2:
                risks.append(
                    {
                        "type": "overconfidence_drift",
                        "severity": "high",
                        "description": "Confidence increasing despite outcome validation",
                    }
                )

        # Contradiction suppression
        contradiction_scores = [c["score"] for c in self.contradiction_history]
        if len(contradiction_scores) > 10:
            if max(contradiction_scores[-10:]) < 0.3:
                risks.append(
                    {
                        "type": "contradiction_suppression",
                        "severity": "moderate",
                        "description": "Contradiction pressure artificially low",
                    }
                )

        # Theory rigidity
        if len(self.theory_themes) < 3:
            risks.append(
                {
                    "type": "theory_rigidity",
                    "severity": "high",
                    "description": "Very limited theory diversity; potential rigidity",
                }
            )

        # Coherence degradation
        coherence_vals = [c["coherence"] for c in self.confidence_history]
        if len(coherence_vals) > 20:
            if coherence_vals[-1] < coherence_vals[0] * 0.7:
                risks.append(
                    {
                        "type": "coherence_degradation",
                        "severity": "high",
                        "description": "Theoretical coherence declining significantly",
                    }
                )

        # Reflection stagnation
        if len(self.reflection_patterns) < 3:
            risks.append(
                {
                    "type": "reflection_stagnation",
                    "severity": "moderate",
                    "description": "Limited reflection diversity; potential shallow introspection",
                }
            )

        return risks

    def _analyze_capital_simulation(self) -> Dict:
        """Analyze capital simulation results."""
        return getattr(self, "capital_simulation_summary", {})

    def set_capital_simulation_summary(self, summary: dict):
        """Set the summary of capital simulation."""
        self.capital_simulation_summary = summary

    def _analyze_transition_memory(self) -> Dict:
        """Analyze transition memory performance."""
        return {
            "total_transition_memory_hits": self.transition_memory_hits,
            "hit_rate": (
                self.transition_memory_hits / len(self.days)
                if len(self.days) > 0
                else 0.0
            ),
        }

    def set_capital_simulation_logs(self, logs: list):
        """WIRING FIX: Set daily logs from capital simulator."""
        self.capital_simulation_logs = logs

    def export_prediction_analysis_csv(self, file_path: Path):
        """Export prediction analysis and capital simulation data to CSV."""
        from pathlib import Path

        import pandas as pd

        if not self.prediction_history or not self.capital_simulation_logs:
            print("No data to export for prediction analysis CSV.")
            return

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine prediction history and capital simulation logs
        # Assuming both lists are ordered by date/day_index and have the same length
        combined_data = []
        rows = min(len(self.prediction_history), len(self.capital_simulation_logs))
        if rows == 0:
            print("No data to export for prediction analysis CSV.")
            return

        for i in range(rows):
            pred_rec = self.prediction_history[i] or {}
            cap_rec = self.capital_simulation_logs[i] or {}
            prediction = pred_rec.get("prediction") or {}

            # The actual outcome for prediction i (made on day i for day i+1)
            # is evaluated and stored in prior_prediction_result of day i+1
            actual_dir = None
            if i + 1 < len(self.prediction_history):
                next_rec = self.prediction_history[i + 1] or {}
                next_res = next_rec.get("prior_prediction_result") or {}
                if hasattr(next_res, "to_dict"):
                    next_res = next_res.to_dict()
                if isinstance(next_res, dict):
                    actual_dir = next_res.get("actual_direction")

            if hasattr(prediction, "to_dict"):
                prediction = prediction.to_dict()

            if not isinstance(prediction, dict):
                prediction = {}
            if not isinstance(cap_rec, dict):
                cap_rec = {}

            baseline = (
                cap_rec.get("policies", {}).get("baseline", {})
                if isinstance(cap_rec, dict)
                else {}
            )

            combined_data.append(
                {
                    "date": pred_rec.get("date"),
                    "prediction_direction": prediction.get("direction"),
                    "prediction_confidence": prediction.get("confidence")
                    or baseline.get("conviction"),
                    "actual_direction": actual_dir,
                    "transition_pressure_score": pred_rec.get(
                        "transition_pressure_score"
                    ),
                    "transition_breakout_risk": pred_rec.get(
                        "transition_breakout_risk"
                    ),
                    "theory_usefulness_score": extract_usefulness_score(
                        pred_rec.get("theory_usefulness")
                    ),
                    "theory_usefulness_label": (
                        pred_rec.get("theory_usefulness", {}).get("label", "unknown")
                        if isinstance(pred_rec.get("theory_usefulness"), dict)
                        else "unknown"
                    ),
                    "regime_similarity": pred_rec.get("regime_similarity"),
                    "capital_before": baseline.get("capital_before")
                    or cap_rec.get("capital_before"),
                    "capital_after": baseline.get("capital_after")
                    or cap_rec.get("capital_after"),
                    "daily_return_pct": baseline.get("daily_return_pct")
                    or cap_rec.get("daily_return_pct"),
                    # v2.0 Dimensions
                    "volume_state": pred_rec.get("volume_state"),
                    "volatility_regime": pred_rec.get("volatility_regime"),
                    "momentum_regime": pred_rec.get("momentum_regime"),
                    # v3.0 Dimensions
                    "regime_subtype": pred_rec.get("regime_subtype"),
                    "analog_divergence_claim": pred_rec.get("analog_divergence_claim"),
                    "regime_history": pred_rec.get("regime_history"),
                }
            )

        df = pd.DataFrame(combined_data)
        df.to_csv(file_path, index=False)
        print(f"Exported prediction analysis to {file_path}")

    def _count_branches(self, text: str) -> int:
        """Lightweight count of If/Else logic branches."""
        if not text:
            return 0
        count = 0
        patterns = [r"^\s*if\b", r"^\s*else\s+if\b", r"^\s*else\b"]

        for line in text.splitlines():
            cleaned = line.strip().strip("*").strip("#").strip().lower()
            if any(re.search(p, cleaned) for p in patterns):
                count += 1

        if count == 0:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for s in sentences:
                cleaned = s.strip().lower()
                if any(re.search(p, cleaned) for p in patterns):
                    count += 1
        return count

    def _analyze_mechanisms(self) -> Dict:
        """Analyze persistent mechanisms from the repository."""
        from memory.knowledge.knowledge_repository import KnowledgeRepository

        repo = KnowledgeRepository()
        mechanisms = repo.list_mechanisms()

        if not mechanisms:
            return {
                "mechanisms_alive": 0,
                "mechanisms_created": 0,
                "mechanisms_reused": 0,
                "mechanisms_retired": 0,
                "avg_mechanism_age": 0.0,
                "mechanism_stability": 1.0,
                "reuse_rate": 0.0,
                "evidence_accumulated": 0,
                "top_stable_mechanisms": [],
                "top_contradicted_mechanisms": [],
                "candidate_invariants": [],
            }

        alive = [m for m in mechanisms if m.status != "retired"]
        created = len(mechanisms)
        reused = sum(m.times_reused for m in mechanisms)
        retired = sum(1 for m in mechanisms if m.status == "retired")

        ages = [(m.last_seen - m.first_seen + 1) for m in mechanisms]
        avg_age = sum(ages) / len(ages) if ages else 0.0

        stabilities = []
        for m in mechanisms:
            if m.days_active > 0:
                stabilities.append(1.0 - (m.times_modified / m.days_active))
            else:
                stabilities.append(1.0)
        avg_stability = sum(stabilities) / len(stabilities) if stabilities else 1.0

        reuse_rate = reused / created if created > 0 else 0.0

        evidence = sum(
            m.support_count
            + m.contradiction_count
            + m.prediction_helped
            + m.prediction_harmed
            for m in mechanisms
        )

        sorted_by_age = sorted(
            mechanisms, key=lambda x: (x.last_seen - x.first_seen + 1), reverse=True
        )
        top_stable = [
            (
                m.mechanism_id or m.canonical_name,
                m.last_seen - m.first_seen + 1,
                m.status,
            )
            for m in sorted_by_age
        ]

        sorted_by_contra = sorted(
            mechanisms, key=lambda x: x.contradiction_count, reverse=True
        )
        top_contra = [
            (m.mechanism_id or m.canonical_name, m.contradiction_count)
            for m in sorted_by_contra
            if m.contradiction_count > 0
        ]

        candidate_invariants = []
        for m in mechanisms:
            unique_regimes = len(set(m.regimes_seen))
            unique_theories = len(m.associated_theory_ids)
            if (
                m.status == "stable"
                and unique_regimes >= 2
                and unique_theories >= 2
                and m.prediction_helped >= 3
            ):
                candidate_invariants.append(
                    (
                        m.mechanism_id or m.canonical_name,
                        m.description or m.canonical_name,
                    )
                )

        return {
            "mechanisms_alive": len(alive),
            "mechanisms_created": created,
            "mechanisms_reused": reused,
            "mechanisms_retired": retired,
            "avg_mechanism_age": avg_age,
            "mechanism_stability": round(avg_stability, 3),
            "reuse_rate": reuse_rate,
            "evidence_accumulated": evidence,
            "top_stable_mechanisms": top_stable,
            "top_contradicted_mechanisms": top_contra,
            "candidate_invariants": candidate_invariants,
        }
