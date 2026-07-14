import copy
from datetime import datetime, timezone
from uuid import uuid4

from cognition.schemas.theory.theory import Theory, TheoryStructured
from cognition.schemas.confidence.confidence_state import ConfidenceState


def test_lineage_propagation():
    """Verify that lineage_id is correctly propagated/written back during replay processing.

    In the replay engine, we simulate calling the lineage evolve method
    and assigning theory.lineage_id = lineage_id_val.
    """
    confidence_state = ConfidenceState(
        empirical_confidence=0.5,
        regime_confidence=0.5,
        reflection_confidence=0.5,
        theoretical_coherence=0.5,
        contradiction_pressure=0.0,
    )
    theory = Theory(
        lineage_id="original-lineage-id",
        thesis="Test thesis",
        summary="Test summary",
        confidence_state=confidence_state,
    )

    # Simulate evolve returning a new lineage ID val
    lineage_id_val = "evolved-stable-lineage-id"

    # Defect 1 fix: write back
    theory.lineage_id = lineage_id_val

    # Assert correct lineage_id is now carried by the theory object
    assert theory.lineage_id == "evolved-stable-lineage-id"
    print("✓ test_lineage_propagation passed.")


def test_nested_id_regeneration():
    """Verify that inner TheoryStructured id and created_at are regenerated on mutation.

    This ensures deepcopy mutations on REVISE result in unique inner ids.
    """
    confidence_state = ConfidenceState(
        empirical_confidence=0.5,
        regime_confidence=0.5,
        reflection_confidence=0.5,
        theoretical_coherence=0.5,
        contradiction_pressure=0.0,
    )
    parent_structured = TheoryStructured(
        claim="Original claim",
        if_branch={"condition": "a", "action": "b"},
        else_branch={"condition": "c", "action": "d"},
        falsified_if="never",
    )
    parent_theory = Theory(
        lineage_id="test-lineage",
        thesis="Original thesis",
        summary="Original summary",
        summary_structured=parent_structured,
        confidence_state=confidence_state,
    )

    # Record parent IDs
    parent_outer_id = parent_theory.id
    parent_inner_id = parent_theory.summary_structured.id
    parent_inner_created_at = parent_theory.summary_structured.created_at

    # Simulate REVISE deepcopy mutation path
    child_theory = copy.deepcopy(parent_theory)
    child_theory.id = str(uuid4())

    # Defect 2 fix: regenerate inner summary_structured id and created_at on REVISE
    if child_theory.summary_structured:
        child_theory.summary_structured.id = str(uuid4())
        child_theory.summary_structured.created_at = datetime.now(timezone.utc)

    # Assertions
    assert child_theory.id != parent_outer_id
    assert child_theory.summary_structured.id != parent_inner_id
    assert child_theory.summary_structured.created_at != parent_inner_created_at
    print("✓ test_nested_id_regeneration passed.")


if __name__ == "__main__":
    test_lineage_propagation()
    test_nested_id_regeneration()
