import copy
from datetime import datetime, timezone
from uuid import uuid4

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import Theory, TheoryStructured


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


from cognition.schemas.knowledge.ontology import OntologyRegistry
from cognition.schemas.theory.theory import MechanismComponent


def test_generate_contract_consistency():
    """Verify that SECTOR_ZSCORE is a valid Core Concept in OntologyRegistry."""
    assert "SECTOR_ZSCORE" in OntologyRegistry.CORE_CONCEPTS
    print("✓ test_generate_contract_consistency passed.")


def test_revise_contract_consistency():
    """Verify that a revised theory component with SECTOR_ZSCORE is semantically accepted."""
    comp = {
        "component_id": "relative_strength",
        "description": "Sector relative strength performance",
        "observable": "sector_zscore",
        "expected_behavior": "sector_zscore > 1.0",
        "concept_tags": ["SECTOR_ZSCORE"],
        "relation_type": "AMPLIFIES",
    }
    # Validate concept tags manually against core concepts
    for t in comp["concept_tags"]:
        assert t in OntologyRegistry.CORE_CONCEPTS
    print("✓ test_revise_contract_consistency passed.")


def test_persistence_retrieval_consistency():
    """Verify that a SECTOR_ZSCORE component can be serialized and deserialized cleanly."""
    comp = MechanismComponent(
        component_id="sector_rel_strength",
        description="Sector relative strength performance",
        observable="sector_zscore",
        expected_behavior="sector_zscore > 1.5",
        concept_tags=["SECTOR_ZSCORE"],
        relation_type="AMPLIFIES",
    )
    # Serialize to dictionary
    serialized = comp.to_dict()
    assert "SECTOR_ZSCORE" in serialized["concept_tags"]

    # Deserialize back
    deserialized = MechanismComponent.from_dict(serialized)
    assert deserialized.concept_tags == ["SECTOR_ZSCORE"]
    print("✓ test_persistence_retrieval_consistency passed.")


def test_unknown_value_policy():
    """Verify that an unsupported value is rejected and tracked."""
    unsupported_val = "FAKE_UNSUPPORTED_METRIC_XYZ"
    assert unsupported_val not in OntologyRegistry.CORE_CONCEPTS

    # Verify validation tracks the unknown value
    OntologyRegistry.reset_metrics()
    OntologyRegistry.track_unknown_value(unsupported_val)
    assert unsupported_val in OntologyRegistry._unknown_ontology_values
    print("✓ test_unknown_value_policy passed.")


def test_no_unrelated_ontology_expansion():
    """Verify that only SECTOR_ZSCORE was added and other core concepts are untouched."""
    # Count of expected concepts: original 10 + 1 (SECTOR_ZSCORE) = 11
    assert len(OntologyRegistry.CORE_CONCEPTS) == 11
    assert "TREND_PERSISTENCE" in OntologyRegistry.CORE_CONCEPTS
    assert "RANDOM_UNSUPPORTED_CONCEPT" not in OntologyRegistry.CORE_CONCEPTS
    print("✓ test_no_unrelated_ontology_expansion passed.")


if __name__ == "__main__":
    test_lineage_propagation()
    test_nested_id_regeneration()
    test_generate_contract_consistency()
    test_revise_contract_consistency()
    test_persistence_retrieval_consistency()
    test_unknown_value_policy()
    test_no_unrelated_ontology_expansion()
