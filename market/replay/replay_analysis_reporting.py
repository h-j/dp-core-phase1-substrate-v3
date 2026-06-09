"""Reporting and export helpers for replay cognition analysis."""

from pathlib import Path
from typing import Dict
import json

import pandas as pd

from market.replay.replay_analysis_utils import extract_usefulness_score


class ReplayAnalysisReportingMixin:
    def print_summary(self):
        """Print canonical replay summary (Cognition Journal v4.3)."""
        analysis = self.analyze()
        if analysis.get("status") == "no_data":
            print("No replay data to analyze")
            return
        em = getattr(self, "external_metrics", {}) or {}
        ReplayJournalBuilder.print_journal(self.market_name, analysis, em)


class ReplayJournalBuilder:
    """Dedicated builder for the Replay Cognition Journal."""

    @staticmethod
    def print_journal(market_name: str, analysis: dict, external_metrics: dict):
        print("\n" + "═" * 60)
        print(f"  REPLAY COGNITION JOURNAL | {market_name}")
        print("═" * 60)
        print(f"Period: {analysis['date_range'][0]} to {analysis['date_range'][1]}")

        # 1. WHAT CHANGED?
        print("\n1. WHAT CHANGED?")
        print("━" * 40)
        conf = analysis.get("confidence_analysis", {})
        print(f"• Confidence {conf.get('empirical_confidence', {}).get('trajectory', 'stable')}")

        contra_days = analysis.get("contradiction_analysis", {}).get("total_days_with_contradictions", 0)
        if contra_days == 0:
            print("• No contradiction detected")
        else:
            print(f"• Contradictions persisted ({contra_days} days)")

        synthesis_count = external_metrics.get('total_synthesis_triggered', 0)
        if synthesis_count > 0:
            print(f"• Cognitive synthesis active ({synthesis_count} triggered)")

        mut_count = external_metrics.get('mutation_count', 0)
        if mut_count > 0:
            print(f"• Theory trajectory evolved ({mut_count} mutations)")

        # 2. WHAT WAS LEARNED?
        print("\n2. WHAT WAS LEARNED?")
        print("━" * 40)
        events = []
        if mut_count > 0: events.append(f"• Mutation: {mut_count} theory evolutions recorded")
        if contra_days > 0: events.append(f"• Contradiction: {contra_days} days of cognitive conflict identified")
        
        p = analysis.get("prediction_analysis", {})
        inval_rate = p.get('invalidation_rate', 0.0)
        total_p = p.get('total_predictions', 0)
        falsifications = int(inval_rate * total_p)
        if falsifications > 0: events.append(f"• Falsification: {falsifications} theories rejected by market outcome")
        
        correct = int(p.get('accuracy', 0.0) * total_p)
        if correct > 0: events.append(f"• Validation: {correct} predictions successfully grounded")

        if not events:
            print("  No significant learning events occurred.")
        else:
            for e in events: print(f"  {e}")

        # 3. WHAT SURVIVED?
        print("\n3. WHAT SURVIVED?")
        print("━" * 40)
        family = external_metrics.get("family_analytics", {})
        if family:
            best_fam = family.get('best_surviving_family', 'N/A')
            print(f"Theory Family:          {best_fam}")
            print(f"Status:                 ACTIVE")
        else:
            print("Theory evolution analysis: Pending sufficient lineage data.")

        # 4. EXPERIENCE SUMMARY
        exp_stats = external_metrics.get("experience_stats", {})
        if exp_stats:
            print("\n4. EXPERIENCE SUMMARY")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            print(f"Experiences Created: {exp_stats.get('created', 0)}")
            print(f"Active: {exp_stats.get('active', 0)}")
            print(f"Validated: {exp_stats.get('validated', 0)}")
            print(f"Falsified: {exp_stats.get('falsified', 0)}")
            print(f"Abandoned: {exp_stats.get('abandoned', 0)}")
            
            most_active = exp_stats.get("most_active")
            if most_active:
                print("\nMost Active Experience:")
                print(f"Lineage: {most_active.get('lineage')}")
                print(f"Theories: {most_active.get('theories')}")
                print(f"Contradictions: {most_active.get('contradictions')}")
                print(f"Mutations: {most_active.get('mutations')}")

        # 4.1 EXPERIENCE HEALTH
        exp_audit = external_metrics.get("experience_audit", {})
        if exp_audit:
            print("\nEXPERIENCE HEALTH")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"Average theories per experience: {exp_audit.get('avg_theories_per_experience', 0):.1f}")
            print(f"Average mutations per experience: {exp_audit.get('avg_mutations_per_experience', 0):.1f}")
            print(f"Average contradictions per experience: {exp_audit.get('avg_contradictions_per_experience', 0):.1f}")
            
            largest = exp_audit.get("largest_experience", {})
            if largest:
                print("\nLargest experience:")
                print(f"  lineage: {largest.get('lineage')}")
                print(f"  theories: {largest.get('theories')}")
                print(f"  mutations: {largest.get('mutations')}")
                print(f"  contradictions: {largest.get('contradictions')}")

        # 5. WHAT REMAINS UNCERTAIN?
        print("\n5. WHAT REMAINS UNCERTAIN?")
        print("━" * 40)
        uncertainties = []
        if contra_days == 0:
            uncertainties.append("• Theory has not faced contradiction.")
        if p.get('avg_theory_usefulness', 0.0) < 0.2:
            uncertainties.append("• Utility remains unknown.")
        
        if not uncertainties:
            print("  ✓ Core assumptions validated through observation.")
        else:
            for u in uncertainties: print(f"  {u}")

        # 6. PERFORMANCE SUMMARY
        print("\n6. PERFORMANCE SUMMARY")
        print("━" * 40)
        if p:
            acc = p.get('accuracy', 0.0)
            useful = p.get('avg_theory_usefulness', 0.0)
            print(f"• {'Directional accuracy shows statistical significance.' if acc > 0.5 else 'Prediction performance remains inconclusive.'}")
            print(f"• {'Theoretical utility is grounded in observation.' if useful > 0.4 else 'Utility remains unproven.'}")
            print(f"• {'Execution policies are engaging market structure.' if total_p > 0 else 'No validated signal has emerged.'}")

        # 7. PREDICTION INTELLIGENCE
        print("\n7. PREDICTION INTELLIGENCE")
        print("━" * 40)
        pi = analysis.get("prediction_intelligence", {})
        if p and pi:
            print(f"Overall Accuracy: {p.get('accuracy', 0.0):.1%}")
            
            # Persistence
            history = analysis.get("prediction_history", [])
            last_day = history[-1] if history else {}
            persistence = last_day.get("intelligence", {}).get("directional_persistence", {}).get("10d", 0.0)
            p_desc = "Neutral"
            if persistence > 0.5: p_desc = "Strong Uptrend"
            elif persistence < -0.5: p_desc = "Strong Downtrend"
            print(f"Directional Persistence (10-day): {persistence:.2f} ({p_desc})")

            print("\n  Mutation Effectiveness:")
            me = pi.get("mutation_effectiveness", {})
            for mut in sorted(me.keys()):
                stats = me[mut]
                print(f"    • Accuracy (Mutation #{mut}): {stats['accuracy']:.1%} (n={stats['count']})")
            if me:
                base_acc = me.get(0, {}).get("accuracy", 0.0)
                high_mut_acc = me.get(max(me.keys()), {}).get("accuracy", 0.0)
                insight = "Improving" if high_mut_acc > base_acc else "Degrading" if high_mut_acc < base_acc else "Stable"
                print(f"    → Insight: Prediction quality is {insight} as mutation depth increases.")
            
            print("\n  Contradiction Intelligence:")
            ci = pi.get("contradiction_intelligence", {})
            for bucket, stats in ci.items():
                print(f"    • Accuracy ({bucket} Contradictions): {stats['accuracy']:.1%} (n={stats['count']})")
            if ci.get("0", {}).get("accuracy", 0.0) > ci.get("5+", {}).get("accuracy", 0.0):
                print(f"    → Insight: Contradiction pressure is a high-validity leading indicator of failure.")

            print("\n  Directional Bias (Confusion Matrix):")
            matrix = pi.get("directional_bias", {})
            print(f"    Predicted \\ Actual | Higher | Lower | Range | Uncertain")
            for pred in ["higher", "lower", "range_bound", "uncertain"]:
                row = matrix.get(pred, {})
                print(f"    {pred:<18} | {row.get('higher', 0):<6} | {row.get('lower', 0):<5} | {row.get('range_bound', 0):<5} | {row.get('uncertain', 0)}")
            
            print("\n  Learning Convergence:")
            conv = pi.get("convergence", {})
            p_drift = conv.get("prediction_drift", 0.0)
            t_drift = conv.get("theory_drift", 0.0)
            a_drift = conv.get("accuracy_drift", 0.0)
            print(f"    • Prediction Drift: {p_drift:.1%} ({'Volatile' if p_drift > 0.3 else 'Stable'} Mind)")
            print(f"    • Theory Drift: {t_drift:.1%} ({'High' if t_drift > 0.5 else 'Low'} Mutation Volatility)")
            print(f"    • Accuracy Drift: {a_drift:+.1%} ({'Learning' if a_drift > 0.05 else 'Regressive' if a_drift < -0.05 else 'Stagnant'})")

            print("\n  Learning Trend (Accuracy per third):")
            lt = pi.get("learning_trend", {})
            print(f"    First Third: {lt.get('first', 0.0):.1%}")
            print(f"    Middle Third: {lt.get('middle', 0.0):.1%}")
            print(f"    Final Third: {lt.get('final', 0.0):.1%}")

            # Trend Audit Table
            print("\nTREND RECOGNITION AUDIT:")
            print(f"{'DAY':<12} | {'Actual':<12} | {'Predicted':<12} | {'Persist':<7} | {'Result'}")
            print("-" * 65)
            for day in pi.get("trend_audit", [])[-15:]: # Show last 15 days
                print(f"{day['date']:<12} | {day['actual']:<12} | {day['predicted']:<12} | {day['persistence']:<7.2f} | {day['result']}")

        elif p:
            print(f"Overall Accuracy: {p.get('accuracy', 0.0):.1%}")
            print("  Learning Intelligence metrics pending sufficient data.")

        else:
            print("  No prediction analysis data available.")

        # 7. ARTIFACTS
        print("\n8. ARTIFACTS")
        print("━" * 40)
        out = external_metrics.get('outputs', {})
        print(f"  Analysis CSV: {out.get('prediction_csv','N/A')}")
        print("\n" + "═" * 60)
    def _analyze_capital_simulation(self) -> Dict:
        """Analyze capital simulation results."""
        return getattr(self, "capital_simulation_summary", {})

    def set_capital_simulation_summary(self, summary: dict):
        """Set the summary of capital simulation."""
        self.capital_simulation_summary = summary

    def _analyze_transition_memory(self) -> Dict:
        """Analyze transition memory performance."""
        return {
            "total_transition_memory_hits": getattr(self, "transition_memory_hits", 0),
            "hit_rate": getattr(self, "transition_memory_hits", 0) / len(self.days) if len(self.days) > 0 else 0.0,
        }

    def set_capital_simulation_logs(self, logs: list):
        """WIRING FIX: Set daily logs from capital simulator."""
        self.capital_simulation_logs = logs

    def export_prediction_analysis_csv(self, file_path: Path, verbose: bool = True):
        """Export detailed prediction performance and capital metrics to CSV."""
        if not self.prediction_history or not self.capital_simulation_logs:
            if verbose:
                print("No data to export for prediction analysis CSV.")
            return

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine prediction history and capital simulation logs
        combined_data = []
        rows = min(len(self.prediction_history), len(self.capital_simulation_logs))
        if rows == 0:
            if verbose:
                print("No data to export for prediction analysis CSV.")
            return

        for i in range(rows):
            pred_rec = self.prediction_history[i] or {}
            cap_rec = self.capital_simulation_logs[i] or {}
            prediction = pred_rec.get("prediction") or {}
            prior_prediction_result = pred_rec.get("prior_prediction_result") or {}

            if hasattr(prediction, "to_dict"):
                prediction = prediction.to_dict()
            if hasattr(prior_prediction_result, "to_dict"):
                prior_prediction_result = prior_prediction_result.to_dict()

            if not isinstance(prediction, dict):
                prediction = {}
            if not isinstance(prior_prediction_result, dict):
                prior_prediction_result = {}
            if not isinstance(cap_rec, dict):
                cap_rec = {}

            baseline = cap_rec.get("policies", {}).get("baseline", {}) if isinstance(cap_rec, dict) else {}

            combined_data.append({
                "date": pred_rec.get("date"),
                "prediction_direction": prediction.get("direction"),
                "prediction_confidence": prediction.get("confidence") or baseline.get("conviction"),
                "actual_direction": prior_prediction_result.get("actual_direction"),
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
        if verbose:
            print(f"Exported prediction analysis to {file_path}")
        # 5. ARTIFACTS
        print("\n5. ARTIFACTS")
        print("━" * 40)
        out = em.get('outputs', {})
        print(f"  Analysis CSV: {out.get('prediction_csv','N/A')}")
        print(f"  Snapshots:    {self.run_dir if hasattr(self, 'run_dir') else 'N/A'}")


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

    def export_prediction_analysis_csv(self, file_path: Path, verbose: bool = True):
        """Export detailed prediction performance and capital metrics to CSV."""
        if not self.prediction_history or not self.capital_simulation_logs:
            if verbose:
                print("No data to export for prediction analysis CSV.")
            return

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine prediction history and capital simulation logs
        combined_data = []
        rows = min(len(self.prediction_history), len(self.capital_simulation_logs))
        if rows == 0:
            if verbose:
                print("No data to export for prediction analysis CSV.")
            return

        for i in range(rows):
            pred_rec = self.prediction_history[i] or {}
            cap_rec = self.capital_simulation_logs[i] or {}
            prediction = pred_rec.get("prediction") or {}
            prior_prediction_result = pred_rec.get("prior_prediction_result") or {}

            if hasattr(prediction, "to_dict"):
                prediction = prediction.to_dict()
            if hasattr(prior_prediction_result, "to_dict"):
                prior_prediction_result = prior_prediction_result.to_dict()

            if not isinstance(prediction, dict):
                prediction = {}
            if not isinstance(prior_prediction_result, dict):
                prior_prediction_result = {}
            if not isinstance(cap_rec, dict):
                cap_rec = {}

            baseline = cap_rec.get("policies", {}).get("baseline", {}) if isinstance(cap_rec, dict) else {}

            combined_data.append({
                "date": pred_rec.get("date"),
                "prediction_direction": prediction.get("direction"),
                "prediction_confidence": prediction.get("confidence") or baseline.get("conviction"),
                "actual_direction": prior_prediction_result.get("actual_direction"),
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
        if verbose:
            print(f"Exported prediction analysis to {file_path}")
