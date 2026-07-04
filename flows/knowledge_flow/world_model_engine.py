import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from cognition.schemas.knowledge.ontology import OntologyRegistry
from cognition.schemas.knowledge.principle import Principle
from cognition.schemas.knowledge.world_model import WorldModel
from interfaces.ollama_client import OllamaClient


class WorldModelEngine:
    """
    Consolidates active principles into narrative system descriptions
    and extracts structured regime constraints for deterministicOverrides.
    """

    def __init__(self, llm_client=None):
        self.client = llm_client if llm_client else OllamaClient()

    def synthesize(
        self,
        active_principles: List[Principle],
        step: int,
        decision_metrics: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Synthesizes active principles into narrative descriptions and extracts structured regime constraints.
        """
        from cognition.schemas.knowledge.principle import PrincipleStatus

        # Filter to Trusted and Canonical principles primarily
        trusted_canonical = [
            p
            for p in active_principles
            if p.status in [PrincipleStatus.TRUSTED, PrincipleStatus.CANONICAL]
        ]
        # Fall back to emerging/active if none exist yet to prevent cold start emptiness
        principles_to_use = (
            trusted_canonical if trusted_canonical else active_principles
        )

        if not principles_to_use:
            return WorldModel(
                step=step,
                narrative_summary="Baseline world model. No active principles recorded yet.",
                active_principle_ids=[],
                regime_constraints={},
                dominant_mechanisms=[],
                active_constraints=[],
                supporting_canonical_principles=[],
                confidence=0.5,
                stability="Emerging",
                evidence_count=0,
                applicable_regimes=[],
            )

        principles_list = [
            {
                "id": p.id,
                "statement": p.statement,
                "status": p.status.value,
                "falsifiable_predictions": [
                    fp.to_dict() for fp in p.falsifiable_predictions
                ],
            }
            for p in principles_to_use
        ]
        principles_text = json.dumps(principles_list, indent=2)

        metrics_text = ""
        if decision_metrics:
            metrics_text = f"\n=== DECISION INTELLIGENCE METRICS ===\n{json.dumps(decision_metrics, indent=2)}\n"

        # Unified Narrative and Constraints Synthesis Prompt
        prompt = f"""You are the World Model Engine of an agentic cognitive system.
Your goal is to synthesize active trusted principles into a cohesive matured world model representing the market dynamics.
{metrics_text}
=== ACTIVE TRUSTED PRINCIPLES ===
{principles_text}

=== INSTRUCTIONS ===
1. Generate a "narrative_summary" paragraph describing the physical market structure and active forces.
2. Extract "dominant_mechanisms" backed by these principles (e.g. Institutional accumulation, Weak retail participation).
3. Map "active_constraints" describing constraints associated with the principles.
4. Extract "explanatory_constraints": A list of descriptive constraint tokens chosen EXACTLY from: {OntologyRegistry.EXPLANATORY_CONSTRAINTS}.
5. List "applicable_regimes" based on the applicability filters of the principles, chosen EXACTLY from: {OntologyRegistry.APPLICABLE_REGIMES}.
6. Rate the world model "stability" as "Emerging", "Stable", or "Matured" based on the age/stability of the principles.

Respond STRICTLY in JSON format with the following keys:
{{
  "narrative_summary": "The narrative text...",
  "dominant_mechanisms": [
     {{
        "mechanism": "Mechanism name",
        "description": "Mechanism explanation",
        "supporting_principles": ["principle-id"]
     }}
  ],
  "active_constraints": [
     {{
        "regime_subtype": "regime name",
        "constraint": "Description of constraint",
        "supporting_principles": ["principle-id"]
     }}
  ],
  "explanatory_constraints": ["HIGH_UNCERTAINTY", "TRANSITION_REGIME"],
  "applicable_regimes": ["range_bound", "trend"],
  "stability": "Stable"
}}
"""
        narrative_summary = "Grounded world model narrative description."
        dominant_mechanisms = []
        active_constraints = []
        applicable_regimes = []
        explanatory_constraints = []
        stability = "Emerging"
        confidence = 0.5
        evidence_count = 0

        # Calculate stats
        if principles_to_use:
            confidence = sum(p.confidence for p in principles_to_use) / len(
                principles_to_use
            )
            evidence_count = sum(p.support_count for p in principles_to_use)
            avg_age = sum(p.stability_age for p in principles_to_use) / len(
                principles_to_use
            )
            if avg_age > 15:
                stability = "Matured"
            elif avg_age > 5:
                stability = "Stable"
            else:
                stability = "Emerging"

        max_attempts = 3
        attempt = 0
        is_valid = False
        res = {}
        validation_errors = []
        while attempt < max_attempts:
            try:
                res_raw = self.client.generate(prompt, json_format=True)
                res = json.loads(res_raw)

                # Check compliance of explanatory_constraints and applicable_regimes
                exp_c = res.get("explanatory_constraints", [])
                app_r = res.get("applicable_regimes", [])

                all_ok = True
                errors = []
                for c in exp_c:
                    if c not in OntologyRegistry.EXPLANATORY_CONSTRAINTS:
                        all_ok = False
                        errors.append(
                            f"Explanatory constraint '{c}' not in allowed list."
                        )
                for r in app_r:
                    if r not in OntologyRegistry.APPLICABLE_REGIMES:
                        all_ok = False
                        errors.append(f"Applicable regime '{r}' not in allowed list.")

                if all_ok:
                    is_valid = True
                    break
                else:
                    validation_errors = errors
            except Exception as e:
                validation_errors = [str(e)]

            attempt += 1
            prompt = (
                prompt
                + f"\n\nONTOLOGY VALIDATION FAILURE ON ATTEMPT {attempt}: {validation_errors}. Please choose exactly from allowed taxonomy lists."
            )

        if is_valid:
            narrative_summary = res.get("narrative_summary", narrative_summary)
            dominant_mechanisms = res.get("dominant_mechanisms", dominant_mechanisms)
            active_constraints = res.get("active_constraints", active_constraints)
            explanatory_constraints = res.get(
                "explanatory_constraints", explanatory_constraints
            )
            applicable_regimes = res.get("applicable_regimes", applicable_regimes)
            stability = res.get("stability", stability)
        else:
            print(
                f"WARNING: Unified world model synthesis failed ontology compliance: {validation_errors}"
            )

        # Convert descriptive explanatory constraints to deterministic limits mapping
        regime_constraints = (
            res.get("regime_constraints", {})
            if "res" in locals() and isinstance(res, dict)
            else {}
        )
        for c in explanatory_constraints:
            c_upper = c.upper()
            for regime in ["range_bound", "trend", "breakout", "fatigue", "neutral"]:
                if regime not in regime_constraints:
                    regime_constraints[regime] = {
                        "blocked_bias": "neutral",
                        "max_confidence": 0.90,
                    }
                if "HIGH_UNCERTAINTY" in c_upper or "WEAK_PARTICIPATION" in c_upper:
                    regime_constraints[regime]["max_confidence"] = min(
                        regime_constraints[regime]["max_confidence"], 0.45
                    )
                if "TRANSITION" in c_upper or "TRANSITION_REGIME" in c_upper:
                    regime_constraints[regime]["max_confidence"] = min(
                        regime_constraints[regime]["max_confidence"], 0.40
                    )
                if "LOW_LIQUIDITY" in c_upper or "LIQUIDITY_CONSTRAINED" in c_upper:
                    regime_constraints[regime]["max_confidence"] = min(
                        regime_constraints[regime]["max_confidence"], 0.42
                    )
                    regime_constraints[regime]["blocked_bias"] = "bullish"
                if "BEARISH_DOMINANT" in c_upper or "BEARISH_PRESSURE" in c_upper:
                    regime_constraints[regime]["blocked_bias"] = "bullish"
                if "BULLISH_DOMINANT" in c_upper or "BULLISH_PRESSURE" in c_upper:
                    regime_constraints[regime]["blocked_bias"] = "bearish"

        # Grounding: ensure supporting_canonical_principles holds the statements of canonical principles
        supporting_canonical_principles = [
            p.statement
            for p in principles_to_use
            if p.status == PrincipleStatus.CANONICAL
        ]

        return WorldModel(
            step=step,
            narrative_summary=narrative_summary,
            active_principle_ids=[p.id for p in principles_to_use],
            regime_constraints=regime_constraints,
            dominant_mechanisms=dominant_mechanisms,
            active_constraints=active_constraints,
            supporting_canonical_principles=supporting_canonical_principles,
            confidence=round(confidence, 3),
            stability=stability,
            evidence_count=evidence_count,
            applicable_regimes=applicable_regimes,
            explanatory_constraints=explanatory_constraints,
        )
