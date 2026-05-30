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

from collections import defaultdict
from datetime import datetime

from statistics import mean, median
import statistics
from market.replay.prediction_probe import PredictionDirection
from pathlib import Path
from typing import List, Dict, Union

def extract_usefulness_score(value):
    """Normalizes theory_usefulness to a float score. Supports dict or numeric."""
    if isinstance(value, dict):
        return float(value.get("score", 0.0))
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0

class ReplayAnalysisEngine:
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
        self.transition_memory_hits = 0
        self.miss_analysis = [] # v2.1 Miss Audit

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
            }
        )
        
        if transition_memory_hit:
            self.transition_memory_hits += 1

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
                    contradiction_result.get("contradictions") or 
                    contradiction_result.get("indicators", [])
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
                        (m.get("similarity") if isinstance(m, dict) else getattr(m, "similarity", 0))
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
                    "contradiction_score": float(contradiction_result.get("score", 0)),
                    "regime_similarity": float(regime_sim),
                    "theory_usefulness": theory_usefulness, # Store the full dict
                    "theory_summary": theory_summary,
                    "transition_pressure_score": float(transition_pressure.get("pressure_score", 0.0)) if transition_pressure else 0.0,
                    "transition_breakout_risk": bool(transition_pressure.get("breakout_risk", False)) if transition_pressure else False,
                    "participation_confirmation": participation_confirmation,
                    # v2.0 dimensions
                    "volume_state": volume_state,
                    "volatility_regime": volatility_regime,
                    "momentum_regime": momentum_regime,
                }
            )

        if transition_pressure:
            self.transition_pressure_history.append(
                {
                    "date": date,
                    "day_index": day_index,
                    "direction_bias": transition_pressure.get("direction_bias", "neutral"),
                    "pressure_score": float(transition_pressure.get("pressure_score", 0.0)),
                    "stability_score": float(transition_pressure.get("stability_score", 0.7)),
                    "breakout_risk": bool(transition_pressure.get("breakout_risk", False)),
                    "drivers": transition_pressure.get("drivers", []),
                    "contradiction_score": float(contradiction_result.get("score", 0)),
                    "prediction_direction": prediction.get("direction", "uncertain") if prediction else "uncertain",
                }
            )
        
        if decisions:
            self.decisions_history.append(
                {
                    "date": date,
                    "decisions": decisions
                }
            )

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
            "transition_memory_analysis": self._analyze_transition_memory(),
            "prediction_history": self.prediction_history,
            "transition_pressure_history": self.transition_pressure_history,
            "risks": self._detect_cognition_risks(),
        }

        return analysis

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
                "mean": (
                    mean(contradiction_pressure)
                    if contradiction_pressure
                    else 0
                ),
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
                "message": "No transition pressure data recorded"
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
                1 for d in high_pressure_gt_0_5
                if "prior_prediction_result" in d and d.get("prior_prediction_result", {}).get("direction_score", 0) >= 0.5
            )
            accuracy_when_pressure_gt_0_5 = correct / len(high_pressure_gt_0_5)

        # Accuracy when pressure > 0.7
        accuracy_when_pressure_gt_0_7 = 0.0
        if high_pressure_gt_0_7:
            correct = sum(
                1 for d in high_pressure_gt_0_7
                if "prior_prediction_result" in d and d.get("prior_prediction_result", {}).get("direction_score", 0) >= 0.5
            )
            accuracy_when_pressure_gt_0_7 = correct / len(high_pressure_gt_0_7)

        # Accuracy analysis when pressure > 0.6 (legacy)
        accuracy_when_high_pressure = 0.0
        if high_pressure_days:
            correct_high_pressure = sum(
                1 for d in high_pressure_days
                if "prior_prediction_result" in d and d.get("prior_prediction_result", {}).get("direction_score", 0) >= 0.5
            )
            accuracy_when_high_pressure = correct_high_pressure / len(high_pressure_days)

        # Accuracy when breakout_risk=True
        breakout_risk_days = [d for d in tp_data if d["breakout_risk"]]
        accuracy_when_breakout_risk = 0.0
        if breakout_risk_days:
            correct_breakout = sum(
                1 for d in breakout_risk_days
                if "prior_prediction_result" in d and d.get("prior_prediction_result", {}).get("direction_score", 0) >= 0.5
            )
            accuracy_when_breakout_risk = correct_breakout / len(breakout_risk_days)

        # Transition capture rate: pressure > 0.5 AND directional move
        transition_attempts = sum(
            1 for d in tp_data
            if d["direction_bias"] in ["higher", "lower"]
        )
        transition_hits = sum(
            1 for d in tp_data
            if d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") in ["higher", "lower"]
        )
        transition_hit_rate = transition_hits / transition_attempts if transition_attempts > 0 else 0.0

        # TUNED: High-pressure transition capture (when pressure > 0.5 + directional bias)
        high_pressure_directional = sum(
            1 for d in high_pressure_gt_0_5
            if d["direction_bias"] in ["higher", "lower"]
        )
        high_pressure_transitions_captured = sum(
            1 for d in high_pressure_gt_0_5
            if d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") in ["higher", "lower"]
        )
        transition_capture_under_high_pressure = (
            high_pressure_transitions_captured / high_pressure_directional
            if high_pressure_directional > 0 else 0.0
        )

        # False positives: high pressure but direction missed
        false_positives = sum(
            1 for d in high_pressure_gt_0_5
            if d.get("prediction_direction") == "uncertain"
        )

        # False negatives: low pressure but missed actual move (proxy: low stability + move happened)
        false_negatives = sum(
            1 for d in tp_data
            if d["stability_score"] < 0.4
            and d.get("prediction_direction") in ["higher", "lower"]
        )

        # TUNED: Missed transitions analysis with pressure context
        missed_high_pressure = [
            d for d in tp_data
            if d["pressure_score"] > 0.5
            and d["direction_bias"] in ["higher", "lower"]
            and d.get("prediction_direction") == "uncertain"
        ]
        missed_high_pressure_avg_score = (
            mean([d["pressure_score"] for d in missed_high_pressure])
            if missed_high_pressure else 0.0
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
            "high_pressure_rate_0_5": len(high_pressure_gt_0_5) / len(tp_data) if tp_data else 0.0,
            "high_pressure_rate_0_7": len(high_pressure_gt_0_7) / len(tp_data) if tp_data else 0.0,
            "accuracy_when_pressure_gt_0_5": round(accuracy_when_pressure_gt_0_5, 3),
            "accuracy_when_pressure_gt_0_6": round(accuracy_when_high_pressure, 3),
            "accuracy_when_pressure_gt_0_7": round(accuracy_when_pressure_gt_0_7, 3),
            "breakout_risk_count": breakout_risk_count,
            "breakout_risk_rate": breakout_risk_count / len(tp_data) if tp_data else 0.0,
            "accuracy_when_breakout_risk": round(accuracy_when_breakout_risk, 3),
            "transition_hit_rate": round(transition_hit_rate, 3),
            "transition_capture_under_high_pressure": round(transition_capture_under_high_pressure, 3),
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "missed_high_pressure_count": len(missed_high_pressure),
            "missed_high_pressure_avg_score": round(missed_high_pressure_avg_score, 3),
            "direction_bias_distribution": direction_counts,
            "top_drivers": sorted(driver_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def _analyze_predictions(self) -> Dict:
        """Analyze prediction probe performance."""
        if not self.prediction_history:
            return {}

        total = len(self.prediction_history)
        # scored rows have a prior_prediction_result with a direction_score
        scored = [
            r
            for r in self.prediction_history
            if r.get("prior_prediction_result")
            and r["prior_prediction_result"].get("direction_score") is not None
        ]

        def is_correct(row):
            return row["prior_prediction_result"].get("direction_score", 0) == 1.0

        def is_partial(row):
            return row["prior_prediction_result"].get("direction_score", 0) == 0.5

        scored_count = len(scored)
        correct = sum(1 for r in scored if is_correct(r))
        partial = sum(1 for r in scored if is_partial(r))
        mean_conf = (
            mean([r["prediction"].get("confidence", 0) for r in scored])
            if scored
            else 0.0
        )
        
        # Task 2.1: Median Confidence
        conf_list = [r["prediction"].get("confidence", 0) for r in scored]
        median_conf = median(conf_list) if conf_list else 0.0

        # By direction
        directions = ["higher", "lower", "range_bound"]
        accuracy_by_direction = {}
        for d in directions:
            rows = [r for r in scored if r.get("prediction", {}).get("direction") == d]
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0
            
            # Task 2.2: Extended direction metrics
            partial_acc = (sum(1 for r in rows if is_correct(r)) + sum(1 for r in rows if is_partial(r))) / cnt if cnt else 0.0
            avg_conf_dir = statistics.mean([r["prediction"].get("confidence", 0) for r in rows]) if cnt else 0.0
            accuracy_by_direction[d] = {
                "count": cnt, 
                "accuracy": acc, 
                "partial_accuracy": partial_acc, 
                "avg_confidence": avg_conf_dir
            }

        # Contradiction buckets
        def bucket(score: float) -> str:
            if score >= 0.66:
                return "high"
            if score >= 0.33:
                return "medium"
            return "low"

        buckets = {"low": [], "medium": [], "high": []}
        for r in scored:
            b = bucket(r.get("contradiction_score", 0.0))
            buckets[b].append(r)

        accuracy_by_contradiction = {}
        for bname, rows in buckets.items():
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0
            accuracy_by_contradiction[bname] = {"count": cnt, "accuracy": acc}

        # v1.5 Confidence Calibration Buckets (0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
        cal_buckets = {"0.0-0.2": [], "0.2-0.4": [], "0.4-0.6": [], "0.6-0.8": [], "0.8-1.0": []}
        for r in scored:
            c = r["prediction"].get("confidence", 0.0)
            if c < 0.2: cal_buckets["0.0-0.2"].append(r)
            elif c < 0.4: cal_buckets["0.2-0.4"].append(r)
            elif c < 0.6: cal_buckets["0.4-0.6"].append(r)
            elif c < 0.8: cal_buckets["0.6-0.8"].append(r)
            else: cal_buckets["0.8-1.0"].append(r)

        accuracy_by_confidence_bucket = {}
        gaps = []
        for bname, rows in cal_buckets.items():
            cnt = len(rows)
            acc = sum(1 for r in rows if is_correct(r)) / cnt if cnt else 0.0
            p_acc = (sum(1 for r in rows if is_correct(r)) + sum(1 for r in rows if is_partial(r))) / cnt if cnt else 0.0
            avg_c = statistics.mean([r["prediction"].get("confidence", 0) for r in rows]) if cnt else 0.0
            
            gap = avg_c - acc if cnt else 0.0
            if cnt > 0: gaps.append(abs(gap))
            
            accuracy_by_confidence_bucket[bname] = {
                "count": cnt, 
                "actual_accuracy": acc, 
                "partial_accuracy": p_acc,
                "avg_confidence": avg_c,
                "gap": gap
            }
        
        calibration_score = statistics.mean(gaps) if gaps else 0.0

        # Usefulness Bands
        useful_buckets = {"0-0.3": [], "0.3-0.5": [], "0.5-0.7": [], "0.7+": []}
        for r in scored:
            v = extract_usefulness_score(r.get("theory_usefulness", 0.0))
            if v < 0.3: useful_buckets["0-0.3"].append(r)
            elif v < 0.5: useful_buckets["0.3-0.5"].append(r)
            elif v < 0.7: useful_buckets["0.5-0.7"].append(r)
            else: useful_buckets["0.7+"].append(r)
        
        accuracy_by_usefulness = {
            b: {"count": len(rs), "accuracy": sum(1 for r in rs if is_correct(r))/len(rs) if rs else 0.0}
            for b, rs in useful_buckets.items()
        }

        # Contradiction Bands
        contra_buckets = {"0-0.2": [], "0.2-0.5": [], "0.5+": []}
        for r in scored:
            v = r.get("contradiction_score", 0.0)
            if v < 0.2: contra_buckets["0-0.2"].append(r)
            elif v < 0.5: contra_buckets["0.2-0.5"].append(r)
            else: contra_buckets["0.5+"].append(r)

        accuracy_by_contradiction_severity = {
            b: {"count": len(rs), "accuracy": sum(1 for r in rs if is_correct(r))/len(rs) if rs else 0.0}
            for b, rs in contra_buckets.items()
        }

        # Theory Usefulness Analysis
        usefulness_scores = []
        missing_usefulness_count = 0
        for r in self.prediction_history:
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
            r for r in scored
            if r.get("theory_usefulness", {}).get("score", 0.0) > 0.7
        ]
        accuracy_when_high_usefulness = (
            sum(1 for r in high_usefulness_predictions if is_correct(r)) / len(high_usefulness_predictions)
            if high_usefulness_predictions else 0.0
        )

        # Prediction Drift
        change_count = 0
        if len(self.prediction_history) > 1:
            for i in range(1, len(self.prediction_history)):
                if self.prediction_history[i-1]["prediction"].get("direction") != self.prediction_history[i]["prediction"].get("direction"):
                    change_count += 1
        prediction_drift = change_count / (len(self.prediction_history) - 1) if len(self.prediction_history) > 1 else 0.0

        # Rolling Confidence Drift
        conf_vals = [r["prediction"].get("confidence", 0) for r in self.prediction_history]
        rolling_drift = {
            "7d": statistics.mean(conf_vals[-7:]) if len(conf_vals) >= 7 else 0.0,
            "15d": statistics.mean(conf_vals[-15:]) if len(conf_vals) >= 15 else 0.0
        }

        # Task 2.2: Add 'uncertain'
        uncertain_rows = [r for r in self.prediction_history if r.get("prediction", {}).get("direction") == PredictionDirection.uncertain.value]
        avg_conf_uncertain = mean([r["prediction"].get("confidence", 0) for r in uncertain_rows]) if uncertain_rows else 0.0
        accuracy_by_direction["uncertain"] = {"count": len(uncertain_rows), "accuracy": 0.0, "partial_accuracy": 0.0, "avg_confidence": avg_conf_uncertain}

        # Regime similarity > 0.9
        high_regime = [r for r in scored if r.get("regime_similarity", 0.0) > 0.9]
        regime_acc = sum(1 for r in high_regime if is_correct(r)) / len(high_regime) if high_regime else 0.0

        # Theory usefulness > 0.5
        useful = [r for r in scored if extract_usefulness_score(r.get("theory_usefulness", 0.0)) > 0.5]
        useful_acc = sum(1 for r in useful if is_correct(r)) / len(useful) if useful else 0.0

        # Task 2.4: Prediction slices by pressure
        pressure_gt_0_5 = [r for r in scored if r.get("transition_pressure_score", 0.0) > 0.5]
        acc_pressure_gt_0_5 = sum(1 for r in pressure_gt_0_5 if is_correct(r)) / len(pressure_gt_0_5) if pressure_gt_0_5 else 0.0

        pressure_gt_0_7 = [r for r in scored if r.get("transition_pressure_score", 0.0) > 0.7]
        acc_pressure_gt_0_7 = sum(1 for r in pressure_gt_0_7 if is_correct(r)) / len(pressure_gt_0_7) if pressure_gt_0_7 else 0.0

        # Task 2.5: False breakout
        false_breakouts = [
            r for r in scored
            if r.get("transition_breakout_risk")
            and not is_correct(r)
        ]

        # Task 2.6: Best breakout capture
        best_breakout_captures = [
            r for r in scored
            if r.get("transition_breakout_risk")
            and is_correct(r)
            and r["prediction"].get("direction") in [PredictionDirection.higher.value, PredictionDirection.lower.value]
        ]

        # Missed transition cases: range_bound -> higher / lower
        missed_range_to_higher = [
            r
            for r in scored
            if r.get("prediction", {}).get("direction") == "range_bound"
            and r.get("prior_prediction_result", {}).get("actual_direction") == "higher"
            and not is_correct(r)
        ]
        missed_range_to_lower = [
            r
            for r in scored
            if r.get("prediction", {}).get("direction") == "range_bound"
            and r.get("prior_prediction_result", {}).get("actual_direction") == "lower"
            and not is_correct(r)
        ]

        def sample_top(rows, n=5):
            return [
                {"date": r.get("date"), "theory_summary": r.get("theory_summary", ""), "confidence": r.get("prediction", {}).get("confidence")}
                for r in rows[:n]
            ]

        correlation_coeff = 0.0
        confidences = [r["prediction"].get("confidence", 0) for r in scored if r.get("prediction")]
        scores = [r["prior_prediction_result"].get("direction_score", 0) for r in scored]
        if len(confidences) > 1 and len(scores) > 1:
            try:
                correlation_val = statistics.correlation(confidences, scores)
            except Exception:
                correlation_coeff = 0.0

        return {
            "total_predictions": total,
            "scored_predictions": scored_count,
            "accuracy": correct / scored_count if scored_count else 0.0,
            "partial_accuracy": (correct + partial) / scored_count if scored_count else 0.0,
            "uncertain_rate": sum(1 for r in self.prediction_history if r.get("prediction", {}).get("direction") == "uncertain") / total if total else 0.0,
            "invalidation_rate": sum(1 for r in scored if r.get("prior_prediction_result", {}).get("invalidation_triggered")) / scored_count if scored_count else 0.0,
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
            "missed_range_to_higher": {"count": len(missed_range_to_higher), "samples": sample_top(missed_range_to_higher)},
            "missed_range_to_lower": {"count": len(missed_range_to_lower), "samples": sample_top(missed_range_to_lower)},
            "false_breakouts": {"count": len(false_breakouts), "samples": sample_top(false_breakouts)},
            "best_breakout_captures": {"count": len(best_breakout_captures), "samples": sample_top(best_breakout_captures)},
            "avg_theory_usefulness": avg_theory_usefulness,
            "high_usefulness_days": high_usefulness_days,
            "accuracy_when_high_usefulness": accuracy_when_high_usefulness,
            "missing_usefulness_values": missing_usefulness_count,
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

    def print_summary(self):
        """Print analysis summary."""
        analysis = self.analyze()

        if analysis.get("status") == "no_data":
            print("No replay data to analyze")
            return

        em = getattr(self, "external_metrics", {}) or {}

        print("\n" + "=" * 60)
        print("COGNITIVE REPLAY SUMMARY (v3.1+)")
        print("=" * 60)

        # Header
        print(
            f"\nReplay Period: {analysis['date_range'][0]} to {analysis['date_range'][1]} ({analysis['total_days']} days)"
        )

        # 1. Cognitive Core
        print("\nCOGNITIVE CORE")
        print("--------------")
        active = em.get("active_theories", "N/A")
        print(f"Active theories: {active}")
        family = em.get("family_analytics", {})
        print("Active theory lifecycle: New/Mutated/Retired/Revived")
        if em.get("family_analytics"):
            print(
                f"  Best surviving family: {family.get('best_surviving_family') or 'None'}"
            )
            print(
                f"  Most revived family: {family.get('most_revived_family') or 'None'}"
            )
        else:
            print("  Best surviving family: N/A")
            print("  Most revived family: N/A")

        # regime & memory
        regime_recall = em.get("regime_recall_hit_rate", analysis.get("transition_memory_analysis", {}).get("hit_rate", 0.0))
        mem_use = em.get("memory_retrieval_usefulness", 0.0)
        
        # Read actual theory usefulness from prediction analysis
        pred_analysis = analysis.get("prediction_analysis", {})
        avg_usefulness = pred_analysis.get("avg_theory_usefulness", 0.0)

        print(f"Regime recall hit rate: {regime_recall:.2f}")
        print(f"Memory retrieval usefulness: {mem_use:.2f}")
        print(f"Avg theory usefulness: {avg_usefulness:.2f}")

        grounded = em.get("grounded_reflection", 0.0)
        narrative = em.get("narrative_inflation", 0.0)
        meta = em.get("meta_commentary", 0.0)
        print(f"Grounded reflection: {grounded:.3f}")
        print(f"Narrative inflation: {narrative:.3f}")
        print(f"Meta commentary: {meta:.3f}")

        print("\nPurpose: Is thinker improving? (see Confidence & Prediction sections)")

        # 2. Confidence & coherence
        conf = analysis.get("confidence_analysis", {})
        print("\nCONFIDENCE DYNAMICS")
        print("-------------------")
        if conf:
            emp = conf.get("empirical_confidence", {})
            coh = conf.get("theoretical_coherence", {})
            print(f"Empirical: {emp.get('initial',0):.2f} → {emp.get('final',0):.2f} ({emp.get('trajectory','N/A')})")
            print(f"Coherence: {coh.get('initial',0):.2f} → {coh.get('final',0):.2f} ({coh.get('trend','N/A')})")
        else:
            print("No confidence data")

        # 3. Prediction performance
        p = analysis.get("prediction_analysis", {})
        print("\nPREDICTION PERFORMANCE")
        print("----------------------")
        if p:
            print(f"Total predictions: {p.get('total_predictions',0)}")
            print(f"Accuracy: {p.get('accuracy',0.0):.1%}")
            print(f"Partial accuracy: {p.get('partial_accuracy',0.0):.1%}")
            print(f"Uncertain rate: {p.get('uncertain_rate',0.0):.1%}")
            print(f"Mean confidence: {p.get('mean_confidence',0.0):.3f} | Median: {p.get('median_confidence',0.0):.3f} | Corr: {p.get('confidence_accuracy_correlation',0.0):.3f}")
            print(f"Avg theory usefulness: {p.get('avg_theory_usefulness', 0.0):.3f}")
            print(f"High usefulness days (>0.7): {p.get('high_usefulness_days', 0)}")
            print(f"Accuracy when usefulness >0.7: {p.get('accuracy_when_high_usefulness', 0.0):.1%}")
            print(f"Missing usefulness values: {p.get('missing_usefulness_values', 0)}")

            print("\nBy direction:")
            for d, info in p.get('accuracy_by_direction', {}).items():
                print(f"  {d:<12}: Acc={info['accuracy']:.1%} | Partial={info['partial_accuracy']:.1%} | n={info['count']} | AvgConf={info['avg_confidence']:.2f}")

            # Top misses
            # reuse existing samples if present in missed lists
            top_misses = []
            for key in ['missed_range_to_higher','missed_range_to_lower','false_breakouts']:
                entry = p.get(key, {})
                if entry and entry.get('count'):
                    top_misses.append((key, entry.get('count')))
            if top_misses:
                print("\nTop misses:")
                for k, c in top_misses:
                    print(f"  {k}: {c}")
        else:
            print("No prediction data")

        # 4. Cross-asset intelligence
        print("\nCROSS-ASSET ANALYSIS")
        print("--------------------")
        # Cross-asset details are printed by ReplayExecutor when available; show placeholder or external summary
        cross = em.get('outputs', {}).get('cross_asset_summary') if em else None
        if cross and Path(cross).exists():
            try:
                import json

                with open(cross, 'r') as f:
                    cs = json.load(f)
                print(f"Primary market: {cs.get('primary_market')}")
                print(f"Secondary market: {cs.get('secondary_market')}")
                print(f"Primary accuracy: {cs.get('primary_accuracy',0.0):.1%}")
                print(f"Secondary accuracy: {cs.get('secondary_accuracy',0.0):.1%}")
                print(f"Divergence hit rates: primary={cs.get('primary_divergence_hit_rate',0.0):.1%}, secondary={cs.get('secondary_divergence_hit_rate',0.0):.1%}")
            except Exception:
                print("Cross-asset summary present but failed to read")
        else:
            print("Cross-asset analysis: not available (run with RELIANCE dataset present)")

        # 5. Transition pressure
        tp = analysis.get('transition_pressure_analysis', {})
        print("\nTRANSITION PRESSURE")
        print("-------------------")
        if tp and tp.get('status') != 'no_data':
            print(f"Avg pressure: {tp.get('avg_pressure',0.0):.3f} | Avg stability: {tp.get('avg_stability',0.0):.3f}")
            print(f"High pressure days (>0.5): {tp.get('pressure_distribution', {}).get('gt_0_5',0)}")
            print(f"Breakout flags: {tp.get('breakout_risk_count',0)} | Accuracy when breakout: {tp.get('accuracy_when_breakout_risk',0.0):.1%}")
        else:
            print("No transition pressure data")

        # 6. Decision policies (capital simulation)
        cap = analysis.get('capital_simulation_analysis', {})
        print("\nDECISION POLICY RESULTS")
        print("-----------------------")
        if cap:
            for policy_key in ['baseline','high_conviction','breakout']:
                p = cap.get(policy_key, {})
                if not p: continue
                name = policy_key.replace('_',' ').title()
                print(f"\n{name}: Return={p.get('return_pct',0.0):+.2%} | Trades={p.get('trade_count',0)} | WinRate={p.get('win_rate',0.0):.1%} | MaxDD={p.get('max_drawdown',0.0):.1%}")
            best = cap.get('best_performer','N/A')
            print(f"\nBest performer: {best}")
        else:
            print('No capital simulation data')

        # 7. Key insights (auto-generated)
        print("\nKEY INSIGHTS")
        print("------------")
        insights = []
        if conf:
            traj = conf.get('empirical_confidence',{}).get('trajectory')
            if traj == 'rising':
                insights.append('✓ Empirical confidence rising over replay')
            elif traj == 'declining':
                insights.append('⚠ Empirical confidence declining')
        if p and p.get('calibration_score',0) > 0.15:
            insights.append('⚠ Calibration gap detected (consider recalibration)')
        if tp and tp.get('false_positives',0) > max(3, int(tp.get('total_days',0)*0.1)):
            insights.append('⚠ Transition pressure over-triggering (many false positives)')

        if not insights:
            print('  No critical insights detected')
        else:
            for i in insights:
                print(f'  {i}')

        if p and p.get('scored_predictions', 0) >= 5:
            if p.get('accuracy', 0.0) > 0.55:
                print('  ✓ prediction quality improving')
            if tp and tp.get('breakout_risk_count', 0) >= 3 and tp.get('accuracy_when_breakout_risk', 0.0) > p.get('accuracy', 0.0):
                print('  ✓ breakout signal outperforming baseline')
            if cap and cap.get('high_conviction', {}).get('trade_count', 0) > 0 and cap.get('high_conviction', {}).get('return_pct', 0.0) > cap.get('baseline', {}).get('return_pct', 0.0):
                print('  ✓ selective execution improving returns')
            if p.get('confidence_accuracy_correlation', 0.0) > 0.25:
                print('  ✓ confidence calibration strengthening')

        if analysis.get('contradiction_analysis', {}).get('persistence_ratio', 0.0) > 0.70 and len(self.days) >= 5:
            print('  ⚠ contradiction elevated')

        if p:
            if p.get('accuracy', 0.0) < 0.45:
                print('  ⚠ prediction accuracy below baseline')
            if p.get('mean_confidence', 0.0) > 0.6 and p.get('accuracy', 0.0) > 0.5:
                print('  ✓ confidence well-calibrated with moderate accuracy')
        if conf:
            coh_drop = conf.get('theoretical_coherence', {}).get('initial', 0.0) - conf.get('theoretical_coherence', {}).get('final', 0.0)
            if coh_drop > 0.08:
                print('  ⚠ coherence degrading significantly')
        if cross_asset:
            if cross_asset.get('primary_divergence_hit_rate', 0.0) > 0.25:
                print('  ✓ cross-asset divergence adding signal')
            elif cross_asset.get('secondary_divergence_hit_rate', 0.0) > 0.25:
                print('  ✓ specialist asset divergence hit rate strong')

        # 8. Outputs
        print("\nOUTPUTS")
        print("-------")
        out = em.get('outputs', {})
        print(f"  CSV: {out.get('prediction_csv','N/A')}")
        print(f"  Charts: {out.get('charts_dir','N/A')}")
        print(f"  Cross-asset JSON: {out.get('cross_asset_summary','N/A')}")

        print('\n' + '=' * 60 + '\n')

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
            "hit_rate": self.transition_memory_hits / len(self.days) if len(self.days) > 0 else 0.0,
        }

    def set_capital_simulation_logs(self, logs: list):
        """WIRING FIX: Set daily logs from capital simulator."""
        self.capital_simulation_logs = logs

    def export_prediction_analysis_csv(self, file_path: Path):
        """Export prediction analysis and capital simulation data to CSV."""
        import pandas as pd
        from pathlib import Path

        if not self.prediction_history or not self.capital_simulation_logs:
            print("No data to export for prediction analysis CSV.")
            return

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine prediction history and capital simulation logs
        # Assuming both lists are ordered by date/day_index and have the same length
        combined_data = []
        for i in range(len(self.prediction_history)):
            pred_rec = self.prediction_history[i]
            cap_rec = self.capital_simulation_logs[i]
            baseline = cap_rec.get("policies", {}).get("baseline", {})

            combined_data.append({
                "date": pred_rec["date"],
                "prediction_direction": pred_rec["prediction"].get("direction"),
                "prediction_confidence": pred_rec["prediction"].get("confidence") or baseline.get("conviction"),
                "actual_direction": pred_rec["prior_prediction_result"].get("actual_direction"),
                "transition_pressure_score": pred_rec.get("transition_pressure_score"),
                "transition_breakout_risk": pred_rec.get("transition_breakout_risk"),
                "theory_usefulness_score": extract_usefulness_score(pred_rec.get("theory_usefulness")),
                "theory_usefulness_label": pred_rec.get("theory_usefulness", {}).get("label", "unknown") if isinstance(pred_rec.get("theory_usefulness"), dict) else "unknown",
                "regime_similarity": pred_rec.get("regime_similarity"),
                "capital_before": baseline.get("capital_before") or cap_rec.get("capital_before"),
                "capital_after": baseline.get("capital_after") or cap_rec.get("capital_after"),
                "daily_return_pct": baseline.get("daily_return_pct") or cap_rec.get("daily_return_pct"),
                # v2.0 Dimensions
                "volume_state": pred_rec.get("volume_state"),
                "volatility_regime": pred_rec.get("volatility_regime"),
                "momentum_regime": pred_rec.get("momentum_regime"),
                # v3.0 Dimensions
                "regime_subtype": pred_rec.get("regime_subtype"),
                "analog_divergence_claim": pred_rec.get("analog_divergence_claim"),
                "regime_history": pred_rec.get("regime_history"),
            })

        df = pd.DataFrame(combined_data)
        df.to_csv(file_path, index=False)
        print(f"Exported prediction analysis to {file_path}")
