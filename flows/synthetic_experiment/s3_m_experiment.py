import json
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple


class S3MEnvironment:
    """
    Simulation and evaluation engine for Experiment S3-M:
    Marginal Explanatory Value Measurement Harness.
    """

    @staticmethod
    def generate_world(family: int, seed: int) -> Dict[str, Any]:
        """
        Generates a synthetic world instance for S3-M.
        """
        random.seed(seed)
        num_features = 10
        experiences = []

        trigger_idx = 0
        redundant_idx = 1
        partition_idx = 2
        subpop_idx = 3

        # Core features generation
        for t in range(1, 1001):
            feats = {}
            for i in range(num_features):
                feats[f"F_{i}"] = 1 if random.random() < 0.5 else 0

            # Planted outcome probability Y0 base rate is 0.50
            p_y0 = 0.50

            if family == 1:
                # Family 1: Exact Redundancy. F_1 is identical or 98% correlated to F_0.
                # True causal driver is F_0 == 1.
                if random.random() < 0.98:
                    feats[f"F_{redundant_idx}"] = feats[f"F_{trigger_idx}"]
                else:
                    feats[f"F_{redundant_idx}"] = 1 - feats[f"F_{trigger_idx}"]

                if feats[f"F_{trigger_idx}"] == 1:
                    p_y0 = 0.85
                else:
                    p_y0 = 0.50

            elif family == 2:
                # Family 2: Subsumption. General cause F_0 == 1 (Y0: 0.85).
                # Subsumed cause is F_0 == 1 AND F_2 == 1.
                if feats[f"F_{trigger_idx}"] == 1:
                    p_y0 = 0.85
                else:
                    p_y0 = 0.50

            elif family == 3:
                # Family 3: Independent Signals. F_0 == 1 (Y0: 0.85) and F_2 == 1 (Y0: 0.85).
                # F_0 and F_2 are independent.
                # If both are 1, probability is 0.85. If either is 1, it's 0.85.
                if feats[f"F_{trigger_idx}"] == 1 or feats[f"F_{partition_idx}"] == 1:
                    p_y0 = 0.85
                else:
                    p_y0 = 0.50

            elif family == 4:
                # Family 4: Complementary Interaction.
                # F_0 == 1 -> weak effect (Y0: 0.58)
                # F_3 == 1 -> weak effect (Y0: 0.58)
                # F_0 == 1 AND F_3 == 1 -> strong effect (Y0: 0.85)
                f0 = feats[f"F_{trigger_idx}"]
                f3 = feats[f"F_{subpop_idx}"]
                if f0 == 1 and f3 == 1:
                    p_y0 = 0.85
                elif f0 == 1 or f3 == 1:
                    p_y0 = 0.58
                else:
                    p_y0 = 0.50

            elif family == 5:
                # Family 5: Competing / Overlapping Explanations.
                # F_0 == 1 is the true causal driver.
                # F_1 is correlated with F_0 (80%). F_2 is correlated with F_0 (60%).
                if random.random() < 0.80:
                    feats[f"F_{redundant_idx}"] = feats[f"F_{trigger_idx}"]
                else:
                    feats[f"F_{redundant_idx}"] = 1 - feats[f"F_{trigger_idx}"]

                if random.random() < 0.60:
                    feats[f"F_{partition_idx}"] = feats[f"F_{trigger_idx}"]
                else:
                    feats[f"F_{partition_idx}"] = 1 - feats[f"F_{trigger_idx}"]

                if feats[f"F_{trigger_idx}"] == 1:
                    p_y0 = 0.85
                else:
                    p_y0 = 0.50

            elif family == 6:
                # Family 6: Null / Noise. All pure noise.
                p_y0 = 0.50

            outcome = "Y0" if random.random() < p_y0 else "Y1"
            experiences.append({"day": t, "features": feats, "outcome": outcome})

        # Feature anonymization mappings
        feature_indices = list(range(num_features))
        random.shuffle(feature_indices)
        feature_map = {}
        reverse_feature_map = {}
        for i, idx in enumerate(feature_indices):
            anon_name = f"VAR_{idx}"
            feature_map[f"F_{i}"] = anon_name
            reverse_feature_map[anon_name] = f"F_{i}"

        outcomes = ["VAL_A", "VAL_B"]
        random.shuffle(outcomes)
        outcome_map = {"Y0": outcomes[0], "Y1": outcomes[1]}
        reverse_outcome_map = {outcomes[0]: "Y0", outcomes[1]: "Y1"}

        # Ex-ante Ground Truth / Expected Oracle Set
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
                    "scope": [],
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
                    "scope": [],
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
                        "lag": 0,
                    },
                    "scope": [],
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
                        "field": feature_map[f"F_{partition_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
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
        elif family == 5:
            ex_ante_truth.append(
                {
                    "trigger": {
                        "field": feature_map[f"F_{trigger_idx}"],
                        "operator": "==",
                        "value": 1,
                        "lag": 0,
                    },
                    "scope": [],
                    "target": {
                        "field": "outcome",
                        "operator": "==",
                        "value": outcome_map["Y0"],
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
            "ex_ante_truth": ex_ante_truth,
            "feature_map": feature_map,
            "reverse_feature_map": reverse_feature_map,
            "outcome_map": outcome_map,
            "reverse_outcome_map": reverse_outcome_map,
        }

    @staticmethod
    def generate_candidate_bank(
        family: int, feature_map: Dict[str, str], outcome_map: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Generates a symmetric candidate bank containing Oracle, redundant,
        subsumed, independent decoys, noise, and complementary interaction candidates.
        """
        candidates = []
        all_feats = list(feature_map.values())
        target_val = outcome_map["Y0"]
        opp_target_val = outcome_map["Y1"]

        # 1. Oracle & complementary candidates
        # Add basic candidates for VAR_0 to VAR_9 (trigger, lag, outcome)
        for f in all_feats:
            for lag in [0, 1]:
                for val in [target_val, opp_target_val]:
                    candidates.append(
                        {
                            "trigger": {
                                "field": f,
                                "operator": "==",
                                "value": 1,
                                "lag": lag,
                            },
                            "scope": [],
                            "target": {
                                "field": "outcome",
                                "operator": "==",
                                "value": val,
                            },
                        }
                    )

        # 2. Scope-based / subsumed candidates
        # Add conjunctive candidates (trigger F_0, scope F_1)
        for f1 in all_feats:
            for f2 in all_feats:
                if f1 == f2:
                    continue
                for val in [target_val, opp_target_val]:
                    candidates.append(
                        {
                            "trigger": {
                                "field": f1,
                                "operator": "==",
                                "value": 1,
                                "lag": 0,
                            },
                            "scope": [{"field": f2, "operator": "==", "value": 1}],
                            "target": {
                                "field": "outcome",
                                "operator": "==",
                                "value": val,
                            },
                        }
                    )
                    candidates.append(
                        {
                            "trigger": {
                                "field": f1,
                                "operator": "==",
                                "value": 1,
                                "lag": 0,
                            },
                            "scope": [{"field": f2, "operator": "==", "value": 0}],
                            "target": {
                                "field": "outcome",
                                "operator": "==",
                                "value": val,
                            },
                        }
                    )

        # Deduplicate
        seen = set()
        deduped = []
        for c in candidates:
            c_str = json.dumps(c, sort_keys=True)
            if c_str not in seen:
                seen.add(c_str)
                deduped.append(c)

        # Shuffle candidates to ensure ordering is not bias-producing
        random.shuffle(deduped)
        return deduped

    @staticmethod
    def is_prop_active(
        prop: Dict[str, Any],
        exp: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        full_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        trigger = prop["trigger"]
        scope = prop["scope"]

        # Scope match check
        for s in scope:
            if exp["features"].get(s["field"]) != s["value"]:
                return False

        # Trigger match check
        if trigger["lag"] == 1:
            day = exp["day"]
            if day <= 1:
                return False
            history = full_history if full_history is not None else experiences
            if day - 2 < len(history) and history[day - 2]["day"] == day - 1:
                prev_exp = history[day - 2]
            else:
                prev_exp = None
                for e in history:
                    if e["day"] == day - 1:
                        prev_exp = e
                        break
                if prev_exp is None:
                    return False
            return prev_exp["features"].get(trigger["field"]) == trigger["value"]
        else:
            return exp["features"].get(trigger["field"]) == trigger["value"]

    @staticmethod
    def evaluate_proposition_single(
        prop: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        full_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates a single proposition in isolation.
        """
        n_act = 0
        n_act_target = 0
        n_ctrl = 0
        n_ctrl_target = 0

        trigger = prop["trigger"]
        target = prop["target"]

        for idx, exp in enumerate(experiences):
            if trigger["lag"] == 1 and exp["day"] <= 1:
                continue

            active = S3MEnvironment.is_prop_active(prop, exp, experiences, full_history)
            if active:
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

        complexity = 1.0 + len(prop["scope"]) + (1.0 if trigger["lag"] == 1 else 0.0)
        adjusted_utility = utility - 5.0 * complexity

        return {
            "n_act": n_act,
            "lift": round(lift, 4),
            "utility": round(utility, 4),
            "complexity": complexity,
            "adjusted_utility": round(adjusted_utility, 4),
        }

    @staticmethod
    def evaluate_propositions(
        propositions: List[Dict[str, Any]], experiences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Standard additive evaluation of a set of propositions.
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

        for p in propositions:
            eval_res = S3MEnvironment.evaluate_proposition_single(p, experiences)
            raw_utility += eval_res["utility"]
            complexity_score += eval_res["complexity"]
            prop_evals.append({"proposition": p, **eval_res})

        adjusted_utility = raw_utility - 5.0 * complexity_score
        return {
            "raw_utility": round(raw_utility, 4),
            "complexity_score": round(complexity_score, 4),
            "adjusted_utility": round(adjusted_utility, 4),
            "propositions_eval": prop_evals,
        }

    @staticmethod
    def check_proposition_match(p: Dict[str, Any], g: Dict[str, Any]) -> bool:
        if p["target"]["value"] != g["target"]["value"]:
            return False

        p_preds = [(p["trigger"]["field"], p["trigger"]["value"], p["trigger"]["lag"])]
        for s in p["scope"]:
            p_preds.append((s["field"], s["value"], 0))

        g_preds = [(g["trigger"]["field"], g["trigger"]["value"], g["trigger"]["lag"])]
        for s in g["scope"]:
            g_preds.append((s["field"], s["value"], 0))

        return sorted(p_preds) == sorted(g_preds)

    @staticmethod
    def check_oracle_equivalence(
        selected: List[Dict[str, Any]], oracle: List[Dict[str, Any]]
    ) -> bool:
        """
        Checks if selected set matches the Oracle set under equivalence classes.
        """
        if len(selected) != len(oracle):
            return False

        # Match each oracle element with a unique selected element
        matched = [False] * len(selected)
        for o in oracle:
            found = False
            for idx, s in enumerate(selected):
                if not matched[idx] and S3MEnvironment.check_proposition_match(s, o):
                    matched[idx] = True
                    found = True
                    break
            if not found:
                return False
        return True

    @staticmethod
    def select_m1(
        candidates: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        k_budget: int = 3,
    ) -> List[Dict[str, Any]]:
        scored = []
        for c in candidates:
            res = S3MEnvironment.evaluate_proposition_single(c, experiences)
            scored.append((c, res["adjusted_utility"]))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored[:k_budget] if x[1] > 0]

    @staticmethod
    def select_m2(
        candidates: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        k_budget: int = 3,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        selected = []
        order_sensitive = False

        def get_residual_utility(
            prop: Dict[str, Any], current_selected: List[Dict[str, Any]]
        ) -> float:
            residuals = []
            for exp in experiences:
                covered = False
                for s in current_selected:
                    if S3MEnvironment.is_prop_active(s, exp, experiences):
                        covered = True
                        break
                if not covered:
                    residuals.append(exp)

            if not residuals:
                complexity = (
                    1.0
                    + len(prop["scope"])
                    + (1.0 if prop["trigger"]["lag"] == 1 else 0.0)
                )
                return -5.0 * complexity

            res = S3MEnvironment.evaluate_proposition_single(prop, residuals)
            return res["adjusted_utility"]

        while len(selected) < k_budget:
            best_cand = None
            best_val = -float("inf")
            for c in candidates:
                if c in selected:
                    continue
                val = get_residual_utility(c, selected)
                if val > best_val:
                    best_val = val
                    best_cand = c
            if best_cand is not None and best_val > 0:
                selected.append(best_cand)
            else:
                break

        if len(selected) > 1:
            import itertools

            perm_scores = []
            for perm in itertools.permutations(selected):
                step_utils = []
                temp_selected = []
                for p in perm:
                    u = get_residual_utility(p, temp_selected)
                    step_utils.append(u)
                    temp_selected.append(p)
                perm_scores.append(tuple(step_utils))
            if len(set(perm_scores)) > 1:
                order_sensitive = True

        return selected, order_sensitive

    @staticmethod
    def select_m3(
        candidates: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        lam: float,
        k_budget: int = 3,
    ) -> List[Dict[str, Any]]:
        selected = []

        def get_set_score(subset: List[Dict[str, Any]]) -> float:
            if not subset:
                return 0.0
            sum_utils = 0.0
            for p in subset:
                res = S3MEnvironment.evaluate_proposition_single(p, experiences)
                sum_utils += res["adjusted_utility"]

            overlap_count = 0
            for exp in experiences:
                active_count = 0
                for p in subset:
                    if S3MEnvironment.is_prop_active(p, exp, experiences):
                        active_count += 1
                if active_count > 1:
                    overlap_count += active_count - 1
            return sum_utils - lam * overlap_count

        while len(selected) < k_budget:
            best_cand = None
            best_score = -float("inf")
            for c in candidates:
                if c in selected:
                    continue
                test_set = selected + [c]
                score = get_set_score(test_set)
                if score > best_score:
                    best_score = score
                    best_cand = c
            current_score = get_set_score(selected)
            if best_cand is not None and best_score > current_score and best_score > 0:
                selected.append(best_cand)
            else:
                break
        return selected

    @staticmethod
    def select_m4(
        candidates: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        k_budget: int = 3,
    ) -> List[Dict[str, Any]]:
        selected = []

        def get_joint_performance(subset: List[Dict[str, Any]]) -> float:
            if not subset:
                return 0.0
            n_act = 0
            n_act_correct = 0

            for exp in experiences:
                active_props = []
                for p in subset:
                    if S3MEnvironment.is_prop_active(p, exp, experiences):
                        active_props.append(p)
                if active_props:
                    n_act += 1
                    correct_count = 0
                    for p in active_props:
                        if exp["outcome"] == p["target"]["value"]:
                            correct_count += 1
                    n_act_correct += correct_count / len(active_props)

            p_cond = (n_act_correct / n_act) if n_act > 0 else 0.5
            lift = p_cond - 0.50
            raw_utility = n_act * lift
            total_complexity = sum(
                1.0 + len(p["scope"]) + (1.0 if p["trigger"]["lag"] == 1 else 0.0)
                for p in subset
            )
            return raw_utility - 5.0 * total_complexity

        while len(selected) < k_budget:
            best_cand = None
            best_perf = -float("inf")
            for c in candidates:
                if c in selected:
                    continue
                test_set = selected + [c]
                perf = get_joint_performance(test_set)
                if perf > best_perf:
                    best_perf = perf
                    best_cand = c
            current_perf = get_joint_performance(selected)
            if best_cand is not None and best_perf > current_perf and best_perf > 0:
                selected.append(best_cand)
            else:
                break
        return selected

    @staticmethod
    def select_m5(
        candidates: List[Dict[str, Any]],
        experiences: List[Dict[str, Any]],
        gamma: float,
        k_budget: int = 3,
    ) -> List[Dict[str, Any]]:
        selected = []

        def get_m5_score(subset: List[Dict[str, Any]]) -> float:
            if not subset:
                return len(experiences) * math.log(0.5)
            n_act = 0
            n_act_correct = 0
            n_ctrl = 0

            for exp in experiences:
                active_props = []
                for p in subset:
                    if S3MEnvironment.is_prop_active(p, exp, experiences):
                        active_props.append(p)
                if active_props:
                    n_act += 1
                    correct_count = 0
                    for p in active_props:
                        if exp["outcome"] == p["target"]["value"]:
                            correct_count += 1
                    n_act_correct += correct_count / len(active_props)
                else:
                    n_ctrl += 1

            p_cond = (n_act_correct + 1.0) / (n_act + 2.0)
            log_l = n_act_correct * math.log(p_cond) + (
                n_act - n_act_correct
            ) * math.log(1.0 - p_cond)
            log_l += n_ctrl * math.log(0.50)
            total_complexity = sum(
                1.0 + len(p["scope"]) + (1.0 if p["trigger"]["lag"] == 1 else 0.0)
                for p in subset
            )
            return log_l - gamma * total_complexity

        while len(selected) < k_budget:
            best_cand = None
            best_score = -float("inf")
            for c in candidates:
                if c in selected:
                    continue
                test_set = selected + [c]
                score = get_m5_score(test_set)
                if score > best_score:
                    best_score = score
                    best_cand = c
            current_score = get_m5_score(selected)
            if best_cand is not None and best_score > current_score:
                selected.append(best_cand)
            else:
                break
        return selected
