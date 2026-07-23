"""
Regression Test for SD-001: Structural Identity Reachability Across Cosmetic Prompt Layout Changes.

Asserts that identity of evolving cognitive objects (theories, abstractions, propositions, lineages)
is governed by deterministic Structural Identity ("{day}:{stage}:{family_ordinal}") rather than text content hashes.
Cosmetic prompt layout changes (extra whitespace, line breaks, section reordering) alter content_hash
while the structural ID and lineage ID remain 100% reachable and identical.
"""
from pathlib import Path
import tempfile
import pytest

from cognition.schemas.identity import build_structural_id, compute_content_hash
from memory.lineage.theory_lineage import TheoryLineageEngine


def test_structural_id_formatting():
    """Verify structural ID formatting specification "{day}:{stage}:{family_ordinal}"."""
    assert build_structural_id(0, "theory", 0) == "0:theory:0"
    assert build_structural_id(1, "abstraction", 0) == "1:abstraction:0"
    assert build_structural_id(2, "proposition", 1) == "2:proposition:1"


def test_sd001_regression_structural_identity_reachability_across_cosmetic_changes():
    """
    REGRESSION TEST REPRODUCING SD-001:
    1. Run lineage generation with prompt layout template A.
    2. Record structural ID ("0:theory:0"), lineage ID ("0:theory:0"), and content_hash A.
    3. Introduce a cosmetic prompt-layout change (extra whitespace / line breaks / section reordering).
    4. Rerun lineage generation with prompt layout template B.
    5. Assert lineage remains reachable by the SAME structural ID ("0:theory:0") while content_hash differs.
    """
    text_template_a = (
        "Market Memory: RELIANCE 2026-07-01\n"
        "Current Market Observation: Absorption in compression regime.\n"
        "Claim: Compression regime driven by passive absorption."
    )

    text_template_b = (
        "=== MARKET MEMORY ===\n"
        "  RELIANCE 2026-07-01  \n\n"
        "CURRENT MARKET OBSERVATION:\n"
        "  Absorption in compression regime.\n\n"
        "CLAIM:\n"
        "  Compression regime driven by passive absorption."
    )

    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        path1 = Path(tmpdir1) / "lineage1.json"
        engine1 = TheoryLineageEngine(storage_path=path1)
        res1 = engine1.evolve_theory(text_template_a, confidence_state={}, step=0)
        rec1 = res1["record"]

        path2 = Path(tmpdir2) / "lineage2.json"
        engine2 = TheoryLineageEngine(storage_path=path2)
        res2 = engine2.evolve_theory(text_template_b, confidence_state={}, step=0)
        rec2 = res2["record"]

        # Structural IDs and Lineage IDs MUST BE BIT-IDENTICAL
        assert rec1.id == "0:theory:0"
        assert rec2.id == "0:theory:0"
        assert rec1.lineage_id == "0:theory:0"
        assert rec2.lineage_id == "0:theory:0"
        assert rec1.id == rec2.id
        assert rec1.lineage_id == rec2.lineage_id

        # Content Hashes MUST DIFFER due to cosmetic prompt layout changes
        assert rec1.content_hash != rec2.content_hash
        assert rec1.content_hash == compute_content_hash(text_template_a)
        assert rec2.content_hash == compute_content_hash(text_template_b)

        # Counterfactual targeting check: target by structural ID
        target_lineage_id = "0:theory:0"
        found1 = engine1.get_theory(target_lineage_id)
        found2 = engine2.get_theory(target_lineage_id)
        assert found1 is not None
        assert found2 is not None
        assert found1.id == target_lineage_id
        assert found2.id == target_lineage_id
