import time
from typing import Any, Dict, List

from flows.minimal_learning_cycle.config import (COMPILATION_ADMISSION_BUDGET,
                                                 EVIDENCE_ACCUMULATION_BUDGET,
                                                 VALIDATION_BUDGET)


class ERCController:
    def __init__(self):
        self.budgets = {
            "COMPILATION": COMPILATION_ADMISSION_BUDGET,
            "EVIDENCE": EVIDENCE_ACCUMULATION_BUDGET,
            "VALIDATION": VALIDATION_BUDGET,
        }
        self.logs: List[Dict[str, Any]] = []
        self.request_counter = 0

    def check_and_deduct(
        self, resource_type: str, proposition_id: str, cost: int
    ) -> bool:
        """
        Authoritative budget check. Returns True if authorized, False otherwise.
        """
        self.request_counter += 1
        request_id = f"REQ_{self.request_counter:04d}"

        if resource_type not in self.budgets:
            raise ValueError(f"Unknown resource type: {resource_type}")

        before = self.budgets[resource_type]
        authorized = before >= cost

        if authorized:
            self.budgets[resource_type] -= cost
            after = self.budgets[resource_type]
            decision = "AUTHORIZED"
            reason_code = "BUDGET_AVAILABLE"
        else:
            after = before
            decision = "REJECTED"
            reason_code = "BUDGET_EXHAUSTED"

        log_entry = {
            "request_id": request_id,
            "resource_type": resource_type,
            "proposition_id": proposition_id,
            "requested_cost": cost,
            "available_budget_before": before,
            "authorization_decision": decision,
            "available_budget_after": after,
            "reason_code": reason_code,
            "timestamp": time.time(),
        }
        self.logs.append(log_entry)

        return authorized
