import json
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple


class S2REnvironment:
    """
    Repaired environment generator and operations harness for S2-R experiment.
    """

    @staticmethod
    def generate_world(family: int, seed: int) -> Dict[str, Any]:
        """
        Generates a synthetic world instance.
        Families:
        1: PRESERVE (persistent support)
        2: REJECT (persistent contradiction/null)
        3: RESTRICT (context-dependent success/failure)
        4: SPLIT (heterogeneous subpopulations)
        5: REVERSE (apparent historical success followed by distribution shift)
        """
        random.seed(seed)

        # 10 binary features
        num_features = 10
        experiences = []

        # We assign F_0 to be the trigger, and F_1 to be the conditioning feature
        trigger_idx = 0
        partition_idx = 1

        # Generate 1000 experiences
        for t in range(1, 1001):
            feats = {}
            for i in range(num_features):
                feats[f"F_{i}"] = 1 if random.random() < 0.5 else 0

            # Outcome generation
            p_y0 = 0.50
            if feats[f"F_{trigger_idx}"] == 1:
                if family == 1:
                    p_y0 = 0.85
                elif family == 2:
                    p_y0 = 0.50
                elif family == 3:
                    if feats[f"F_{partition_idx}"] == 1:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.50
                elif family == 4:
                    if feats[f"F_{partition_idx}"] == 1:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.15
                elif family == 5:
                    if t <= 250:
                        p_y0 = 0.85
                    else:
                        p_y0 = 0.15
            else:
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

        parent_belief = {
            "trigger_var": feature_map[f"F_{trigger_idx}"],
            "target_val": outcome_map["Y0"],
            "scope": {},
        }

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

        # Determine eligible partitions
        eligible_partitions = []
        other_features = [
            feature_map[f"F_{i}"] for i in range(num_features) if i != trigger_idx
        ]

        part_indices = list(range(len(other_features)))
        random.shuffle(part_indices)

        for idx, anon_feat in enumerate(other_features):
            part_id = f"PART_{part_indices[idx]:03d}"
            trigger_anon = parent_belief["trigger_var"]

            # Count activations in both branches
            activations_a = sum(
                1
                for e in formation_exps
                if e["features"][trigger_anon] == 1 and e["features"][anon_feat] == 1
            )
            activations_b = sum(
                1
                for e in formation_exps
                if e["features"][trigger_anon] == 1 and e["features"][anon_feat] == 0
            )

            # Count control experiences in both branches
            controls_a = sum(
                1
                for e in formation_exps
                if e["features"][trigger_anon] == 0 and e["features"][anon_feat] == 1
            )
            controls_b = sum(
                1
                for e in formation_exps
                if e["features"][trigger_anon] == 0 and e["features"][anon_feat] == 0
            )

            # Require at least 15 active and 15 control in both branches to ensure robust lift comparison
            if (
                activations_a >= 15
                and activations_b >= 15
                and controls_a >= 15
                and controls_b >= 15
            ):
                branch_a_stats = S2REnvironment.compute_evidence(
                    formation_exps,
                    trigger_anon,
                    parent_belief["target_val"],
                    {anon_feat: 1},
                )
                branch_b_stats = S2REnvironment.compute_evidence(
                    formation_exps,
                    trigger_anon,
                    parent_belief["target_val"],
                    {anon_feat: 0},
                )

                eligible_partitions.append(
                    {
                        "partition_id": part_id,
                        "feature": anon_feat,
                        "branch_A_stats": branch_a_stats,
                        "branch_B_stats": branch_b_stats,
                    }
                )

        eligible_partitions.sort(key=lambda x: x["partition_id"])

        # Define ex-ante ground truth
        # Find which partition ID represents F_1
        gt_part_id = None
        f1_anon = feature_map[f"F_{partition_idx}"]
        for p in eligible_partitions:
            if p["feature"] == f1_anon:
                gt_part_id = p["partition_id"]
                break

        ex_ante_ops = {
            1: ("PRESERVE", None),
            2: ("REJECT", None),
            3: ("RESTRICT", gt_part_id),
            4: ("SPLIT", gt_part_id),
            5: ("REVERSE", None),
        }

        ex_ante_op, ex_ante_part = ex_ante_ops[family]

        return {
            "family": family,
            "seed": seed,
            "experiences": anon_experiences,
            "formation_experiences": formation_exps,
            "prospective_experiences": prospective_exps,
            "parent_belief": parent_belief,
            "feature_map": feature_map,
            "reverse_feature_map": reverse_feature_map,
            "outcome_map": outcome_map,
            "reverse_outcome_map": reverse_outcome_map,
            "eligible_partitions": eligible_partitions,
            "ex_ante_op": ex_ante_op,
            "ex_ante_part": ex_ante_part,
        }

    @staticmethod
    def compute_evidence(
        experiences: List[Dict[str, Any]],
        trigger_var: str,
        target_val: str,
        scope: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Computes repaired Evidence Object statistics with control-group baselines.
        """
        scope = scope or {}

        def matches_scope(e: Dict[str, Any]) -> bool:
            for k, v in scope.items():
                if e["features"].get(k) != v:
                    return False
            return True

        scope_exps = [e for e in experiences if matches_scope(e)]

        # Active Group (trigger == 1)
        active_exps = [e for e in scope_exps if e["features"].get(trigger_var) == 1]
        n_act = len(active_exps)
        n_sup = sum(1 for e in active_exps if e["outcome"] == target_val)
        p_cond = (n_sup / n_act) if n_act > 0 else 0.5

        # Control Group (trigger == 0)
        control_exps = [e for e in scope_exps if e["features"].get(trigger_var) == 0]
        n_ctrl = len(control_exps)
        n_ctrl_target = sum(1 for e in control_exps if e["outcome"] == target_val)
        p_control = (n_ctrl_target / n_ctrl) if n_ctrl > 0 else 0.5

        # Control-Group Lift
        conditional_lift = p_cond - p_control

        # Standard Error of Difference (for CI uncertainty)
        var_cond = (p_cond * (1.0 - p_cond) / n_act) if n_act > 0 else 0.25
        var_ctrl = (p_control * (1.0 - p_control) / n_ctrl) if n_ctrl > 0 else 0.25
        se_diff = math.sqrt(var_cond + var_ctrl)
        uncertainty = 1.96 * se_diff

        # Slices for temporal metrics
        mid = len(experiences) // 2
        early_exps = experiences[:mid]
        late_exps = experiences[mid:]

        def compute_subset_lift(subset: List[Dict[str, Any]]) -> float:
            sub_scope = [e for e in subset if matches_scope(e)]
            sub_act = [e for e in sub_scope if e["features"].get(trigger_var) == 1]
            sub_ctrl = [e for e in sub_scope if e["features"].get(trigger_var) == 0]

            if len(sub_act) == 0 or len(sub_ctrl) == 0:
                return 0.0

            sub_cond = sum(1 for e in sub_act if e["outcome"] == target_val) / len(
                sub_act
            )
            sub_control = sum(1 for e in sub_ctrl if e["outcome"] == target_val) / len(
                sub_ctrl
            )
            return sub_cond - sub_control

        historical_lift = compute_subset_lift(early_exps)
        recent_lift = compute_subset_lift(late_exps)
        temporal_shift = recent_lift - historical_lift

        # Drift: std dev of control-group lift across 5 slices of 100 days
        slice_lifts = []
        slice_size = len(experiences) // 5
        for s in range(5):
            slice_exps = experiences[s * slice_size : (s + 1) * slice_size]
            slice_lifts.append(compute_subset_lift(slice_exps))

        mean_slice_lift = sum(slice_lifts) / 5
        drift_index = math.sqrt(
            sum((x - mean_slice_lift) ** 2 for x in slice_lifts) / 5
        )

        return {
            "col_0": n_act,
            "col_1": n_sup,
            "col_2": n_act - n_sup,
            "col_3": round(p_cond, 4),
            "col_4": round(p_control, 4),
            "col_5": round(conditional_lift, 4),
            "col_6": round(uncertainty, 4),
            "col_7": round(historical_lift, 4),
            "col_8": round(recent_lift, 4),
            "col_9": round(temporal_shift, 4),
            "col_10": 0.0,
            "col_11": round(drift_index, 4),
        }

    @staticmethod
    def execute_op(
        op: str,
        partition_id: Optional[str],
        parent_belief: Dict[str, Any],
        eligible_partitions: List[Dict[str, Any]],
        formation_experiences: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Mechanically applies the selected operation to parent_belief to yield active successor beliefs.
        """
        # Exactly identical to S2 logic to preserve the semantics of operations.
        if op == "PRESERVE":
            return [parent_belief]

        elif op == "REJECT":
            return []

        elif op == "REVERSE":
            active_outcomes = set(e["outcome"] for e in formation_experiences)
            if len(active_outcomes) != 2:
                active_outcomes = {parent_belief["target_val"], "VAL_OTHER"}
            other_val = list(active_outcomes - {parent_belief["target_val"]})[0]

            return [
                {
                    "trigger_var": parent_belief["trigger_var"],
                    "target_val": other_val,
                    "scope": parent_belief["scope"].copy(),
                }
            ]

        elif op == "RESTRICT":
            if not partition_id:
                raise ValueError("RESTRICT requires partition_id")
            partition = next(
                (p for p in eligible_partitions if p["partition_id"] == partition_id),
                None,
            )
            if not partition:
                raise ValueError(f"Invalid partition_id: {partition_id}")

            new_scope = parent_belief["scope"].copy()
            new_scope[partition["feature"]] = 1
            return [
                {
                    "trigger_var": parent_belief["trigger_var"],
                    "target_val": parent_belief["target_val"],
                    "scope": new_scope,
                }
            ]

        elif op == "SPLIT":
            if not partition_id:
                raise ValueError("SPLIT requires partition_id")
            partition = next(
                (p for p in eligible_partitions if p["partition_id"] == partition_id),
                None,
            )
            if not partition:
                raise ValueError(f"Invalid partition_id: {partition_id}")

            trigger_anon = parent_belief["trigger_var"]
            feat_anon = partition["feature"]

            branch_a_exps = [
                e
                for e in formation_experiences
                if e["features"][trigger_anon] == 1 and e["features"][feat_anon] == 1
            ]
            branch_b_exps = [
                e
                for e in formation_experiences
                if e["features"][trigger_anon] == 1 and e["features"][feat_anon] == 0
            ]

            def majority_outcome(exps: List[Dict[str, Any]], default: str) -> str:
                if not exps:
                    return default
                counts = {}
                for e in exps:
                    counts[e["outcome"]] = counts.get(e["outcome"], 0) + 1
                return max(counts, key=counts.get)

            target_a = majority_outcome(branch_a_exps, parent_belief["target_val"])
            target_b = majority_outcome(branch_b_exps, parent_belief["target_val"])

            scope_a = parent_belief["scope"].copy()
            scope_a[feat_anon] = 1

            scope_b = parent_belief["scope"].copy()
            scope_b[feat_anon] = 0

            return [
                {"trigger_var": trigger_anon, "target_val": target_a, "scope": scope_a},
                {"trigger_var": trigger_anon, "target_val": target_b, "scope": scope_b},
            ]
        else:
            raise ValueError(f"Unknown operation: {op}")

    @staticmethod
    def evaluate_beliefs(
        beliefs: List[Dict[str, Any]], prospective_experiences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates a set of beliefs prospectively on evaluation experiences.
        Computes both Raw Prospective Utility and Complexity Adjusted Utility.
        """
        if not beliefs:
            return {
                "raw_utility": 0.0,
                "complexity_score": 0.0,
                "adjusted_utility": 0.0,
            }

        raw_utility = 0.0
        complexity_score = 0.0

        for belief in beliefs:
            trigger_var = belief["trigger_var"]
            target_val = belief["target_val"]
            scope = belief["scope"]

            # Filter prospective matching scope
            def matches_scope(e: Dict[str, Any]) -> bool:
                for k, v in scope.items():
                    if e["features"].get(k) != v:
                        return False
                return True

            scope_exps = [e for e in prospective_experiences if matches_scope(e)]

            # Active
            active_exps = [e for e in scope_exps if e["features"].get(trigger_var) == 1]
            n_act = len(active_exps)

            # Control
            control_exps = [
                e for e in scope_exps if e["features"].get(trigger_var) == 0
            ]
            n_ctrl = len(control_exps)

            if n_act > 0 and n_ctrl > 0:
                p_cond = (
                    sum(1 for e in active_exps if e["outcome"] == target_val) / n_act
                )
                p_control = (
                    sum(1 for e in control_exps if e["outcome"] == target_val) / n_ctrl
                )
                lift = p_cond - p_control
                raw_utility += n_act * lift

            # Complexity score: 1 base point + 1 per condition in scope
            complexity_score += 1.0 + len(scope)

        # Complexity penalty: 5.0 per complexity score unit
        adjusted_utility = raw_utility - 5.0 * complexity_score

        return {
            "raw_utility": round(raw_utility, 4),
            "complexity_score": round(complexity_score, 4),
            "adjusted_utility": round(adjusted_utility, 4),
        }


def format_agent_a_prompt_repaired(
    parent_belief: Dict[str, Any],
    formation_experiences: List[Dict[str, Any]],
    eligible_partitions: List[Dict[str, Any]],
) -> str:
    """
    Symmetric and anonymized prompt for Agent A (Raw Experience).
    """
    trigger = parent_belief["trigger_var"]
    target = parent_belief["target_val"]

    # Shuffle and format eligible partitions symmetrically
    shuffled_partitions = eligible_partitions.copy()
    random.shuffle(shuffled_partitions)

    partitions_str = ""
    for p in shuffled_partitions:
        partitions_str += (
            f"- Partition ID: {p['partition_id']} (when {p['feature']} == 1)\n"
        )

    all_keys = sorted(list(formation_experiences[0]["features"].keys()))
    header = "| Day | Outcome | " + " | ".join(all_keys) + " |"
    divider = "| --- | --- | " + " | ".join(["---"] * len(all_keys)) + " |"

    rows = [header, divider]
    for exp in formation_experiences[:100]:
        feats_val = [str(exp["features"][k]) for k in all_keys]
        rows.append(
            f"| {exp['day']} | {exp['outcome']} | " + " | ".join(feats_val) + " |"
        )

    table_str = "\n".join(rows)

    # Repaired operations list: Equal description length and prominence
    operations = [
        "- PRESERVE: Retain the parent belief exactly as it is (expected trigger: {trigger} -> target: {target}). Require partition_id = null.",
        "- REJECT: Deactivate the parent belief entirely (makes no prospective predictions). Require partition_id = null.",
        "- REVERSE: Invert the target outcome expected by the trigger (expect the opposite target outcome). Require partition_id = null.",
        "- RESTRICT: Narrow the scope of the parent belief trigger by adding one contextual partition variable. Require a valid partition_id.",
        "- SPLIT: Create two distinct successor rules partitioned on a contextual partition variable. Require a valid partition_id.",
    ]
    random.shuffle(operations)
    ops_str = "\n".join(operations)

    return f"""You are a scientific cognitive agent.
Your task is to select the best epistemic operation for a parent belief based on raw experience data.

Parent Belief:
- Trigger Variable: {trigger}
- Expected Target Outcome: {target}
- Target rule: WHEN {trigger} == 1 EXPECT outcome == {target}

Available Operations (shuffled ordering):
{ops_str}

Eligible Partitions list:
{partitions_str}

Raw Chronological Experiences (first 100 days):
{table_str}

Respond ONLY with a JSON object in the following format:
{{
  "operation": "PRESERVE" | "REJECT" | "RESTRICT" | "SPLIT" | "REVERSE",
  "partition_id": "PART_XYZ" | null
}}
"""


def format_agent_c_prompt_repaired(
    parent_belief: Dict[str, Any],
    parent_stats: Dict[str, Any],
    eligible_partitions: List[Dict[str, Any]],
) -> str:
    """
    Symmetric and anonymized prompt for Agent C (Full Evidence).
    Represents candidate partition statistics symmetrically and compactly without nested tables.
    """
    trigger = parent_belief["trigger_var"]
    target = parent_belief["target_val"]

    parent_stats_str = " | ".join(f"{k}: {v}" for k, v in sorted(parent_stats.items()))

    # Shuffle and format eligible partitions symmetrically and compactly
    shuffled_partitions = eligible_partitions.copy()
    random.shuffle(shuffled_partitions)

    partitions_str = ""
    for p in shuffled_partitions:
        part_id = p["partition_id"]
        # Compact representation
        lift_a = p["branch_A_stats"]["col_5"]
        n_a = p["branch_A_stats"]["col_0"]
        lift_b = p["branch_B_stats"]["col_5"]
        n_b = p["branch_B_stats"]["col_0"]

        partitions_str += f"- Partition ID: {part_id} | Branch A Lift: {lift_a:+.4f} (N={n_a}) | Branch B Lift: {lift_b:+.4f} (N={n_b})\n"

    operations = [
        "- PRESERVE: Retain the parent belief exactly as it is (expected trigger: {trigger} -> target: {target}). Require partition_id = null.",
        "- REJECT: Deactivate the parent belief entirely (makes no prospective predictions). Require partition_id = null.",
        "- REVERSE: Invert the target outcome expected by the trigger (expect the opposite target outcome). Require partition_id = null.",
        "- RESTRICT: Narrow the scope of the parent belief trigger by adding one contextual partition variable. Require a valid partition_id.",
        "- SPLIT: Create two distinct successor rules partitioned on a contextual partition variable. Require a valid partition_id.",
    ]
    random.shuffle(operations)
    ops_str = "\n".join(operations)

    return f"""You are a scientific cognitive agent.
Your task is to select the best epistemic operation for a parent belief based on compiled statistical evidence.

Parent Belief:
- Trigger Variable: {trigger}
- Expected Target Outcome: {target}
- Target rule: WHEN {trigger} == 1 EXPECT outcome == {target}

The statistical metrics are defined as follows:
- col_0: total activation count of parent trigger
- col_1: count of active trigger experiences where outcome matches expected target
- col_2: count of active trigger experiences where outcome does not match expected target
- col_3: ratio of matching outcomes to activations (col_1 / col_0)
- col_4: control-group target rate (unconditional target probability when trigger is inactive)
- col_5: conditional lift of trigger over control group (col_3 - col_4)
- col_6: uncertainty estimate of the lift (confidence interval width)
- col_7: historical lift (first half of training window)
- col_8: recent lift (second half of training window)
- col_9: temporal shift indicator (col_8 - col_7)
- col_10: missing-data rate
- col_11: variance/drift index of lift across temporal blocks

Parent Belief Statistics:
{parent_stats_str}

Eligible Partitions (compact summary):
{partitions_str}

Available Operations (shuffled ordering):
{ops_str}

Respond ONLY with a JSON object in the following format:
{{
  "operation": "PRESERVE" | "REJECT" | "RESTRICT" | "SPLIT" | "REVERSE",
  "partition_id": "PART_XYZ" | null
}}
"""
