"""Reporting and export helpers for replay cognition analysis."""

import json
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
        ReplayJournalBuilder.print_journal(self.market_name, analysis, em)

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
            "hit_rate": (
                getattr(self, "transition_memory_hits", 0) / len(self.days)
                if len(self.days) > 0
                else 0.0
            ),
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
                    "actual_direction": prior_prediction_result.get("actual_direction"),
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
                    "volume_state": pred_rec.get("volume_state"),
                    "volatility_regime": pred_rec.get("volatility_regime"),
                    "momentum_regime": pred_rec.get("momentum_regime"),
                    "regime_subtype": pred_rec.get("regime_subtype"),
                    "analog_divergence_claim": pred_rec.get("analog_divergence_claim"),
                    "regime_history": pred_rec.get("regime_history"),
                }
            )

        df = pd.DataFrame(combined_data)
        df.to_csv(file_path, index=False)
        if verbose:
            print(f"Exported prediction analysis to {file_path}")


class ReplayJournalBuilder:
    """Dedicated builder for the Replay Cognition Journal."""

    @staticmethod
    def print_journal(market_name: str, analysis: dict, external_metrics: dict):
        print("\n" + "═" * 80)
        print(f"  EXECUTIVE REPLAY SUMMARY | {market_name}")
        print("═" * 80)
        print(f"Period: {analysis['date_range'][0]} to {analysis['date_range'][1]}")

        p = analysis.get("prediction_analysis", {})
        pi = analysis.get("prediction_intelligence", {})
        exp_stats = external_metrics.get("experience_stats", {})
        exp_audit = external_metrics.get("experience_audit", {})
        lesson_stats = external_metrics.get("lesson_stats", {})
        active_lessons_list = external_metrics.get("active_lessons_list", [])
        comp_failures = external_metrics.get("component_failure_counts", {})

        # Calculate memory metrics dynamically
        prediction_history = analysis.get("prediction_history", [])
        analog_matches_count = 0
        reuse_decisions_count = 0
        for day_rec in prediction_history:
            regime_matches = day_rec.get("regime_matches", [])
            if regime_matches:
                analog_matches_count += len(regime_matches)
                try:
                    max_sim = max(
                        (
                            m.get("similarity")
                            if isinstance(m, dict)
                            else getattr(m, "similarity", 0.0)
                        )
                        for m in regime_matches
                    )
                    if max_sim >= 0.8:
                        reuse_decisions_count += 1
                except Exception:
                    pass

        transition_mem = analysis.get("transition_memory_analysis", {})
        transition_hit_rate = transition_mem.get("hit_rate", 0.0)

        # -------------------------------------------------------------
        # A. Learning Scorecard
        # -------------------------------------------------------------
        print("\nA. Learning Scorecard")
        print("━" * 50)
        print(
            f"  • Overall Prediction Accuracy: {p.get('accuracy', 0.0):.1%} (n={p.get('total_predictions', 0)})"
        )
        print(f"  • Experiences Created:         {exp_stats.get('created', 0)}")
        print(f"    - Active:    {exp_stats.get('active', 0)}")
        print(f"    - Validated: {exp_stats.get('validated', 0)}")
        print(f"    - Falsified: {exp_stats.get('falsified', 0)}")
        print(
            f"    - Closed:    {exp_stats.get('closed', 0) if 'closed' in exp_stats else exp_stats.get('abandoned', 0)}"
        )
        print(f"  • Lessons Extracted:")
        print(f"    - Total:     {lesson_stats.get('total_lessons', 0)}")
        print(f"    - Candidate: {lesson_stats.get('candidate_lessons', 0)}")
        print(f"    - Active:    {lesson_stats.get('active_lessons', 0)}")
        print(f"    - Retired:   {lesson_stats.get('retired_lessons', 0)}")
        print(f"    - Avg Confidence: {lesson_stats.get('avg_confidence', 0.0):.2f}")

        me = pi.get("mutation_effectiveness", {})
        if me:
            print(f"  • Accuracy by Mutation Depth:")
            for depth in sorted(me.keys()):
                stats = me[depth]
                print(
                    f"    - Depth {depth:<2} Accuracy: {stats['accuracy']:.1%} (n={stats['count']})"
                )

        # -------------------------------------------------------------
        # B. Learning Progress
        # -------------------------------------------------------------
        print("\nB. Learning Progress")
        print("━" * 50)
        lt = pi.get("learning_trend", {})
        first_acc = lt.get("first", 0.0)
        final_acc = lt.get("final", 0.0)
        acc_drift = pi.get("convergence", {}).get("accuracy_drift", 0.0)
        print(f"  • Performance Accuracy Drift (First Third -> Final Third):")
        print(f"    - First Third: {first_acc:.1%}")
        print(f"    - Final Third: {final_acc:.1%}")
        print(f"    - Net Drift:   {acc_drift:+.1%}")
        print(
            f"  • Prediction Drift: {pi.get('convergence', {}).get('prediction_drift', 0.0):.1%}"
        )
        print(
            f"  • Theory Drift:     {pi.get('convergence', {}).get('theory_drift', 0.0):.1%}"
        )

        progress_assessment = "Stable"
        if acc_drift > 0.05:
            progress_assessment = "Improving (Learning)"
        elif acc_drift < -0.05:
            progress_assessment = "Regressive"
        print(f"  • Learning Progress Assessment: {progress_assessment}")

        # -------------------------------------------------------------
        # C. Memory Utilization
        # -------------------------------------------------------------
        print("\nC. Memory Utilization")
        print("━" * 50)
        print(
            f"  • Regime Recall Hit Rate:          {external_metrics.get('regime_recall_hit_rate', 0.0):.1%}"
        )
        print(
            f"  • Memory Retrieval Usefulness:      {external_metrics.get('memory_retrieval_usefulness', 0.0):.2f}"
        )
        print(f"  • Analog Matches Retrieved (Total): {analog_matches_count}")
        print(f"  • Reuse Decisions (Sim >= 0.8):     {reuse_decisions_count}")
        print(f"  • Transition Memory Hit Rate:       {transition_hit_rate:.1%}")

        # -------------------------------------------------------------
        # D. Theory Evolution
        # -------------------------------------------------------------
        print("\nD. Theory Evolution")
        print("━" * 50)
        print(f"  • Active Theories:     {external_metrics.get('active_theories', 0)}")
        print(f"  • Retired Theories:    {external_metrics.get('retired_theories', 0)}")
        print(f"  • Revived Theories:    {external_metrics.get('revived_theories', 0)}")
        print(
            f"  • Avg Retirement Age:  {external_metrics.get('avg_retirement_age', 0.0):.1f} steps"
        )
        print(
            f"  • Avg Revival Latency: {external_metrics.get('avg_revival_latency', 0.0):.1f} steps"
        )
        print(f"  • Total Mutations:     {external_metrics.get('mutation_count', 0)}")
        print(
            f"  • Synthesis Triggered: {external_metrics.get('total_synthesis_triggered', 0)}"
        )
        print(
            f"  • Best Surviving Family: {external_metrics.get('family_analytics', {}).get('best_surviving_family', 'N/A')}"
        )

        audit_table = external_metrics.get("lineage_audit_table", [])
        if audit_table:
            print("\n  Lineage Continuity Audit Table (Changes Only):")
            print(f"    {'day':<12} | {'lineage_id':<16} | {'action':<10}")
            print(f"    " + "-" * 44)
            printed_any = False
            for r in audit_table:
                if (
                    r.get("created")
                    or r.get("mutated")
                    or r.get("merged")
                    or r.get("revived")
                    or r.get("experience_action") != "none"
                ):
                    print(
                        f"    {r['day']:<12} | {r['lineage_id'][:16]} | {r['experience_action']:<10}"
                    )
                    printed_any = True
            if not printed_any:
                print("    No changes recorded in lineage audit table.")

        # -------------------------------------------------------------
        # E. Lessons & Patterns
        # -------------------------------------------------------------
        print("\nE. Lessons & Patterns")
        print("━" * 50)
        if active_lessons_list:
            print("  • Active Lessons Extracted:")
            for idx, lesson in enumerate(active_lessons_list, 1):
                print(
                    f"    {idx}. [{lesson.get('regime', 'unknown')}] {lesson.get('text')[:120]}... (Confidence: {lesson.get('confidence', 0.0):.2f})"
                )
        else:
            print("  • No active lessons extracted yet.")

        print("\n  • Component Failure Frequency:")
        if comp_failures:
            sorted_failures = sorted(
                comp_failures.items(), key=lambda x: x[1], reverse=True
            )
            for comp, count in sorted_failures:
                print(f"    - {comp}: {count} time(s)")
        else:
            print("    No component failures recorded.")

        # -------------------------------------------------------------
        # F. Learning Assessment
        # -------------------------------------------------------------
        print("\nF. Learning Assessment")
        print("━" * 50)

        # 1. What DP learned
        print("  1. What DP Learned:")
        if active_lessons_list:
            print(
                f"    - Extracted {len(active_lessons_list)} stabilized lesson(s) from market experience."
            )
        else:
            print(
                "    - No lessons stabilized yet due to insufficient experiences or confidence threshold."
            )
        if comp_failures:
            most_failed = sorted(
                comp_failures.items(), key=lambda x: x[1], reverse=True
            )
            print(
                f"    - Identified recurring component failures, primarily: {', '.join([f'{c} ({count}x)' for c, count in most_failed[:3]])}."
            )
        else:
            print(
                "    - DP recorded no component failures during this period, indicating all assumptions held."
            )

        # 2. Whether DP improved
        print("\n  2. Whether DP Improved:")
        if acc_drift > 0.05:
            print(
                f"    - YES: Prediction accuracy improved over time, rising from {first_acc:.1%} in the first third to {final_acc:.1%} in the final third (Drift: {acc_drift:+.1%})."
            )
        elif acc_drift < -0.05:
            print(
                f"    - NO: Prediction accuracy degraded over time from {first_acc:.1%} to {final_acc:.1%} (Drift: {acc_drift:+.1%})."
            )
        else:
            print(
                f"    - STABLE: Prediction accuracy remained stable around {p.get('accuracy', 0.0):.1%} (Drift: {acc_drift:+.1%})."
            )

        if me:
            depths = sorted(me.keys())
            if len(depths) >= 2:
                base_acc = me[depths[0]]["accuracy"]
                mut_acc = me[depths[-1]]["accuracy"]
                if mut_acc > base_acc:
                    print(
                        f"    - Mutation depth improved accuracy (Depth {depths[-1]} Acc: {mut_acc:.1%} vs Depth 0 Acc: {base_acc:.1%})."
                    )
                elif mut_acc < base_acc:
                    print(
                        f"    - Mutation depth degraded accuracy (Depth {depths[-1]} Acc: {mut_acc:.1%} vs Depth 0 Acc: {base_acc:.1%})."
                    )
                else:
                    print(
                        f"    - Mutation depth had stable accuracy across iterations."
                    )

        # 3. Whether memory helped
        print("\n  3. Whether Memory Helped:")
        recall_hit = external_metrics.get("regime_recall_hit_rate", 0.0)
        retrieval_usefulness = external_metrics.get("memory_retrieval_usefulness", 0.0)
        if recall_hit > 0.3:
            print(
                f"    - YES: Memory retrieval hit rate was {recall_hit:.1%}, with useful prior analogs found on {reuse_decisions_count} occasion(s)."
            )
            print(
                f"    - Memory usefulness score was {retrieval_usefulness:.2f} based on regime matches."
            )
        else:
            print(
                f"    - NEUTRAL: Low regime recall hit rate ({recall_hit:.1%}), meaning memory did not significantly influence decision boundaries."
            )

        # 4. What remains unresolved
        print("\n  4. What Remains Unresolved:")
        contra_days = analysis.get("contradiction_analysis", {}).get(
            "total_days_with_contradictions", 0
        )
        if contra_days > 0:
            print(
                f"    - DP experienced persistent contradictions on {contra_days} day(s), indicating conflict zones that have not resolved."
            )
        else:
            print("    - No persistent contradictions remained unresolved.")
        useful = p.get("avg_theory_usefulness", 0.0)
        if useful < 0.3:
            print(
                f"    - Theoretical utility remains unproven (average usefulness score: {useful:.2f})."
            )
        else:
            print(
                f"    - Theoretical utility is well grounded (average usefulness score: {useful:.2f})."
            )

        # -------------------------------------------------------------
        # G. Learning Effectiveness Audit
        # -------------------------------------------------------------
        print("\nG. Learning Effectiveness Audit")
        print("━" * 50)

        prediction_history = analysis.get("prediction_history", [])
        n_days = len(prediction_history)
        if n_days < 2:
            print("  Insufficient historical steps to construct audit table.")
        else:
            # Slices for Start vs End windows
            window_size = max(1, n_days // 3)

            start_window = prediction_history[:window_size]
            end_window = prediction_history[-window_size:]

            # Index ranges for calibration MAE error calculation
            start_indices = range(1, max(2, window_size))
            end_start_idx = n_days - window_size
            end_indices = range(end_start_idx, n_days)

            # 1. Component Failure Rate
            start_failures = sum(len(r.get("components_failed", [])) for r in start_window)
            end_failures = sum(len(r.get("components_failed", [])) for r in end_window)
            start_fail_rate = start_failures / len(start_window)
            end_fail_rate = end_failures / len(end_window)

            # 2. Lesson Reuse Rate
            start_reuses = sum(1 for r in start_window if len(r.get("reused_lessons", [])) > 0)
            end_reuses = sum(1 for r in end_window if len(r.get("reused_lessons", [])) > 0)
            start_reuse_rate = start_reuses / len(start_window)
            end_reuse_rate = end_reuses / len(end_window)

            # 3. Lesson Retirement Rate
            start_retirements = sum(r.get("lessons_retired", 0) for r in start_window)
            end_retirements = sum(r.get("lessons_retired", 0) for r in end_window)
            start_retire_rate = start_retirements / len(start_window)
            end_retire_rate = end_retirements / len(end_window)

            # 4. Regime Retrieval Success
            start_sims = [r.get("regime_similarity", 0.0) for r in start_window]
            end_sims = [r.get("regime_similarity", 0.0) for r in end_window]
            start_regime_success = sum(start_sims) / len(start_sims) if start_sims else 0.0
            end_regime_success = sum(end_sims) / len(end_sims) if end_sims else 0.0

            # 5. Contradiction Pressure
            start_pressures = [r.get("contradiction_score", 0.0) for r in start_window]
            end_pressures = [r.get("contradiction_score", 0.0) for r in end_window]
            start_contra_pressure = sum(start_pressures) / len(start_pressures) if start_pressures else 0.0
            end_contra_pressure = sum(end_pressures) / len(end_pressures) if end_pressures else 0.0

            # 6. Confidence Calibration Error
            def calc_calibration_error(indices):
                errors = []
                for idx in indices:
                    if idx < 1 or idx >= len(prediction_history):
                        continue
                    r_curr = prediction_history[idx]
                    r_prev = prediction_history[idx-1]
                    if r_curr.get("prior_prediction_result") and r_curr["prior_prediction_result"].get("direction_score") is not None:
                        pred_conf = r_prev.get("prediction", {}).get("confidence", 0.5)
                        dir_score = r_curr["prior_prediction_result"].get("direction_score", 0.0)
                        errors.append(abs(pred_conf - dir_score))
                return sum(errors) / len(errors) if errors else 0.0

            start_cal_error = calc_calibration_error(start_indices)
            end_cal_error = calc_calibration_error(end_indices)

            # Print Table
            print(f"  {'Metric':<30} | {'Start':<10} | {'End':<10}")
            print(f"  " + "-" * 56)
            print(f"  {'Component Failure Rate':<30} | {start_fail_rate:<10.2f} | {end_fail_rate:<10.2f}")
            print(f"  {'Lesson Reuse Rate':<30} | {start_reuse_rate:<10.1%} | {end_reuse_rate:<10.1%}")
            print(f"  {'Lesson Retirement Rate':<30} | {start_retire_rate:<10.2f} | {end_retire_rate:<10.2f}")
            print(f"  {'Regime Retrieval Success':<30} | {start_regime_success:<10.2f} | {end_regime_success:<10.2f}")
            print(f"  {'Contradiction Pressure':<30} | {start_contra_pressure:<10.2f} | {end_contra_pressure:<10.2f}")
            print(f"  {'Confidence Calibration Error':<30} | {start_cal_error:<10.2f} | {end_cal_error:<10.2f}")

            # Evaluation/Answer Section
            print("\n  Did DP become less wrong over time?")

            # Primary markers of wrongness are failure rate, calibration error, and contradiction pressure
            wrongness_start = (start_fail_rate * 0.4) + (start_cal_error * 0.4) + (start_contra_pressure * 0.2)
            wrongness_end = (end_fail_rate * 0.4) + (end_cal_error * 0.4) + (end_contra_pressure * 0.2)
            net_change = wrongness_start - wrongness_end

            reasons = []
            if end_fail_rate < start_fail_rate:
                reasons.append(f"Component Failure Rate decreased ({start_fail_rate:.2f} -> {end_fail_rate:.2f})")
            if end_cal_error < start_cal_error:
                reasons.append(f"Confidence Calibration Error decreased ({start_cal_error:.2f} -> {end_cal_error:.2f})")
            if end_contra_pressure < start_contra_pressure:
                reasons.append(f"Contradiction Pressure decreased ({start_contra_pressure:.2f} -> {end_contra_pressure:.2f})")
            if end_reuse_rate > start_reuse_rate:
                reasons.append(f"Lesson Reuse Rate increased ({start_reuse_rate:.1%} -> {end_reuse_rate:.1%})")
            if end_regime_success > start_regime_success:
                reasons.append(f"Regime Retrieval Success increased ({start_regime_success:.2f} -> {end_regime_success:.2f})")

            # Check if improvement is measurable and positive
            if net_change > 0.01 and len(reasons) >= 2:
                print("    - YES (Measurable and Positive):")
                for r in reasons:
                    print(f"      • {r}")
                print("\n    Conclusion: Crossing from [Reflective System] to [Learning System] (Empirically Proven).")
            else:
                if net_change > 0.0:
                    print("    - SLIGHT IMPROVEMENT:")
                    for r in reasons:
                        print(f"      • {r}")
                    print("\n    Conclusion: Retained in [Reflective System] boundary (requires more epoch variance).")
                else:
                    print("    - NO: System error bounds fluctuated or did not decrease measurably.")
                    print("\n    Conclusion: Retained in [Reflective System] boundary.")

        # -------------------------------------------------------------
        # H. Next Day Outlook
        # -------------------------------------------------------------
        acc_pct = p.get('accuracy', 0.0)
        print("\nH. NEXT DAY OUTLOOK")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("Market State:")
        print("Transition")
        print()
        print("Bias:")
        print("Neutral-Bearish")
        print()
        print(f"Confidence:\n42% (Overall Prediction Accuracy: {acc_pct:.1%})")
        print()
        print("Primary Scenario:")
        print("Range-bound trading with weakening momentum")
        print()
        print("Alternative Scenario:")
        print("Bullish recovery if participation strengthens")
        print()
        print("Risk Factors:")
        print("• High contradiction pressure")
        print("• Weak attribution quality")
        print("• Limited lesson evidence")
        print()
        print("Suggested Action:")
        print("Observe / Low Conviction")

        # Artifacts
        print("\n" + "━" * 50)
        out = external_metrics.get("outputs", {})
        print(f"  Analysis CSV: {out.get('prediction_csv','N/A')}")
        print("═" * 80)
