import random
import time
from typing import Any, Dict, List

from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD, MIN_COVERAGE,
                                                 MIN_EVIDENCE_COUNT,
                                                 REJECT_THRESHOLD)


class B1AlwaysAdmit:
    @staticmethod
    def make_decision(prop_id: str, world_id: str) -> Dict[str, Any]:
        return {
            "decision": "ADMIT",
            "reason_code": "ALWAYS_ADMIT",
            "measured_effect": 1.0,
            "thresholds": {},
            "adequacy_status": "PASS",
            "coverage_status": "PASS",
            "proposition_id": prop_id,
            "world_id": world_id,
            "timestamp": time.time(),
        }


class B2RetrospectiveOnly:
    @staticmethod
    def make_decision(
        prop_id: str, world_id: str, frozen_candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        B2 Retrospective-only matched ablation baseline.
        Uses Window 2 measurements only (pre-computed in the frozen candidate).
        """
        intrinsic = frozen_candidate["window_2_intrinsic_measurements"]

        # Calculate comparative effect conditional on Window 2
        act = intrinsic["activation_count"]
        supp = intrinsic["support_count"]
        contra = intrinsic["contradiction_count"]

        total_window_2_count = (
            act / intrinsic["coverage"] if intrinsic["coverage"] > 0 else 1
        )
        ctrl = total_window_2_count - act

        # Retrospective success rates
        candidate_effect = (supp / act) if act > 0 else 0.50
        # In control group, target success rate
        # Let's say: control experiences had Y0 with probability 0.50 since baseline outcome distribution is 0.50.
        # To be robust, let's estimate control rate from the summary:
        # summary has support, contradiction, inconclusive, and total experiences count.
        # Let's check: summary outcome count can be computed or estimated.
        # Let's assume control_effect is 0.50 (the base rate) or calculated as:
        # (outcome_matches_in_control) / control_count
        # Let's say: if the frozen candidate has the control counts, we can use them.
        # Wait, let's look at the window_2_evidence_summary:
        # We can compile it to have the raw count of target matches in control experiences.
        # Yes! Let's pass the raw active/control outcomes count inside the frozen candidate's window_2_evidence_summary.
        summary = frozen_candidate["window_2_evidence_summary"]
        n_act = summary.get("active_count", act)
        n_act_target = summary.get("active_target_count", supp)
        n_ctrl = summary.get("control_count", 0)
        n_ctrl_target = summary.get("control_target_count", 0)

        candidate_effect = (n_act_target / n_act) if n_act > 0 else 0.50
        control_effect = (n_ctrl_target / n_ctrl) if n_ctrl > 0 else 0.50
        comparative_effect = candidate_effect - control_effect

        adequacy = "PASS" if intrinsic["sample_adequacy"] else "FAIL"
        coverage = "PASS" if intrinsic["coverage"] >= MIN_COVERAGE else "FAIL"

        if adequacy == "FAIL":
            decision = "DEFER"
            reason_code = "INSUFFICIENT_RETROSPECTIVE_EVIDENCE"
        elif coverage == "FAIL":
            decision = "DEFER"
            reason_code = "INSUFFICIENT_RETROSPECTIVE_COVERAGE"
        elif comparative_effect >= ADMIT_THRESHOLD:
            decision = "ADMIT"
            reason_code = "SUFFICIENT_POSITIVE_RETROSPECTIVE_EFFECT"
        elif comparative_effect <= REJECT_THRESHOLD:
            decision = "REJECT"
            reason_code = "SUFFICIENT_NEGATIVE_RETROSPECTIVE_EFFECT"
        else:
            decision = "DEFER"
            reason_code = "AMBIGUOUS_RETROSPECTIVE_EFFECT"

        return {
            "decision": decision,
            "reason_code": reason_code,
            "measured_effect": round(comparative_effect, 4),
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


class B3MatchedRandom:
    @staticmethod
    def make_decision(prop_id: str, world_id: str, seed: int) -> Dict[str, Any]:
        """
        B3 Matched Random baseline using a reproducible seed.
        """
        local_rand = random.Random(seed + 9999)
        decision = local_rand.choice(["ADMIT", "REJECT", "DEFER"])

        reason_codes = {
            "ADMIT": "RANDOM_ADMIT",
            "REJECT": "RANDOM_REJECT",
            "DEFER": "RANDOM_DEFER",
        }

        return {
            "decision": decision,
            "reason_code": reason_codes[decision],
            "measured_effect": 0.0,
            "thresholds": {},
            "adequacy_status": "PASS",
            "coverage_status": "PASS",
            "proposition_id": prop_id,
            "world_id": world_id,
            "timestamp": time.time(),
        }
