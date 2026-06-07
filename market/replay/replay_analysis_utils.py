"""Shared replay analysis helpers."""


def extract_usefulness_score(value):
    """Normalize theory usefulness to a float score. Supports dict or numeric values."""
    if isinstance(value, dict):
        return float(value.get("score", 0.0))
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0
