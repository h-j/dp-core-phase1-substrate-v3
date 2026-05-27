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

from statistics import mean, median, correlation
import statistics
from market.replay.prediction_probe import PredictionDirection
from pathlib import Path
class ReplayAnalysisEngine:
    """
    Analyzes cognition behavior over replay execution.
    """

    def __init__(self):
        """Initialize analysis state."""
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
        epistemic_quality: dict | None = None,
        prediction: dict | None = None,
        prior_prediction_result: dict | None = None,
        regime_matches: list | None = None,
        theory_usefulness: dict | None = None,
        transition_pressure: dict | None = None,
        decisions: dict | None = None,
        # v2.0 enriched dimensions
        volume_state: str | None = None,
        volatility_regime: str | None = None,
        momentum_regime: str | None = None,
        transition_memory_hit: bool = False,
    ):
        """Record cognition state for a day."""
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
                "theory_usefulness": theory_usefulness or {},
                "transition_pressure": transition_pressure or {},
                "decisions": decisions or {},
                # v2.0 dimensions
                "volume_state": volume_state,
                "volatility_regime": volatility_regime,
                "momentum_regime": momentum_regime
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
            if theory_usefulness:
                try:
                    theory_usefulness_score = float(theory_usefulness.get("score", 0))
                except Exception:
                    theory_usefulness_score = 0.0

            self.prediction_history.append(
                {
                    "date": date,
                    "prediction": prediction or {},
                    "prior_prediction_result": prior_prediction_result or {},
                    "contradiction_score": float(contradiction_result.get("score", 0)),
                    "regime_similarity": float(regime_sim),
                    "theory_usefulness": float(theory_usefulness_score),
                    "theory_summary": theory_summary,
                    "transition_pressure_score": float(transition_pressure.get("pressure_score", 0.0)) if transition_pressure else 0.0,
                    "transition_breakout_risk": bool(transition_pressure.get("breakout_risk", False)) if transition_pressure else False,
                    # v2.0 dimensions
                    "volume_state": volume_state,
                    "volatility_regime": volatility_regime,
                    "momentum_regime": momentum_regime
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

    def analyze(self) -> dict:
        """Run comprehensive analysis."""
        if not self.days:
            return {"status": "no_data", "message": "No replay days recorded"}

        analysis = {
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
            "risks": self._detect_cognition_risks(),
        }

        return analysis

    def _analyze_confidence(self) -> dict:
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

    def _analyze_contradictions(self) -> dict:
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

    def _analyze_theories(self) -> dict:
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

    def _analyze_coherence(self) -> dict:
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

    def _analyze_epistemic_quality(self) -> dict:
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

    def _mean_quality_metrics(self, metric_rows: list[dict]) -> dict:
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

    def _analyze_transition_pressure(self) -> dict:
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

    def _analyze_predictions(self) -> dict:
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
            v = r.get("theory_usefulness", 0.0)
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
        useful = [r for r in scored if r.get("theory_usefulness", 0.0) > 0.5]
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
                correlation_val = correlation(confidences, scores)
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
        }

    def _detect_cognition_risks(self) -> list:
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

        print("\n" + "=" * 40)
        print("REPLAY ANALYSIS SUMMARY")
        print("=" * 40)

        print(
            f"\nReplay Period: {analysis['date_range'][0]} to "
            f"{analysis['date_range'][1]} ({analysis['total_days']} days)"
        )

        if "confidence_analysis" in analysis:
            conf = analysis["confidence_analysis"]
            print("\nConfidence Dynamics:")
            print(
                f"  Empirical: {conf['empirical_confidence']['initial']:.2f} → "
                f"{conf['empirical_confidence']['final']:.2f} "
                f"({conf['empirical_confidence']['trajectory']})"
            )
            print(
                f"  Coherence: {conf['theoretical_coherence']['initial']:.2f} → "
                f"{conf['theoretical_coherence']['final']:.2f} "
                f"({conf['theoretical_coherence']['trend']})"
            )

        if "contradiction_analysis" in analysis:
            cont = analysis["contradiction_analysis"]
            print("\nContradiction Dynamics:")
            print(
                f"  Days with contradictions: {cont['total_days_with_contradictions']} "
                f"({cont['persistence_ratio']:.1%})"
            )
            print(f"  Trend: {cont['score_trend']}")

        if "theory_analysis" in analysis:
            theory = analysis["theory_analysis"]
            print("\nTheory Patterns:")
            print(
                f"  Theme diversity: {theory['theme_diversity']} themes, "
                f"risk: {theory['theme_repetition_risk']}"
            )
            print(f"  Top themes: {', '.join([t[0] for t in theory['top_themes']])}")

        if analysis.get("epistemic_quality_analysis"):
            quality = analysis["epistemic_quality_analysis"].get("theory", {})
            if quality:
                print("\nEpistemic Quality:")
                print(
                    f"  Compression: {quality['compression_score']:.2f}, "
                    f"narrative density: {quality['narrative_density']:.2f}, "
                    f"causal inflation: {quality['causal_inflation']:.2f}"
                )

        if analysis.get("prediction_analysis"):
            p = analysis["prediction_analysis"]
            # Task 5: Summary output formatting
            print("\nPrediction Analysis")
            print("------------------")
            print(f"  Total predictions: {p['total_predictions']}")
            print(f"  Accuracy: {p['accuracy']:.1%}")
            print(f"  Partial: {p['partial_accuracy']:.1%}")
            print(f"  Uncertain: {p['uncertain_rate']:.1%}")
            print(f"\n  Mean confidence: {p['mean_confidence']:.3f}")
            print(f"  Median confidence: {p['median_confidence']:.3f}")
            print(f"  Confidence correlation: {p['confidence_accuracy_correlation']:.3f}")

            print(f"\n  Accuracy @ Pressure > 0.5: {p.get('accuracy_when_pressure_gt_0_5', 0.0):.1%}")
            print(f"  Accuracy @ Pressure > 0.7: {p.get('accuracy_when_pressure_gt_0_7', 0.0):.1%}")

            print("\nv1.5 Calibration Summary")
            print("-----------------------")
            print(f"  Overall Calibration Score (MAE): {p.get('calibration_score', 0.0):.3f}")
            print(f"  Prediction Direction Drift: {p.get('prediction_drift', 0.0):.1%}")
            print(f"  Rolling Confidence: 7d={p['rolling_drift']['7d']:.2f}, 15d={p['rolling_drift']['15d']:.2f}")

            print("\nAccuracy by Direction (Regime)")
            print("---------------------")
            for d, info in p.get("accuracy_by_direction", {}).items():
                print(f"    {d:<12}: {info['accuracy']:.1%} (n={info['count']}) | Avg Conf: {info['avg_confidence']:.2f}")

            print("\nAccuracy by Usefulness")
            print("---------------------")
            for b, info in p.get("accuracy_by_usefulness", {}).items():
                print(f"    {b:<12}: {info['accuracy']:.1%} (n={info['count']})")

            print("\nAccuracy by Contradiction Severity")
            print("---------------------------------")
            for b, info in p.get("accuracy_by_contradiction_severity", {}).items():
                print(f"    {b:<12}: {info['accuracy']:.1%} (n={info['count']})")

            print("\nConfidence Calibration Buckets")
            print("-----------------------------")
            for b, info in p.get("accuracy_by_confidence_bucket", {}).items():
                print(f"    {b}: Acc={info['actual_accuracy']:.1%}, AvgConf={info['avg_confidence']:.2f}, Gap={info['gap']:.3f}")


            print(f"\n  Accuracy when regime similarity > 0.9: {p.get('accuracy_regime_similarity_gt_0_9', 0.0):.1%}")
            print(f"  Accuracy when theory usefulness > 0.5: {p.get('accuracy_theory_usefulness_gt_0_5', 0.0):.1%}")

            print("\n  Missed transition samples (range_bound → higher):")
            print(f"    Count: {p.get('missed_range_to_higher', {}).get('count', 0)}")
            for s in p.get('missed_range_to_higher', {}).get('samples', []):
                print(f"      - {s['date']}: conf={s.get('confidence')} | {s.get('theory_summary','')[:80]}")

            print("\n  Missed transition samples (range_bound → lower):")
            print(f"    Count: {p.get('missed_range_to_lower', {}).get('count', 0)}")
            for s in p.get('missed_range_to_lower', {}).get('samples', []):
                print(f"      - {s['date']}: conf={s.get('confidence')} | {s.get('theory_summary','')[:80]}")

            print("\n  False Breakouts:")
            print(f"    Count: {p.get('false_breakouts', {}).get('count', 0)}")
            for s in p.get('false_breakouts', {}).get('samples', []):
                print(f"      - {s['date']}: conf={s.get('confidence')} | {s.get('theory_summary','')[:80]}")

            print("\n  Best Breakout Captures:")
            print(f"    Count: {p.get('best_breakout_captures', {}).get('count', 0)}")
            for s in p.get('best_breakout_captures', {}).get('samples', []):
                print(f"      - {s['date']}: conf={s.get('confidence')} | {s.get('theory_summary','')[:80]}")


        if analysis.get("transition_pressure_analysis"):
            tp = analysis["transition_pressure_analysis"]
            if tp.get("status") != "no_data":
                print("\nTransition Pressure Analysis (Calibration Audit):")
                print(f"  Avg pressure: {tp.get('avg_pressure', 0.0):.3f} | Avg stability: {tp.get('avg_stability', 0.7):.3f}")
                
                # Pressure distribution with multiple thresholds
                dist = tp.get('pressure_distribution', {})
                print(f"\n  Pressure Distribution:")
                print(f"    >0.5: {dist.get('gt_0_5', 0)} days ({tp.get('high_pressure_rate_0_5', 0.0):.1%})")
                print(f"    >0.6: {dist.get('gt_0_6', 0)} days")
                print(f"    >0.7: {dist.get('gt_0_7', 0)} days ({tp.get('high_pressure_rate_0_7', 0.0):.1%})")
                
                # Accuracy metrics at different thresholds
                print(f"\n  Accuracy by Pressure Threshold:")
                print(f"    @>0.5: {tp.get('accuracy_when_pressure_gt_0_5', 0.0):.1%}")
                print(f"    @>0.6: {tp.get('accuracy_when_pressure_gt_0_6', 0.0):.1%}")
                print(f"    @>0.7: {tp.get('accuracy_when_pressure_gt_0_7', 0.0):.1%}")
                
                print(f"\n  Breakout Risk:")
                print(f"    Count: {tp.get('breakout_risk_count', 0)} ({tp.get('breakout_risk_rate', 0.0):.1%})")
                print(f"    Accuracy when flagged: {tp.get('accuracy_when_breakout_risk', 0.0):.1%}")
                
                print(f"\n  Transition Capture:")
                print(f"    Overall hit rate: {tp.get('transition_hit_rate', 0.0):.1%}")
                print(f"    Under high pressure (>0.5): {tp.get('transition_capture_under_high_pressure', 0.0):.1%}")
                
                print(f"\n  Misses & False Signals:")
                print(f"    False positives: {tp.get('false_positives', 0)}")
                print(f"    False negatives: {tp.get('false_negatives', 0)}")
                print(f"    Missed high-pressure (>0.5): {tp.get('missed_high_pressure_count', 0)} (avg score: {tp.get('missed_high_pressure_avg_score', 0.0):.3f})")
                
                print(f"\n  Direction distribution: {tp.get('direction_bias_distribution', {})}")
                print(f"  Top drivers: {', '.join([d[0] for d in tp.get('top_drivers', [])])}")
        if "risks" in analysis and analysis["risks"]:
            print("\n⚠  Detected Risks:")
            for risk in analysis["risks"]:
                print(
                    f"  [{risk['severity'].upper()}] {risk['type']}: "
                    f"{risk['description']}"
                )

        if "capital_simulation_analysis" in analysis:
            print("\nDecision Policy Results")
            print("-----------------------")
            cap = analysis["capital_simulation_analysis"]
            
            for policy_key in ["baseline", "high_conviction", "breakout"]:
                p = cap.get(policy_key, {})
                if not p: continue
                
                name = policy_key.replace("_", " ").title()
                print(f"\n{name}:")
                print(f"  Capital: ₹{p.get('ending_capital', 0):,.2f}")
                print(f"  Return:  {p.get('return_pct', 0.0):+.2%}")
                print(f"  Trades:  {p.get('trade_count', 0)}")
                print(f"  Win Rate: {p.get('win_rate', 0.0):.1%}")
                print(f"  Max DD:   {p.get('max_drawdown', 0.0):.1%}")
                print(f"  Avg Conv: {p.get('avg_conviction', 0.0):.3f}")

            best = cap.get('best_performer', 'N/A')
            print(f"\nBest Performer: {best.replace('_', ' ').title()}")

        print("\n" + "=" * 70 + "\n")

    def _analyze_capital_simulation(self) -> dict:
        """Analyze capital simulation results."""
        return getattr(self, "capital_simulation_summary", {})

    def set_capital_simulation_summary(self, summary: dict):
        """Set the summary of capital simulation."""
        self.capital_simulation_summary = summary

    def _analyze_transition_memory(self) -> dict:
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
                "theory_usefulness_score": pred_rec.get("theory_usefulness"),
                "regime_similarity": pred_rec.get("regime_similarity"),
                "capital_before": baseline.get("capital_before") or cap_rec.get("capital_before"),
                "capital_after": baseline.get("capital_after") or cap_rec.get("capital_after"),
                "daily_return_pct": baseline.get("daily_return_pct") or cap_rec.get("daily_return_pct"),
                # v2.0 Dimensions
                "volume_state": pred_rec.get("volume_state"),
                "volatility_regime": pred_rec.get("volatility_regime"),
                "momentum_regime": pred_rec.get("momentum_regime"),
            })

        df = pd.DataFrame(combined_data)
        df.to_csv(file_path, index=False)
        print(f"Exported prediction analysis to {file_path}")
