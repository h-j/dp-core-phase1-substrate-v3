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
        # Fetch knowledge objects passed from repository
        if hasattr(self, "knowledge_repository") and self.knowledge_repository:
            em["principles"] = self.knowledge_repository.list_principles()
            em["world_models"] = list(self.knowledge_repository.world_models.values())
            em["open_questions"] = self.knowledge_repository.list_open_questions()
            em["reconciliation_reports"] = (
                self.knowledge_repository.list_reconciliation_reports()
            )
            em["evidence_gaps"] = self.knowledge_repository.list_evidence_gaps()
            em["mechanisms"] = self.knowledge_repository.list_mechanisms()
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
            start_failures = sum(
                len(r.get("components_failed", [])) for r in start_window
            )
            end_failures = sum(len(r.get("components_failed", [])) for r in end_window)
            start_fail_rate = start_failures / len(start_window)
            end_fail_rate = end_failures / len(end_window)

            # 2. Lesson Reuse Rate
            start_reuses = sum(
                1 for r in start_window if len(r.get("reused_lessons", [])) > 0
            )
            end_reuses = sum(
                1 for r in end_window if len(r.get("reused_lessons", [])) > 0
            )
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
            start_regime_success = (
                sum(start_sims) / len(start_sims) if start_sims else 0.0
            )
            end_regime_success = sum(end_sims) / len(end_sims) if end_sims else 0.0

            # 5. Contradiction Pressure
            start_pressures = [r.get("contradiction_score", 0.0) for r in start_window]
            end_pressures = [r.get("contradiction_score", 0.0) for r in end_window]
            start_contra_pressure = (
                sum(start_pressures) / len(start_pressures) if start_pressures else 0.0
            )
            end_contra_pressure = (
                sum(end_pressures) / len(end_pressures) if end_pressures else 0.0
            )

            # 6. Confidence Calibration Error
            def calc_calibration_error(indices):
                errors = []
                for idx in indices:
                    if idx < 1 or idx >= len(prediction_history):
                        continue
                    r_curr = prediction_history[idx]
                    r_prev = prediction_history[idx - 1]
                    if (
                        r_curr.get("prior_prediction_result")
                        and r_curr["prior_prediction_result"].get("direction_score")
                        is not None
                    ):
                        pred_conf = r_prev.get("prediction", {}).get("confidence", 0.5)
                        dir_score = r_curr["prior_prediction_result"].get(
                            "direction_score", 0.0
                        )
                        errors.append(abs(pred_conf - dir_score))
                return sum(errors) / len(errors) if errors else 0.0

            start_cal_error = calc_calibration_error(start_indices)
            end_cal_error = calc_calibration_error(end_indices)

            # Print Table
            print(f"  {'Metric':<30} | {'Start':<10} | {'End':<10}")
            print(f"  " + "-" * 56)
            print(
                f"  {'Component Failure Rate':<30} | {start_fail_rate:<10.2f} | {end_fail_rate:<10.2f}"
            )
            print(
                f"  {'Lesson Reuse Rate':<30} | {start_reuse_rate:<10.1%} | {end_reuse_rate:<10.1%}"
            )
            print(
                f"  {'Lesson Retirement Rate':<30} | {start_retire_rate:<10.2f} | {end_retire_rate:<10.2f}"
            )
            print(
                f"  {'Regime Retrieval Success':<30} | {start_regime_success:<10.2f} | {end_regime_success:<10.2f}"
            )
            print(
                f"  {'Contradiction Pressure':<30} | {start_contra_pressure:<10.2f} | {end_contra_pressure:<10.2f}"
            )
            print(
                f"  {'Confidence Calibration Error':<30} | {start_cal_error:<10.2f} | {end_cal_error:<10.2f}"
            )

            # Evaluation/Answer Section
            print("\n  Did DP become less wrong over time?")

            # Primary markers of wrongness are failure rate, calibration error, and contradiction pressure
            wrongness_start = (
                (start_fail_rate * 0.4)
                + (start_cal_error * 0.4)
                + (start_contra_pressure * 0.2)
            )
            wrongness_end = (
                (end_fail_rate * 0.4)
                + (end_cal_error * 0.4)
                + (end_contra_pressure * 0.2)
            )
            net_change = wrongness_start - wrongness_end

            reasons = []
            if end_fail_rate < start_fail_rate:
                reasons.append(
                    f"Component Failure Rate decreased ({start_fail_rate:.2f} -> {end_fail_rate:.2f})"
                )
            if end_cal_error < start_cal_error:
                reasons.append(
                    f"Confidence Calibration Error decreased ({start_cal_error:.2f} -> {end_cal_error:.2f})"
                )
            if end_contra_pressure < start_contra_pressure:
                reasons.append(
                    f"Contradiction Pressure decreased ({start_contra_pressure:.2f} -> {end_contra_pressure:.2f})"
                )
            if end_reuse_rate > start_reuse_rate:
                reasons.append(
                    f"Lesson Reuse Rate increased ({start_reuse_rate:.1%} -> {end_reuse_rate:.1%})"
                )
            if end_regime_success > start_regime_success:
                reasons.append(
                    f"Regime Retrieval Success increased ({start_regime_success:.2f} -> {end_regime_success:.2f})"
                )

            # Check if improvement is measurable and positive
            if net_change > 0.01 and len(reasons) >= 2:
                print("    - YES (Measurable and Positive):")
                for r in reasons:
                    print(f"      • {r}")
                print(
                    "\n    Conclusion: Crossing from [Reflective System] to [Learning System] (Empirically Proven)."
                )
            else:
                if net_change > 0.0:
                    print("    - SLIGHT IMPROVEMENT:")
                    for r in reasons:
                        print(f"      • {r}")
                    print(
                        "\n    Conclusion: Retained in [Reflective System] boundary (requires more epoch variance)."
                    )
                else:
                    print(
                        "    - NO: System error bounds fluctuated or did not decrease measurably."
                    )
                    print("\n    Conclusion: Retained in [Reflective System] boundary.")

        # -------------------------------------------------------------
        # H. Next Day Outlook
        # -------------------------------------------------------------
        acc_pct = p.get("accuracy", 0.0)
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

        # -------------------------------------------------------------
        # I. Knowledge Health Dashboard
        # -------------------------------------------------------------
        print("\nI. Knowledge Health Dashboard")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        principles = external_metrics.get("principles") or []
        world_models = external_metrics.get("world_models") or []
        open_questions = external_metrics.get("open_questions") or []
        reconciliation_reports = external_metrics.get("reconciliation_reports") or []

        # 1. Knowledge Compression Ratio
        obs_count = len(prediction_history)
        theory_count = external_metrics.get(
            "active_theories", 0
        ) + external_metrics.get("retired_theories", 0)
        if theory_count == 0:
            theory_count = len(
                set(
                    r.get("theory_id") for r in prediction_history if r.get("theory_id")
                )
            )
        lessons_count = lesson_stats.get("total_lessons", 0)
        principles_count = len(principles)
        wm_count = len(world_models)

        print("\n  1. Knowledge Compression Ratio:")
        print(f"    Observations:        {obs_count}")
        print(f"    Generated Theories:   {theory_count}")
        print(f"    Lessons:               {lessons_count}")
        print(f"    Principles:            {principles_count}")
        print(f"    World Models:          {wm_count}")
        print()
        print(
            f"    Compression Ratio:   {obs_count} → {theory_count} → {lessons_count} → {principles_count} → {wm_count}"
        )

        # 2. Principle Stability
        active_stable = [
            p for p in principles if p.status.value in ["active", "stable"]
        ]
        print("\n  2. Principle Stability:")
        if active_stable:
            total_age = 0
            total_confidence = 0.0
            for p in active_stable:
                age = max(1, obs_count - p.created_at_step)
                total_age += age
                total_confidence += p.confidence

                rev_count = len(p.revision_history)
                val_rate = (
                    p.support_count / (p.support_count + p.contradiction_count)
                    if (p.support_count + p.contradiction_count) > 0
                    else 1.0
                )

                print(f"    - Principle {p.id[:8]} (Status: {p.status.value.upper()})")
                print(f"      Statement:       {p.statement}")
                print(f"      Age:             {age} step(s)")
                print(f"      Revisions:       {rev_count}")
                print(
                    f"      Support/Contra:  {p.support_count} / {p.contradiction_count}"
                )
                print(f"      Validation Rate: {val_rate:.1%}")
                print(f"      Confidence:      {p.confidence:.2f}")
                print(f"      Uses (Applied):  {p.uses_count} times")
                print(
                    f"      Utility Score:   {p.usefulness_score:.2f} (Helped: {p.predictions_helped} | Harmed: {p.predictions_harmed})"
                )
                print(f"      Conf Adjustments:{p.confidence_adjustments_triggered}")
                print(f"      WM Influence:    {p.world_model_influence_count}")

            avg_stability = (
                (total_confidence / len(active_stable)) if active_stable else 0.0
            )
            print(f"\n    Average Principle Stability Score: {avg_stability:.2f}")
        else:
            print("    No active or stable principles to report.")

        # 3. Principle Coverage
        covered_theories = set()
        all_theories = set(
            r.get("theory_id") for r in prediction_history if r.get("theory_id")
        )
        for p in principles:
            if p.status.value in ["active", "stable"]:
                for tid in (
                    p.associated_lineage_ids
                    + p.supporting_theory_ids
                    + p.contradicting_theory_ids
                ):
                    if tid in all_theories:
                        covered_theories.add(tid)

        coverage_pct = (
            (len(covered_theories) / len(all_theories)) if all_theories else 0.0
        )
        print("\n  3. Principle Coverage:")
        print(f"    Generated theories:   {len(all_theories)}")
        print(f"    Covered by principles: {len(covered_theories)}")
        print(f"    Coverage:             {coverage_pct:.1%}")

        # 4. Principle Compression Efficiency
        explained_per_p = []
        for p in active_stable:
            explained_count = len(set(p.associated_lineage_ids))
            explained_per_p.append(explained_count)

        avg_efficiency = (
            (sum(explained_per_p) / len(active_stable)) if active_stable else 0.0
        )
        print("\n  4. Principle Compression Efficiency:")
        print(
            f"    Average theories explained per principle: {avg_efficiency:.1f} theories/principle"
        )

        # 5. World Model Stability
        if world_models:
            wms = sorted(world_models, key=lambda x: (x.step, x.created_at))
            latest_wm = wms[-1]
            prev_wm = wms[-2] if len(wms) > 1 else None

            days_since = max(0, obs_count - latest_wm.step)
            rev_count = len(wms) - 1
            wm_confidence = (
                sum(p.confidence for p in active_stable) / len(active_stable)
                if active_stable
                else 0.5
            )

            print("\n  5. World Model Stability:")
            print(f"    Current Version:              v{len(wms)}")
            print(
                f"    Previous Version:             v{len(wms)-1 if len(wms) > 1 else 'N/A'}"
            )
            print(f"    Revisions Count:              {rev_count}")
            print(f"    Days Since Last Revision:     {days_since} step(s)")
            print(f"    Confidence:                   {wm_confidence:.2f}")
            print(
                f"    Active Supporting Principles: {len(latest_wm.active_principle_ids)}"
            )
            print(f"    Narrative Summary:            {latest_wm.narrative_summary}")

            if prev_wm:
                retired_diff = len(
                    set(prev_wm.active_principle_ids)
                    - set(latest_wm.active_principle_ids)
                )
                added_diff = len(
                    set(latest_wm.active_principle_ids)
                    - set(prev_wm.active_principle_ids)
                )
                print(f"    Revision Trigger:")
                if retired_diff > 0:
                    print(f"      • {retired_diff} principle(s) retired/demoted")
                if added_diff > 0:
                    print(f"      • {added_diff} principle(s) added/promoted")
                if retired_diff == 0 and added_diff == 0:
                    print("      • Periodic consolidation step")
        else:
            print("\n  5. World Model Stability:")
            print("    No world model generated yet.")

        # 6. Principle Lifecycle Distribution
        statuses = [p.status.value for p in principles]
        lifecycle = {
            "candidate": statuses.count("candidate"),
            "active": statuses.count("active"),
            "stable": statuses.count("stable"),
            "challenged": statuses.count("challenged"),
            "revised": statuses.count("revised"),
            "retired": statuses.count("retired"),
        }
        print("\n  6. Principle Lifecycle Distribution:")
        print(f"    Candidate:  {lifecycle['candidate']}")
        print(f"    Active:     {lifecycle['active']}")
        print(f"    Stable:     {lifecycle['stable']}")
        print(f"    Challenged: {lifecycle['challenged']}")
        print(f"    Revised:    {lifecycle['revised']}")
        print(f"    Retired:    {lifecycle['retired']}")

        # Calculate Knowledge Debt breakdown
        active_oq = [q for q in open_questions if q.status.value == "active"]
        active_oq_count = len(active_oq)
        candidate_count = lifecycle["candidate"]
        uncovered_theories_count = len(all_theories - covered_theories)

        unexplained_obs_count = 0
        for r in prediction_history:
            failed_comps = r.get("components_failed", [])
            if not failed_comps:
                continue
            is_obs_explained = False
            for comp in failed_comps:
                for p in active_stable:
                    for fp in p.falsifiable_predictions:
                        if fp.target_component == comp:
                            context_match = True
                            for k, v in fp.applicability_filter.items():
                                val = r.get(k)
                                pred_val = r.get("prediction", {}).get(k)
                                if isinstance(v, (list, tuple, set)):
                                    if val not in v and pred_val not in v:
                                        context_match = False
                                        break
                                else:
                                    if val != v and pred_val != v:
                                        context_match = False
                                        break
                            if context_match:
                                is_obs_explained = True
                                break
                    if is_obs_explained:
                        break
                if is_obs_explained:
                    break
            if not is_obs_explained:
                unexplained_obs_count += 1

        knowledge_debt = (
            candidate_count
            + active_oq_count
            + uncovered_theories_count
            + unexplained_obs_count
        )

        # 7. Knowledge Growth Rate & Debt
        revised_p_count = sum(1 for p in principles if len(p.revision_history) > 0)
        retired_p_count = statuses.count("retired")
        print("\n  7. Knowledge Growth Rate & Debt:")
        print(f"    New Principles Created:  {len(principles)}")
        print(f"    Principles Revised:      {revised_p_count}")
        print(f"    Principles Retired:      {retired_p_count}")
        print(f"    World Model Updates:     {len(world_models)}")
        print(f"    Knowledge Debt Score:    {knowledge_debt:.1f}")
        print(f"      - Unexplained Obs:     {unexplained_obs_count}")
        print(f"      - Active Open Questions:{active_oq_count}")
        print(f"      - Uncovered Theories:   {uncovered_theories_count}")
        print(f"      - Candidate Backlog:    {candidate_count}")

        # 8. Explanatory Power
        explained_exps = 0
        total_exps = len(prediction_history)
        for r in prediction_history:
            tid = r.get("theory_id")
            if not tid:
                continue
            is_exp_covered = False
            for p in active_stable:
                if (
                    tid
                    in p.associated_lineage_ids
                    + p.supporting_theory_ids
                    + p.contradicting_theory_ids
                ):
                    is_exp_covered = True
                    break
            if is_exp_covered:
                explained_exps += 1

        explanatory_power = (explained_exps / total_exps) if total_exps > 0 else 0.0
        print("\n  8. Explanatory Power:")
        print(f"    Explanatory Power Rate:   {explanatory_power:.1%}")

        # 9. Knowledge Novelty
        novel_theories = 0
        total_theories = len(all_theories)
        for tid in all_theories:
            is_novel = True
            for p in principles:
                if p.status.value in ["active", "stable"]:
                    if (
                        tid
                        in p.associated_lineage_ids
                        + p.supporting_theory_ids
                        + p.contradicting_theory_ids
                    ):
                        is_novel = False
                        break
            if is_novel:
                novel_theories += 1

        novelty_rate = (novel_theories / total_theories) if total_theories > 0 else 0.0
        print("\n  9. Knowledge Novelty:")
        print(
            f"    Novel Theories Rate:      {novelty_rate:.1%} (unexplained by active principles)"
        )

        # 10. Open Questions (Future Curiosity Layer)
        print("\n  10. Open Questions (Future Curiosity Layer):")
        if active_oq:
            print("    Open Questions:")
            for q in active_oq:
                print(f"      • {q.question_text}")
                print(
                    f"        Hypothesized factors: {', '.join(q.hypothesized_factors)}"
                )
        else:
            print("    No unresolved open questions.")

        # 11. Knowledge Reconciliation Report
        print("\n  11. Knowledge Reconciliation Report:")
        if reconciliation_reports:
            latest_report = reconciliation_reports[-1]
            print(f"    Latest Reconciliation at step: {latest_report.step}")
            print(latest_report.summary_text)
        else:
            print("    No reconciliation cycle run yet.")

        # 12. Knowledge Influence
        guided_count = sum(
            1
            for r in prediction_history
            if len(r.get("principles_accepted", [])) > 0
            or r.get("world_model_applied", False)
        )
        experience_only_count = len(prediction_history) - guided_count
        print("\n  12. Knowledge Influence:")
        print(
            f"    Knowledge Guided Predictions:  {guided_count} (uses active principles or world models)"
        )
        print(
            f"    Experience Only Predictions:   {experience_only_count} (no active principles/world models applied)"
        )

        # 13. Knowledge Reuse Rate
        reinforce_count = sum(
            1 for r in prediction_history if r.get("novelty_decision") == "REINFORCE"
        )
        revise_count = sum(
            1 for r in prediction_history if r.get("novelty_decision") == "REVISE"
        )
        generate_count = sum(
            1 for r in prediction_history if r.get("novelty_decision") == "GENERATE"
        )
        total_decisions = reinforce_count + revise_count + generate_count
        reinforce_pct = (
            (reinforce_count / total_decisions) if total_decisions > 0 else 0.0
        )
        revise_pct = (revise_count / total_decisions) if total_decisions > 0 else 0.0
        generate_pct = (
            (generate_count / total_decisions) if total_decisions > 0 else 0.0
        )
        print("\n  13. Knowledge Reuse Rate:")
        print(
            f"    Reinforced Existing Theory: {reinforce_count} ({reinforce_pct:.1%})"
        )
        print(f"    Revised Existing Theory:    {revise_count} ({revise_pct:.1%})")
        print(f"    Generated New Theory:       {generate_count} ({generate_pct:.1%})")

        # 14. Evidence Gap Registry
        evidence_gaps = external_metrics.get("evidence_gaps") or []
        print("\n  14. Evidence Gap Registry (Curiosity Layer):")
        if evidence_gaps:
            for g in evidence_gaps:
                print(f"    - Gap ID: {g.id[:8]} (Priority: {g.priority})")
                print(f"      Missing Evidence:   {g.missing_evidence}")
                print(f"      Candidate Source:   {g.candidate_data_source}")
                print(f"      Expected Value:     {g.expected_explanatory_value}")
        else:
            print("    No active evidence gaps recorded.")

        # -------------------------------------------------------------
        # J. Paper Trading Performance
        # -------------------------------------------------------------
        pt_summary = external_metrics.get("paper_trading_summary")
        if pt_summary:
            print("\nJ. Paper Trading Performance")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(
                f"  • Total Return:             {pt_summary.get('total_return_pct', 0.0):.2f}%"
            )
            print(
                f"  • Sharpe Ratio:             {pt_summary.get('sharpe_ratio', 0.0):.2f}"
            )
            print(
                f"  • Max Drawdown:             {pt_summary.get('max_drawdown_pct', 0.0):.2f}%"
            )
            print(
                f"  • Directional Accuracy:     {pt_summary.get('directional_accuracy_pct', 0.0):.2f}%"
            )
            print(
                f"  • Commitment Accuracy:      {pt_summary.get('commitment_accuracy_pct', 0.0):.2f}%"
            )
            print(
                f"  • Average Conviction Score: {pt_summary.get('avg_conviction_score', 0.0):.2f}"
            )
            print(
                f"  • Final Capital:            ₹{pt_summary.get('final_capital', 0.0):,.2f}"
            )

        # -------------------------------------------------------------
        # K. Decision Intelligence
        # -------------------------------------------------------------
        di_metrics = external_metrics.get("decision_intelligence")
        if di_metrics:
            print("\nK. Decision Intelligence")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(
                f"  • Total Decisions:          {di_metrics.get('total_decisions', 0)}"
            )
            print(f"  • Executed Decisions:       {di_metrics.get('executed', 0)}")
            print(f"  • Skipped Decisions:        {di_metrics.get('skipped', 0)}")
            print(
                f"  • High Conviction (>=0.6):  {di_metrics.get('high_conviction', 0)}"
            )
            print(
                f"  • Low Conviction (<0.4):    {di_metrics.get('low_conviction', 0)}"
            )
            print(
                f"  • Decision Accuracy:        {di_metrics.get('decision_accuracy_pct', 0.0):.2f}%"
            )
            print(
                f"  • Allocation Efficiency:    {di_metrics.get('allocation_efficiency', 0.0):.4f}"
            )
            print(
                f"  • Average Conviction:       {di_metrics.get('avg_conviction', 0.0):.2f}"
            )
            print(
                f"  • False High Conviction:    {di_metrics.get('false_high_conviction_pct', 0.0):.2f}%"
            )
            print(
                f"  • False Low Conviction:     {di_metrics.get('false_low_conviction_pct', 0.0):.2f}%"
            )
            print(
                f"  • Decision Stability:       {di_metrics.get('decision_stability', 0.0):.4f}"
            )

            top_lin = di_metrics.get("top_lineages", [])
            print(
                f"  • Top Performing Lineages:   {', '.join(top_lin) if top_lin else 'None'}"
            )

            top_pri = di_metrics.get("top_principles", [])
            print(
                f"  • Top Performing Principles: {', '.join(top_pri) if top_pri else 'None'}"
            )

            top_mem = di_metrics.get("top_memories", [])
            print(
                f"  • Most Helpful Memory Ret:   {', '.join(top_mem) if top_mem else 'None'}"
            )

            top_harm = di_metrics.get("top_harmful_contradictions", [])
            print(
                f"  • Most Harmful Contradiction: {', '.join(top_harm) if top_harm else 'None'}"
            )

            print(
                f"  • Knowledge Changes:        {di_metrics.get('knowledge_changes_count', 0)} action(s)"
            )

        # -------------------------------------------------------------
        # L. Ontology Compliance Report
        # -------------------------------------------------------------
        from cognition.schemas.knowledge.ontology import OntologyRegistry

        print("\nL. Ontology Compliance Report")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        tc_chk = OntologyRegistry._theory_components_checked
        tc_val = OntologyRegistry._theory_components_valid
        tc_pct = (tc_val / tc_chk * 100.0) if tc_chk > 0 else 100.0

        mc_chk = tc_chk
        mc_val = tc_val
        mc_pct = tc_pct

        pf_chk = OntologyRegistry._principle_filters_checked
        pf_val = OntologyRegistry._principle_filters_valid
        pf_pct = (pf_val / pf_chk * 100.0) if pf_chk > 0 else 100.0

        print(f"  • Theory Components Checked:    {tc_chk}")
        print(f"  • Theory Components Valid:      {tc_val} ({tc_pct:.1f}%)")
        print(f"  • Mechanism Components Checked: {mc_chk}")
        print(f"  • Mechanism Components Valid:   {mc_val} ({mc_pct:.1f}%)")
        print(f"  • Principle Filters Checked:    {pf_chk}")
        print(f"  • Principle Filters Valid:      {pf_val} ({pf_pct:.1f}%)")
        print(
            f"  • Rejected Filters Count:       {OntologyRegistry._rejected_filters_count}"
        )
        print(
            f"  • Regenerated Filters Count:    {OntologyRegistry._regenerated_filters_count}"
        )

        unknowns = sorted(list(OntologyRegistry._unknown_ontology_values))
        print(
            f"  • Unknown Taxonomy Values:      {', '.join(unknowns) if unknowns else 'None'}"
        )

        # -------------------------------------------------------------
        # M. Knowledge Formation Instrumentation
        # -------------------------------------------------------------
        print("\nM. Knowledge Formation Instrumentation")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        mechanisms = external_metrics.get("mechanisms") or []
        mech_reused = sum(max(0, len(m.associated_theory_ids) - 1) for m in mechanisms)
        candidate_p = sum(1 for p in principles if p.status.value == "candidate")
        validated_p = sum(
            1 for p in principles if p.status.value not in ["candidate", "retired"]
        )
        avg_sup = (
            (sum(p.support_count for p in principles) / len(principles))
            if principles
            else 0.0
        )
        avg_con = (
            (sum(p.contradiction_count for p in principles) / len(principles))
            if principles
            else 0.0
        )

        maturation_times = []
        for p in principles:
            transition_step = None
            for entry in p.maturation_history:
                if (
                    entry.status_before == "candidate"
                    and entry.status_after != "candidate"
                ):
                    transition_step = entry.step
                    break
            if transition_step is not None:
                maturation_times.append(max(0, transition_step - p.created_at_step))
        avg_maturation_time = (
            (sum(maturation_times) / len(maturation_times)) if maturation_times else 0.0
        )

        print(f"  • Mechanisms Discovered:        {len(mechanisms)}")
        print(f"  • Mechanisms Reused:            {mech_reused} time(s)")
        print(f"  • Candidate Principles:         {candidate_p}")
        print(f"  • Validated Principles:         {validated_p}")
        print(f"  • Average Support Count:        {avg_sup:.2f}")
        print(f"  • Average Contradiction Count:   {avg_con:.2f}")
        print(f"  • Average Maturation Time:      {avg_maturation_time:.2f} step(s)")
        print(f"  • Knowledge Guided Predictions:  {guided_count} step(s)")
        print(f"  • Principle Coverage:           {coverage_pct:.1%}")

        tm = analysis.get("theory_mutation_metrics") or {}
        print(
            f"  • Average Theory Word Count:    {tm.get('avg_theory_word_count', 0.0):.1f}"
        )
        print(
            f"  • Average Mechanism Count:      {tm.get('avg_mechanism_count', 0.0):.1f}"
        )
        print(
            f"  • Average Conditional Clauses:  {tm.get('avg_conditional_clauses', 0.0):.1f}"
        )
        print(
            f"  • Total Exceptions Added:       {tm.get('total_exceptions_added', 0)}"
        )
        print(
            f"  • Total Mechanisms Retired:     {tm.get('total_mechanisms_retired', 0)}"
        )
        print(
            f"  • Total Mechanisms Added:       {tm.get('total_mechanisms_added', 0)}"
        )
        print(
            f"  • Total Mechanisms Modified:    {tm.get('total_mechanisms_modified', 0)}"
        )
        print(
            f"  • Mechanism Stability:          {tm.get('avg_mechanism_stability', 1.0):.3f}"
        )

        words_before = tm.get("words_before_mutation", 0)
        words_after = tm.get("words_after_mutation", 0)
        word_pct = tm.get("word_compression_pct", 0.0)
        mechs_before = tm.get("mechanisms_before_mutation", 0)
        mechs_after = tm.get("mechanisms_after_mutation", 0)
        mech_pct = tm.get("mechanism_compression_pct", 0.0)

        print(
            f"  • Mutation Word Compression:    {words_before} → {words_after} ({word_pct:+.1f}%)"
        )
        print(
            f"  • Mutation Mech Compression:    {mechs_before} → {mechs_after} ({mech_pct:+.1f}%)"
        )

        # -------------------------------------------------------------
        # N. Mechanism Registry Health
        # -------------------------------------------------------------
        print("\nN. Mechanism Registry Health")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        mm = analysis.get("mechanism_metrics") or {}
        print(f"  • Mechanisms Alive:            {mm.get('mechanisms_alive', 0)}")
        print(f"  • Mechanisms Created:          {mm.get('mechanisms_created', 0)}")
        print(f"  • Mechanisms Reused:           {mm.get('mechanisms_reused', 0)}")
        print(f"  • Mechanisms Retired:          {mm.get('mechanisms_retired', 0)}")
        print(
            f"  • Average Mechanism Age:       {mm.get('avg_mechanism_age', 0.0):.2f} step(s)"
        )
        print(
            f"  • Mechanism Stability:         {mm.get('mechanism_stability', 1.0):.2f}"
        )
        print(f"  • Reuse Rate:                  {mm.get('reuse_rate', 0.0):.1%}")
        print(
            f"  • Evidence Accumulated:        {mm.get('evidence_accumulated', 0)} observation(s)"
        )

        print("\n  Top Stable Mechanisms:")
        top_stable = mm.get("top_stable_mechanisms", [])
        if top_stable:
            for name, age, status in top_stable[:3]:
                print(f"    - {name} (age: {age} steps, status: {status})")
        else:
            print("    - None")

        print("\n  Top Contradicted Mechanisms:")
        top_contra = mm.get("top_contradicted_mechanisms", [])
        if top_contra:
            for name, count in top_contra[:3]:
                print(f"    - {name} (contradictions: {count})")
        else:
            print("    - None")

        print("\n  Candidate Invariants:")
        invariants = mm.get("candidate_invariants", [])
        if invariants:
            for name, desc in invariants:
                print(f"    - {name}: {desc}")
        else:
            print("    - None")

        # -------------------------------------------------------------
        # O. Proposition Compilation Statistics
        # -------------------------------------------------------------
        comp_metrics = external_metrics.get("compilation_metrics")
        if (
            comp_metrics
            and isinstance(comp_metrics, dict)
            and not hasattr(comp_metrics, "_mock_self")
        ):
            print("\nO. Proposition Compilation Statistics")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(
                f"  • Theories Processed (Generated):{comp_metrics.get('theories_generated', 0)}"
            )
            print(
                f"  • Propositions Compiled (Total):{comp_metrics.get('propositions_compiled', 0)}"
            )
            print(
                f"  • Compilation Success Rate:     {comp_metrics.get('compilation_success_rate', 0.0):.1%}"
            )
            print(
                f"  • Success Count:                {comp_metrics.get('compilation_success_count', 0)}"
            )
            print(
                f"  • Partial Count:                {comp_metrics.get('compilation_partial_count', 0)}"
            )
            print(
                f"  • Failed Count:                 {comp_metrics.get('compilation_failed_count', 0)}"
            )
            print("\n  [Semantic Compilation stage]")
            print(
                f"  • Semantic Propositions Created: {comp_metrics.get('semantic_propositions_created', 0)}"
            )
            print(
                f"  • Semantic Failures:            {comp_metrics.get('semantic_failures', 0)}"
            )
            print(
                f"  • Ontology Mapping Failures:     {comp_metrics.get('ontology_mapping_failures', 0)}"
            )
            print("\n  [Parameter Grounding stage]")
            print(
                f"  • Propositions Grounded:        {comp_metrics.get('propositions_grounded', 0)}"
            )
            print(
                f"  • Percentile Groundings Applied: {comp_metrics.get('percentile_grounding', 0)}"
            )
            print(
                f"  • Relative References Resolved:  {comp_metrics.get('relative_references_resolved', 0)}"
            )
            print(
                f"  • Grounding Failures:           {comp_metrics.get('grounding_failures', 0)}"
            )
            print("\n  [Validation Engine stage]")
            print(
                f"  • Propositions Evaluated:        {comp_metrics.get('propositions_evaluated', 0)}"
            )
            print(
                f"  • Validation Records Created:   {comp_metrics.get('validation_records_created', 0)}"
            )
            print(
                f"  • Supported Records:            {comp_metrics.get('supported_records', 0)}"
            )
            print(
                f"  • Contradicted Records:         {comp_metrics.get('contradicted_records', 0)}"
            )
            print(
                f"  • Partially Supported Records:  {comp_metrics.get('partially_supported_records', 0)}"
            )
            print(
                f"  • Undecidable Records:          {comp_metrics.get('undecidable_records', 0)}"
            )

            bm = external_metrics.get("belief_metrics", {})
            if bm:
                print("\n  [Closed-Loop Belief Dynamics & World Model]")
                print(
                    f"  • Active Lineages Tracked:       {bm.get('active_lineages', 0)}"
                )
                print(
                    f"  • Weakened Lineages:             {bm.get('weakened_lineages', 0)}"
                )
                print(
                    f"  • Retired Lineages:              {bm.get('retired_lineages', 0)}"
                )
                print(
                    f"  • Mean Confidence (Active):      {bm.get('mean_confidence', 0.0):.3f}"
                )
                print(
                    f"  • Mean Uncertainty (Active):     {bm.get('mean_uncertainty', 0.0):.3f}"
                )
                print(
                    f"  • Belief Transition Events:      {bm.get('total_transition_events', 0)}"
                )
                print(
                    f"  • Promoted Lessons:              {bm.get('total_lessons', 0)}"
                )
                print(
                    f"  • Hard WM Constraints Active:    {bm.get('hard_constraints', 0)}"
                )
                print(
                    f"  • Soft WM Priors Active:         {bm.get('soft_constraints', 0)}"
                )

            reasons = comp_metrics.get("failure_reasons", {})
            if reasons:
                print("  • Failure Reasons / Categories:")
                for reason, count in sorted(
                    reasons.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"    - {reason}: {count} time(s)")

        # Artifacts
        print("\n" + "━" * 50)
        out = external_metrics.get("outputs", {})
        print(f"  Analysis CSV: {out.get('prediction_csv','N/A')}")
        if pt_summary:
            print(f"  Paper Trade Log CSV: {out.get('paper_trade_csv','N/A')}")
        if di_metrics:
            print(f"  Decision Journal:    {out.get('decision_journal_json','N/A')}")
        print("═" * 80)
