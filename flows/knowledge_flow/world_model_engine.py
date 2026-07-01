import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

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

    def synthesize(self, active_principles: List[Principle], step: int) -> WorldModel:
        """
        Synthesizes active principles into narrative descriptions and extracts structured regime constraints.
        """
        from cognition.schemas.knowledge.principle import PrincipleStatus

        # Filter to Trusted and Canonical principles primarily
        trusted_canonical = [
            p for p in active_principles
            if p.status in [PrincipleStatus.TRUSTED, PrincipleStatus.CANONICAL]
        ]
        # Fall back to emerging/active if none exist yet to prevent cold start emptiness
        principles_to_use = trusted_canonical if trusted_canonical else active_principles

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
                applicable_regimes=[]
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

        # Unified Narrative and Constraints Synthesis Prompt
        prompt = f"""You are the World Model Engine of an agentic cognitive system.
Your goal is to synthesize active trusted principles into a cohesive matured world model representing the market dynamics.

=== ACTIVE TRUSTED PRINCIPLES ===
{principles_text}

=== INSTRUCTIONS ===
1. Generate a "narrative_summary" paragraph describing the physical market structure and active forces.
2. Extract "dominant_mechanisms" backed by these principles (e.g. Institutional accumulation, Weak retail participation).
3. Map "active_constraints" (e.g. Avoid bullish bias, Cap confidence at 45%, Expect failed breakout) to specific regime subtypes.
4. Extract "regime_constraints" overrides mapping regime subtypes to details:
   - "blocked_bias": "bullish", "bearish", or "neutral"
   - "max_confidence": float
5. List "applicable_regimes" based on the applicability filters of the principles.
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
        "max_confidence": 0.45,
        "supporting_principles": ["principle-id"]
     }}
  ],
  "regime_constraints": {{
     "range_bound": {{
        "blocked_bias": "bullish",
        "max_confidence": 0.45
     }}
  }},
  "applicable_regimes": ["range_bound", "trend"],
  "stability": "Stable"
}}
"""
        narrative_summary = "Grounded world model narrative description."
        regime_constraints = {}
        dominant_mechanisms = []
        active_constraints = []
        applicable_regimes = []
        stability = "Emerging"
        confidence = 0.5
        evidence_count = 0

        # Calculate stats
        if principles_to_use:
            confidence = sum(p.confidence for p in principles_to_use) / len(principles_to_use)
            evidence_count = sum(p.support_count for p in principles_to_use)
            avg_age = sum(p.stability_age for p in principles_to_use) / len(principles_to_use)
            if avg_age > 15:
                stability = "Matured"
            elif avg_age > 5:
                stability = "Stable"
            else:
                stability = "Emerging"

        try:
            res_raw = self.client.generate(prompt, json_format=True)
            res = json.loads(res_raw)
            narrative_summary = res.get("narrative_summary", narrative_summary)
            regime_constraints = res.get("regime_constraints", regime_constraints)
            dominant_mechanisms = res.get("dominant_mechanisms", dominant_mechanisms)
            active_constraints = res.get("active_constraints", active_constraints)
            applicable_regimes = res.get("applicable_regimes", applicable_regimes)
            stability = res.get("stability", stability)
        except Exception as e:
            print(f"WARNING: Unified world model synthesis failed: {e}")

        # Grounding: ensure supporting_canonical_principles holds the statements of canonical principles
        supporting_canonical_principles = [
            p.statement for p in principles_to_use
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
        )
