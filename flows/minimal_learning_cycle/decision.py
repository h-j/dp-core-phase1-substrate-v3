import time
from typing import Any, Dict

from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD,
                                                 REJECT_THRESHOLD)


class MLCDecision:
    @staticmethod
    def make_decision(
        prop_id: str, world_id: str, prospective_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exhaustive mutually exclusive decision tree.
        """
        comp_effect = prospective_res["comparative_effect"]
        adequacy = prospective_res["prospective_adequacy"]
        coverage = prospective_res["prospective_coverage"]

        if adequacy == "FAIL":
            decision = "DEFER"
            reason_code = "INSUFFICIENT_PROSPECTIVE_EVIDENCE"
        elif coverage == "FAIL":
            decision = "DEFER"
            reason_code = "INSUFFICIENT_PROSPECTIVE_COVERAGE"
        elif comp_effect >= ADMIT_THRESHOLD:
            decision = "ADMIT"
            reason_code = "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT"
        elif comp_effect <= REJECT_THRESHOLD:
            decision = "REJECT"
            reason_code = "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT"
        else:
            decision = "DEFER"
            reason_code = "AMBIGUOUS_PROSPECTIVE_EFFECT"

        return {
            "decision": decision,
            "reason_code": reason_code,
            "measured_effect": comp_effect,
            "thresholds": {
                "admit_threshold": ADMIT_THRESHOLD,
                "reject_threshold": REJECT_THRESHOLD,
            },
            "adequacy_status": adequacy,
            "coverage_status": coverage,
            "proposition_id": prop_id,
            "world_id": world_id,
            "timestamp": time.time(),
        }

    @staticmethod
    def classify_defer_origin(
        decision_dict: Dict[str, Any], ground_truth: Dict[str, Any]
    ) -> str:
        """
        Forensic defer causal origin auditor. Does not influence decision.
        """
        sys_dec = decision_dict["decision"]
        sys_reason = decision_dict["reason_code"]

        gt_dec = ground_truth["expected_decision"]
        gt_reason = ground_truth[
            "expected_reason"
        ]  # "EVIDENCE_LIMITED" or "EFFECT_AMBIGUITY"

        if sys_dec != "DEFER":
            return "OTHER_DEFER_MISMATCH"

        if gt_dec == "DEFER":
            if gt_reason == "EVIDENCE_LIMITED":
                if sys_reason in [
                    "INSUFFICIENT_PROSPECTIVE_EVIDENCE",
                    "INSUFFICIENT_PROSPECTIVE_COVERAGE",
                    "FAILED_READINESS",
                ]:
                    return "EXPECTED_EVIDENCE_LIMITED_DEFER"
            elif gt_reason == "EFFECT_AMBIGUITY":
                if sys_reason == "AMBIGUOUS_PROSPECTIVE_EFFECT":
                    return "EXPECTED_EFFECT_AMBIGUITY_DEFER"
        elif gt_dec == "ADMIT":
            if sys_reason == "INSUFFICIENT_PROSPECTIVE_EVIDENCE":
                return "UNEXPECTED_PROSPECTIVE_EVIDENCE_DEFER_ON_ADMIT_WORLD"
            elif sys_reason == "INSUFFICIENT_PROSPECTIVE_COVERAGE":
                return "UNEXPECTED_PROSPECTIVE_COVERAGE_DEFER_ON_ADMIT_WORLD"
            elif sys_reason == "FAILED_READINESS":
                return "UNEXPECTED_READINESS_DEFER_ON_ADMIT_WORLD"
        elif gt_dec == "REJECT":
            if sys_reason == "INSUFFICIENT_PROSPECTIVE_EVIDENCE":
                return "UNEXPECTED_PROSPECTIVE_EVIDENCE_DEFER_ON_REJECT_WORLD"
            elif sys_reason == "INSUFFICIENT_PROSPECTIVE_COVERAGE":
                return "UNEXPECTED_PROSPECTIVE_COVERAGE_DEFER_ON_REJECT_WORLD"
            elif sys_reason == "FAILED_READINESS":
                return "UNEXPECTED_READINESS_DEFER_ON_REJECT_WORLD"

        return "OTHER_DEFER_MISMATCH"
