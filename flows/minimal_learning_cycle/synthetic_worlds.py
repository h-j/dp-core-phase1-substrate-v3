import random
from typing import Any, Dict, List, Optional

from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD,
                                                 REJECT_THRESHOLD)


class SealedWindow:
    def __init__(self, data: List[Dict[str, Any]]):
        self._data = data
        self._sealed = True

    def unseal(self):
        self._sealed = False

    def _check_access(self):
        if self._sealed:
            raise PermissionError(
                "Access to Window 3 is sealed until ERC prospective validation authorization is completed."
            )

    def __getitem__(self, item):
        self._check_access()
        return self._data[item]

    def __iter__(self):
        self._check_access()
        return iter(self._data)

    def __len__(self):
        self._check_access()
        return len(self._data)


class MLCSyntheticWorld:
    @staticmethod
    def generate_world(family: str, seed: int) -> Dict[str, Any]:
        """
        Generates a synthetic world for MLC v0.1.
        Families:
        - "A" (ADMIT): true comparative effect >= ADMIT_THRESHOLD
        - "B" (REJECT): true comparative effect <= REJECT_THRESHOLD
        - "C1" (DEFER_EVIDENCE_LIMITED): trigger probability is very low
        - "C2" (DEFER_EFFECT_AMBIGUITY): comparative effect in (REJECT_THRESHOLD, ADMIT_THRESHOLD)
        """
        random.seed(seed)
        num_features = 10
        experiences = []

        trigger_idx = 0

        # P(F_i == 1) defaults to 0.50
        # For Family C1, trigger F_0 is extremely rare
        p_trigger = 0.01 if family == "C1" else 0.50

        # Outcome probability Y0 conditional on F_0 == 1
        if family == "A":
            p_y0_active = 0.85
            p_y0_control = 0.50
            expected_decision = "ADMIT"
            expected_reason = "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT"
        elif family == "B":
            p_y0_active = 0.15
            p_y0_control = 0.50
            expected_decision = "REJECT"
            expected_reason = "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT"
        elif family == "C1":
            p_y0_active = 0.85
            p_y0_control = 0.50
            expected_decision = "DEFER"
            expected_reason = "EVIDENCE_LIMITED"
        elif family == "C2":
            # Effect lies in the ambiguity interval (-0.05, 0.15). E.g. lift is 0.05.
            p_y0_active = 0.55
            p_y0_control = 0.50
            expected_decision = "DEFER"
            expected_reason = "EFFECT_AMBIGUITY"
        else:
            raise ValueError(f"Unknown family: {family}")

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

        # Map experiences to anonymized names
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

        # Define the three strictly isolated windows
        # Window 1: days 1-200 (Formation)
        # Window 2: days 201-600 (Evidence)
        # Window 3: days 601-1000 (Prospective Validation)
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
