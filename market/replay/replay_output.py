"""Replay snapshot and console output helpers."""

import json


class ReplayOutputMixin:
    # _format_historical_context and _format_regime_context moved to CognitionPipeline

    def _save_snapshot(self, day_idx: int, date_str: str, snapshot_data: dict):
        """Save replay snapshot to disk."""
        prediction = snapshot_data.get("prediction")
        prior_prediction_result = snapshot_data.get("prior_prediction_result")
        snapshot = {
            "day_index": day_idx,
            "date": date_str,
            "observation_text": snapshot_data["observation"].observation_text, # Keep for direct access
            "theory_summary": snapshot_data["theory"].summary,  # Legacy summary
            "theory_summary_structured": snapshot_data["theory"].summary_structured.model_dump() if snapshot_data["theory"].summary_structured else None,  # Canonical access
            "confidence_state": snapshot_data["confidence"].model_dump(), # Use model_dump for Pydantic objects
            "contradiction_score": snapshot_data["contradiction"].get("score", 0),
            "reflection_summary": snapshot_data["reflection"].reflection_summary,
            "epistemic_quality": snapshot_data.get("epistemic_quality", {}),
            "horizon": snapshot_data.get("horizon", {}),
            "regime_signature": snapshot_data.get("regime_signature", {}),
            "regime_matches": snapshot_data.get("regime_matches", []),
            "theory_usefulness": snapshot_data.get("theory_usefulness", {}),
            "candle_type": snapshot_data["observation"].candle_type,
            "participation_strength": snapshot_data["observation"].participation_strength,
            "participation_confirmation": snapshot_data["observation"].participation_confirmation,
            "prediction": prediction.to_dict() if hasattr(prediction, "to_dict") else prediction,
            "prior_prediction_result": (
                prior_prediction_result.to_dict()
                if hasattr(prior_prediction_result, "to_dict")
                else prior_prediction_result
            ),
            # v3.0 Regime Persistence
            "regime_subtype": snapshot_data.get("regime_subtype"),
            "falsifiability_conditions": snapshot_data.get("falsifiability_conditions"),
            "analog_divergence_claim": snapshot_data.get("analog_divergence_claim"),
            "theory_regime_subtype": snapshot_data.get("theory_regime_subtype"),
            "theory_falsifiability_conditions": snapshot_data.get("theory_falsifiability_conditions"),
            "regime_history": snapshot_data.get("regime_history"),
            "dialectical_triggered": snapshot_data.get("dialectical_triggered", False),
            "dialectical_synthesis": snapshot_data.get("dialectical_synthesis"),
        }

        # Attempt to preserve structured theory JSON when available.
        theory_summary_structured = None
        try:
            import json as _json

            raw = snapshot.get("theory_summary", "")
            parsed = _json.loads(raw) if raw else None
            if isinstance(parsed, dict):
                theory_summary_structured = parsed
        except Exception:
            theory_summary_structured = None

        snapshot["theory_summary_structured"] = theory_summary_structured

        import json

        snapshot_file = self.replay_dir / "logs" / f"day_{day_idx:04d}_{date_str}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

    def _print_day_log(
        self,
        day_idx: int,
        date_str: str,
        observation,
        theory,
        reflection,
        confidence,
        contradiction,
        horizon,
        regime_matches,
        theory_usefulness,
        transition_pressure=None,
        prediction=None,
        prior_prediction_result=None,
    ):
        """Print formatted day log."""
        if self.quiet:
            return

        print(f"\n── COGNITIVE TRACE: DAY {day_idx} ── {date_str} ──────────────────")
        
        print(f"Observation:")
        print(f"  {observation.observation_text[:160]}...")

        print(f"Theory:")
        theory_claim = theory.summary_structured.claim if theory.summary_structured else theory.summary
        print(f"  {theory_claim[:120]}...")

        print(f"Contradiction:")
        contra_summary = contradiction.get('summary', 'None') if contradiction.get('indicators') else "None detected structurally"
        print(f"  {contra_summary}")
        tension_summary = getattr(reflection, 'tension_summary', None)
        if contra_summary == "None detected structurally" and tension_summary and tension_summary != "None":
            print(f"Tension: {tension_summary}")

        print(f"Reflection:")
        print(f"  {reflection.reflection_summary[:400]}...")

        print(f"\nLesson:")
        lesson = "None"
        if hasattr(self, 'replay_analysis_engine') and self.replay_analysis_engine and self.replay_analysis_engine.days:
            lesson = self.replay_analysis_engine.days[-1].get("lesson", "None") or "None"
            
        if lesson == "None" or not lesson:
             print("  No lesson extracted yet.")
             print("  Requires contradiction, mutation, synthesis,")
             print("  falsification, revival, or validation outcome.")
        else:
             print(f"  {lesson}")
