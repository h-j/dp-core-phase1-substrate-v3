import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from cognition.schemas.proposition.canonical_semantic_proposition import \
    CanonicalSemanticProposition
from cognition.schemas.proposition.market_proposition import \
    CompiledProposition

logger = logging.getLogger(__name__)

CONCEPT_TO_FIELD = {
    "speculative_liquidity": "delivery_pct_5d",
    "net_institutional_flow": "fii_net",
    "net_domestic_flow": "dii_net",
    "sector_relative_strength": "sector_zscore",
    "liquidity_absorption": "liquidity_absorption_rate",
    "asset_price": "close",
    "daily_high": "high",
    "daily_low": "low",
    "volume_state": "volume",
    "volatility_regime": "volatility_regime",
}


class ParameterGrounder:

    DEFAULT_THRESHOLDS = {
        "delivery_pct_5d": {"ELEVATED": 60.0, "DEPRESSED": 40.0},
        "fii_net": {"ELEVATED": 1000.0, "DEPRESSED": -1000.0},
        "dii_net": {"ELEVATED": 500.0, "DEPRESSED": -500.0},
        "sector_zscore": {"ELEVATED": 1.0, "DEPRESSED": -1.0},
        "liquidity_absorption_rate": {"ELEVATED": 60.0, "DEPRESSED": 30.0},
        "volume": {"ELEVATED": 1000000.0, "DEPRESSED": 100000.0},
    }

    def __init__(self):
        self.percentile_groundings_applied = 0
        self.relative_references_resolved = 0

    def ground(
        self,
        canonical: CanonicalSemanticProposition,
        history_df: Optional[pd.DataFrame],
        step: int,
    ) -> CompiledProposition:
        """
        Grounds CanonicalSemanticProposition concepts into explicit Executable CompiledPropositions
        without invoking any LLM.
        """
        # Reset counters per grounding run
        self.percentile_groundings_applied = 0
        self.relative_references_resolved = 0

        # Check semantic compilation success
        if (
            canonical.compiler_provenance.get("status") != "SUCCESS"
            or not canonical.trigger_concept
            or not canonical.target_concept
        ):
            return CompiledProposition(
                theory_id=canonical.theory_id,
                lineage_id=canonical.lineage_id,
                replay_step=step,
                compilation_status="FAILED",
                failure_reason=canonical.compiler_provenance.get(
                    "reason", "Missing concepts or compiler failed."
                ),
                compiler_trace=canonical.compiler_provenance,
            )

        try:
            # 1. Ground Trigger
            trigger_def = self._ground_concept(
                canonical.trigger_concept, history_df, is_target=False
            )

            # 2. Ground Target
            target_def = self._ground_concept(
                canonical.target_concept, history_df, is_target=True
            )

            # 3. Ground Scope
            scope_def = []
            if canonical.scope_concept:
                for sc in canonical.scope_concept:
                    g_scope = self._ground_concept(sc, history_df, is_target=False)
                    if g_scope:
                        scope_def.append(g_scope)

            # 4. Instrument Grounding Trace Metadata
            trace = dict(canonical.compiler_provenance)
            trace["grounding_provenance"] = {
                "grounded_at_step": step,
                "percentile_groundings_applied": self.percentile_groundings_applied,
                "relative_references_resolved": self.relative_references_resolved,
            }

            status = "SUCCESS"
            reason = None
            if not trigger_def or not target_def:
                status = "PARTIAL"
                reason = "Failed to map some semantic concepts to database fields."

            return CompiledProposition(
                theory_id=canonical.theory_id,
                lineage_id=canonical.lineage_id,
                replay_step=step,
                compilation_status=status,
                failure_reason=reason,
                trigger_definition=trigger_def,
                target_definition=target_def,
                scope_definition=scope_def,
                compiler_trace=trace,
            )
        except Exception as e:
            return CompiledProposition(
                theory_id=canonical.theory_id,
                lineage_id=canonical.lineage_id,
                replay_step=step,
                compilation_status="FAILED",
                failure_reason=f"Grounding failure: {str(e)}",
                compiler_trace=canonical.compiler_provenance,
            )

    def _ground_concept(
        self,
        concept_dict: Dict[str, Any],
        history_df: Optional[pd.DataFrame],
        is_target: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if not concept_dict or "concept" not in concept_dict:
            return None

        concept = concept_dict["concept"]
        qualifier = concept_dict.get("qualifier", "")
        lag = concept_dict.get("lag", 0)

        field = CONCEPT_TO_FIELD.get(concept)
        if not field:
            return None

        # Resolve relative comparison references (e.g. close[t] > close[t-1])
        if qualifier in ["GREATER_THAN_PREVIOUS", "LESS_THAN_PREVIOUS"]:
            self.relative_references_resolved += 1
            op = ">" if qualifier == "GREATER_THAN_PREVIOUS" else "<"
            return {
                "operand_left": {"field": field, "time_offset": 0},
                "operator": op,
                "operand_right": {"field": field, "time_offset": -1},
            }

        # Resolve flat price outcome
        if qualifier == "FLAT":
            if is_target:
                return {"field": "outcome", "operator": "==", "value": "flat"}
            return {"field": field, "operator": "==", "value": "flat"}

        # Resolve compression and regime labels
        if qualifier == "COMPRESSED":
            return {"field": field, "operator": "==", "value": "compressed"}
        if qualifier == "EXPANDED":
            return {"field": field, "operator": "==", "value": "expanded"}

        # Resolve volume rolling mean transforms (volume[t] > rolling_mean(volume,20))
        if field == "volume" and qualifier == "ELEVATED":
            self.relative_references_resolved += 1
            return {
                "operand_left": {"field": "volume", "time_offset": 0},
                "operator": ">",
                "operand_right": {
                    "field": "volume",
                    "transform": "ROLLING_MEAN",
                    "window_size": 20,
                    "time_offset": 0,
                },
            }

        # Compute standard thresholds / percentiles
        val = None
        op = "=="
        if qualifier == "ELEVATED":
            op = ">"
            # Ground speculative_liquidity to 85th percentile of delivery_pct_5d
            percentile_rank = 85.0 if field == "delivery_pct_5d" else 80.0
            val = self._compute_percentile(field, percentile_rank, history_df)
            self.percentile_groundings_applied += 1
        elif qualifier == "DEPRESSED":
            op = "<"
            val = self._compute_percentile(field, 20.0, history_df)
            self.percentile_groundings_applied += 1
        else:
            # Default values for mappings
            op = "=="
            val = "normal" if field == "volatility_regime" else 0.5

        if is_target:
            # Return directional outcome mapping
            direction = "up" if op == ">" else "down"
            return {"field": "outcome", "operator": "==", "value": direction}

        res = {"field": field, "operator": op, "value": val}
        if "lag" in concept_dict:
            res["lag"] = lag

        return res

    def _compute_percentile(
        self, field: str, percentile_rank: float, history_df: Optional[pd.DataFrame]
    ) -> float:
        if (
            history_df is not None
            and not history_df.empty
            and field in history_df.columns
        ):
            # Take rolling window of last 60 days
            subset = history_df[field].tail(60).dropna()
            if not subset.empty:
                return float(np.percentile(subset, percentile_rank))

        # Fallback defaults
        defaults = self.DEFAULT_THRESHOLDS.get(field, {})
        qualifier = "ELEVATED" if percentile_rank >= 50.0 else "DEPRESSED"
        return defaults.get(qualifier, 0.5)
