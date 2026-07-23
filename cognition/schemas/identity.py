"""
Structural Identity Module for Cognitive Objects.

Provides deterministic structural identity formatting: "{day}:{stage}:{family_ordinal}"
and content hashing for integrity/deduplication.
"""
import hashlib
from typing import Optional


def build_structural_id(day: int, stage: str, ordinal: int = 0) -> str:
    """
    Builds a deterministic structural ID for a cognitive object.

    Format: "{day}:{stage}:{family_ordinal}"
    Example: "0:theory:0", "1:abstraction:0", "0:proposition:0"
    """
    stage_clean = stage.strip().lower()
    return f"{day}:{stage_clean}:{ordinal}"


def compute_content_hash(text: str) -> str:
    """
    Computes a deterministic content hash over LLM text for integrity and deduplication.
    """
    if not text:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
