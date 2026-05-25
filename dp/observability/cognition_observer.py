"""Cognition observability utilities.

Tracks longitudinal cognition metrics per replay step and persists them
as a run-specific JSON time-series.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev
import json
import re
from typing import Any, Dict, List, Optional


@dataclass
class StepMetrics:
    step: int
    date: str
    contradiction_count: int = 0
    contradiction_half_life: float = 0.0
    median_contradiction_half_life: float = 0.0
    oldest_unresolved_contradiction: int = 0
    contradiction_resolution_rate: float = 0.0
    avg_contradiction_severity: float = 0.0
    highest_contradiction: float = 0.0

    theory_count: int = 0
    active_theories: int = 0
    new_theories: int = 0
    mutated_theories: int = 0
    merged_theories: int = 0
    retired_theories: int = 0
    revived_theories: int = 0
    contradicted_theories: int = 0
    avg_retirement_age: float = 0.0
    avg_revival_latency: float = 0.0
    avg_theory_age: float = 0.0
    longest_surviving_theory: int = 0
    theory_mutation_count: int = 0

    avg_confidence: float = 0.0
    confidence_delta: float = 0.0
    confidence_volatility: float = 0.0
    confidence_saturation_score: float = 0.0

    reflection_count: int = 0
    reflection_depth_score: float = 0.0
    grounded_reflection_score: float = 0.0
    meta_commentary_score: float = 0.0
    critique_specificity: float = 0.0
    memory_reference_count: int = 0
    critique_density: float = 0.0

    avg_abstraction_length: float = 0.0
    compression_ratio: float = 0.0
    generic_phrase_score: float = 0.0
    inflation_relapse_score: float = 0.0

    extras: Optional[Dict[str, Any]] = None


class CognitionObserver:
    """Observer that collects and persists cognition metrics per step."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics: List[StepMetrics] = []

    def update(
        self,
        step: int,
        date: str,
        contradiction_metrics: Dict[str, float],
        theory_metrics: Dict[str, int],
        lineage_metrics: Dict[str, float],
        confidence_values: List[float],
        reflection_text: str,
        abstractions: List[str],
        extras: Optional[Dict[str, Any]] = None,
    ) -> StepMetrics:
        """Compute and persist metrics from real cognition state."""
        contradiction_count = int(contradiction_metrics.get("active_contradictions", 0))
        contradiction_half_life = float(contradiction_metrics.get("half_life", 0.0))
        median_contradiction_half_life = float(
            contradiction_metrics.get("median_half_life", 0.0)
        )
        oldest_unresolved = int(contradiction_metrics.get("oldest_unresolved", 0))
        contradiction_resolution_rate = float(
            contradiction_metrics.get("resolution_rate", 0.0)
        )
        avg_contradiction_severity = float(
            contradiction_metrics.get("avg_severity", 0.0)
        )
        highest_contradiction = float(contradiction_metrics.get("highest", 0.0))

        theory_count = int(lineage_metrics.get("active_theories", 0))
        new_theories = int(theory_metrics.get("created", 0))
        mutated_theories = int(theory_metrics.get("mutated", 0))
        merged_theories = int(theory_metrics.get("merged", 0))
        retired_theories = int(theory_metrics.get("retired", 0))
        revived_theories = int(theory_metrics.get("revived", 0))
        contradicted_theories = int(lineage_metrics.get("contradicted_theories", 0))
        avg_retirement_age = float(lineage_metrics.get("avg_retirement_age", 0.0))
        avg_revival_latency = float(lineage_metrics.get("avg_revival_latency", 0.0))
        avg_theory_age = float(lineage_metrics.get("avg_theory_age", 0.0))
        longest_surviving = int(lineage_metrics.get("longest_surviving", 0))
        theory_mutation_count = int(lineage_metrics.get("mutation_count", 0))

        avg_conf = float(mean(confidence_values)) if confidence_values else 0.0
        confidence_delta = (
            float(confidence_values[-1] - confidence_values[0])
            if len(confidence_values) >= 2
            else 0.0
        )
        confidence_volatility = (
            float(pstdev(confidence_values)) if len(confidence_values) >= 2 else 0.0
        )
        confidence_saturation = (
            sum(1 for v in confidence_values if v > 0.85) / len(confidence_values)
            if confidence_values
            else 0.0
        )

        sentences = [s.strip() for s in reflection_text.split(".") if s.strip()]
        reflection_count = 1 if reflection_text else 0
        reflection_depth_score = float(len(sentences)) if reflection_text else 0.0
        critique_terms = [
            "weak",
            "uncertain",
            "limited",
            "contradict",
            "conflict",
            "caution",
            "fragile",
        ]
        critique_density = sum(
            reflection_text.lower().count(term) for term in critique_terms
        ) / max(1, len(reflection_text.split()))
        reflection_quality = self._reflection_quality(
            reflection_text=reflection_text,
            theory_text=str(extras.get("theory_text", "")) if extras else "",
            contradiction_text=(
                str(extras.get("contradiction_text", "")) if extras else ""
            ),
        )

        avg_ab_len = (
            float(mean([len(a.split()) for a in abstractions])) if abstractions else 0.0
        )
        obs_len = extras.get("observation_length", 1) if extras else 1
        compression_ratio = avg_ab_len / obs_len if obs_len else 0.0
        generic_phrase_score = float(
            extras.get("generic_phrase_score", 0.0) if extras else 0.0
        )
        inflation_relapse_score = float(
            extras.get("inflation_relapse_score", 0.0) if extras else 0.0
        )

        metrics = StepMetrics(
            step=step,
            date=date,
            contradiction_count=contradiction_count,
            contradiction_half_life=contradiction_half_life,
            median_contradiction_half_life=median_contradiction_half_life,
            oldest_unresolved_contradiction=oldest_unresolved,
            contradiction_resolution_rate=contradiction_resolution_rate,
            avg_contradiction_severity=avg_contradiction_severity,
            highest_contradiction=highest_contradiction,
            theory_count=theory_count,
            active_theories=theory_count,
            new_theories=new_theories,
            mutated_theories=mutated_theories,
            merged_theories=merged_theories,
            retired_theories=retired_theories,
            revived_theories=revived_theories,
            avg_theory_age=avg_theory_age,
            avg_retirement_age=avg_retirement_age,
            avg_revival_latency=avg_revival_latency,
            longest_surviving_theory=longest_surviving,
            theory_mutation_count=theory_mutation_count,
            contradicted_theories=contradicted_theories,
            avg_confidence=avg_conf,
            confidence_delta=confidence_delta,
            confidence_volatility=confidence_volatility,
            confidence_saturation_score=confidence_saturation,
            reflection_count=reflection_count,
            reflection_depth_score=reflection_depth_score,
            grounded_reflection_score=reflection_quality["grounded_reflection_score"],
            meta_commentary_score=reflection_quality["meta_commentary_score"],
            critique_specificity=reflection_quality["critique_specificity"],
            memory_reference_count=0,
            critique_density=critique_density,
            avg_abstraction_length=avg_ab_len,
            compression_ratio=compression_ratio,
            generic_phrase_score=generic_phrase_score,
            inflation_relapse_score=inflation_relapse_score,
            extras=extras,
        )

        self.metrics.append(metrics)
        with open(self.storage_path, "w") as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2, default=str)

        return metrics

    def _reflection_quality(
        self,
        reflection_text: str,
        theory_text: str,
        contradiction_text: str,
    ) -> Dict[str, float]:
        lower_reflection = reflection_text.lower()
        meta_terms = [
            "prompt",
            "provided validation",
            "validation process",
            "good-style",
            "this critique",
            "the critique",
            "requested",
            "approach",
        ]
        sharp_terms = [
            "breadth",
            "volatility",
            "participation",
            "liquidity",
            "continuation",
            "compression",
            "fragility",
            "contradiction",
            "tension",
            "unresolved",
            "weak",
            "unsupported",
            "untested",
            "evidenced",
        ]
        theory_terms = self._salient_terms(theory_text)
        contradiction_terms = self._salient_terms(contradiction_text)
        grounded_hits = sum(
            1 for term in theory_terms | contradiction_terms if term in lower_reflection
        )
        grounded_reflection_score = min(
            1.0, grounded_hits / max(1, min(4, len(theory_terms | contradiction_terms)))
        )
        meta_commentary_score = min(
            1.0,
            sum(1 for term in meta_terms if term in lower_reflection) / 2,
        )
        critique_specificity = min(
            1.0,
            sum(1 for term in sharp_terms if term in lower_reflection) / 4,
        )
        return {
            "grounded_reflection_score": round(grounded_reflection_score, 3),
            "meta_commentary_score": round(meta_commentary_score, 3),
            "critique_specificity": round(critique_specificity, 3),
        }

    def _salient_terms(self, text: str) -> set[str]:
        blocked_terms = {
            "theory",
            "market",
            "recent",
            "current",
            "contains",
            "signal",
            "explicit",
            "detected",
        }
        return {
            word
            for word in re.findall(r"[a-z][a-z-]{4,}", text.lower())
            if word not in blocked_terms
        }


def default_observer_path(base_dir: Path) -> Path:
    return base_dir / "observability_metrics.json"
