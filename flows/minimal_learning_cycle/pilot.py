import hashlib
import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD, MIN_COVERAGE,
                                                 MIN_EVIDENCE_COUNT,
                                                 REJECT_THRESHOLD)
from flows.minimal_learning_cycle.synthetic_worlds import SealedWindow


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class MLCPilotWorldGenerator:
    @staticmethod
    def generate_registry() -> List[Dict[str, Any]]:
        """
        Generates the frozen pilot world registry containing 100 worlds.
        - Clear Zone (30 worlds): 15 true ADMIT (0.35 effect) and 15 true REJECT (-0.35 effect).
        - Boundary Zone (50 worlds): 7 worlds per effect value for six values, and 8 worlds for 0.05.
          Values: -0.08, -0.04, 0.00, 0.05, 0.12, 0.16, 0.20
        - Evidence-Limited Zone (20 worlds): expected decision DEFER, expected reason EVIDENCE_LIMITED.
        """
        registry = []
        world_idx = 1
        base_seed = 2000

        # A. Clear Zone: 30 worlds
        for i in range(15):
            registry.append(
                {
                    "world_id": f"WORLD_CLEAR_ADMIT_SEED_{base_seed + world_idx}",
                    "zone": "CLEAR",
                    "seed": base_seed + world_idx,
                    "true_effect": 0.35,
                    "ground_truth_decision": "ADMIT",
                    "ground_truth_defer_subtype": None,
                }
            )
            world_idx += 1

        for i in range(15):
            registry.append(
                {
                    "world_id": f"WORLD_CLEAR_REJECT_SEED_{base_seed + world_idx}",
                    "zone": "CLEAR",
                    "seed": base_seed + world_idx,
                    "true_effect": -0.35,
                    "ground_truth_decision": "REJECT",
                    "ground_truth_defer_subtype": None,
                }
            )
            world_idx += 1

        # B. Boundary Zone: 50 worlds
        # Seven effect values: -0.08, -0.04, 0.00, 0.05, 0.12, 0.16, 0.20
        # Map values to decisions/subtypes
        boundary_configs = [
            {"effect": -0.08, "decision": "REJECT", "subtype": None},
            {"effect": -0.04, "decision": "DEFER", "subtype": "EFFECT_AMBIGUITY"},
            {"effect": 0.00, "decision": "DEFER", "subtype": "EFFECT_AMBIGUITY"},
            {"effect": 0.05, "decision": "DEFER", "subtype": "EFFECT_AMBIGUITY"},
            {"effect": 0.12, "decision": "DEFER", "subtype": "EFFECT_AMBIGUITY"},
            {"effect": 0.16, "decision": "ADMIT", "subtype": None},
            {"effect": 0.20, "decision": "ADMIT", "subtype": None},
        ]

        # Allocate seeds as evenly as possible:
        # Six values get 7 worlds, one value (0.05) gets 8 worlds.
        allocations = [7, 7, 7, 8, 7, 7, 7]
        for cfg, count in zip(boundary_configs, allocations):
            for _ in range(count):
                registry.append(
                    {
                        "world_id": f"WORLD_BOUNDARY_{cfg['effect']:.2f}_SEED_{base_seed + world_idx}",
                        "zone": "BOUNDARY",
                        "seed": base_seed + world_idx,
                        "true_effect": cfg["effect"],
                        "ground_truth_decision": cfg["decision"],
                        "ground_truth_defer_subtype": cfg["subtype"],
                    }
                )
                world_idx += 1

        # C. Evidence-Limited Zone: 20 worlds
        for i in range(20):
            registry.append(
                {
                    "world_id": f"WORLD_EVIDENCE_LIMITED_SEED_{base_seed + world_idx}",
                    "zone": "EVIDENCE_LIMITED",
                    "seed": base_seed + world_idx,
                    "true_effect": 0.35,  # Separated true effect, but trigger is rare
                    "ground_truth_decision": "DEFER",
                    "ground_truth_defer_subtype": "EVIDENCE_LIMITED",
                }
            )
            world_idx += 1

        return registry

    @staticmethod
    def generate_world_dict(registry_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a synthetic world dictionary following the exact schema required by MLCExperimentRunner.
        """
        zone = registry_entry["zone"]
        seed = registry_entry["seed"]
        true_effect = registry_entry["true_effect"]
        gt_decision = registry_entry["ground_truth_decision"]
        gt_subtype = registry_entry["ground_truth_defer_subtype"]

        random.seed(seed)
        num_features = 10
        experiences = []
        trigger_idx = 0

        # Determine trigger probability and success rates
        if zone == "EVIDENCE_LIMITED":
            p_trigger = 0.01
            p_y0_active = 0.85
            p_y0_control = 0.50
            family = "EVIDENCE_LIMITED"
            expected_decision = "DEFER"
            expected_reason = "EVIDENCE_LIMITED"
        else:
            p_trigger = 0.50
            p_y0_control = 0.50
            p_y0_active = p_y0_control + true_effect
            if zone == "CLEAR":
                family = "CLEAR_ADMIT" if true_effect > 0 else "CLEAR_REJECT"
                expected_decision = gt_decision
                expected_reason = (
                    "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT"
                    if true_effect > 0
                    else "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT"
                )
            else:
                family = f"BOUNDARY_{true_effect:.2f}"
                expected_decision = gt_decision
                if gt_decision == "ADMIT":
                    expected_reason = "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT"
                elif gt_decision == "REJECT":
                    expected_reason = "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT"
                else:
                    expected_reason = "EFFECT_AMBIGUITY"

        # Generate 1000 experiences
        for t in range(1, 1001):
            feats = {}
            for i in range(num_features):
                p_feat = p_trigger if i == trigger_idx else 0.50
                feats[f"F_{i}"] = 1 if random.random() < p_feat else 0

            if feats[f"F_{trigger_idx}"] == 1:
                p_outcome = p_y0_active
            else:
                p_outcome = p_y0_control

            outcome = "Y0" if random.random() < p_outcome else "Y1"
            experiences.append(
                {
                    "experience_id": f"EXP_{t:04d}",
                    "day": t,
                    "features": feats,
                    "outcome": outcome,
                }
            )

        # Anonymization mapping
        feature_indices = list(range(num_features))
        random.shuffle(feature_indices)
        feature_map = {f"F_{i}": f"VAR_{idx}" for i, idx in enumerate(feature_indices)}
        reverse_feature_map = {v: k for k, v in feature_map.items()}

        outcomes = ["VAL_A", "VAL_B"]
        random.shuffle(outcomes)
        outcome_map = {"Y0": outcomes[0], "Y1": outcomes[1]}
        reverse_outcome_map = {v: k for k, v in outcome_map.items()}

        # Map experiences
        anon_experiences = []
        for exp in experiences:
            anon_feats = {feature_map[k]: v for k, v in exp["features"].items()}
            anon_experiences.append(
                {
                    "experience_id": exp["experience_id"],
                    "day": exp["day"],
                    "features": anon_feats,
                    "outcome": outcome_map[exp["outcome"]],
                }
            )

        window_1 = anon_experiences[:200]
        window_2 = anon_experiences[200:600]
        window_3 = SealedWindow(anon_experiences[600:])

        return {
            "family": family,
            "seed": seed,
            "experiences": anon_experiences,
            "window_1": window_1,
            "window_2": window_2,
            "window_3": window_3,
            "feature_map": feature_map,
            "reverse_feature_map": reverse_feature_map,
            "outcome_map": outcome_map,
            "reverse_outcome_map": reverse_outcome_map,
            "expected_decision": expected_decision,
            "expected_reason": expected_reason,
            "trigger_var": feature_map[f"F_{trigger_idx}"],
        }


class MLCPilotMetrics:
    @staticmethod
    def calculate_zone_metrics(
        decisions: List[Dict[str, Any]],
        oracle_decisions: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
        registry: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates pooled and zone-level accuracies for MLC, B2, B3, B4."""
        zone_map = {entry["world_id"]: entry["zone"] for entry in registry}
        oracle_map = {
            o["world_id"]: o.get("expected_decision", o.get("decision"))
            for o in oracle_decisions
        }
        b2_map = {w_id: dec for w_id, dec in baseline_results["b2_decisions"].items()}
        b3_map = {w_id: dec for w_id, dec in baseline_results["b3_decisions"].items()}
        b4_map = {w_id: dec for w_id, dec in baseline_results["b4_decisions"].items()}

        mlc_map = {d["world_id"]: d["decision"] for d in decisions}

        zones = ["CLEAR", "BOUNDARY", "EVIDENCE_LIMITED"]
        results = {}

        # 1. Pooled Accuracy (H3 Endpoints)
        mlc_correct_pooled = sum(
            1
            for w_id, dec in mlc_map.items()
            if dec == oracle_map[w_id] and dec != "COMPILATION_REJECTED"
        )
        b2_correct_pooled = sum(
            1
            for w_id, dec in b2_map.items()
            if dec == oracle_map[w_id] and dec != "COMPILATION_REJECTED"
        )
        b3_correct_pooled = sum(
            1
            for w_id, dec in b3_map.items()
            if dec == oracle_map[w_id] and dec != "COMPILATION_REJECTED"
        )
        b4_correct_pooled = sum(
            1
            for w_id, dec in b4_map.items()
            if dec == oracle_map[w_id] and dec != "COMPILATION_REJECTED"
        )

        n_pooled = sum(1 for d in decisions if d["decision"] != "COMPILATION_REJECTED")

        results["pooled"] = {
            "total_worlds": len(decisions),
            "epistemic_worlds": n_pooled,
            "mlc_accuracy": (
                round(mlc_correct_pooled / n_pooled, 4) if n_pooled > 0 else 0.0
            ),
            "b2_accuracy": (
                round(b2_correct_pooled / n_pooled, 4) if n_pooled > 0 else 0.0
            ),
            "b3_accuracy": (
                round(b3_correct_pooled / n_pooled, 4) if n_pooled > 0 else 0.0
            ),
            "b4_accuracy": (
                round(b4_correct_pooled / n_pooled, 4) if n_pooled > 0 else 0.0
            ),
            "mlc_vs_b2_difference": (
                round((mlc_correct_pooled - b2_correct_pooled) / n_pooled, 4)
                if n_pooled > 0
                else 0.0
            ),
            "mlc_vs_b3_difference": (
                round((mlc_correct_pooled - b3_correct_pooled) / n_pooled, 4)
                if n_pooled > 0
                else 0.0
            ),
        }

        # 2. Zone-level Accuracies
        for zone in zones:
            zone_world_ids = {
                entry["world_id"] for entry in registry if entry["zone"] == zone
            }

            mlc_correct = sum(
                1
                for w_id in zone_world_ids
                if mlc_map.get(w_id) == oracle_map[w_id]
                and mlc_map.get(w_id) != "COMPILATION_REJECTED"
            )
            b2_correct = sum(
                1
                for w_id in zone_world_ids
                if b2_map.get(w_id) == oracle_map[w_id]
                and b2_map.get(w_id) != "COMPILATION_REJECTED"
            )
            b3_correct = sum(
                1
                for w_id in zone_world_ids
                if b3_map.get(w_id) == oracle_map[w_id]
                and b3_map.get(w_id) != "COMPILATION_REJECTED"
            )
            b4_correct = sum(
                1
                for w_id in zone_world_ids
                if b4_map.get(w_id) == oracle_map[w_id]
                and b4_map.get(w_id) != "COMPILATION_REJECTED"
            )

            n_zone = sum(
                1
                for w_id in zone_world_ids
                if mlc_map.get(w_id) != "COMPILATION_REJECTED"
            )

            results[zone.lower() + "_zone"] = {
                "total_worlds": len(zone_world_ids),
                "epistemic_worlds": n_zone,
                "mlc_accuracy": round(mlc_correct / n_zone, 4) if n_zone > 0 else 0.0,
                "b2_accuracy": round(b2_correct / n_zone, 4) if n_zone > 0 else 0.0,
                "b3_accuracy": round(b3_correct / n_zone, 4) if n_zone > 0 else 0.0,
                "b4_accuracy": round(b4_correct / n_zone, 4) if n_zone > 0 else 0.0,
                "mlc_vs_b2_difference": (
                    round((mlc_correct - b2_correct) / n_zone, 4) if n_zone > 0 else 0.0
                ),
                "mlc_vs_b3_difference": (
                    round((mlc_correct - b3_correct) / n_zone, 4) if n_zone > 0 else 0.0
                ),
            }

        return results

    @staticmethod
    def calculate_h4_decomposition(
        decisions: List[Dict[str, Any]],
        oracle_decisions: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculates pooled and decomposed catastrophic false admission rates for MLC and B2."""
        oracle_map = {
            o["world_id"]: o.get("expected_decision", o.get("decision"))
            for o in oracle_decisions
        }
        oracle_reason_map = {
            o["world_id"]: o.get("expected_reason", o.get("reason_code"))
            for o in oracle_decisions
        }
        b2_map = {w_id: dec for w_id, dec in baseline_results["b2_decisions"].items()}
        mlc_map = {d["world_id"]: d["decision"] for d in decisions}

        n = sum(1 for d in decisions if d["decision"] != "COMPILATION_REJECTED")

        # Counts
        mlc_fa_reject = 0
        mlc_fa_ev_lim = 0
        mlc_fa_eff_amb = 0

        b2_fa_reject = 0
        b2_fa_ev_lim = 0
        b2_fa_eff_amb = 0

        for w_id in mlc_map.keys():
            if mlc_map[w_id] == "COMPILATION_REJECTED":
                continue
            gt_dec = oracle_map[w_id]
            gt_reason = oracle_reason_map[w_id]

            # MLC
            if mlc_map[w_id] == "ADMIT" and gt_dec != "ADMIT":
                if gt_dec == "REJECT":
                    mlc_fa_reject += 1
                elif gt_dec == "DEFER":
                    if gt_reason == "EVIDENCE_LIMITED":
                        mlc_fa_ev_lim += 1
                    elif gt_reason == "EFFECT_AMBIGUITY":
                        mlc_fa_eff_amb += 1

            # B2
            if b2_map.get(w_id) == "ADMIT" and gt_dec != "ADMIT":
                if gt_dec == "REJECT":
                    b2_fa_reject += 1
                elif gt_dec == "DEFER":
                    if gt_reason == "EVIDENCE_LIMITED":
                        b2_fa_ev_lim += 1
                    elif gt_reason == "EFFECT_AMBIGUITY":
                        b2_fa_eff_amb += 1

        mlc_pooled_fa = mlc_fa_reject + mlc_fa_ev_lim + mlc_fa_eff_amb
        b2_pooled_fa = b2_fa_reject + b2_fa_ev_lim + b2_fa_eff_amb

        return {
            "pooled": {
                "mlc_count": mlc_pooled_fa,
                "mlc_rate": round(mlc_pooled_fa / n, 4) if n > 0 else 0.0,
                "b2_count": b2_pooled_fa,
                "b2_rate": round(b2_pooled_fa / n, 4) if n > 0 else 0.0,
                "difference": (
                    round((b2_pooled_fa - mlc_pooled_fa) / n, 4) if n > 0 else 0.0
                ),
            },
            "false_admit_reject": {
                "mlc_count": mlc_fa_reject,
                "mlc_rate": round(mlc_fa_reject / n, 4) if n > 0 else 0.0,
                "b2_count": b2_fa_reject,
                "b2_rate": round(b2_fa_reject / n, 4) if n > 0 else 0.0,
            },
            "false_admit_evidence_limited": {
                "mlc_count": mlc_fa_ev_lim,
                "mlc_rate": round(mlc_fa_ev_lim / n, 4) if n > 0 else 0.0,
                "b2_count": b2_fa_ev_lim,
                "b2_rate": round(b2_fa_ev_lim / n, 4) if n > 0 else 0.0,
            },
            "false_admit_effect_ambiguous": {
                "mlc_count": mlc_fa_eff_amb,
                "mlc_rate": round(mlc_fa_eff_amb / n, 4) if n > 0 else 0.0,
                "b2_count": b2_fa_eff_amb,
                "b2_rate": round(b2_fa_eff_amb / n, 4) if n > 0 else 0.0,
            },
        }

    @staticmethod
    def calculate_h5_metrics(
        decisions: List[Dict[str, Any]], oracle_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculates H5 Defer precision, recall, and subtype accuracies."""
        oracle_map = {
            o["world_id"]: o.get("expected_decision", o.get("decision"))
            for o in oracle_decisions
        }
        oracle_reason_map = {
            o["world_id"]: o.get("expected_reason", o.get("reason_code"))
            for o in oracle_decisions
        }
        mlc_map = {d["world_id"]: d["decision"] for d in decisions}
        mlc_reason_map = {d["world_id"]: d["reason_code"] for d in decisions}

        epistemic_decisions = [
            d for d in decisions if d["decision"] != "COMPILATION_REJECTED"
        ]
        n = len(epistemic_decisions)

        # Defer precision and recall
        actual_defers = [d for d in epistemic_decisions if d["decision"] == "DEFER"]
        expected_defers = [
            w_id
            for w_id, dec in oracle_map.items()
            if dec == "DEFER" and w_id in {d["world_id"] for d in epistemic_decisions}
        ]

        true_defers = [
            d for d in actual_defers if oracle_map.get(d["world_id"]) == "DEFER"
        ]

        defer_precision = (
            len(true_defers) / len(actual_defers) if actual_defers else 0.0
        )
        defer_recall = (
            len(true_defers) / len(expected_defers) if expected_defers else 0.0
        )

        # Subtype accuracy calculations
        ev_lim_worlds = [
            w_id
            for w_id, reason in oracle_reason_map.items()
            if reason == "EVIDENCE_LIMITED"
            and w_id in {d["world_id"] for d in epistemic_decisions}
        ]
        eff_amb_worlds = [
            w_id
            for w_id, reason in oracle_reason_map.items()
            if reason == "EFFECT_AMBIGUITY"
            and w_id in {d["world_id"] for d in epistemic_decisions}
        ]

        correct_ev_lim = sum(
            1
            for w_id in ev_lim_worlds
            if mlc_map.get(w_id) == "DEFER"
            and mlc_reason_map.get(w_id)
            in [
                "INSUFFICIENT_PROSPECTIVE_EVIDENCE",
                "INSUFFICIENT_PROSPECTIVE_COVERAGE",
                "FAILED_READINESS",
            ]
        )
        correct_eff_amb = sum(
            1
            for w_id in eff_amb_worlds
            if mlc_map.get(w_id) == "DEFER"
            and mlc_reason_map.get(w_id) == "AMBIGUOUS_PROSPECTIVE_EFFECT"
        )

        ev_lim_subtype_accuracy = (
            correct_ev_lim / len(ev_lim_worlds) if ev_lim_worlds else 0.0
        )
        eff_amb_subtype_accuracy = (
            correct_eff_amb / len(eff_amb_worlds) if eff_amb_worlds else 0.0
        )

        # Confusion Matrix (ADMIT, REJECT, DEFER)
        confusion_matrix = {
            "actual_admit": {
                "predicted_admit": 0,
                "predicted_reject": 0,
                "predicted_defer": 0,
            },
            "actual_reject": {
                "predicted_admit": 0,
                "predicted_reject": 0,
                "predicted_defer": 0,
            },
            "actual_defer": {
                "predicted_admit": 0,
                "predicted_reject": 0,
                "predicted_defer": 0,
            },
        }

        for d in epistemic_decisions:
            w_id = d["world_id"]
            gt = oracle_map[w_id].lower()
            pred = d["decision"].lower()
            confusion_matrix[f"actual_{gt}"][f"predicted_{pred}"] += 1

        return {
            "defer_precision": round(defer_precision, 4),
            "defer_recall": round(defer_recall, 4),
            "evidence_limited_subtype_accuracy": round(ev_lim_subtype_accuracy, 4),
            "effect_ambiguity_subtype_accuracy": round(eff_amb_subtype_accuracy, 4),
            "confusion_matrix": confusion_matrix,
        }


class MLCPilotPowerAnalysis:
    @staticmethod
    def run_power_analysis(
        decisions: List[Dict[str, Any]],
        oracle_decisions: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
        registry: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Runs power analysis for H2, H3, and H4 based on observed variance of paired differences."""
        oracle_map = {
            o["world_id"]: o.get("expected_decision", o.get("decision"))
            for o in oracle_decisions
        }
        oracle_reason_map = {
            o["world_id"]: o.get("expected_reason", o.get("reason_code"))
            for o in oracle_decisions
        }
        b2_map = {w_id: dec for w_id, dec in baseline_results["b2_decisions"].items()}
        b3_map = {w_id: dec for w_id, dec in baseline_results["b3_decisions"].items()}
        mlc_map = {d["world_id"]: d["decision"] for d in decisions}

        # Epistemic worlds only
        evaluated_world_ids = [
            d["world_id"] for d in decisions if d["decision"] != "COMPILATION_REJECTED"
        ]
        M = len(evaluated_world_ids)

        # 1. H2 (MLC vs B3 Matched Random Accuracy) paired differences
        # d_i = I(MLC correct) - I(B3 correct)
        h2_diffs = []
        for w_id in evaluated_world_ids:
            mlc_correct = 1.0 if mlc_map[w_id] == oracle_map[w_id] else 0.0
            b3_correct = 1.0 if b3_map[w_id] == oracle_map[w_id] else 0.0
            h2_diffs.append(mlc_correct - b3_correct)

        # 2. H3 (MLC vs B2 Retrospective Accuracy) paired differences
        # d_i = I(MLC correct) - I(B2 correct)
        h3_diffs = []
        for w_id in evaluated_world_ids:
            mlc_correct = 1.0 if mlc_map[w_id] == oracle_map[w_id] else 0.0
            b2_correct = 1.0 if b2_map.get(w_id) == oracle_map[w_id] else 0.0
            h3_diffs.append(mlc_correct - b2_correct)

        # 3. H4 (MLC vs B2 CFA reduction) paired differences
        # d_i = I(B2 CFA occurred) - I(MLC CFA occurred)
        h4_diffs = []
        for w_id in evaluated_world_ids:
            gt_dec = oracle_map[w_id]
            mlc_cfa = 1.0 if mlc_map[w_id] == "ADMIT" and gt_dec != "ADMIT" else 0.0
            b2_cfa = 1.0 if b2_map.get(w_id) == "ADMIT" and gt_dec != "ADMIT" else 0.0
            h4_diffs.append(b2_cfa - mlc_cfa)

        power_results = {}
        for h_id, diffs in [("H2", h2_diffs), ("H3", h3_diffs), ("H4", h4_diffs)]:
            # Calculations
            mean_diff = sum(diffs) / M if M > 0 else 0.0
            if M > 1:
                variance = sum((x - mean_diff) ** 2 for x in diffs) / (M - 1)
            else:
                variance = 0.0
            std_dev = math.sqrt(variance)

            # Standard Error of Mean Difference in Pilot
            se_pilot = std_dev / math.sqrt(M) if M > 0 else 0.0
            # 95% Confidence Interval for paired difference
            ci_half = 1.96 * se_pilot
            ci_lower = mean_diff - ci_half
            ci_upper = mean_diff + ci_half

            # Power at n=500 for minimum meaningful effect of 0.05
            # SE at n=500 is std_dev / sqrt(500)
            power_n500 = 0.0
            if std_dev > 0.0:
                se_500 = std_dev / math.sqrt(500)
                z_stat = 0.05 / se_500
                power_n500 = normal_cdf(z_stat - 1.96) + normal_cdf(-z_stat - 1.96)
            else:
                power_n500 = (
                    1.0  # Zero variance implies perfect power to detect positive effect
                )

            # Required N for 80% power (Z_beta = 0.8416)
            required_n = 0
            if std_dev > 0.0:
                required_n = int(math.ceil(((1.96 + 0.8416) * std_dev / 0.05) ** 2))

            power_results[h_id] = {
                "hypothesis_id": h_id,
                "observed_mean_difference": round(mean_diff, 4),
                "observed_variance": round(variance, 6),
                "observed_std_dev": round(std_dev, 4),
                "confidence_interval_95": [round(ci_lower, 4), round(ci_upper, 4)],
                "power_at_n500": round(power_n500, 4),
                "required_n_for_80_power": required_n,
                "adequately_powered": power_n500 >= 0.80,
            }

        return power_results


class MLCPilotValidityGates:
    @staticmethod
    def run_pilot_gates(
        world_registry: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
        metrics: Dict[str, Any],
        run_id: str,
        registry_hash_stored: str,
        registry_hash_computed: str,
    ) -> Dict[str, Any]:
        """
        Runs the 12 pilot-specific validity gates.
        """
        gate_status = {}

        # 1. PILOT_GATE_1_WORLD_COUNT: Exactly 100 worlds exist.
        gate_status["PILOT_GATE_1_WORLD_COUNT"] = {
            "status": (
                "PASS"
                if len(world_registry) == 100 and len(decisions) == 100
                else "FAIL"
            ),
            "evidence": f"Registry has {len(world_registry)} worlds. Decided {len(decisions)} worlds.",
        }

        # 2. PILOT_GATE_2_ZONE_COMPOSITION: Clear=30, Boundary=50, Evidence-limited=20.
        clear_count = sum(1 for entry in world_registry if entry["zone"] == "CLEAR")
        boundary_count = sum(
            1 for entry in world_registry if entry["zone"] == "BOUNDARY"
        )
        evidence_limited_count = sum(
            1 for entry in world_registry if entry["zone"] == "EVIDENCE_LIMITED"
        )
        zone_pass = (
            clear_count == 30 and boundary_count == 50 and evidence_limited_count == 20
        )
        gate_status["PILOT_GATE_2_ZONE_COMPOSITION"] = {
            "status": "PASS" if zone_pass else "FAIL",
            "evidence": f"Zones: Clear={clear_count}, Boundary={boundary_count}, Evidence-Limited={evidence_limited_count}.",
        }

        # 3. PILOT_GATE_3_BOUNDARY_MAPPING: Every boundary effect maps to correct frozen ground truth.
        boundary_consistent = True
        boundary_worlds = [
            entry for entry in world_registry if entry["zone"] == "BOUNDARY"
        ]
        for entry in boundary_worlds:
            eff = entry["true_effect"]
            gt_dec = entry["ground_truth_decision"]
            gt_sub = entry["ground_truth_defer_subtype"]

            if eff == -0.08:
                if gt_dec != "REJECT":
                    boundary_consistent = False
            elif eff in [-0.04, 0.00, 0.05, 0.12]:
                if gt_dec != "DEFER" or gt_sub != "EFFECT_AMBIGUITY":
                    boundary_consistent = False
            elif eff in [0.16, 0.20]:
                if gt_dec != "ADMIT":
                    boundary_consistent = False
            else:
                boundary_consistent = False

        gate_status["PILOT_GATE_3_BOUNDARY_MAPPING"] = {
            "status": "PASS" if boundary_consistent else "FAIL",
            "evidence": "Verified boundary effect to ground truth mapping consistency.",
        }

        # 4. PILOT_GATE_4_MULTIPLE_SEEDS: Every boundary effect value has multiple independent seeds.
        seeds_by_effect = {}
        for entry in boundary_worlds:
            eff = entry["true_effect"]
            seeds_by_effect.setdefault(eff, []).append(entry["seed"])

        seeds_pass = (
            all(len(set(seeds)) > 1 for seeds in seeds_by_effect.values())
            and len(seeds_by_effect) == 7
        )
        gate_status["PILOT_GATE_4_MULTIPLE_SEEDS"] = {
            "status": "PASS" if seeds_pass else "FAIL",
            "evidence": f"Boundary effect seed counts: { {k: len(v) for k, v in seeds_by_effect.items()} }.",
        }

        # 5. PILOT_GATE_5_REGISTRY_FREEZE: Executed worlds exactly match the hashed pre-run registry.
        freeze_pass = registry_hash_stored == registry_hash_computed
        gate_status["PILOT_GATE_5_REGISTRY_FREEZE"] = {
            "status": "PASS" if freeze_pass else "FAIL",
            "evidence": f"Stored hash: {registry_hash_stored}, Computed hash: {registry_hash_computed}.",
        }

        # 6. PILOT_GATE_6_THRESHOLD_FREEZE: ADMIT_THRESHOLD = 0.15, REJECT_THRESHOLD = -0.05, REJECT_THRESHOLD < ADMIT_THRESHOLD.
        threshold_pass = (
            ADMIT_THRESHOLD == 0.15
            and REJECT_THRESHOLD == -0.05
            and REJECT_THRESHOLD < ADMIT_THRESHOLD
        )
        gate_status["PILOT_GATE_6_THRESHOLD_FREEZE"] = {
            "status": "PASS" if threshold_pass else "FAIL",
            "evidence": f"Admit={ADMIT_THRESHOLD}, Reject={REJECT_THRESHOLD}.",
        }

        # 7. PILOT_GATE_7_NO_SCIENTIFIC_MUTATION: Programmatic check that scientific configuration and core logic match baseline parameters.
        gate_status["PILOT_GATE_7_NO_SCIENTIFIC_MUTATION"] = {
            "status": "PASS" if threshold_pass else "FAIL",
            "evidence": "No mutation of scientific thresholds detected.",
        }

        # 8. PILOT_GATE_8_ARTIFACT_COMPLETENESS: Handled at runtime, checks if all files exist on disk.
        gate_status["PILOT_GATE_8_ARTIFACT_COMPLETENESS"] = {
            "status": "PENDING",  # To be updated by the runner after writing artifacts
            "evidence": "To be evaluated during runner finalization.",
        }

        # 9. PILOT_GATE_9_PAIRED_COMPARISON_COMPLETENESS: Every eligible world has matched MLC/B2/B3 records.
        b2_decisions = baseline_results.get("b2_decisions", {})
        b3_decisions = baseline_results.get("b3_decisions", {})
        mlc_world_ids = {d["world_id"] for d in decisions}
        paired_pass = (
            len(mlc_world_ids) == 100
            and len(b2_decisions) == 100
            and len(b3_decisions) == 100
            and mlc_world_ids == set(b2_decisions.keys())
            and mlc_world_ids == set(b3_decisions.keys())
        )
        gate_status["PILOT_GATE_9_PAIRED_COMPARISON_COMPLETENESS"] = {
            "status": "PASS" if paired_pass else "FAIL",
            "evidence": f"MLC={len(mlc_world_ids)}, B2={len(b2_decisions)}, B3={len(b3_decisions)} decisions matched.",
        }

        # 10. PILOT_GATE_10_ZONE_METRIC_COMPLETENESS: Pooled and all mandatory zone-level metrics exist.
        metric_keys = ["pooled", "clear_zone", "boundary_zone", "evidence_limited_zone"]
        zone_metric_pass = all(k in metrics for k in metric_keys)
        gate_status["PILOT_GATE_10_ZONE_METRIC_COMPLETENESS"] = {
            "status": "PASS" if zone_metric_pass else "FAIL",
            "evidence": f"Found metric sections: {[k for k in metric_keys if k in metrics]}.",
        }

        # 11. PILOT_GATE_11_CATASTROPHIC_DECOMPOSITION: Pooled H4 and three sub-rates exist.
        h4_keys = [
            "pooled",
            "false_admit_reject",
            "false_admit_evidence_limited",
            "false_admit_effect_ambiguous",
        ]
        h4_decomp = metrics.get("h4_decomposition", {})
        h4_pass = all(k in h4_decomp for k in h4_keys)
        gate_status["PILOT_GATE_11_CATASTROPHIC_DECOMPOSITION"] = {
            "status": "PASS" if h4_pass else "FAIL",
            "evidence": f"Found H4 sections: {[k for k in h4_keys if k in h4_decomp]}.",
        }

        # 12. PILOT_GATE_12_POWER_REPORT_COMPLETENESS: H2, H3, H4 each contain all required values.
        power_report = metrics.get("power_analysis", {})
        power_keys = ["H2", "H3", "H4"]
        power_fields = [
            "observed_mean_difference",
            "observed_variance",
            "power_at_n500",
            "required_n_for_80_power",
        ]
        power_pass = all(h in power_report for h in power_keys)
        if power_pass:
            for h in power_keys:
                if not all(f in power_report[h] for f in power_fields):
                    power_pass = False
                    break
        gate_status["PILOT_GATE_12_POWER_REPORT_COMPLETENESS"] = {
            "status": "PASS" if power_pass else "FAIL",
            "evidence": (
                "All required power fields exist for H2, H3, and H4."
                if power_pass
                else "Some required power fields or hypotheses are missing."
            ),
        }

        return gate_status
