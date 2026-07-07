from typing import Any, Dict, List, Set

import pandas as pd

from flows.synthetic_experiment.schemas import (CandidateProposition,
                                                EvidenceObject, Experience)
from flows.synthetic_experiment.synthetic_harness import check_predicate


def get_ground_truth_propositions(
    t_start: int, t_end: int, shift_step: int = 500
) -> Set[str]:
    """
    Returns the set of proposition IDs that represent true planted predictive relations
    during the specified timestep range.
    """
    true_props = {"prop_signal_up"}

    # Decaying relationship is true if evaluation window has some overlap with first half
    if t_start < 750:
        true_props.add("prop_signal_decay_up")

    # Shift relationship: before shift UP is true, after shift DOWN is true
    midpoint = (t_start + t_end) / 2
    if midpoint < shift_step:
        true_props.add("prop_signal_shift_up")
    else:
        true_props.add("prop_signal_shift_down")

    return true_props


def evaluate_selection(
    selected_ids: List[str],
    candidates: List[CandidateProposition],
    evaluation_experiences: List[Experience],
    t_start: int,
    t_end: int,
    shift_step: int = 500,
) -> Dict[str, Any]:
    """
    Calculates Precision at K and Out-of-Sample Realized Lift for selected propositions
    over the evaluation experiences.
    """
    true_props = get_ground_truth_propositions(t_start, t_end, shift_step)

    # 1. Precision at K
    matching = [p for p in selected_ids if p in true_props]
    precision = len(matching) / len(selected_ids) if selected_ids else 0.0

    # 2. Out-of-sample Realized Lift
    candidate_map = {c.proposition_id: c for c in candidates}
    lifts = []

    for prop_id in selected_ids:
        candidate = candidate_map.get(prop_id)
        if not candidate:
            continue

        activations = 0
        supported = 0
        target_value = candidate.expected_effect_predicate.value

        # Calculate unconditional base rate of outcome in the evaluation set matching scope
        scope_count = 0
        target_in_scope_count = 0

        for exp in evaluation_experiences:
            scope_ok = all(check_predicate(exp, p) for p in candidate.scope_predicates)
            if not scope_ok:
                continue

            scope_count += 1
            if exp.outcome == target_value:
                target_in_scope_count += 1

            if check_predicate(exp, candidate.trigger_predicate):
                activations += 1
                if exp.outcome == target_value:
                    supported += 1

        cond_prob = (supported / activations) if activations > 0 else 0.0
        base_rate = (target_in_scope_count / scope_count) if scope_count > 0 else 0.5
        lift = cond_prob - base_rate
        lifts.append(lift)

    mean_lift = sum(lifts) / len(lifts) if lifts else 0.0

    return {
        "precision": precision,
        "mean_lift": mean_lift,
        "selected_ids": selected_ids,
        "true_propositions": list(true_props),
    }


def run_anova_and_stats(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs a one-way ANOVA across the agent conditions for the primary metrics.
    Supports pure Python fallback if scipy is not installed.
    """
    metrics = ["precision", "mean_lift"]
    anova_results = {}

    for metric in metrics:
        groups = {}
        for cond, group in results_df.groupby("condition"):
            groups[cond] = group[metric].tolist()

        if len(groups) < 2:
            continue

        # ANOVA calculations
        grand_total = 0.0
        total_n = 0
        ss_total_sum = 0.0

        for cond, vals in groups.items():
            grand_total += sum(vals)
            total_n += len(vals)
            ss_total_sum += sum(x**2 for x in vals)

        if total_n <= len(groups):
            continue

        grand_mean = grand_total / total_n
        ss_total = ss_total_sum - (grand_total**2 / total_n)

        ss_between = 0.0
        for cond, vals in groups.items():
            ss_between += (sum(vals) ** 2) / len(vals)
        ss_between -= grand_total**2 / total_n

        ss_within = ss_total - ss_between
        df_between = len(groups) - 1
        df_within = total_n - len(groups)

        ms_between = ss_between / df_between if df_between > 0 else 0.0
        ms_within = ss_within / df_within if df_within > 0 else 0.0

        f_stat = ms_between / ms_within if ms_within > 0 else 0.0

        # Try to calculate p-value using scipy
        p_val = None
        try:
            from scipy import stats

            # Use scipy's f distribution survival function
            p_val = float(stats.f.sf(f_stat, df_between, df_within))
        except ImportError:
            # Simple approximation of F survival function for large df
            if f_stat >= 10.0:
                p_val = 1e-16
            elif f_stat >= 3.32:
                p_val = 0.01
            elif f_stat >= 2.37:
                p_val = 0.05
            else:
                p_val = 0.50

        anova_results[metric] = {
            "F_statistic": f_stat,
            "p_value": p_val,
            "df_between": df_between,
            "df_within": df_within,
            "group_means": {
                cond: sum(vals) / len(vals) for cond, vals in groups.items()
            },
        }

    return anova_results
