from typing import Any, Dict, List, Optional, Tuple


class OntologyRegistry:
    ONTOLOGY_VERSION = "1.0.0"
    VALIDATION_TAXONOMY_VERSION = "1.0.0"

    # Runtime categorical vocabularies
    REGIME_SUBTYPE = [
        "neutral",
        "fatigue",
        "pressure_loaded_range",
        "pressure_loaded",
        "liquidity_constrained",
        "expansion_confirmed",
    ]

    VOLUME_STATE = ["dry", "normal", "elevated", "spike"]

    VOLATILITY_REGIME = ["compressed", "expanded", "normal"]

    MOMENTUM_REGIME = ["strengthening", "weakening", "flat"]

    PARTICIPATION_STRENGTH = ["weak", "normal", "strong"]

    PARTICIPATION_CONFIRMATION = [
        "bullish_confirmed",
        "bearish_confirmed",
        "divergence",
        "weak_move",
        "normal",
    ]

    TREND_STATE = [
        "extended_higher",
        "closed_higher",
        "extended_lower",
        "closed_lower",
        "range_bound",
    ]

    LIQUIDITY_STATE = [
        "ample_with_strength",
        "ample_with_selling",
        "broad_participation",
        "even_flow",
        "concentrated_in_large_caps",
        "selective",
    ]

    BREADTH_STATE = [
        "strongly_participatory",
        "strengthened",
        "mixed",
        "weakened",
        "deteriorated",
        "nascent",
    ]

    CORE_CONCEPTS = [
        "TREND_PERSISTENCE",
        "VOLATILITY_EXPANSION",
        "VOLATILITY_COMPRESSION",
        "LIQUIDITY_ABSORPTION",
        "INSTITUTIONAL_ACCUMULATION",
        "MEAN_REVERSION",
        "MOMENTUM",
        "BREAKOUT_VALIDATION",
        "BREAKOUT_FAILURE",
        "DELIVERY_EXHAUSTION",
    ]

    RELATION_TYPES = [
        "AMPLIFIES",
        "DAMPENS",
        "CONTRADICTS",
        "DEPENDS_ON",
        "CO-OCCURS_WITH",
    ]

    EXPLANATORY_CONSTRAINTS = [
        "HIGH_UNCERTAINTY",
        "LOW_LIQUIDITY",
        "TRANSITION_REGIME",
        "WEAK_PARTICIPATION",
        "BULLISH_PRESSURE",
        "BEARISH_PRESSURE",
        "HIGH_VOLATILITY",
    ]

    APPLICABLE_REGIMES = ["range_bound", "trend", "breakout", "fatigue", "neutral"]

    # Global tracking counters for taxonomy compliance
    _theory_components_checked = 0
    _theory_components_valid = 0
    _mechanism_components_checked = 0
    _mechanism_components_valid = 0
    _principle_filters_checked = 0
    _principle_filters_valid = 0
    _rejected_filters_count = 0
    _regenerated_filters_count = 0
    _unknown_ontology_values = set()

    @classmethod
    def reset_metrics(cls):
        cls._theory_components_checked = 0
        cls._theory_components_valid = 0
        cls._mechanism_components_checked = 0
        cls._mechanism_components_valid = 0
        cls._principle_filters_checked = 0
        cls._principle_filters_valid = 0
        cls._rejected_filters_count = 0
        cls._regenerated_filters_count = 0
        cls._unknown_ontology_values = set()

    @classmethod
    def track_theory_components(cls, checked: int, valid: int):
        cls._theory_components_checked += checked
        cls._theory_components_valid += valid

    @classmethod
    def track_mechanism_components(cls, checked: int, valid: int):
        cls._mechanism_components_checked += checked
        cls._mechanism_components_valid += valid

    @classmethod
    def track_principle_filters(cls, checked: int, valid: int):
        cls._principle_filters_checked += checked
        cls._principle_filters_valid += valid

    @classmethod
    def track_filter_rejected(cls):
        cls._rejected_filters_count += 1

    @classmethod
    def track_filter_regenerated(cls):
        cls._regenerated_filters_count += 1

    @classmethod
    def track_unknown_value(cls, val: str):
        cls._unknown_ontology_values.add(val)

    @classmethod
    def validate_filter(cls, filter_dict: dict) -> Tuple[bool, Optional[str]]:
        """
        Validates that the keys and values in the applicability filter conform to the OntologyRegistry.
        Returns (is_valid, error_message).
        """
        if not isinstance(filter_dict, dict):
            return False, f"Filter must be a dictionary, got {type(filter_dict)}"

        allowed_keys = {
            "regime_subtype": cls.REGIME_SUBTYPE,
            "volatility_regime": cls.VOLATILITY_REGIME,
            "volume_state": cls.VOLUME_STATE,
            "momentum_regime": cls.MOMENTUM_REGIME,
        }

        for k, v in filter_dict.items():
            if k not in allowed_keys:
                cls.track_unknown_value(f"key:{k}")
                return (
                    False,
                    f"Key '{k}' is not a valid applicability filter dimension. Choose from: {list(allowed_keys.keys())}",
                )

            # We accept a list, set, tuple, string, None, "all", or "null"
            values_to_check = []
            if isinstance(v, (list, tuple, set)):
                values_to_check = list(v)
            else:
                values_to_check = [v]

            for val in values_to_check:
                if (
                    val is not None
                    and val != "all"
                    and val != "null"
                    and val not in allowed_keys[k]
                ):
                    cls.track_unknown_value(str(val))
                    return (
                        False,
                        f"Value '{val}' for key '{k}' is not in the allowed ontology list: {allowed_keys[k]}.",
                    )

        return True, None

    @classmethod
    def get_applicability_filter_snippet(cls) -> str:
        """Returns prompt snippet for dynamic inject of allowed applicability filter taxonomies."""
        return f"""
ONTOLOGY TAXONOMY CONTRACT:
When generating values for applicability_filter, choose EXACTLY from:
- "regime_subtype": Choose exactly one of: {cls.REGIME_SUBTYPE}
- "volatility_regime": Choose exactly one of: {cls.VOLATILITY_REGIME}
- "volume_state": Choose exactly one of: {cls.VOLUME_STATE}
- "momentum_regime": Choose exactly one of: {cls.MOMENTUM_REGIME}

You may also use "all" to match any state in a dimension, or omit the key/set to null if not filtered.
Do NOT generate free-form categories or synonyms (e.g. do not use "low", "high", "momentum", "range_bound", "moderate").
"""
