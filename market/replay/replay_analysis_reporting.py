"""Reporting and export helpers for replay cognition analysis."""

from pathlib import Path
from typing import Dict

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

        print("\n" + "═" * 60)
        print(f"  REPLAY COGNITION JOURNAL | {self.market_name}")
        print("═" * 60)
        print(f"Period: {analysis['date_range'][0]} to {analysis['date_range'][1]}")

        # 1. WHAT CHANGED?
        print("\n1. WHAT CHANGED?")
        print("━" * 40)
        conf = analysis.get("confidence_analysis", {})
        emp = conf.get("empirical_confidence", {})
        print(f"• Confidence {emp.get('trajectory', 'stable')}")

        contra_days = analysis.get("contradiction_analysis", {}).get("total_days_with_contradictions", 0)
        if contra_days == 0:
            print("• No contradiction detected")
        else:
            print(f"• Contradictions persisted ({contra_days} days)")

        synthesis_count = em.get('total_synthesis_triggered', 0)
        if synthesis_count == 0:
            print("• No synthesis triggered")
        else:
            print(f"• Cognitive synthesis active ({synthesis_count} triggered)")

        mut_count = em.get('mutation_count', 0)
        if mut_count == 0:
            print("• No theory mutation observed")
        else:
            print(f"• Theory trajectory evolved ({mut_count} mutations)")

        # 2. WHAT WAS LEARNED?
        print("\n2. WHAT WAS LEARNED?")
        print("━" * 40)
        events = []
        if mut_count > 0: events.append(f"• Mutation: {mut_count} adaptive shifts recorded")
        if contra_days > 0: events.append(f"• Contradiction: {contra_days} days of cognitive conflict identified")
        if synthesis_count > 0: events.append(f"• Synthesis: {synthesis_count} cognitive syntheses resolved conflict")
        
        p = analysis.get("prediction_analysis", {})
        inval_rate = p.get('invalidation_rate', 0.0)
        total_p = p.get('total_predictions', 0)
        falsifications = int(inval_rate * total_p)
        if falsifications > 0: events.append(f"• Falsification: {falsifications} theories rejected by market outcome")
        
        revivals = em.get('revived_theories', 0)
        if revivals > 0: events.append(f"• Revival: {revivals} theories restored from memory")
        
        correct = int(p.get('accuracy', 0.0) * total_p)
        if correct > 0: events.append(f"• Validation: {correct} predictions successfully grounded")

        if not events:
            print("  No significant learning events occurred.")
            print("  Current theory remains largely untested.")
        else:
            for e in events: print(f"  {e}")

        # 3. WHAT SURVIVED?
        print("\n3. WHAT SURVIVED?")
        print("━" * 40)
        family = em.get("family_analytics", {})
        if family:
            best_fam = family.get('best_surviving_family', 'N/A')
            print(f"Theory Family:          {best_fam}")
            print(f"Age:                    {em.get('longest_surviving', 0)} days")
            print(f"Mutations:              {mut_count}")
            print(f"Contradictions Survived: {analysis.get('contradiction_analysis', {}).get('total_days_with_contradictions', 0)}")
            print(f"Peak Utility:           {p.get('accuracy_when_high_usefulness', 0.0):.2f}")
            print(f"Status:                 ACTIVE")
        else:
            print("Theory evolution analysis: Pending sufficient lineage data.")

        # 4. WHAT REMAINS UNCERTAIN?
        print("\n4. WHAT REMAINS UNCERTAIN?")
        print("━" * 40)
        uncertainties = []
        if contra_days == 0:
            uncertainties.append("• Theory has not faced contradiction.")
        if inval_rate == 0:
            uncertainties.append("• Falsification boundary remains untested.")
        if p.get('avg_theory_usefulness', 0.0) < 0.2:
            uncertainties.append("• Utility remains unknown.")
        
        tp_analysis = analysis.get('transition_pressure_analysis', {})
        if tp_analysis.get('avg_pressure', 0.0) > 0.4:
            uncertainties.append("• Regime transition remains unresolved.")
        if conf.get("contradiction_pressure", {}).get("final", 0.0) > 0.4:
            uncertainties.append("• Contradiction pressure elevated.")
            
        if not uncertainties:
            print("  ✓ Core assumptions validated through observation.")
        else:
            for u in uncertainties: print(f"  {u}")

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
