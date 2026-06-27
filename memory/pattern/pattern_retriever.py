from typing import List, Tuple

from cognition.schemas.pattern.pattern import Pattern
from memory.experience.experience_repository import ExperienceRepository
from memory.pattern.pattern_repository import PatternRepository
from memory.replay.regime_memory import (RegimeMatch, RegimeMemoryStore,
                                         RegimeSignature)


class PatternRetriever:
    """
    Enables Pattern Retrieval using existing Regime Signature infrastructure.
    """

    def __init__(
        self,
        pattern_repo: PatternRepository,
        experience_repo: ExperienceRepository,
        regime_memory: RegimeMemoryStore,
    ):
        self.pattern_repo = pattern_repo
        self.experience_repo = experience_repo
        self.regime_memory = regime_memory

    def retrieve_patterns(
        self,
        current_signature: RegimeSignature,
        limit: int = 3,
        min_similarity: float = 0.45,
    ) -> List[Pattern]:
        """
        Retrieves patterns by finding matches from RegimeMemoryStore,
        mapping them to experiences/dates, and scoring patterns accordingly.
        """
        # 1. Retrieve similar regimes from memory store using signature infrastructure
        matches = self.regime_memory.retrieve(
            current_signature,
            current_contradictions=[],
            limit=5,
            min_similarity=min_similarity,
        )

        matched_dates = {m.date: m.similarity for m in matches}
        all_patterns = self.pattern_repo.get_all()
        scored_patterns: List[Tuple[Pattern, float]] = []

        for pattern in all_patterns:
            max_sim = 0.0

            # Match 1: By dates of source experiences
            for exp_id in pattern.source_experience_ids:
                exp = self.experience_repo.storage.get(exp_id)
                if exp and exp.created_at in matched_dates:
                    sim = matched_dates[exp.created_at]
                    if sim > max_sim:
                        max_sim = sim

            # Match 2: Categorical fallback if no date overlap
            if max_sim == 0.0:
                # If current trend is in the pattern's regime contexts
                if current_signature.trend in pattern.regime_context:
                    max_sim = 0.5
                    # Extra confidence if volatility matches too
                    if current_signature.volatility_state in pattern.regime_context:
                        max_sim = 0.7

            if max_sim >= min_similarity:
                scored_patterns.append((pattern, max_sim))

        # Sort by similarity score descending
        scored_patterns.sort(key=lambda x: -x[1])

        # Return unique patterns up to limit
        seen_ids = set()
        result = []
        for pat, _ in scored_patterns:
            if pat.pattern_id not in seen_ids:
                seen_ids.add(pat.pattern_id)
                result.append(pat)
                if len(result) >= limit:
                    break

        return result
