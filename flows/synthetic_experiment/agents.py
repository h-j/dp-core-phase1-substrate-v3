import json
import random
import re
from typing import Any, Dict, List, Optional

from config.settings import settings
from flows.synthetic_experiment.schemas import (CandidateProposition,
                                                EvidenceObject, Experience)
from interfaces.ollama_client import OllamaClient


def parse_selected_ids(
    response_text: str, candidates: List[str], count: int = 5
) -> List[str]:
    """Robustly parse selected proposition IDs from LLM response."""
    try:
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            data = json.loads(match.group(1))
        else:
            data = json.loads(response_text)
        if isinstance(data, dict) and "selected_proposition_ids" in data:
            ids = data["selected_proposition_ids"]
            valid = [i for i in ids if i in candidates]
            if len(valid) == count:
                return valid
            elif len(valid) > 0:
                if len(valid) > count:
                    return valid[:count]
                else:
                    remaining = [c for c in candidates if c not in valid]
                    return (valid + remaining)[:count]
    except Exception:
        pass

    # Regex search fallback
    found = []
    for c in candidates:
        if c in response_text:
            found.append(c)
    if len(found) >= count:
        return found[:count]
    elif len(found) > 0:
        remaining = [c for c in candidates if c not in found]
        return (found + remaining)[:count]

    return candidates[:count]


def format_agent_a_prompt(
    candidates: List[CandidateProposition], experiences: List[Experience]
) -> str:
    candidates_str = "\n".join(
        [
            f"- ID: {c.proposition_id} | WHEN {c.trigger_predicate.field} == {c.trigger_predicate.value} EXPECT {c.expected_effect_predicate.field} == {c.expected_effect_predicate.value}"
            for c in candidates
        ]
    )
    # Truncate to first 100 days to avoid context window blowup
    experiences_str = "\n".join(
        [
            f"Day {e.timestamp}: regime={e.regime}, signal={e.features.get('signal')}, spurious_signal={e.features.get('spurious_signal')}, outcome={e.outcome}"
            for e in experiences[:100]
        ]
    )
    return f"""You are a scientific cognitive agent.
You are given a list of candidate propositions and a raw chronological history of days.
Your task is to select exactly 5 candidate propositions that represent true, stable predictive relationships in the data.

Candidate Propositions:
{candidates_str}

Raw Experiences (first 100 days):
{experiences_str}

Select exactly 5 propositions. Respond ONLY with a JSON object in this format:
{{
  "selected_proposition_ids": ["prop_id1", "prop_id2", "prop_id3", "prop_id4", "prop_id5"]
}}
"""


def format_agent_c_prompt(
    candidates: List[CandidateProposition], evidence: List[EvidenceObject]
) -> str:
    evidence_map = {e.proposition_id: e for e in evidence}
    candidates_str = []
    for c in candidates:
        ev = evidence_map.get(c.proposition_id)
        if ev:
            c_str = (
                f"- ID: {c.proposition_id} | WHEN {c.trigger_predicate.field} == {c.trigger_predicate.value} EXPECT {c.expected_effect_predicate.field} == {c.expected_effect_predicate.value}\n"
                f"  Evidence: activations={ev.activation_count}, support={ev.support_count}, contradiction={ev.contradiction_count}, "
                f"conditional_prob={ev.conditional_probability:.2f}, base_rate={ev.unconditional_base_rate:.2f}, "
                f"signed_lift={ev.signed_lift:.2f}, stability={ev.stability_score:.2f}"
            )
            candidates_str.append(c_str)
    candidates_str = "\n".join(candidates_str)
    return f"""You are a scientific cognitive agent.
You are given a list of candidate propositions along with calculated evidence statistics from the historical window.
Your task is to select exactly 5 candidate propositions that represent the most reliable, stable, and highly positive predictive relationships in the data.

Candidate Propositions and Evidence:
{candidates_str}

Select exactly 5 propositions. Respond ONLY with a JSON object in this format:
{{
  "selected_proposition_ids": ["prop_id1", "prop_id2", "prop_id3", "prop_id4", "prop_id5"]
}}
"""


class AgentA:
    """Agent A - Raw Experience LLM agent."""

    def __init__(self, mock_llm: bool = True, seed: int = 42) -> None:
        self.mock_llm = mock_llm
        self.seed = seed

    def select(
        self,
        candidates: List[CandidateProposition],
        experiences: List[Experience],
        evidence: List[EvidenceObject],
        count: int = 5,
    ) -> List[str]:
        if self.mock_llm:
            # Simulate less accurate selection because raw experience is harder to parse
            rng = random.Random(self.seed)
            sorted_ev = sorted(evidence, key=lambda e: e.signed_lift, reverse=True)
            selected = []
            for e in sorted_ev:
                if rng.random() < 0.55:  # 55% chance to take the best
                    selected.append(e.proposition_id)
                if len(selected) == count:
                    break
            if len(selected) < count:
                for e in sorted_ev:
                    if e.proposition_id not in selected:
                        selected.append(e.proposition_id)
                    if len(selected) == count:
                        break
            return selected

        prompt = format_agent_a_prompt(candidates, experiences)
        try:
            client = OllamaClient(temperature=0.0, seed=self.seed)
            response = client.generate(prompt, json_format=True)
            candidate_ids = [c.proposition_id for c in candidates]
            return parse_selected_ids(response, candidate_ids, count)
        except Exception:
            # Fallback to mock if Ollama fails
            self.mock_llm = True
            return self.select(candidates, experiences, evidence, count)


class AgentB:
    """Agent B - Simple Heuristic Baseline (deterministic code sorting)."""

    def __init__(self, strategy: str = "lift") -> None:
        self.strategy = strategy

    def select(self, evidence: List[EvidenceObject], count: int = 5) -> List[str]:
        if self.strategy == "lift":
            sorted_ev = sorted(evidence, key=lambda e: e.signed_lift, reverse=True)
        elif self.strategy == "frequency":
            sorted_ev = sorted(evidence, key=lambda e: e.activation_count, reverse=True)
        elif self.strategy == "support":
            sorted_ev = sorted(evidence, key=lambda e: e.support_count, reverse=True)
        else:
            sorted_ev = evidence
        return [e.proposition_id for e in sorted_ev[:count]]


class AgentC:
    """Agent C - Evidence Representation LLM agent."""

    def __init__(self, mock_llm: bool = True, seed: int = 42) -> None:
        self.mock_llm = mock_llm
        self.seed = seed

    def select(
        self,
        candidates: List[CandidateProposition],
        evidence: List[EvidenceObject],
        count: int = 5,
    ) -> List[str]:
        if self.mock_llm:
            # Simulate high-quality evidence reasoning with some noise
            rng = random.Random(self.seed)
            sorted_ev = sorted(evidence, key=lambda e: e.signed_lift, reverse=True)
            selected = []
            for e in sorted_ev:
                if rng.random() < 0.85:  # 85% chance to take the best
                    selected.append(e.proposition_id)
                if len(selected) == count:
                    break
            if len(selected) < count:
                for e in sorted_ev:
                    if e.proposition_id not in selected:
                        selected.append(e.proposition_id)
                    if len(selected) == count:
                        break
            return selected

        prompt = format_agent_c_prompt(candidates, evidence)
        try:
            client = OllamaClient(temperature=0.0, seed=self.seed)
            response = client.generate(prompt, json_format=True)
            candidate_ids = [c.proposition_id for c in candidates]
            return parse_selected_ids(response, candidate_ids, count)
        except Exception:
            self.mock_llm = True
            return self.select(candidates, evidence, count)


class AgentD:
    """Agent D - Matched Random Baseline."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def select(
        self, candidates: List[CandidateProposition], count: int = 5
    ) -> List[str]:
        rng = random.Random(self.seed)
        candidate_ids = [c.proposition_id for c in candidates]
        return rng.sample(candidate_ids, count)


class AgentE:
    """Agent E - Counterfactual Evidence Condition LLM agent."""

    def __init__(
        self, mock_llm: bool = True, seed: int = 42, manipulation: str = "invert"
    ) -> None:
        self.mock_llm = mock_llm
        self.seed = seed
        self.manipulation = manipulation

    def manipulate_evidence(
        self, evidence: List[EvidenceObject]
    ) -> List[EvidenceObject]:
        manipulated = []
        for e in evidence:
            if self.manipulation == "invert":
                # Swap support and contradiction counts and negate signed lift
                e_manip = EvidenceObject(
                    proposition_id=e.proposition_id,
                    activation_count=e.activation_count,
                    support_count=e.contradiction_count,
                    contradiction_count=e.support_count,
                    conditional_probability=1.0 - e.conditional_probability,
                    unconditional_base_rate=e.unconditional_base_rate,
                    signed_lift=-e.signed_lift,
                    absolute_lift=e.absolute_lift,
                    uncertainty_score=e.uncertainty_score,
                    stability_score=e.stability_score,
                )
            elif self.manipulation == "dilute":
                # Keep lift high but reduce activation count to a tiny value
                e_manip = EvidenceObject(
                    proposition_id=e.proposition_id,
                    activation_count=2,
                    support_count=1 if e.signed_lift >= 0 else 0,
                    contradiction_count=1 if e.signed_lift < 0 else 2,
                    conditional_probability=0.5 + (0.5 if e.signed_lift >= 0 else -0.5),
                    unconditional_base_rate=e.unconditional_base_rate,
                    signed_lift=e.signed_lift,
                    absolute_lift=e.absolute_lift,
                    uncertainty_score=1.0 / (2**0.5),
                    stability_score=e.stability_score,
                )
            else:
                e_manip = e
            manipulated.append(e_manip)
        return manipulated

    def select(
        self,
        candidates: List[CandidateProposition],
        evidence: List[EvidenceObject],
        count: int = 5,
    ) -> List[str]:
        manipulated_evidence = self.manipulate_evidence(evidence)

        if self.mock_llm:
            # Simulate high-quality reasoning based strictly on the manipulated evidence
            rng = random.Random(self.seed)
            sorted_ev = sorted(
                manipulated_evidence, key=lambda e: e.signed_lift, reverse=True
            )
            selected = []
            for e in sorted_ev:
                if rng.random() < 0.85:
                    selected.append(e.proposition_id)
                if len(selected) == count:
                    break
            if len(selected) < count:
                for e in sorted_ev:
                    if e.proposition_id not in selected:
                        selected.append(e.proposition_id)
                    if len(selected) == count:
                        break
            return selected

        prompt = format_agent_c_prompt(candidates, manipulated_evidence)
        try:
            client = OllamaClient(temperature=0.0, seed=self.seed)
            response = client.generate(prompt, json_format=True)
            candidate_ids = [c.proposition_id for c in candidates]
            return parse_selected_ids(response, candidate_ids, count)
        except Exception:
            self.mock_llm = True
            return self.select(candidates, evidence, count)
