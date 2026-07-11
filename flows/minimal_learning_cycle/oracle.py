import time
from typing import Any, Dict


class B4Oracle:
    @staticmethod
    def make_decision(
        prop_id: str, world_id: str, ground_truth: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        B4 Oracle baseline. Reads hidden ex-ante world generation records.
        """
        decision = ground_truth["expected_decision"]
        reason = ground_truth["expected_reason"]

        # Format reason code based on oracle outputs
        if decision == "ADMIT":
            reason_code = "ORACLE_ADMIT"
        elif decision == "REJECT":
            reason_code = "ORACLE_REJECT"
        else:
            if reason == "EVIDENCE_LIMITED":
                reason_code = "ORACLE_DEFER_EVIDENCE_LIMITED"
            else:
                reason_code = "ORACLE_DEFER_EFFECT_AMBIGUITY"

        return {
            "decision": decision,
            "reason_code": reason_code,
            "measured_effect": 0.0,
            "thresholds": {},
            "adequacy_status": "PASS",
            "coverage_status": "PASS",
            "proposition_id": prop_id,
            "world_id": world_id,
            "timestamp": time.time(),
        }
