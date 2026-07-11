from typing import Any, Dict, List

from flows.minimal_learning_cycle.config import (MIN_COVERAGE,
                                                 MIN_EVIDENCE_COUNT)
from flows.minimal_learning_cycle.measurement import MLCMeasurement


class MLCProspectiveValidation:
    @staticmethod
    def evaluate(
        prop: Dict[str, Any],
        prospective_experiences: List[Dict[str, Any]],
        full_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Prospective validation using Window 3 only.
        """
        n_act = 0
        n_act_target = 0
        n_ctrl = 0
        n_ctrl_target = 0

        target = prop["target_definition"]

        for exp in prospective_experiences:
            # Check activation
            active = MLCMeasurement.is_prop_active(
                prop, exp, prospective_experiences, full_history
            )

            if active:
                n_act += 1
                if exp["outcome"] == target["value"]:
                    n_act_target += 1
            else:
                n_ctrl += 1
                if exp["outcome"] == target["value"]:
                    n_ctrl_target += 1

        candidate_effect = (n_act_target / n_act) if n_act > 0 else 0.50
        control_effect = (n_ctrl_target / n_ctrl) if n_ctrl > 0 else 0.50
        comparative_effect = candidate_effect - control_effect

        total_count = len(prospective_experiences)
        coverage = (n_act / total_count) if total_count > 0 else 0.0

        prospective_adequacy = "PASS" if n_act >= MIN_EVIDENCE_COUNT else "FAIL"
        prospective_coverage = "PASS" if coverage >= MIN_COVERAGE else "FAIL"

        return {
            "candidate_effect": round(candidate_effect, 4),
            "control_effect": round(control_effect, 4),
            "comparative_effect": round(comparative_effect, 4),
            "prospective_adequacy": prospective_adequacy,
            "prospective_coverage": prospective_coverage,
            "active_count": n_act,
            "control_count": n_ctrl,
        }
