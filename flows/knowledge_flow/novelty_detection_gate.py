import json
from typing import Any, Dict, List, Optional, Tuple

from interfaces.ollama_client import OllamaClient


class NoveltyDetectionGate:
    """
    Novelty Detection Gate evaluates whether a new market observation or regime
    requires generating a new theory, revising the prior theory, or reinforcing (reusing) it.
    """

    def __init__(self, llm_client: Optional[OllamaClient] = None):
        self.client = llm_client or OllamaClient(temperature=0.0, seed=42)

    def compute_novelty_score(
        self,
        regime_similarity: Optional[float],
        prior_prediction: Optional[Any],
        prior_prediction_result: Optional[Any],
        prior_attribution: Optional[Any],
        active_principles: List[Any],
        regime_subtype: str,
    ) -> float:
        """
        Calculates a continuous novelty score [0.0, 1.0] based on four factors.
        """
        # Factor 1: Regime Mismatch (Weight: 0.25)
        regime_mismatch = 1.0 - (
            regime_similarity if regime_similarity is not None else 0.5
        )

        # Factor 2: Failed Component Ratio (Weight: 0.35)
        if prior_attribution and hasattr(prior_attribution, "components_failed"):
            failed_count = len(prior_attribution.components_failed)
            # Normalize over a cap of 3 failures
            failed_ratio = min(1.0, failed_count / 3.0)
        elif (
            isinstance(prior_attribution, dict)
            and "components_failed" in prior_attribution
        ):
            failed_count = len(prior_attribution["components_failed"])
            failed_ratio = min(1.0, failed_count / 3.0)
        else:
            failed_ratio = 0.0

        # Factor 3: Existing Principle Coverage (Weight: 0.20)
        principle_coverage = 0.0
        for p in active_principles:
            if hasattr(p, "falsifiable_predictions"):
                for fp in p.falsifiable_predictions:
                    val = fp.applicability_filter.get("regime_subtype")
                    if isinstance(val, (list, tuple, set)):
                        if regime_subtype in val:
                            principle_coverage = 1.0
                            break
                    else:
                        if val == regime_subtype:
                            principle_coverage = 1.0
                            break
            if principle_coverage > 0.0:
                break
        principle_uncovered = 1.0 - principle_coverage

        # Factor 4: Prediction Surprise (Weight: 0.20)
        surprise = 0.5
        if prior_prediction and prior_prediction_result:
            try:
                # Support both class objects and dicts
                conf = getattr(prior_prediction, "confidence", 0.5)
                if isinstance(prior_prediction, dict):
                    conf = prior_prediction.get("confidence", 0.5)

                score = getattr(prior_prediction_result, "direction_score", 0.5)
                if isinstance(prior_prediction_result, dict):
                    score = prior_prediction_result.get("direction_score", 0.5)

                if conf is not None and score is not None:
                    surprise = abs(conf - score)
            except Exception:
                pass

        # Weighted Novelty Sum
        score = (
            0.25 * regime_mismatch
            + 0.35 * failed_ratio
            + 0.20 * principle_uncovered
            + 0.20 * surprise
        )
        return float(max(0.0, min(1.0, score)))

    def is_novel(
        self,
        observation: Any,
        regime_subtype: str,
        prior_theory: Optional[Any],
        prior_prediction: Optional[Any],
        prior_prediction_result: Optional[Any],
        prior_attribution: Optional[Any],
        active_principles: List[Any],
    ) -> Tuple[str, float, str]:
        """
        Runs the full novelty gate.
        Returns:
            decision (str): "REINFORCE", "REVISE", or "GENERATE"
            score (float): The calculated Novelty Score
            rationale (str): Description explaining the critique output.
        """
        # If there is no prior theory, we must generate a new one
        if not prior_theory:
            return "GENERATE", 1.0, "No prior theory exists."

        # Get observation text safely
        observation_text = ""
        if hasattr(observation, "observation_text"):
            observation_text = observation.observation_text
        elif isinstance(observation, dict):
            observation_text = observation.get("raw_content", "")
        else:
            observation_text = str(observation)

        # Get prior claim safely
        prior_claim = ""
        if (
            hasattr(prior_theory, "summary_structured")
            and prior_theory.summary_structured
        ):
            prior_claim = prior_theory.summary_structured.claim
        elif hasattr(prior_theory, "summary"):
            prior_claim = prior_theory.summary
        else:
            prior_claim = str(prior_theory)

        sim = 0.5
        # Estimate similarity using dict fields if present
        if isinstance(observation, dict):
            sim = observation.get("regime_similarity", 0.5)

        # Calculate Novelty Score
        score = self.compute_novelty_score(
            regime_similarity=sim,
            prior_prediction=prior_prediction,
            prior_prediction_result=prior_prediction_result,
            prior_attribution=prior_attribution,
            active_principles=active_principles,
            regime_subtype=regime_subtype,
        )

        failed_comps = []
        if prior_attribution:
            if hasattr(prior_attribution, "components_failed"):
                failed_comps = prior_attribution.components_failed
            elif isinstance(prior_attribution, dict):
                failed_comps = prior_attribution.get("components_failed", [])

        surprise = 0.5
        if prior_prediction and prior_prediction_result:
            try:
                conf = (
                    prior_prediction.get("confidence", 0.5)
                    if isinstance(prior_prediction, dict)
                    else getattr(prior_prediction, "confidence", 0.5)
                )
                dir_score = (
                    prior_prediction_result.get("direction_score", 0.5)
                    if isinstance(prior_prediction_result, dict)
                    else getattr(prior_prediction_result, "direction_score", 0.5)
                )
                surprise = abs(conf - dir_score)
            except Exception:
                pass

        # Trigger Micro Reflection Critique via LLM
        prompt = f"""You are the reflective critique model for the Cognition Engine.
We computed a quantitative Novelty Score of {score:.2f} (where >= 0.60 suggests generating a new theory, 0.30 to 0.60 suggests revising the existing theory, and < 0.30 suggests reinforcing it).

Current State:
- Current Observation: {observation_text}
- Regime Subtype: {regime_subtype}
- Existing Theory: {prior_claim}

Prior Step Performance:
- Failed Components: {failed_comps}
- Prediction Surprise (Error): {surprise:.2f}

Run a Micro Reflection Critique to finalize the decision. Choose one of:
- "REINFORCE": Bypasses theory generation, reusing the existing theory directly. Use this if the prior theory succeeded and the regime/observation is consistent.
- "REVISE": Triggers a minor revision of the existing theory's assumptions/falsification checks to adapt to slight differences.
- "GENERATE": Triggers standard full theory generation because the observation is highly novel or the prior theory completely broke down.

Respond in JSON format:
{{
  "critique": "Short critique explaining how the existing theory aligns or diverges.",
  "decision": "REINFORCE, REVISE, or GENERATE",
  "explanation": "Rationale for the chosen decision."
}}
"""
        try:
            res_raw = self.client.generate(prompt, json_format=True)
            res = json.loads(res_raw)
            decision = res.get("decision", "GENERATE")
            if decision not in ["REINFORCE", "REVISE", "GENERATE"]:
                # Fallback to score-based thresholds
                if score < 0.30:
                    decision = "REINFORCE"
                elif score < 0.60:
                    decision = "REVISE"
                else:
                    decision = "GENERATE"

            critique = res.get("critique", "")
            explanation = res.get("explanation", "")
            rationale = f"Critique: {critique} | Explanation: {explanation}"
            return decision, score, rationale
        except Exception as e:
            # Fallback to threshold-based policy on failure
            if score < 0.30:
                decision = "REINFORCE"
            elif score < 0.60:
                decision = "REVISE"
            else:
                decision = "GENERATE"
            return decision, score, f"Fallback due to exception: {e}"
