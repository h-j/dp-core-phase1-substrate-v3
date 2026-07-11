import time
from typing import Any, Dict, List, Optional

from flows.minimal_learning_cycle.config import (MIN_COVERAGE,
                                                 MIN_EVIDENCE_COUNT)


class MLCMeasurement:
    @staticmethod
    def is_tautological(prop: Dict[str, Any]) -> bool:
        trigger = prop["trigger_definition"]
        scope = prop["scope_definition"]

        # Check if the trigger field is constrained in the scope
        for s in scope:
            if s["field"] == trigger["field"]:
                return True
        return False

    @staticmethod
    def verify_proposition_compilation(prop: Dict[str, Any]) -> bool:
        """
        Authoring-time specificity invariant check.
        """
        if not prop.get("trigger_definition") or not prop.get("target_definition"):
            return False

        trigger = prop["trigger_definition"]
        target = prop["target_definition"]

        if trigger["field"] == target["field"]:
            return False

        if MLCMeasurement.is_tautological(prop):
            return False

        # Specificity: Trigger/target must be deterministic
        if trigger["operator"] != "==" or target["operator"] != "==":
            return False

        # Contradiction pre-registered
        if not prop.get("contradiction_definition"):
            return False

        return True

    @staticmethod
    def is_prop_active(
        prop: Dict[str, Any],
        exp: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        full_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        trigger = prop["trigger_definition"]
        scope = prop["scope_definition"]

        # Scope context checks
        for s in scope:
            if exp["features"].get(s["field"]) != s["value"]:
                return False

        # Trigger check with lag
        if trigger["lag"] == 1:
            day = exp["day"]
            if day <= 1:
                return False
            history = full_history if full_history is not None else experiences

            # Find the experience of day - 1 safely
            if day - 2 < len(history) and history[day - 2]["day"] == day - 1:
                prev_exp = history[day - 2]
            else:
                prev_exp = None
                for e in history:
                    if e["day"] == day - 1:
                        prev_exp = e
                        break
                if prev_exp is None:
                    return False
            return prev_exp["features"].get(trigger["field"]) == trigger["value"]
        else:
            return exp["features"].get(trigger["field"]) == trigger["value"]

    @staticmethod
    def attribute_experience(
        prop: Dict[str, Any],
        exp: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        window_id: str,
        full_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Runtime specificity attribution. Enforces mutual exclusivity of attribution classes.
        """
        trigger = prop["trigger_definition"]
        target = prop["target_definition"]
        contra = prop["contradiction_definition"]

        active = MLCMeasurement.is_prop_active(prop, exp, experiences, full_history)

        scope_context = {}
        for s in prop["scope_definition"]:
            scope_context[s["field"]] = exp["features"].get(s["field"]) == s["value"]

        if not active:
            # For a non-activated proposition: no outcome attribution may be generated.
            return {
                "experience_id": exp["experience_id"],
                "proposition_id": prop["proposition_id"],
                "window_id": window_id,
                "trigger_activated": False,
                "target_outcome": exp["outcome"],
                "attribution_class": "NONE",
                "support": 0.0,
                "contradiction": 0.0,
                "inconclusive": 0.0,
                "scope_context": scope_context,
            }

        # Proposition is activated: support + contradiction + inconclusive = 1
        support = 0.0
        contradiction = 0.0
        inconclusive = 0.0

        # We check target match (support) vs contradiction match
        if exp["outcome"] == target["value"]:
            support = 1.0
            attr_class = "SUPPORT"
        elif exp["outcome"] == contra["value"]:
            contradiction = 1.0
            attr_class = "CONTRADICTION"
        else:
            inconclusive = 1.0
            attr_class = "INCONCLUSIVE"

        return {
            "experience_id": exp["experience_id"],
            "proposition_id": prop["proposition_id"],
            "window_id": window_id,
            "trigger_activated": True,
            "target_outcome": exp["outcome"],
            "attribution_class": attr_class,
            "support": support,
            "contradiction": contradiction,
            "inconclusive": inconclusive,
            "scope_context": scope_context,
        }

    @staticmethod
    def compute_metrics(
        prop: Dict[str, Any],
        experiences: List[Dict[str, Any]],
        window_id: str,
        full_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Shared measurement function. Computes comparison-agnostic intrinsic measurements.
        """
        total_count = len(experiences)
        if total_count == 0:
            return {
                "activation_count": 0,
                "support_count": 0,
                "contradiction_count": 0,
                "inconclusive_count": 0,
                "sample_adequacy": False,
                "coverage": 0.0,
                "stability": 0.0,
                "complexity": prop["complexity_cost"],
                "equivalence": False,
                "redundancy": False,
            }

        support_count = 0
        contradiction_count = 0
        inconclusive_count = 0
        activation_count = 0

        # Split half lists for stability
        half_len = total_count // 2
        first_half = experiences[:half_len]
        second_half = experiences[half_len:]

        success_first = 0
        act_first = 0
        success_second = 0
        act_second = 0

        target_val = prop["target_definition"]["value"]

        for idx, exp in enumerate(experiences):
            attr = MLCMeasurement.attribute_experience(
                prop, exp, experiences, window_id, full_history
            )
            if attr["trigger_activated"]:
                activation_count += 1
                if attr["attribution_class"] == "SUPPORT":
                    support_count += 1
                elif attr["attribution_class"] == "CONTRADICTION":
                    contradiction_count += 1
                else:
                    inconclusive_count += 1

                # Collect split halves stats
                if idx < half_len:
                    act_first += 1
                    if attr["attribution_class"] == "SUPPORT":
                        success_first += 1
                else:
                    act_second += 1
                    if attr["attribution_class"] == "SUPPORT":
                        success_second += 1

        p1 = (success_first / act_first) if act_first > 0 else 0.50
        p2 = (success_second / act_second) if act_second > 0 else 0.50
        stability = 1.0 - abs(p1 - p2)

        coverage = activation_count / total_count
        sample_adequacy = activation_count >= MIN_EVIDENCE_COUNT

        return {
            "activation_count": activation_count,
            "support_count": support_count,
            "contradiction_count": contradiction_count,
            "inconclusive_count": inconclusive_count,
            "sample_adequacy": sample_adequacy,
            "coverage": round(coverage, 4),
            "stability": round(stability, 4),
            "complexity": prop["complexity_cost"],
            "equivalence": False,
            "redundancy": False,
        }
