import re
from typing import Set

from cognition.schemas.reflection.reflection_event import ReflectionEvent
from interfaces.ollama_client import OllamaClient


class ReflectionFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(
        self,
        theory,
        validation,
        contradiction_result=None,
        market_observation=None,
        # v3.0 explicit overrides
        regime_subtype: str = None,
        falsifiability_conditions: list = None,
        analog_divergence_claim: str = None,
        theory_regime_subtype: str = None,
        theory_falsifiability_conditions: list = None,
        regime_history: dict = None,
    ) -> ReflectionEvent:
        contradiction_result = contradiction_result or {}
        contradiction_summary = contradiction_result.get(
            "summary", "No explicit contradiction detected."
        )
        contradiction_indicators = contradiction_result.get("indicators", [])

        # Resolve finalized v3.0 fields with explicit fallbacks
        final_regime_subtype = regime_subtype if regime_subtype is not None else getattr(market_observation, 'regime_subtype', 'neutral')
        if not final_regime_subtype:
            final_regime_subtype = "neutral"
            
        final_analog_claim = analog_divergence_claim if analog_divergence_claim is not None else getattr(market_observation, 'analog_divergence_claim', 'None')
        if not final_analog_claim:
            final_analog_claim = "None"

        observation_section = ""
        if market_observation is not None:
            observation_section = (
                f"Observation: {market_observation.observation_text}\n"
                f"Candle: {getattr(market_observation, 'candle_type', 'neutral')}\n"
                f"Participation: {getattr(market_observation, 'participation_strength', 'normal')}, {getattr(market_observation, 'participation_confirmation', 'normal')}\n"
                f"Volatility: {getattr(market_observation, 'volatility_state', 'unknown')}\n"
                f"Regime Subtype: {final_regime_subtype}\n"
                f"Analog Divergence: {final_analog_claim}\n"
            )

        # v3.1 Tuning Correction: Reduced history burden
        seen_count = regime_history.get("seen_count", 0) if regime_history else 0
        if seen_count < 2:
            history_context_for_prompt = "No prior subtype history."
        else:
            res = regime_history.get("historical_resolution", {})
            dominant_res = max(res, key=res.get) if res else "uncertain"
            history_context_for_prompt = f"""
Historical Subtype Memory:
Subtype: {regime_history.get('subtype', 'neutral')}
Seen: {seen_count}
Dominant resolution: {dominant_res}
Avg usefulness: {regime_history.get('avg_usefulness', 0.0):.2f}

Use subtype history only if materially relevant. Primary focus remains: 1 observation, 2 subtype, 3 falsifiability. History is secondary context. Do not force reflection to explain history.
"""
        print(f"[Reflection History Debug] seen_count: {seen_count}, context: {history_context_for_prompt}")

        # v3.0 Regime and falsifiability context
        t_subtype = theory_regime_subtype if theory_regime_subtype is not None else getattr(theory, 'regime_subtype', 'neutral')
        if not t_subtype: t_subtype = "neutral"
        t_falsifiability = theory_falsifiability_conditions if theory_falsifiability_conditions is not None else getattr(theory, 'falsifiability_conditions', [])
        regime_context = f"\nTheory Regime Subtype: {t_subtype}"
        if t_falsifiability:
            regime_context += f"\nTheory is falsified if: " + "; ".join(t_falsifiability)

        prompt = f"""
Reflect on the following theory validation using structured market observation dimensions.

Theory:
{theory.summary}

{observation_section}
Contradiction:
{contradiction_summary}
{'; '.join(contradiction_indicators)}
{regime_context} # This already includes theory's falsifiability
{history_context_for_prompt}

Validation:
{validation.validation_summary}

Return:
- compressed critique, 2-4 sentences.
- strictly name the current regime subtype at the start.
- state whether the regime remains supported or is falsified based on boundary conditions
- evaluate analog divergence if present
- reference specific theory and contradiction indicators
- identify one unresolved tension
- identify what remains weak, untested, ambiguous, or contradicted
- preserve unresolved tension instead of resolving it rhetorically
- evaluate uncertainty and confidence pressure directly
- avoid overconfidence, reinforcement bias, and self-congratulation
- avoid generic philosophical language or broad market commentary
- prefer falsifiable weakness statements over praise.
- maximum 4 sentences.
- do not praise the theory, prompt, or validation process
- do not use headings or numbered sections
- no markdown

Good style:
Observed continuation remains insufficiently tested under volatility expansion; contradicts prior participation strength assumption.

Bad style:
This theory appears insightful and coherent.
"""

        result = self.client.generate(prompt)
        reflection_summary = self._clean_reflection(
            result,
            theory_text=theory.summary,
            contradiction_summary=contradiction_summary,
        )

        return ReflectionEvent(
            related_theory_id=theory.id,
            reflection_summary=reflection_summary,
            confidence_impact="moderate",
        )

    def _clean_reflection(
        self,
        reflection: str,
        theory_text: str = "",
        contradiction_summary: str = "",
    ) -> str:

        blocked_phrases = [
            "well-crafted",
            "well done",
            "what a",
            "strengths",
            "suggestions",
            "overall",
            "here's",
            "here is",
            "well-executed",
            "insightful and coherent",
            "viable framework",
            "epistemic humility",
            "market dynamics are inherently complex",
            "embracing uncertainty",
            "provided validation",
            "validation attempt",
            "good-style critique",
            "good style",
            "bad style",
            "requested",
            "prompt",
            "this approach",
            "a more effective approach",
        ]
        generic_patterns = [
            r"\bthis theory appears\b",
            r"\bthis indicates that\b",
            r"\bthe validation suggests that it may be\b",
            r"\bfinancial markets\b",
            r"\bthe provided validation\b",
            r"\bthe critique should\b",
            r"\ba good-style critique\b",
        ]
        lines = []

        for line in reflection.splitlines():
            cleaned_line = line.strip().strip("*").strip("#").strip()

            if not cleaned_line:
                continue

            lower_line = cleaned_line.lower()

            if any(phrase in lower_line for phrase in blocked_phrases):
                continue

            if any(re.search(pattern, lower_line) for pattern in generic_patterns):
                continue

            if lower_line[:2] in ["1.", "2.", "3.", "4."]:
                continue

            lines.append(cleaned_line)

        cleaned = " ".join(lines)
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
            if sentence.strip()
        ]

        if not sentences: # This fallback should be more specific to the issue
            return self._fallback_reflection(theory_text, contradiction_summary)

        compressed = " ".join(sentences[:4])
        if compressed[-1:] not in [".", "!", "?"]:
            compressed = compressed + "."
        if not self._is_grounded_reflection(
            compressed,
            theory_text=theory_text,
            contradiction_summary=contradiction_summary,
        ):
            return self._fallback_reflection(theory_text, contradiction_summary)
        return compressed

    def _is_grounded_reflection(
        self,
        reflection: str,
        theory_text: str,
        contradiction_summary: str,
    ) -> bool:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", reflection)
            if sentence.strip()
        ]
        if not 2 <= len(sentences) <= 4: # Reflection should be at least 2 sentences
            return False

        lower_reflection = reflection.lower()
        meta_terms = [
            "prompt",
            "validation process",
            "provided validation",
            "good-style",
            "this critique",
            "the critique",
        ]
        if any(term in lower_reflection for term in meta_terms):
            return False

        theory_terms = self._salient_terms(theory_text)
        contradiction_terms = self._salient_terms(contradiction_summary)
        tension_terms = {
            "weak",
            "unresolved",
            "tension",
            "fragile",
            "fragility",
            "limited",
            "insufficient",
            "untested",
            "contradiction",
            "contradicted",
            "masks",
        }
        theory_grounded = any(term in lower_reflection for term in theory_terms)
        contradiction_grounded = (
            contradiction_summary.lower().startswith("no explicit")
            or any(term in lower_reflection for term in contradiction_terms)
            or "contradiction" in lower_reflection
        )
        tension_grounded = any(term in lower_reflection for term in tension_terms)
        return theory_grounded and contradiction_grounded and tension_grounded

    def _fallback_reflection(self, theory_text: str, contradiction_summary: str) -> str:
        lower_theory = theory_text.lower()
        lower_contradiction = contradiction_summary.lower()

        if "breadth" in lower_theory or "breadth" in lower_contradiction:
            return "Breadth weakness remains unresolved under contradiction pressure."
        if "volatility" in lower_theory or "volatility" in lower_contradiction:
            return "Compressed volatility masks fragility under contradiction pressure."
        if "continuation" in lower_theory:
            return "Continuation remains weakly evidenced against caution signals."
        if "participation" in lower_theory:
            return "Participation tension remains weakly evidenced against caution signals."
        if "liquidity" in lower_theory:
            return "Liquidity support remains weakly tested against contradiction pressure."
        return "Theory contradiction remains unresolved."

    def _salient_terms(self, text: str) -> Set[str]:
        blocked_terms = {
            "the",
            "and",
            "that",
            "this",
            "with",
            "from",
            "current",
            "recent",
            "theory",
            "contains",
            "signal",
            "market",
        }
        return {
            term
            for term in re.findall(r"[a-z][a-z-]{4,}", text.lower())
            if term not in blocked_terms
        }
