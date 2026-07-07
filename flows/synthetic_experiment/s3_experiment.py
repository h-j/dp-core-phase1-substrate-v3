import json
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple


class S3Environment:
    """
    Standalone environment generator and evaluation harness for Experiment S3: Novel Proposition Discovery.
    """

    @staticmethod
    def generate_world(family: int, seed: int) -> Dict[str, Any]:
        """
        Generates a synthetic world instance for S3.
        Families:
        1: Missing Interaction between two known variables (F_0 and F_1)
        2: Conditional Boundary not represented (F_0 is active only when F_1 == 0)
        3: Temporal Relationship requiring lag composition (outcome at t depends on F_0 at t-1)
        4: Heterogeneous Subpopulation requiring a novel scope (F_0 works for Y0 when F_2 == 1, works for Y1 when F_2 == 0)
        5: Null Worlds containing no discoverable hidden relationship
        """
        random.seed(seed)

        num_features = 10
        experiences = []

        trigger_idx = 0
        partition_idx = 1
        subpop_idx = 2

        # Generate 1000 experiences
        for t in range(1, 1001):
            feats = {}
            for i in range(num_features):
                feats[f"F_{i}"] = 1 if random.random() < 0.5 else 0

            # Outcome generation based on family and time
            p_y0 = 0.50

            if family == 1:
                # Missing Interaction: target occurs when F_0 == 1 AND F_1 == 1
                if feats[f"F_{trigger_idx}"] == 1 and feats[f"F_{partition_idx}"] == 1:
                    p_y0 = 0.85
                else:
                    p_y0 = 0.50
            elif family == 2:
                # Conditional Boundary: F_0 == 1 but ONLY WHEN F_1 == 0
                if feats[f"F_{trigger_idx}"] == 1:
                    if feats[f"F_{partition_idx}"] == 0:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.50
                else:
                    p_y0 = 0.50
            elif family == 3:
                # Temporal Lag: outcome at t depends on F_0 at t-1.
                # Since we need to access t-1, we check history.
                if t > 1:
                    prev_feats = experiences[-1]["features"]
                    if prev_feats[f"F_{trigger_idx}"] == 1:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.50
                else:
                    p_y0 = 0.50
            elif family == 4:
                # Heterogeneous Subpopulation:
                # If F_2 == 1, F_0 == 1 expectations is Y0 (0.85)
                # If F_2 == 0, F_0 == 1 expectations is Y1 (0.85) -> which means Y0 is 0.15
                if feats[f"F_{trigger_idx}"] == 1:
                    if feats[f"F_{subpop_idx}"] == 1:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.15
                else:
                    p_y0 = 0.50
            elif family == 5:
                # Null Worlds: no signal
                p_y0 = 0.50

            outcome = "Y0" if random.random() < p_y0 else "Y1"
            experiences.append({"day": t, "features": feats, "outcome": outcome})

        # Compile anonymization mappings
        feature_indices = list(range(num_features))
        random.shuffle(feature_indices)
        feature_map = {}  # F_i -> VAR_j
        reverse_feature_map = {}
        for i, idx in enumerate(feature_indices):
            anon_name = f"VAR_{idx}"
            feature_map[f"F_{i}"] = anon_name
            reverse_feature_map[anon_name] = f"F_{i}"

        outcomes = ["VAL_A", "VAL_B"]
        random.shuffle(outcomes)
        outcome_map = {"Y0": outcomes[0], "Y1": outcomes[1]}
        reverse_outcome_map = {outcomes[0]: "Y0", outcomes[1]: "Y1"}

        # Active belief bank initial definition
        active_beliefs = []
        if family in [1, 2, 4]:
            # Initial belief: Trigger F_0 == 1 expects Y0, empty scope
            active_beliefs.append(
                {
                    "trigger_var": feature_map[f"F_{trigger_idx}"],
                    "target_val": outcome_map["Y0"],
                    "scope": {},
                }
            )

        # Ex-ante Ground Truth
        ex_ante_truth = []
        if family == 1:
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
                    },
                    "scope": [
                        {
                            "field": feature_map[f"F_{partition_idx}"],
                            "operator": "==",
                            "value": 1,
                        }
                    ],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y0"],
                    },
                }
            )
        elif family == 2:
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
                    },
                    "scope": [
                        {
                            "field": feature_map[f"F_{partition_idx}"],
                            "operator": "==",
                            "value": 0,
                        }
                    ],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y0"],
                    },
                }
            )
        elif family == 3:
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 1,
                    },
                    "scope": [],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y0"],
                    },
                }
            )
        elif family == 4:
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
                    },
                    "scope": [
                        {
                            "field": feature_map[f"F_{subpop_idx}"],
                            "operator": "==",
                            "value": 1,
                        }
                    ],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y0"],
                    },
                }
            )
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
                    },
                    "scope": [
                        {
                            "field": feature_map[f"F_{subpop_idx}"],
                            "operator": "==",
                            "value": 0,
                        }
                    ],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y1"],
                    },
                }
            )

        # Map experiences
        anon_experiences = []
        for exp in experiences:
            anon_feats = {}
            for k, v in exp["features"].items():
                anon_feats[feature_map[k]] = v
            anon_experiences.append(
                {
                    "day": exp["day"],
                    "features": anon_feats,
                    "outcome": outcome_map[exp["outcome"]],
                }
            )

        formation_exps = anon_experiences[:500]
        prospective_exps = anon_experiences[500:]

        return {
            "family": family,
            "seed": seed,
            "experiences": anon_experiences,
            "formation_experiences": formation_exps,
            "prospective_experiences": prospective_exps,
            "parent_belief": active_beliefs[0] if active_beliefs else None,
            "active_beliefs": active_beliefs,
            "ex_ante_truth": ex_ante_truth,
            "feature_map": feature_map,
            "reverse_feature_map": reverse_feature_map,
            "outcome_map": outcome_map,
            "reverse_outcome_map": reverse_outcome_map,
        }

    @staticmethod
    def compute_residual_evidence(
        experiences: List[Dict[str, Any]],
        active_beliefs: List[Dict[str, Any]],
        feature_map: Dict[str, str],
        outcome_map: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Computes structured Residual Evidence Object.
        Analyzes successes, failures, and lag correlations.
        """
        num_features = 10
        all_features = [f"VAR_{i}" for i in range(num_features)]

        def check_belief_active(b: Dict[str, Any], exp: Dict[str, Any]) -> bool:
            if exp["features"].get(b["trigger_var"]) != 1:
                return False
            for k, v in b["scope"].items():
                if exp["features"].get(k) != v:
                    return False
            return True

        # Unexplained Occurrences
        unexplained = {"VAL_A": [], "VAL_B": []}
        active_failures = []
        active_successes = []

        for exp in experiences:
            # Check if matches any active belief trigger
            matched_belief = None
            for b in active_beliefs:
                if check_belief_active(b, exp):
                    matched_belief = b
                    break

            if matched_belief is not None:
                if exp["outcome"] == matched_belief["target_val"]:
                    active_successes.append((matched_belief, exp))
                else:
                    active_failures.append((matched_belief, exp))
            else:
                if exp["outcome"] == "VAL_A":
                    unexplained["VAL_A"].append(exp)
                elif exp["outcome"] == "VAL_B":
                    unexplained["VAL_B"].append(exp)

        # 1. Unexplained Occurrences Associations
        unexplained_stats = {}
        for val in ["VAL_A", "VAL_B"]:
            val_exps = unexplained[val]
            n_unexplained = len(val_exps)
            unexplained_stats[val] = {}

            for f in all_features:
                p_base = sum(1 for e in experiences if e["features"].get(f) == 1) / len(
                    experiences
                )
                p_unexp = (
                    sum(1 for e in val_exps if e["features"].get(f) == 1)
                    / n_unexplained
                    if n_unexplained > 0
                    else p_base
                )
                unexplained_stats[val][f] = round(p_unexp - p_base, 4)

        # 2. Active Belief Failure Associations
        failure_stats = []
        for idx, b in enumerate(active_beliefs):
            b_fails = [e for mb, e in active_failures if mb == b]
            b_succs = [e for mb, e in active_successes if mb == b]
            n_fails = len(b_fails)
            n_succs = len(b_succs)

            stats = {
                "belief_index": idx,
                "trigger_var": b["trigger_var"],
                "target_val": b["target_val"],
                "features": {},
            }
            for f in all_features:
                if f == b["trigger_var"]:
                    continue
                p_fail = (
                    sum(1 for e in b_fails if e["features"].get(f) == 1) / n_fails
                    if n_fails > 0
                    else 0.0
                )
                p_succ = (
                    sum(1 for e in b_succs if e["features"].get(f) == 1) / n_succs
                    if n_succs > 0
                    else 0.0
                )
                stats["features"][f] = {
                    "p_fail": round(p_fail, 4),
                    "p_succ": round(p_succ, 4),
                    "delta": round(p_fail - p_succ, 4),
                }
            failure_stats.append(stats)

        # 3. Temporal Lag-1 Associations
        lag_stats = {}
        for val in ["VAL_A", "VAL_B"]:
            lag_stats[val] = {}
            for f in all_features:
                # Compute outcome[t] == val conditional on f[t-1] == 1 vs f[t-1] == 0
                n_act = 0
                n_act_target = 0
                n_ctrl = 0
                n_ctrl_target = 0

                for t in range(1, len(experiences)):
                    prev_exp = experiences[t - 1]
                    curr_exp = experiences[t]
                    if prev_exp["features"].get(f) == 1:
                        n_act += 1
                        if curr_exp["outcome"] == val:
                            n_act_target += 1
                    else:
                        n_ctrl += 1
                        if curr_exp["outcome"] == val:
                            n_ctrl_target += 1

                p_cond = (n_act_target / n_act) if n_act > 0 else 0.5
                p_control = (n_ctrl_target / n_ctrl) if n_ctrl > 0 else 0.5
                lag_stats[val][f] = round(p_cond - p_control, 4)

        return {
            "unexplained_associations": unexplained_stats,
            "belief_failure_associations": failure_stats,
            "temporal_lag_associations": lag_stats,
        }

    @staticmethod
    def validate_proposition(
        prop: Dict[str, Any],
        active_beliefs: List[Dict[str, Any]],
        all_features: List[str],
    ) -> bool:
        """
        Validates proposition syntax, vocabulary, duplication, and correctness constraints.
        """
        try:
            if not isinstance(prop, dict):
                return False
            if "trigger" not in prop or "scope" not in prop or "target" not in prop:
                return False

            trigger = prop["trigger"]
            scope = prop["scope"]
            target = prop["target"]

            # Validate Trigger
            if not isinstance(trigger, dict):
                return False
            if trigger.get("field") not in all_features:
                return False
            if trigger.get("operator") != "==":
                return False
            if trigger.get("value") not in [1, 0]:
                return False
            if trigger.get("lag") not in [0, 1]:
                return False

            # Validate Scope
            if not isinstance(scope, list):
                return False
            if len(scope) > 1:
                return False  # Bounded complexity

            scope_fields = set()
            for s in scope:
                if not isinstance(s, dict):
                    return False
                if s.get("field") not in all_features:
                    return False
                if s.get("operator") != "==":
                    return False
                if s.get("value") not in [1, 0]:
                    return False
                if s.get("field") == trigger["field"]:
                    return False  # No tautology/redundancy
                scope_fields.add(s.get("field"))

            if len(scope_fields) != len(scope):
                return False  # Duplicate fields in scope

            # Validate Target
            if not isinstance(target, dict):
                return False
            if target.get("field") != "outcome":
                return False
            if target.get("operator") != "==":
                return False
            if target.get("value") not in ["VAL_A", "VAL_B"]:
                return False

            # Validate semantic duplication of active beliefs
            for b in active_beliefs:
                # Convert active belief scope to list of dicts for comparison
                b_scope_list = [
                    {"field": k, "operator": "==", "value": v}
                    for k, v in b["scope"].items()
                ]
                # Check match
                if (
                    b["trigger_var"] == trigger["field"]
                    and trigger["lag"] == 0
                    and b["target_val"] == target["value"]
                ):
                    # compare scopes
                    s1 = sorted([s["field"] for s in b_scope_list])
                    s2 = sorted([s["field"] for s in scope])
                    if s1 == s2:
                        return False

            return True
        except Exception:
            return False

    @staticmethod
    def evaluate_propositions(
        propositions: List[Dict[str, Any]], experiences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates a set of discovered propositions prospectively.
        Computes Raw Prospective Utility, Complexity Score, and Complexity Adjusted Utility.
        """
        if not propositions:
            return {
                "raw_utility": 0.0,
                "complexity_score": 0.0,
                "adjusted_utility": 0.0,
                "propositions_eval": [],
            }

        raw_utility = 0.0
        complexity_score = 0.0
        prop_evals = []

        for prop in propositions:
            trigger = prop["trigger"]
            scope = prop["scope"]
            target = prop["target"]

            n_act = 0
            n_act_target = 0
            n_ctrl = 0
            n_ctrl_target = 0

            start_t = 2 if trigger["lag"] == 1 else 1

            for t in range(start_t, len(experiences) + 1):
                exp = experiences[t - 1]

                # Scope check
                scope_ok = True
                for s in scope:
                    if exp["features"].get(s["field"]) != s["value"]:
                        scope_ok = False
                        break

                if not scope_ok:
                    continue

                # Trigger evaluation
                if trigger["lag"] == 1:
                    prev_exp = experiences[t - 2]
                    trigger_active = (
                        prev_exp["features"].get(trigger["field"]) == trigger["value"]
                    )
                else:
                    trigger_active = (
                        exp["features"].get(trigger["field"]) == trigger["value"]
                    )

                if trigger_active:
                    n_act += 1
                    if exp["outcome"] == target["value"]:
                        n_act_target += 1
                else:
                    n_ctrl += 1
                    if exp["outcome"] == target["value"]:
                        n_ctrl_target += 1

            p_cond = (n_act_target / n_act) if n_act > 0 else 0.5
            p_control = (n_ctrl_target / n_ctrl) if n_ctrl > 0 else 0.5
            lift = p_cond - p_control
            utility = n_act * lift

            prop_complexity = 1.0 + len(scope) + (1.0 if trigger["lag"] == 1 else 0.0)
            adjusted_util = utility - 5.0 * prop_complexity

            raw_utility += utility
            complexity_score += prop_complexity

            prop_evals.append(
                {
                    "proposition": prop,
                    "n_act": n_act,
                    "lift": round(lift, 4),
                    "utility": round(utility, 4),
                    "complexity": prop_complexity,
                    "adjusted_utility": round(adjusted_util, 4),
                }
            )

        adjusted_utility = raw_utility - 5.0 * complexity_score

        return {
            "raw_utility": round(raw_utility, 4),
            "complexity_score": round(complexity_score, 4),
            "adjusted_utility": round(adjusted_utility, 4),
            "propositions_eval": prop_evals,
        }


def format_s3_agent_a_prompt(
    active_beliefs: List[Dict[str, Any]], formation_experiences: List[Dict[str, Any]]
) -> str:
    """
    Formats the raw experience log prompt for Agent A (symmetric, anonymized).
    """
    # Active beliefs description
    beliefs_str = ""
    if active_beliefs:
        for idx, b in enumerate(active_beliefs):
            scope_str = ", ".join(f"{k} == {v}" for k, v in b["scope"].items())
            scope_desc = f" WHEN {scope_str}" if scope_str else ""
            beliefs_str += f"- Active Belief {idx}: trigger {b['trigger_var']} == 1 EXPECT outcome == {b['target_val']}{scope_desc}\n"
    else:
        beliefs_str = "None (empty belief bank)\n"

    # Raw experience logs table (first 50 days to prevent context blowup)
    all_keys = sorted(list(formation_experiences[0]["features"].keys()))
    header = "| Day | Outcome | " + " | ".join(all_keys) + " |"
    divider = "| --- | --- | " + " | ".join(["---"] * len(all_keys)) + " |"
    rows = [header, divider]
    for exp in formation_experiences[:50]:
        feats_val = [str(exp["features"][k]) for k in all_keys]
        rows.append(
            f"| {exp['day']} | {exp['outcome']} | " + " | ".join(feats_val) + " |"
        )
    table_str = "\n".join(rows)

    operations = [
        "- Propose at most 3 new propositions.",
        "- Propositions must use anonymized fields VAR_0..VAR_9 and target outcomes VAL_A/VAL_B.",
        "- Do not duplicate existing active beliefs.",
        "- Trigger lag can be 0 (same day) or 1 (outcome depends on previous day trigger).",
    ]
    random.shuffle(operations)
    ops_str = "\n".join(operations)

    return f"""You are a scientific cognitive agent.
Your task is to discover new predictive propositions from a chronological experience log.

Initial Active Beliefs:
{beliefs_str}

Discovery Constraints:
{ops_str}

Chronological Log (first 50 days):
{table_str}

Respond ONLY with a JSON list of at most 3 propositions in the following exact format:
[
  {{
    "trigger": {{"field": "VAR_X", "operator": "==", "value": 1, "lag": 0 | 1}},
    "scope": [
      {{"field": "VAR_Y", "operator": "==", "value": 1 | 0}}
    ],
    "target": {{"field": "outcome", "operator": "==", "value": "VAL_A" | "VAL_B"}}
  }}
]
"""


def format_s3_agent_c_prompt(
    active_beliefs: List[Dict[str, Any]], residual_evidence: Dict[str, Any]
) -> str:
    """
    Formats the structured Residual Evidence Object prompt for Agent C (symmetric, anonymized).
    """
    beliefs_str = ""
    if active_beliefs:
        for idx, b in enumerate(active_beliefs):
            scope_str = ", ".join(f"{k} == {v}" for k, v in b["scope"].items())
            scope_desc = f" WHEN {scope_str}" if scope_str else ""
            beliefs_str += f"- Active Belief {idx}: trigger {b['trigger_var']} == 1 EXPECT outcome == {b['target_val']}{scope_desc}\n"
    else:
        beliefs_str = "None (empty belief bank)\n"

    # Format unexplained occurrence associations
    unexp_str = ""
    for val in ["VAL_A", "VAL_B"]:
        feats_list = sorted(
            list(residual_evidence["unexplained_associations"][val].items()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        feats_desc = ", ".join(f"{f}: {lift:+.4f}" for f, lift in feats_list)
        unexp_str += (
            f"- Unexplained {val} associations (lift over baseline): {feats_desc}\n"
        )

    # Format active failures
    fails_str = ""
    if residual_evidence["belief_failure_associations"]:
        for f_stat in residual_evidence["belief_failure_associations"]:
            feats_list = sorted(
                list(f_stat["features"].items()),
                key=lambda x: abs(x[1]["delta"]),
                reverse=True,
            )
            feats_desc = ", ".join(
                f"{feat}: (fail {s['p_fail']:.2f} vs succ {s['p_succ']:.2f}, delta {s['delta']:+.2f})"
                for feat, s in feats_list[:3]
            )
            fails_str += f"- Active Belief {f_stat['belief_index']} failures associated with: {feats_desc}\n"
    else:
        fails_str = "None (no active beliefs to fail)\n"

    # Format temporal lag
    lag_str = ""
    for val in ["VAL_A", "VAL_B"]:
        feats_list = sorted(
            list(residual_evidence["temporal_lag_associations"][val].items()),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        feats_desc = ", ".join(f"{f}: {lift:+.4f}" for f, lift in feats_list)
        lag_str += (
            f"- Lag-1 {val} associations (previous day trigger lift): {feats_desc}\n"
        )

    operations = [
        "- Propose at most 3 new propositions.",
        "- Propositions must use anonymized fields VAR_0..VAR_9 and target outcomes VAL_A/VAL_B.",
        "- Do not duplicate existing active beliefs.",
        "- Trigger lag can be 0 (same day) or 1 (outcome depends on previous day trigger).",
    ]
    random.shuffle(operations)
    ops_str = "\n".join(operations)

    return f"""You are a scientific cognitive agent.
Your task is to discover new predictive propositions using a compiled Residual Evidence Object.

Initial Active Beliefs:
{beliefs_str}

Residual Evidence Object:
1. Unexplained Outcomes Associations:
{unexp_str}

2. Active Belief Failure/Success Associations:
{fails_str}

3. Temporal Lag-1 Associations:
{lag_str}

Discovery Constraints:
{ops_str}

Respond ONLY with a JSON list of at most 3 propositions in the following exact format:
[
  {{
    "trigger": {{"field": "VAR_X", "operator": "==", "value": 1, "lag": 0 | 1}},
    "scope": [
      {{"field": "VAR_Y", "operator": "==", "value": 1 | 0}}
    ],
    "target": {{"field": "outcome", "operator": "==", "value": "VAL_A" | "VAL_B"}}
  }}
]
"""
