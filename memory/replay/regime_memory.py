"""Run-local regime memory for deterministic replay.

Regime memory stores compact signatures from prior steps and retrieves similar
historical regimes. It is intentionally lexical/numeric and contains no future
visibility or random behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class RegimeSignature:
    date: str
    trend: str
    volatility_state: str
    sentiment: str
    confidence_profile: str
    contradiction_severity: float
    active_theory_count: int
    breadth_proxy: str = "unknown"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["contradiction_severity"] = round(self.contradiction_severity, 3)
        return data


@dataclass(frozen=True)
class RegimeMemoryRecord:
    step: int
    signature: RegimeSignature
    active_theories: List[str]
    contradictions: List[str]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "signature": self.signature.to_dict(),
            "active_theories": self.active_theories,
            "contradictions": self.contradictions,
            "confidence": round(self.confidence, 3),
        }


@dataclass(frozen=True)
class RegimeMatch:
    date: str
    similarity: float
    active_theories: List[str]
    contradictions: List[str]
    confidence: float
    recurring_contradiction: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "similarity": round(self.similarity, 3),
            "active_theories": self.active_theories,
            "contradictions": self.contradictions,
            "confidence": round(self.confidence, 3),
            "recurring_contradiction": self.recurring_contradiction,
        }


class RegimeMemoryStore:
    """In-memory historical regime lookup scoped to one replay run."""

    def __init__(self):
        self.records: List[RegimeMemoryRecord] = []

    def build_signature(
        self,
        date: str,
        observation: object,
        confidence_values: Iterable[float],
        contradiction_severity: float,
        active_theory_count: int,
    ) -> RegimeSignature:
        values = list(confidence_values)
        avg_confidence = mean(values) if values else 0.5
        if avg_confidence >= 0.57:
            confidence_profile = "elevated"
        elif avg_confidence <= 0.43:
            confidence_profile = "pressured"
        else:
            confidence_profile = "neutral"

        return RegimeSignature(
            date=date,
            trend=getattr(observation, "trend_state", "unknown"),
            volatility_state=getattr(observation, "volatility_state", "unknown"),
            sentiment=getattr(observation, "macro_sentiment", "unknown"),
            confidence_profile=confidence_profile,
            contradiction_severity=round(float(contradiction_severity), 3),
            active_theory_count=int(active_theory_count),
            breadth_proxy=getattr(observation, "breadth_state", "unknown"),
        )

    def retrieve(
        self,
        signature: RegimeSignature,
        current_contradictions: Iterable[str],
        limit: int = 3,
        min_similarity: float = 0.45,
    ) -> List[RegimeMatch]:
        matches, _ = self.retrieve_explainable(
            signature=signature,
            current_contradictions=current_contradictions,
            limit=limit,
            min_similarity=min_similarity,
        )
        return matches

    def retrieve_explainable(
        self,
        signature: RegimeSignature,
        current_contradictions: Iterable[str],
        limit: int = 3,
        min_similarity: float = 0.45,
    ) -> Tuple[List[RegimeMatch], Any]:
        from memory.provenance import (
            IgnoredCandidate,
            RetrievalDetail,
            RetrievalExplanation,
        )

        current_contradictions = list(current_contradictions)
        matches: List[RegimeMatch] = []
        ignored: List[IgnoredCandidate] = []
        details: List[RetrievalDetail] = []

        max_step = max([r.step for r in self.records], default=1)

        for record in self.records:
            similarity = self._similarity(signature, record.signature)
            if similarity < min_similarity:
                ignored.append(
                    IgnoredCandidate(
                        memory_id=f"MEM_{record.signature.date}",
                        date=record.signature.date,
                        similarity=round(similarity, 4),
                        reason=f"Similarity {similarity:.3f} below minimum threshold {min_similarity:.3f}",
                    )
                )
                continue

            recurring = self._recurring_contradiction(
                current_contradictions,
                record.contradictions,
            )
            match = RegimeMatch(
                date=record.signature.date,
                similarity=similarity,
                active_theories=record.active_theories[:3],
                contradictions=record.contradictions[:3],
                confidence=record.confidence,
                recurring_contradiction=recurring,
            )
            matches.append(match)

        sorted_matches = sorted(matches, key=lambda item: (-item.similarity, item.date))[:limit]

        for rank, match in enumerate(sorted_matches, 1):
            # Recency factor
            rec_record = next((r for r in self.records if r.signature.date == match.date), None)
            rec_step = rec_record.step if rec_record else 0
            step_diff = max(0, max_step - rec_step)
            recency_contrib = round(max(0.0, 1.0 - (step_diff * 0.05)), 4)
            retrieval_score = round(0.8 * match.similarity + 0.2 * recency_contrib, 4)

            details.append(
                RetrievalDetail(
                    memory_id=f"MEM_{match.date}",
                    date=match.date,
                    retrieval_score=retrieval_score,
                    ranking=rank,
                    similarity=round(match.similarity, 4),
                    recency_contribution=recency_contrib,
                    usefulness_estimate=round(match.confidence, 4),
                    provenance_chain=[
                        f"record_date:{match.date}",
                        f"record_step:{rec_step}",
                        f"active_theories:{','.join(match.active_theories[:2])}",
                    ],
                )
            )

        explanation = RetrievalExplanation(
            retrieved_memories=details,
            ignored_candidates=ignored,
            retrieval_success=len(details) > 0,
            query_signature={"date": signature.date, "vol_state": signature.volatility_state},
            top_score=details[0].retrieval_score if details else 0.0,
        )

        return sorted_matches, explanation

    def persist(
        self,
        step: int,
        signature: RegimeSignature,
        active_theories: Iterable[object],
        contradictions: Iterable[str],
        confidence: float,
    ) -> RegimeMemoryRecord:
        record = RegimeMemoryRecord(
            step=step,
            signature=signature,
            active_theories=[
                getattr(theory, "id", str(theory)) for theory in active_theories
            ][:5],
            contradictions=list(contradictions)[:5],
            confidence=float(confidence),
        )
        self.records.append(record)
        return record

    def recall_hit_rate(self) -> float:
        if not self.records:
            return 0.0
        retrievable = sum(
            1
            for idx, record in enumerate(self.records)
            if any(
                self._similarity(record.signature, prior.signature) >= 0.45
                for prior in self.records[:idx]
            )
        )
        return retrievable / len(self.records)

    def retrieval_usefulness(
        self, matches_by_step: Iterable[List[RegimeMatch]]
    ) -> float:
        step_scores = []
        for matches in matches_by_step:
            if not matches:
                step_scores.append(0.0)
                continue
            match_score = mean(match.similarity for match in matches)
            contradiction_bonus = (
                0.1 if any(match.recurring_contradiction for match in matches) else 0.0
            )
            step_scores.append(min(1.0, match_score + contradiction_bonus))
        return mean(step_scores) if step_scores else 0.0

    def _similarity(
        self, current: RegimeSignature, historical: RegimeSignature
    ) -> float:
        categorical_weights: Dict[str, float] = {
            "trend": 0.18,
            "volatility_state": 0.18,
            "sentiment": 0.14,
            "confidence_profile": 0.14,
            "breadth_proxy": 0.14,
        }
        score = sum(
            weight
            for field_name, weight in categorical_weights.items()
            if getattr(current, field_name) == getattr(historical, field_name)
        )
        severity_delta = abs(
            current.contradiction_severity - historical.contradiction_severity
        )
        score += 0.12 * max(0.0, 1.0 - severity_delta)
        theory_delta = abs(current.active_theory_count - historical.active_theory_count)
        score += 0.10 * max(0.0, 1.0 - theory_delta / 8)
        return round(min(1.0, score), 3)

    def _recurring_contradiction(
        self,
        current: List[str],
        historical: List[str],
    ) -> Optional[str]:
        current_norm = {self._normalize(item): item for item in current}
        historical_norm = {self._normalize(item): item for item in historical}
        for normalized in sorted(current_norm):
            if normalized and normalized in historical_norm:
                return current_norm[normalized]
        return None

    def _normalize(self, value: str) -> str:
        return " ".join(str(value).lower().replace("_", " ").split())
