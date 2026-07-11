from typing import Any, Dict, List


class MLCMetrics:
    @staticmethod
    def calculate_metrics(
        decisions: List[Dict[str, Any]],
        oracle_decisions: List[Dict[str, Any]],
        b2_decisions: List[Dict[str, Any]],
        frozen_candidates: List[Dict[str, Any]],
        erc_logs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Computes accuracy, precision, recall, and comparison differences.
        """
        epistemic_decisions = [
            d for d in decisions if d["decision"] != "COMPILATION_REJECTED"
        ]
        n = len(epistemic_decisions)
        compilation_rejection_count = len(decisions) - n

        if n == 0:
            return {}

        # Mappings
        oracle_map = {o["world_id"]: o["decision"] for o in oracle_decisions}
        oracle_reason_map = {o["world_id"]: o["reason_code"] for o in oracle_decisions}
        b2_map = {b["world_id"]: b["decision"] for b in b2_decisions}

        # Accuracy
        mlc_correct = 0
        b2_correct = 0
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if d["decision"] == oracle_map[w_id]:
                mlc_correct += 1
            if b2_map.get(w_id) == oracle_map[w_id]:
                b2_correct += 1

        mlc_acc = mlc_correct / n
        b2_acc = b2_correct / n

        # Catastrophic False Admission
        # System decision == ADMIT but Oracle != ADMIT
        mlc_catastrophic = 0
        b2_catastrophic = 0
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if d["decision"] == "ADMIT" and oracle_map[w_id] != "ADMIT":
                mlc_catastrophic += 1
            if b2_map.get(w_id) == "ADMIT" and oracle_map[w_id] != "ADMIT":
                b2_catastrophic += 1

        mlc_cat_rate = mlc_catastrophic / n
        b2_cat_rate = b2_catastrophic / n

        # False Rejection Rate
        # System decision == REJECT but Oracle != REJECT
        mlc_false_rej = 0
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if d["decision"] == "REJECT" and oracle_map[w_id] != "REJECT":
                mlc_false_rej += 1
        mlc_false_rej_rate = mlc_false_rej / n

        # DEFER precision & recall
        actual_defers = [d for d in epistemic_decisions if d["decision"] == "DEFER"]
        evaluated_world_ids = {d["world_id"] for d in epistemic_decisions}
        expected_defers = [
            w_id
            for w_id, dec in oracle_map.items()
            if dec == "DEFER" and w_id in evaluated_world_ids
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

        # ERC utilization
        total_comp = sum(
            l["requested_cost"]
            for l in erc_logs
            if l["resource_type"] == "COMPILATION"
            and l["authorization_decision"] == "AUTHORIZED"
        )
        total_ev = sum(
            l["requested_cost"]
            for l in erc_logs
            if l["resource_type"] == "EVIDENCE"
            and l["authorization_decision"] == "AUTHORIZED"
        )
        total_val = sum(
            l["requested_cost"]
            for l in erc_logs
            if l["resource_type"] == "VALIDATION"
            and l["authorization_decision"] == "AUTHORIZED"
        )

        # Mean coverage and activations from frozen candidates Window 2
        coverages = [
            c["window_2_intrinsic_measurements"]["coverage"] for c in frozen_candidates
        ]
        activations = [
            c["window_2_intrinsic_measurements"]["activation_count"]
            for c in frozen_candidates
        ]
        adeq_passes = sum(
            1
            for c in frozen_candidates
            if c["window_2_intrinsic_measurements"]["sample_adequacy"]
        )

        # MLC vs B2 decision differences
        matched_diff = sum(
            1 for d in epistemic_decisions if d["decision"] != b2_map.get(d["world_id"])
        )

        return {
            "overall_decision_accuracy": round(mlc_acc, 4),
            "b2_decision_accuracy": round(b2_acc, 4),
            "mlc_vs_b2_accuracy_difference": round(mlc_acc - b2_acc, 4),
            "catastrophic_false_admission_rate": round(mlc_cat_rate, 4),
            "b2_catastrophic_false_admission_rate": round(b2_cat_rate, 4),
            "mlc_vs_b2_catastrophic_false_admission_difference": round(
                mlc_cat_rate - b2_cat_rate, 4
            ),
            "false_rejection_rate": round(mlc_false_rej_rate, 4),
            "mlc_vs_b2_matched_decision_difference": matched_diff,
            "defer_precision": round(defer_precision, 4),
            "defer_recall": round(defer_recall, 4),
            "compilation_rejection_count": compilation_rejection_count,
            "erc_utilization": {
                "compilation_consumed": total_comp,
                "evidence_consumed": total_ev,
                "validation_consumed": total_val,
            },
            "mean_evidence_activations": (
                round(sum(activations) / len(activations), 4) if activations else 0.0
            ),
            "mean_coverage": (
                round(sum(coverages) / len(coverages), 4) if coverages else 0.0
            ),
            "mean_adequacy_pass_rate": (
                round(adeq_passes / len(frozen_candidates), 4)
                if frozen_candidates
                else 0.0
            ),
        }
