"""
Step Logging Module for Replay Engine.

Handles streamlined single-line day logging, daily snapshot JSON persistence,
and cognitive decision trace collection / Knowledge Graph linking.
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("replay_engine.step_logging")


def print_day_log(
    executor: Any,
    day_idx: int,
    date_str: str,
    market_obs: Any,
    theory: Any,
    reflection: Any,
    confidence_state: Any,
    contradiction_result: dict,
    horizon_view: Any,
    regime_matches: List[Any],
    theory_usefulness: dict,
    transition_pressure: Any,
    prediction_probe: Any,
    prior_prediction_result: Any,
    active_experience: Any = None,
    lesson_info: tuple = None,
    intelligence: dict = None,
):
    """Prints a clean, single-line log summarizing the cognitive state for the day."""
    if executor.quiet:
        return

    # Theory action label
    action_label = "REINFORCE"
    if intelligence:
        if intelligence.get("created"):
            action_label = "GENERATE"
        elif intelligence.get("mutated"):
            action_label = "MUTATE"
        elif intelligence.get("merged"):
            action_label = "MERGE"
        elif intelligence.get("revived"):
            action_label = "REVIVE"
        elif intelligence.get("retired"):
            action_label = "RETIRE"

    lineage_id = (
        intelligence.get("lineage_id", "N/A") if intelligence else "N/A"
    )

    pred_dir = prediction_probe.direction.value if prediction_probe else "uncertain"
    pred_conf = prediction_probe.confidence if prediction_probe else 0.0
    pred_conf_pct = f"{pred_conf*100:3.0f}%"

    trust_score = (
        confidence_state.empirical_confidence if confidence_state else 0.5
    )
    contra_score = (
        float(contradiction_result.get("score", 0.0))
        if contradiction_result
        else 0.0
    )
    contra_count = (
        len(contradiction_result.get("indicators", []))
        if contradiction_result
        else 0
    )

    memory_match = "None"
    if regime_matches and regime_matches[0].similarity > 0.6:
        match_date = getattr(regime_matches[0], "date", "unknown")
        sim_pct = int(regime_matches[0].similarity * 100)
        memory_match = f"{match_date} ({sim_pct}%)"

    failures_str = ""
    if getattr(executor, "_prior_attribution", None) and hasattr(
        executor._prior_attribution, "components_failed"
    ):
        failed = executor._prior_attribution.components_failed
        if failed:
            failures_str = f" | Failures: {','.join(failed)}"

    lesson_str = ""
    if lesson_info and lesson_info[0]:
        lesson_obj, status_reason, _ = lesson_info
        lesson_str = f" | Lesson: {status_reason} ({lesson_obj.status.value})"

    print(
        f"[Day {day_idx:3d} | {date_str}] "
        f"Theory: {action_label:<7} ({lineage_id[:8]}) | "
        f"Bias: {pred_dir:<11}{pred_conf_pct} | "
        f"Trust: {trust_score:.2f} | "
        f"Contra: {contra_score:.2f} (n={contra_count}) | "
        f"Memory: {memory_match}"
        f"{failures_str}{lesson_str}"
    )


def save_step_snapshot(executor: Any, day_idx: int, date_str: str, snapshot_data: dict):
    """Saves daily snapshot JSON files to both run snapshot and output directories."""
    try:
        run_snap_path = (
            executor.run_dir / "snapshots" / f"day_{day_idx:04d}_{date_str}.json"
        )
        with open(run_snap_path, "w") as f:
            json.dump(
                snapshot_data, f, indent=2, default=str
            )

        out_snap_path = (
            executor.base_output_dir
            / "snapshots"
            / f"day_{day_idx:04d}_{date_str}.json"
        )
        with open(out_snap_path, "w") as f:
            json.dump(
                snapshot_data, f, indent=2, default=str
            )
    except Exception as e:
        logger.warning(f"Failed to write snapshot for day {day_idx}: {e}")


def update_knowledge_graph_trace(
    executor: Any,
    day_idx: int,
    date_str: str,
    market_obs: Any,
    theory: Any,
    regime_subtype: str,
    principles_accepted: List[str],
    latest_wm: Any,
    prior_prediction_result: Any,
    reflection: Any,
    audit_created: bool,
    audit_mutated: bool,
):
    """Records Cognitive Decision Trace Collection and links nodes in Knowledge Graph."""
    if not hasattr(executor, "knowledge_graph") or not executor.knowledge_graph:
        return

    try:
        obs_id = f"obs_{date_str}"
        theory_id = f"theory_{theory.id}" if theory else f"theory_{date_str}"
        pred_id = f"pred_{date_str}"
        outcome_id = f"outcome_{date_str}"
        reflection_id = f"refl_{date_str}"
        wm_id = f"wm_{date_str}"

        executor.knowledge_graph.add_node(
            obs_id,
            "Observation",
            f"Obs: {market_obs.candle_type}",
            {
                "regime_subtype": regime_subtype,
                "delivery_pct": getattr(market_obs, "delivery_pct", 0.0),
            },
        )
        executor.knowledge_graph.add_node(
            theory_id,
            "Theory",
            theory.summary,
            {"lineage_id": getattr(theory, "lineage_id", "N/A")},
        )
        executor.knowledge_graph.add_node(
            wm_id,
            "WorldModel",
            (
                latest_wm.narrative_summary
                if latest_wm
                else "Baseline World Model"
            ),
            {
                "stability": getattr(latest_wm, "stability", "Emerging"),
                "confidence": getattr(latest_wm, "confidence", 0.5),
            },
        )
        executor.knowledge_graph.add_node(
            pred_id,
            "Prediction",
            f"Pred: {getattr(executor._prior_prediction, 'direction', 'uncertain')}",
            {
                "confidence": getattr(executor._prior_prediction, "confidence", 0.5),
            },
        )

        if prior_prediction_result:
            executor.knowledge_graph.add_node(
                outcome_id,
                "Outcome",
                f"Actual: {prior_prediction_result.actual_direction}",
                {
                    "direction_score": prior_prediction_result.direction_score,
                    "invalidation_triggered": prior_prediction_result.invalidation_triggered,
                },
            )

        if reflection:
            executor.knowledge_graph.add_node(
                reflection_id,
                "Reflection",
                reflection.reflection_summary[:100],
                {"reflection_id": str(getattr(reflection, "id", ""))},
            )

        executor.knowledge_graph.add_edge(obs_id, theory_id, "TRIGGERS")
        executor.knowledge_graph.add_edge(theory_id, pred_id, "GENERATES")

        for pid in principles_accepted:
            p_obj = executor.knowledge_repository.get_principle(pid)
            if p_obj:
                executor.knowledge_graph.add_node(
                    pid,
                    "Principle",
                    p_obj.statement,
                    {
                        "status": getattr(
                            p_obj.status, "value", p_obj.status
                        ),
                        "trust_score": p_obj.trust_score,
                    },
                )
                executor.knowledge_graph.add_edge(
                    theory_id, pid, "SUPPORTED_BY"
                )
                executor.knowledge_graph.add_edge(pid, wm_id, "INFLUENCES")

        executor.knowledge_graph.add_edge(wm_id, pred_id, "CONSTRAINS")
        if prior_prediction_result:
            executor.knowledge_graph.add_edge(pred_id, outcome_id, "SCORES")
        if reflection and prior_prediction_result:
            executor.knowledge_graph.add_edge(
                outcome_id, reflection_id, "CRITIQUES"
            )
            executor.knowledge_graph.add_edge(
                reflection_id, theory_id, "REVISES"
            )

    except Exception as e:
        logger.warning(f"Trace/Graph collection failed for day {date_str}: {e}")
