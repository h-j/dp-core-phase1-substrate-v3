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

import statistics
from collections import defaultdict
from datetime import datetime


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
            }
        )

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
                "count": len(contradiction_result.get("contradictions", [])),
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
                "mean": statistics.mean(empirical_conf) if empirical_conf else 0,
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
                "mean": statistics.mean(regime_conf) if regime_conf else 0,
            },
            "theoretical_coherence": {
                "initial": coherence[0] if coherence else 0,
                "final": coherence[-1] if coherence else 0,
                "mean": statistics.mean(coherence) if coherence else 0,
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
                    statistics.mean(contradiction_pressure)
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
            "mean_contradiction_score": statistics.mean(scores) if scores else 0,
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
        coherence_mean = statistics.mean(recent_coherence)

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
                statistics.mean(row.get(name, 0) for row in metric_rows),
                3,
            )
            for name in metric_names
        }

    def _detect_cognition_risks(self) -> list:
        """Detect potential cognition dysfunctions."""
        risks = []

        if not self.confidence_history or not self.contradiction_history:
            return risks

        # Overconfidence drift
        empirical_conf = [c["empirical"] for c in self.confidence_history]
        if len(empirical_conf) > 10:
            recent_mean = statistics.mean(empirical_conf[-10:])
            early_mean = statistics.mean(empirical_conf[:10])
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

        print("\n" + "=" * 70)
        print("REPLAY ANALYSIS SUMMARY")
        print("=" * 70)

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

        if "risks" in analysis and analysis["risks"]:
            print("\n⚠  Detected Risks:")
            for risk in analysis["risks"]:
                print(
                    f"  [{risk['severity'].upper()}] {risk['type']}: "
                    f"{risk['description']}"
                )

        print("\n" + "=" * 70 + "\n")
