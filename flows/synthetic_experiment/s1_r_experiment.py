import json
import random
from typing import Any, Dict, List, Optional

from flows.synthetic_experiment.schemas import (CandidateProposition,
                                                EvidenceObject, Experience,
                                                Predicate)
from flows.synthetic_experiment.synthetic_harness import (check_predicate,
                                                          compute_evidence)
from interfaces.ollama_client import OllamaClient


class S1REnvironmentGenerator:
    def __init__(
        self,
        signal_strength: float = 0.8,
        base_rate: float = 0.5,
        noise_level: float = 0.1,
        regime_persistence: float = 0.9,
        sample_size: int = 1000,
        random_seed: int = 42,
    ) -> None:
        self.signal_strength = signal_strength
        self.base_rate = base_rate
        self.noise_level = noise_level
        self.regime_persistence = regime_persistence
        self.sample_size = sample_size
        self.random_seed = random_seed

    def generate(self) -> List[Experience]:
        random.seed(self.random_seed)
        experiences = []
        regime = "A"

        # Define specific days for the small-sample signal to trigger
        # We need na <= 5 in formation (1-500) and eval (501-1000)
        small_sample_formation_days = {50, 150, 250, 350}
        small_sample_evaluation_days = {550, 650, 750, 850}

        for t in range(1, self.sample_size + 1):
            # 1. Transition regime
            if t > 1:
                if random.random() > self.regime_persistence:
                    regime = "B" if regime == "A" else "A"

            # Generate signals
            signal_stable = "high" if random.random() < 0.3 else "low"

            # Small sample triggers ONLY on specified days
            if t <= 500:
                signal_small_sample = (
                    "high" if t in small_sample_formation_days else "low"
                )
            else:
                signal_small_sample = (
                    "high" if t in small_sample_evaluation_days else "low"
                )

            signal_deteriorating = "high" if random.random() < 0.3 else "low"
            signal_regime_mismatch = "high" if random.random() < 0.3 else "low"
            signal_weak = "high" if random.random() < 0.3 else "low"
            signal_inverse = "high" if random.random() < 0.3 else "low"

            features = {
                "signal_stable": signal_stable,
                "signal_small_sample": signal_small_sample,
                "signal_deteriorating": signal_deteriorating,
                "signal_regime_mismatch": signal_regime_mismatch,
                "signal_weak": signal_weak,
                "signal_inverse": signal_inverse,
            }
            # Add 19 dummy features to make candidate pool 50
            for i in range(1, 20):
                features[f"dummy_{i}"] = "high" if random.random() < 0.3 else "low"

            # Determine outcome probability
            p_up = self.base_rate

            # Archetype mappings:
            # Small sample is ALWAYS UP when active
            if signal_small_sample == "high":
                p_up = 1.0
            # Stable signal is UP when active under regime A
            elif regime == "A" and signal_stable == "high":
                p_up = self.signal_strength
            # Deteriorating signal: UP in formation, DOWN in evaluation
            elif signal_deteriorating == "high":
                p_up = (
                    self.signal_strength if t <= 500 else (1.0 - self.signal_strength)
                )
            # Regime mismatch: UP in B, DOWN in A (Evaluation is mostly A)
            elif signal_regime_mismatch == "high":
                p_up = (
                    self.signal_strength
                    if regime == "B"
                    else (1.0 - self.signal_strength)
                )
            # Weak signal: slightly above base rate
            elif signal_weak == "high":
                p_up = self.base_rate + 0.05
            # Inverse signal: DOWN when active (high absolute lift, negative direction)
            elif signal_inverse == "high":
                p_up = 1.0 - self.signal_strength

            # Realize outcome with noise
            if random.random() < self.noise_level:
                outcome = "UP" if random.random() < 0.5 else "DOWN"
            else:
                outcome = "UP" if random.random() < p_up else "DOWN"

            exp = Experience(
                timestamp=t,
                regime=regime,
                features=features,
                outcome=outcome,
            )
            experiences.append(exp)

        return experiences


def generate_s1_r_candidates(num_candidates: int = 50) -> List[CandidateProposition]:
    """Generates the 50 candidate propositions matching archetypes."""
    features = [
        "signal_stable",
        "signal_small_sample",
        "signal_deteriorating",
        "signal_regime_mismatch",
        "signal_weak",
        "signal_inverse",
    ]
    num_dummies = (num_candidates // 2) - len(features)
    for i in range(1, num_dummies + 1):
        features.append(f"dummy_{i}")

    candidates = []
    for feat in features:
        for target_val in ["UP", "DOWN"]:
            prop_id = f"prop_{feat}_{target_val.lower()}"
            cand = CandidateProposition(
                proposition_id=prop_id,
                trigger_predicate=Predicate(field=feat, operator="==", value="high"),
                scope_predicates=[Predicate(field="regime", operator="==", value="A")],
                expected_effect_predicate=Predicate(
                    field="outcome", operator="==", value=target_val
                ),
                evaluation_horizon=1,
            )
            candidates.append(cand)

    return candidates[:num_candidates]


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Helper to compute Pearson correlation coefficient."""
    n = len(x)
    if n == 0:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    den_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / ((den_x * den_y) ** 0.5)


def check_epistemic_complexity(
    evidence: List[EvidenceObject], oos_lifts: Dict[str, float]
) -> Dict[str, float]:
    """Computes correlations between each evidence field and prospective out-of-sample lift."""
    fields = {
        "signed_lift": [e.signed_lift for e in evidence],
        "absolute_lift": [e.absolute_lift for e in evidence],
        "activation_count": [float(e.activation_count) for e in evidence],
        "stability_score": [e.stability_score for e in evidence],
        "conditional_probability": [e.conditional_probability for e in evidence],
    }
    y = [oos_lifts.get(e.proposition_id, 0.0) for e in evidence]

    correlations = {}
    for name, x in fields.items():
        correlations[name] = pearson_correlation(x, y)
    return correlations


def call_ollama_with_retry(
    prompt: str, candidates: List[str], count: int = 5, seed: Optional[int] = None
) -> List[str]:
    """Queries Ollama client with retry logic, validating against candidate IDs."""
    client = OllamaClient(temperature=0.0, seed=seed)
    for attempt in range(3):
        try:
            response = client.generate(prompt, json_format=True)
            # Find and parse JSON blocks
            data = json.loads(response)
            if isinstance(data, dict):
                selections = data.get("selections", [])
                valid = [s for s in selections if s in candidates]
                if len(valid) == count:
                    return valid
        except Exception:
            pass
    # If failed, do not silently replace. Return invalid marker list.
    return ["AGENT_OUTPUT_INVALID"] * count


def format_s1_r_agent_a_prompt(
    candidates: List[CandidateProposition], experiences: List[Experience]
) -> str:
    """Formats the raw experience prompt for Agent A."""
    rows = []
    rows.append(
        "| Day | regime | signal_stable | signal_small_sample | signal_deteriorating | signal_regime_mismatch | signal_weak | signal_inverse | outcome |"
    )
    rows.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for exp in experiences[:100]:
        feat = exp.features
        rows.append(
            f"| {exp.timestamp} | {exp.regime} | {feat.get('signal_stable')} | {feat.get('signal_small_sample')} | {feat.get('signal_deteriorating')} | {feat.get('signal_regime_mismatch')} | {feat.get('signal_weak')} | {feat.get('signal_inverse')} | {exp.outcome} |"
        )
    table = "\n".join(rows)

    candidates_str = "\n".join(
        [
            f"- {c.proposition_id}: WHEN {c.trigger_predicate.field} == {c.trigger_predicate.value} EXPECT outcome == {c.expected_effect_predicate.value}"
            for c in candidates
        ]
    )
    return f"""You are an advanced scientific cognitive agent.
You are given a list of candidate propositions and a raw chronological log of experiences (first 100 days).
Your task is to select exactly 5 candidate propositions that represent true, stable, and highly positive prospective predictive relationships in this data.

Candidate Propositions:
{candidates_str}

Raw Experiences:
{table}

You must select exactly 5 candidate IDs. Respond ONLY with a JSON object of the following format:
{{
  "selections": ["prop_id1", "prop_id2", "prop_id3", "prop_id4", "prop_id5"],
  "reason_codes": ["code1", "code2", "code3", "code4", "code5"]
}}
"""


def format_s1_r_agent_c_prompt(
    candidates: List[CandidateProposition], evidence: List[EvidenceObject]
) -> str:
    """Formats the compiled evidence prompt for Agent C."""
    rows = []
    rows.append(
        "| Candidate ID | Feature Trigger | activations | support | contradiction | conditional_prob | base_rate | signed_lift | absolute_lift | uncertainty | stability |"
    )
    rows.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    evidence_map = {e.proposition_id: e for e in evidence}
    for c in candidates:
        ev = evidence_map.get(c.proposition_id)
        if ev:
            trigger = f"{c.trigger_predicate.field}=={c.trigger_predicate.value}"
            rows.append(
                f"| {c.proposition_id} | {trigger} | {ev.activation_count} | {ev.support_count} | {ev.contradiction_count} | {ev.conditional_probability:.2f} | {ev.unconditional_base_rate:.2f} | {ev.signed_lift:.2f} | {ev.absolute_lift:.2f} | {ev.uncertainty_score:.2f} | {ev.stability_score:.2f} |"
            )
    table = "\n".join(rows)

    return f"""You are an advanced scientific cognitive agent.
You are given a list of candidate propositions and a markdown table summarizing their empirical evidence statistics from a historical training window.
Your task is to select exactly 5 propositions that represent true, stable, and highly positive prospective predictive relationships.

Warning:
- High-lift candidates with tiny activation counts (e.g. <= 10) are likely overfitted noise.
- Candidates with high overall lift but low stability score are deteriorating or unstable.
- Candidates with high absolute lift but negative signed lift predict in the wrong direction.
- Candidates with high activation count but near-zero signed lift have no predictive power.
Only by integrating multiple evidence dimensions (lift, sample size, and stability) can you identify the genuine planted relationships.

Candidates and Evidence:
{table}

You must select exactly 5 candidate IDs. Respond ONLY with a JSON object of the following format:
{{
  "selections": ["prop_id1", "prop_id2", "prop_id3", "prop_id4", "prop_id5"],
  "reason_codes": ["code1", "code2", "code3", "code4", "code5"]
}}
"""
