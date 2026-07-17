import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from cognition.schemas.proposition.canonical_semantic_proposition import \
    CanonicalSemanticProposition
from cognition.schemas.theory.theory import Theory
from interfaces.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class SemanticCompiler:

    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient(temperature=0.0, seed=42)

    def compile(self, theory: Theory) -> CanonicalSemanticProposition:
        """
        Translates a natural language Theory into a threshold-independent
        CanonicalSemanticProposition object.
        """
        # Build text inputs
        thesis_text = theory.thesis or ""
        summary_text = theory.summary or ""
        claim_text = (
            theory.summary_structured.claim if theory.summary_structured else ""
        )

        prompt = f"""You are the DP Canonical Semantic Proposition Compiler.
Your goal is to parse a semantic market theory and compile it into a threshold-independent Canonical Semantic Proposition.
Do NOT invent or output numeric thresholds, quantiles, z-scores, or hardcoded values.

=== SEMANTIC THEORY ===
Thesis: {thesis_text}
Summary: {summary_text}
Claim: {claim_text}

=== AVAILABLE CONCEPTS CATALOG ===
- "speculative_liquidity" (representing delivery percentage)
- "net_institutional_flow" (representing FII/DII net flows)
- "net_domestic_flow" (representing domestic/retail participation)
- "sector_relative_strength" (representing sector zscore or relative strength)
- "liquidity_absorption" (representing market liquidity absorption rates)
- "asset_price" (representing closing price)
- "daily_high" (representing price_action.daily_structure.high)
- "daily_low" (representing price_action.daily_structure.low)
- "volume_state" (representing trading volume state)
- "volatility_regime" (representing market volatility regime)

=== ALLOWED CAUSAL DIRECTIONS ===
"positive" (amplifies target), "negative" (diminishes/reverses target), "neutral"

=== ALLOWED QUALIFIERS ===
- "ELEVATED" (higher than average/baseline)
- "DEPRESSED" (lower than average/baseline)
- "FLAT" (stable, neutral, range-bound)
- "COMPRESSED" (low volatility, tight range)
- "EXPANDED" (high volatility, wide range)
- "GREATER_THAN_PREVIOUS" (relative comparison: current t > prior t-1)
- "LESS_THAN_PREVIOUS" (relative comparison: current t < prior t-1)

=== COMPILATION RULES ===
1. Extract the main "trigger_concept" with fields:
   - "concept" (must be one from the catalog above)
   - "qualifier" (must be one from the qualifiers list above)
   - "lag" (0 or 1)
2. Extract the main "target_concept" with fields:
   - "concept" (must be one from the catalog above)
   - "qualifier" (must be one from the qualifiers list above)
   - "duration_steps" (usually 1)
3. Extract a list of "scope_concept" objects, each with fields:
   - "concept"
   - "qualifier"
4. Rate compilation status:
   - If trigger, target, and causal direction are successfully identified, status is "SUCCESS".
   - Otherwise, status is "PARTIAL" or "FAILED".
5. Provide a failure_reason if status is not "SUCCESS".

You MUST respond strictly with a JSON object conforming exactly to this structure:
{{
  "compilation_status": "SUCCESS" | "PARTIAL" | "FAILED",
  "failure_reason": "string or null",
  "causal_direction": "positive" | "negative" | "neutral",
  "trigger_concept": {{
    "concept": "string",
    "qualifier": "string",
    "lag": 0 | 1
  }} | null,
  "target_concept": {{
    "concept": "string",
    "qualifier": "string",
    "duration_steps": 1
  }} | null,
  "scope_concept": [
    {{
      "concept": "string",
      "qualifier": "string"
    }}
  ] | null
}}
"""
        status = "FAILED"
        reason = "LLM Execution Failure"
        causal_dir = "neutral"
        trigger = {}
        target = {}
        scope = []

        try:
            res_text = self.client.generate(prompt, json_format=True)
            start = res_text.find("{")
            end = res_text.rfind("}") + 1
            json_str = res_text[start:end] if start != -1 and end > start else res_text
            data = json.loads(json_str)

            status = data.get("compilation_status", "FAILED")
            reason = data.get("failure_reason")
            causal_dir = data.get("causal_direction", "neutral")
            trigger = data.get("trigger_concept") or {}
            target = data.get("target_concept") or {}
            scope = data.get("scope_concept") or []

            if status == "SUCCESS" and (not trigger or not target):
                status = "PARTIAL"
                reason = (
                    "Required trigger or target concept missing from SUCCESS response"
                )
        except Exception as e:
            status = "FAILED"
            reason = f"LLM error: {str(e)}"

        trace = {
            "source_theory": theory.id,
            "status": status,
            "reason": reason,
            "compiler_version": "semantic_compiler_v1",
        }

        return CanonicalSemanticProposition(
            id=str(uuid4()),
            theory_id=theory.id,
            lineage_id=theory.lineage_id,
            trigger_concept=trigger,
            target_concept=target,
            scope_concept=scope,
            causal_direction=causal_dir,
            compiler_provenance=trace,
        )
