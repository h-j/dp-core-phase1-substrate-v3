"""Replay finalization, exports, and optional comparison handling."""

from pathlib import Path
from statistics import mean


class ReplayFinalizationMixin:
    def _finalize_replay(self, execution_hash: str, emit_summary: bool):
        # Finalize capital simulation and analysis
        capital_summary = self.capital_simulator.get_summary()
        self.replay_analysis_engine.set_capital_simulation_summary(capital_summary)
        # WIRING FIX 2: Transfer capital simulator daily logs to analysis engine
        self.replay_analysis_engine.set_capital_simulation_logs(
            self.capital_simulator.get_daily_logs()
        )

        # Prepare external metrics (from runtime objects) for richer summary
        try:
            external_metrics = {}
            external_metrics["total_steps"] = len(self.engine)
            external_metrics["execution_hash"] = execution_hash
            external_metrics["total_synthesis_triggered"] = (
                self.total_synthesis_triggered
            )
            if self.theory_lineage:
                external_metrics.update(
                    {
                        "active_theories": self.theory_lineage.active_count(),
                        "contradicted_theories": self.theory_lineage.contradicted_count(),
                        "retired_theories": self.theory_lineage.retired_count(),
                        "revived_theories": self.theory_lineage.revived_count(),
                        "avg_retirement_age": self.theory_lineage.average_retirement_age(),
                        "avg_revival_latency": self.theory_lineage.average_revival_latency(),
                        "longest_surviving": self.theory_lineage.longest_surviving_theory(),
                        "mutation_count": self.theory_lineage.total_mutation_count(),
                        "family_analytics": self.theory_lineage.family_analytics(),
                    }
                )

            if self.observer:
                # derive aggregate observer metrics
                external_metrics.update(
                    {
                        "avg_confidence": (
                            float(
                                mean([m.avg_confidence for m in self.observer.metrics])
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "confidence_volatility": (
                            float(
                                mean(
                                    [
                                        m.confidence_volatility
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "grounded_reflection": (
                            float(
                                mean(
                                    [
                                        m.grounded_reflection_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "meta_commentary": (
                            float(
                                mean(
                                    [
                                        m.meta_commentary_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "narrative_inflation": (
                            float(
                                mean(
                                    [
                                        m.inflation_relapse_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                    }
                )

            # regime memory metrics if available on executor
            try:
                external_metrics["regime_recall_hit_rate"] = (
                    self.regime_memory.recall_hit_rate() if self.regime_memory else 0.0
                )
                external_metrics["memory_retrieval_usefulness"] = (
                    self.regime_memory.retrieval_usefulness(
                        self._regime_matches_by_step
                    )
                    if self.regime_memory
                    else 0.0
                )
            except Exception:
                external_metrics["regime_recall_hit_rate"] = 0.0
                external_metrics["memory_retrieval_usefulness"] = 0.0

            # Output paths
            external_metrics["outputs"] = {
                "prediction_csv": str(self.base_output_dir / "prediction_analysis.csv"),
                **(
                    {
                        "charts_dir": str(self.output_dir),
                        "cross_asset_summary": str(
                            self.base_output_dir / "cross_asset_failure_summary.json"
                        ),
                    }
                    if self.generate_visualizations
                    else {}
                ),
            }

            # Attach to analysis engine for richer printing
            self.replay_analysis_engine.external_metrics = external_metrics
        except Exception:
            pass

        self.replay_analysis_engine.export_prediction_analysis_csv(
            self.base_output_dir / "prediction_analysis.csv",
            verbose=self.debug_output_enabled,
        )

        # v1.6 Visualization Layer Integration
        if self.generate_visualizations:
            try:
                from market.replay.visualization import (
                    generate_visualizations,
                )

                generate_visualizations(
                    analysis=self.replay_analysis_engine.analyze(),
                    logs=self.capital_simulator.get_daily_logs(),
                    tp_history=self.replay_analysis_engine.transition_pressure_history,
                    output_dir=self.output_dir,
                )
                self._log(f"Generated:")
                self._log(f"  - {self.output_dir / 'actual_vs_predicted_curve.png'}")
                self._log(f"  - {self.output_dir / 'policy_capital_comparison.png'}")
                self._log(f"  - {self.output_dir / 'policy_trade_frequency.png'}")
                self._log(f"  - {self.output_dir / 'confidence_calibration.png'}")
                self._log(f"  - {self.output_dir / 'transition_pressure_timeline.png'}")
                self._log(f"  - {self.output_dir / 'combined_dashboard.png'}")
            except Exception as e:
                self._log(f"WARNING: Optional Visualization generation failed: {e}")

        if self.compare_secondary and self.engine.market_name == "RELIANCE":
            nifty_path = (
                Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
            )
            if nifty_path.exists():
                self._log("\nCross-asset comparison: detected NIFTY dataset.")
                self._log("Starting NIFTY replay for cross-asset comparison...")
                try:
                    comparison_executor = self.__class__(
                        max_days=self.max_days,
                        quiet=True,
                        dataset_path=str(nifty_path),
                        market_name="NIFTY 50",
                        compare_secondary=False,
                        generate_visualizations=self.generate_visualizations,
                    )
                    comparison_executor.execute(emit_summary=False)

                    if self.generate_visualizations:
                        from market.replay.visualization import (
                            generate_cross_asset_visualizations,
                        )

                        generate_cross_asset_visualizations(
                            base_output_dir=self.base_output_dir,
                            primary_analysis=self.replay_analysis_engine.analyze(),
                            secondary_analysis=comparison_executor.replay_analysis_engine.analyze(),
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'reliance_vs_nifty_comparison.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'prediction_failure_heatmap.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'cross_asset_divergence_timeline.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'cross_asset_failure_summary.json'}"
                        )
                except Exception as e:
                    self._log(f"WARNING: Cross-asset comparison failed: {e}")

        if emit_summary:
            try:
                # refresh outputs path in external metrics (cross-asset JSON may now exist)
                if hasattr(self.replay_analysis_engine, "external_metrics"):
                    self.replay_analysis_engine.external_metrics["outputs"] = {
                        "prediction_csv": str(
                            self.base_output_dir / "prediction_analysis.csv"
                        ),
                        **(
                            {
                                "charts_dir": str(self.output_dir),
                                "cross_asset_summary": str(
                                    self.base_output_dir
                                    / "cross_asset_failure_summary.json"
                                ),
                            }
                            if self.generate_visualizations
                            else {}
                        ),
                    }
                self.replay_analysis_engine.print_summary()
            except Exception:
                pass

        self._log(f"\n✓ Replay complete")
        if self.debug_output_enabled:
            self._log(f"  Execution hash: {execution_hash[:16]}...")
            self._log(f"  Total synthesis triggered: {self.total_synthesis_triggered}")

        # Console summary (concise)
        try:
            total_steps = len(self.engine)
            active_theories = (
                self.theory_lineage.active_count() if self.theory_lineage else 0
            )
            new_theories = (
                sum(m.new_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            mutated_theories = (
                sum(m.mutated_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            contradicted_theories = (
                self.theory_lineage.contradicted_count() if self.theory_lineage else 0
            )
            retired_theories = (
                sum(m.retired_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            revived_theories = (
                sum(m.revived_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            longest_survival = (
                self.theory_lineage.longest_surviving_theory()
                if self.theory_lineage
                else 0
            )
            avg_retirement_age = (
                self.theory_lineage.average_retirement_age()
                if self.theory_lineage
                else 0.0
            )
            avg_revival_latency = (
                self.theory_lineage.average_revival_latency()
                if self.theory_lineage
                else 0.0
            )
            avg_contradiction_half_life = (
                float(mean([m.contradiction_half_life for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            median_contradiction_half_life = (
                float(
                    mean(
                        [
                            m.median_contradiction_half_life
                            for m in self.observer.metrics
                        ]
                    )
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            avg_contradiction_severity = (
                float(
                    mean([m.avg_contradiction_severity for m in self.observer.metrics])
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            oldest_unresolved = (
                max(
                    (m.oldest_unresolved_contradiction for m in self.observer.metrics),
                    default=0,
                )
                if self.observer
                else 0
            )
            avg_confidence = (
                float(mean([m.avg_confidence for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            confidence_volatility = (
                float(mean([m.confidence_volatility for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            grounded_reflection = (
                float(
                    mean([m.grounded_reflection_score for m in self.observer.metrics])
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            meta_commentary = (
                float(mean([m.meta_commentary_score for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            narrative_inflation = (
                float(mean([m.inflation_relapse_score for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            top_recurring = (
                self.theory_lineage.top_recurring_theory()
                if self.theory_lineage
                else None
            )
            family_analytics = (
                self.theory_lineage.family_analytics() if self.theory_lineage else {}
            )
            epistemic_aggregate = (
                self.epistemic_scoring.aggregate(self.theory_lineage.theories.values())
                if self.epistemic_scoring and self.theory_lineage
                else {"avg_theory_usefulness": 0.0}
            )
            regime_recall_hit_rate = (
                self.regime_memory.recall_hit_rate() if self.regime_memory else 0.0
            )
            memory_retrieval_usefulness = (
                self.regime_memory.retrieval_usefulness(self._regime_matches_by_step)
                if self.regime_memory
                else 0.0
            )

            # Legacy concise replay summary removed - replaced by
            # ReplayAnalysisEngine.print_summary() which now emits
            # the structured v2.3+ summary.
        except Exception:
            pass
