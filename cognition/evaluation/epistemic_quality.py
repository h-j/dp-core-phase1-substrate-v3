"""
Heuristic epistemic quality scoring for generated cognition text.

These metrics are intentionally lightweight. They make narrative inflation
visible without replacing human inspection or LLM generation.
"""

import re
from collections import Counter

GENERIC_PHRASES = [
    "the market is characterized by",
    "investor confidence suggests",
    "stable upward trajectory",
    "this indicates that",
    "the market demonstrates",
    "participants are optimistic",
    "market dynamics are inherently complex",
    "viable framework",
    "stable growth due to",
]

UNCERTAINTY_TERMS = [
    "may",
    "might",
    "could",
    "uncertain",
    "uncertainty",
    "weakly",
    "insufficient",
    "ambiguous",
    "not yet",
    "untested",
    "limited evidence",
]

CONTRADICTION_TERMS = [
    "contradiction",
    "contradict",
    "tension",
    "divergence",
    "conflict",
    "unresolved",
    "inconsistent",
    "despite",
    "however",
]

CAUSAL_INFLATION_PATTERNS = [
    r"\bdue to\b",
    r"\bbecause\b",
    r"\bcaused by\b",
    r"\bleads? to\b",
    r"\bdriven by\b",
    r"\battributed to\b",
    r"\bresults? in\b",
]

SHARP_TERMS = [
    "volatility",
    "breadth",
    "liquidity",
    "participation",
    "regime",
    "continuation",
    "reversal",
    "compression",
    "expansion",
    "coherence",
    "support",
    "tested",
]


def evaluate_epistemic_quality(text: str) -> dict:
    """Return simple heuristic scores for epistemic compression."""
    normalized = _normalize(text)
    words = _words(normalized)
    sentence_count = max(1, len(_sentences(text)))
    word_count = len(words)

    generic_hits = _phrase_hits(normalized, GENERIC_PHRASES)
    causal_hits = sum(
        len(re.findall(pattern, normalized)) for pattern in CAUSAL_INFLATION_PATTERNS
    )
    uncertainty_hits = _term_hits(normalized, UNCERTAINTY_TERMS)
    contradiction_hits = _term_hits(normalized, CONTRADICTION_TERMS)
    sharp_hits = _term_hits(normalized, SHARP_TERMS)
    repeated_terms = _semantic_repetition(words)

    narrative_density = _clamp(
        (word_count / sentence_count - 14) / 24
        + generic_hits * 0.12
        + causal_hits * 0.08
    )
    causal_inflation = _clamp(causal_hits / sentence_count)
    semantic_repetition = _clamp(repeated_terms / max(1, len(set(words))))
    uncertainty_presence = _clamp(uncertainty_hits / 2)
    contradiction_acknowledgment = _clamp(contradiction_hits / 2)
    abstraction_sharpness = _clamp(
        sharp_hits / max(4, sentence_count * 2)
        - generic_hits * 0.12
        - narrative_density * 0.18
    )

    compression_score = _clamp(
        0.35 * abstraction_sharpness
        + 0.2 * uncertainty_presence
        + 0.2 * contradiction_acknowledgment
        + 0.15 * (1 - narrative_density)
        + 0.1 * (1 - causal_inflation)
    )

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "narrative_density": round(narrative_density, 3),
        "uncertainty_presence": round(uncertainty_presence, 3),
        "contradiction_acknowledgment": round(
            contradiction_acknowledgment,
            3,
        ),
        "abstraction_sharpness": round(abstraction_sharpness, 3),
        "causal_inflation": round(causal_inflation, 3),
        "semantic_repetition": round(semantic_repetition, 3),
        "generic_phrase_hits": generic_hits,
        "compression_score": round(compression_score, 3),
    }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z-]{2,}", text.lower())


def _phrase_hits(text: str, phrases: list[str]) -> int:
    return sum(1 for phrase in phrases if phrase in text)


def _term_hits(text: str, terms: list[str]) -> int:
    return sum(len(re.findall(rf"\b{re.escape(term)}\b", text)) for term in terms)


def _semantic_repetition(words: list[str]) -> int:
    stop_words = {
        "the",
        "and",
        "that",
        "with",
        "this",
        "from",
        "under",
        "market",
        "theory",
    }
    counts = Counter(word for word in words if word not in stop_words)
    return sum(count - 2 for count in counts.values() if count > 2)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
