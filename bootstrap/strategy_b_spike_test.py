import os
import json
from unittest.mock import MagicMock
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from flows.minimal_learning_cycle.schemas import PropositionSchema
from cognition.schemas.theory.theory import TheoryStructured
from cognition.schemas.confidence.confidence_state import ConfidenceState

def test_strategy_b_spike_off():
    # Set feature flag to "0"
    os.environ["EKAMNET_STRATEGY_B_SPIKE"] = "0"
    
    flow = TheoryGenerationFlow()
    flow.client = MagicMock()
    flow.client.generate.return_value = json.dumps({
        "claim": "mocked claim",
        "mechanism": "mocked mechanism",
        "if_branch": {"condition": "volume is high", "action": "price goes up"},
        "else_branch": {"condition": "volume is low", "action": "price goes flat"},
        "unless": "unless event",
        "falsified_if": "falsified event",
        "mechanism_components": [],
        "falsification_conditions": [],
        "reuse_decision": "REJECTED"
    })
    
    class DummyAbstraction:
        abstraction_summary = "test abstraction"
        
    theory, _ = flow.process(DummyAbstraction(), regime_history={})
    
    # Assert prompt did NOT get the Strategy B additions
    prompt_used = flow.client.generate.call_args[0][0]
    assert "trigger_definition" not in prompt_used
    assert "target_definition" not in prompt_used
    
    # Optional fields should be default None
    assert theory.summary_structured.trigger_definition is None
    assert theory.summary_structured.target_definition is None

def test_strategy_b_spike_on():
    # Set feature flag to "1"
    os.environ["EKAMNET_STRATEGY_B_SPIKE"] = "1"
    
    flow = TheoryGenerationFlow()
    flow.client = MagicMock()
    flow.client.generate.return_value = json.dumps({
        "claim": "mocked claim",
        "mechanism": "mocked mechanism",
        "if_branch": {"condition": "volume is high", "action": "price goes up"},
        "else_branch": {"condition": "volume is low", "action": "price goes flat"},
        "unless": "unless event",
        "falsified_if": "falsified event",
        "mechanism_components": [],
        "falsification_conditions": [],
        "reuse_decision": "REJECTED",
        
        # Strategy B output fields:
        "trigger_definition": {"field": "volume_state", "operator": "==", "value": 1, "lag": 0},
        "target_definition": {"field": "outcome", "operator": "==", "value": "VAL_A"},
        "scope_definition": [{"field": "delivery_pct", "operator": "==", "value": 1}],
        "expected_direction": 1.0,
        "contradiction_definition": {"field": "outcome", "operator": "==", "value": "VAL_B"},
        "mechanism_type": "Liquidity Absorption",
        "causal_direction": "positive",
        "driver": "volume_state",
        "mediator_or_process": "delivery_pct",
        "target_effect": "price compression"
    })
    
    class DummyAbstraction:
        abstraction_summary = "test abstraction"
        
    theory, _ = flow.process(DummyAbstraction(), regime_history={})
    
    # Assert prompt got the Strategy B instructions
    prompt_used = flow.client.generate.call_args[0][0]
    assert "trigger_definition" in prompt_used
    assert "target_definition" in prompt_used
    
    # Optional fields should be populated correctly
    ts = theory.summary_structured
    assert ts.trigger_definition == {"field": "volume_state", "operator": "==", "value": 1, "lag": 0}
    assert ts.target_definition == {"field": "outcome", "operator": "==", "value": "VAL_A"}
    assert ts.expected_direction == 1.0
    assert ts.mechanism_type == "Liquidity Absorption"
    
    # Check PropositionSchema compilation compatibility
    prop = {
        "proposition_id": "PROP_TEST",
        "source_hypothesis_id": "HYP_TEST",
        "trigger_definition": ts.trigger_definition,
        "target_definition": ts.target_definition,
        "scope_definition": ts.scope_definition,
        "expected_direction": ts.expected_direction,
        "contradiction_definition": ts.contradiction_definition,
        "specificity_definition": {"type": "deterministic"},
        "complexity_cost": 1.0,
        "generation_source": "strategy_b_generation",
        "creation_timestamp": 12345.67,
        "lifecycle_state": "HYPOTHESIS"
    }
    assert PropositionSchema.validate(prop) is True
    print("✓ Strategy B output conforms to PropositionSchema validation requirements.")
