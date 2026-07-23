from typing import Any, Dict, List, Tuple


from flows.minimal_learning_cycle.config import MIN_COVERAGE
from flows.minimal_learning_cycle.measurement import MLCMeasurement


class MLCReadiness:
    @staticmethod
    def check_readiness(
        prop: Dict[str, Any], intrinsic_metrics: Dict[str, Any]
    ) -> Tuple[bool, str]:
        # 1. Specificity validity check
        if not MLCMeasurement.verify_proposition_compilation(prop):
            return False, "FAIL_SPECIFICITY_INVALID"

        # 2. Sample adequacy check
        if not intrinsic_metrics.get("sample_adequacy"):
            return False, "FAIL_SAMPLE_ADEQUACY"

        # 3. Minimum coverage check
        if intrinsic_metrics.get("coverage", 0.0) < MIN_COVERAGE:
            return False, "FAIL_MINIMUM_COVERAGE"

        return True, "READY"


# Fix imports
Tuple = Any
