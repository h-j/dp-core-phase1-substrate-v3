import hashlib
import json
import time
from typing import Any, Dict


class MLCCandidateFreeze:
    @staticmethod
    def freeze(
        prop: Dict[str, Any],
        intrinsic_metrics: Dict[str, Any],
        evidence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Freezes the evaluation candidate and returns an immutable frozen representation with SHA-256 hash.
        """
        # Create deep copy of definition fields to ensure immutability
        frozen_prop_def = json.loads(json.dumps(prop))

        # Serialize the proposition definition deterministically to compute the hash
        serialized_def = json.dumps(frozen_prop_def, sort_keys=True)
        sha256_hash = hashlib.sha256(serialized_def.encode("utf-8")).hexdigest()

        frozen_candidate = {
            "proposition_definition": frozen_prop_def,
            "contradiction_definition": frozen_prop_def["contradiction_definition"],
            "specificity_definition": frozen_prop_def["specificity_definition"],
            "window_2_evidence_summary": json.loads(json.dumps(evidence_summary)),
            "window_2_intrinsic_measurements": json.loads(
                json.dumps(intrinsic_metrics)
            ),
            "threshold_configuration_version": "v0.1_frozen",
            "measurement_function_version": "v0.1_frozen",
            "attribution_function_version": "v0.1_frozen",
            "freeze_timestamp": time.time(),
            "content_hash": sha256_hash,
        }

        return frozen_candidate
