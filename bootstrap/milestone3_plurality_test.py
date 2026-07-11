import os
from unittest.mock import MagicMock
from uuid import uuid4
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from cognition.schemas.theory.theory import Theory, TheoryStructured
from cognition.schemas.confidence.confidence_state import ConfidenceState

def test_process_multiple_generates_sibling_candidates():
    # Setup mocks
    flow = TheoryGenerationFlow()
    flow.client = MagicMock()
    
    # Mock primary responses
    res1 = '{"claim": "Primary claim: liquidity absorption", "mechanism": "absorption", "if_branch": {"condition": "a", "action": "b"}, "else_branch": {"condition": "c", "action": "d"}, "unless": "e", "falsified_if": "f", "mechanism_components": [], "falsification_conditions": [], "reuse_decision": "REJECTED"}'
    ext1 = '{"trigger_definition": {"field": "volume_state", "operator": "==", "value": 1, "lag": 0}, "target_definition": {"field": "outcome", "operator": "==", "value": "VAL_A"}, "scope_definition": [], "expected_direction": 1.0, "contradiction_definition": {"field": "outcome", "operator": "==", "value": "VAL_B"}, "mechanism_type": "absorption", "causal_direction": "positive", "driver": "volume_state", "mediator_or_process": "delivery_pct", "target_effect": "price compression"}'
    
    # Mock alternative responses
    res2 = '{"claim": "Alternative claim: volatility breakout", "mechanism": "breakout", "if_branch": {"condition": "x", "action": "y"}, "else_branch": {"condition": "w", "action": "z"}, "unless": "e", "falsified_if": "f", "mechanism_components": [], "falsification_conditions": [], "reuse_decision": "REJECTED"}'
    ext2 = '{"trigger_definition": {"field": "volume_state", "operator": "==", "value": 1, "lag": 0}, "target_definition": {"field": "outcome", "operator": "==", "value": "VAL_B"}, "scope_definition": [], "expected_direction": -1.0, "contradiction_definition": {"field": "outcome", "operator": "==", "value": "VAL_A"}, "mechanism_type": "breakout", "causal_direction": "negative", "driver": "volume_state", "mediator_or_process": "delivery_pct", "target_effect": "price compression"}'
    
    # Set the side effect to return the 4 sequential responses
    flow.client.generate.side_effect = [res1, ext1, res2, ext2]
    
    class DummyAbstraction:
        abstraction_summary = "test abstraction"
        
    abstraction = DummyAbstraction()
    
    # Run process_multiple
    candidates = flow.process_multiple(
        abstraction=abstraction,
        current_market_observation="Nifty closed flat.",
        count=2
    )
    
    # Assertions
    assert len(candidates) == 2
    c1, c2 = candidates[0], candidates[1]
    
    # Check they share the same alternative_group_id
    assert c1.alternative_group_id is not None
    assert c1.alternative_group_id == c2.alternative_group_id
    
    # Check they have distinct thesis/claim content
    assert c1.thesis != c2.thesis
    assert "Primary claim" in c1.thesis
    assert "Alternative claim" in c2.thesis
    
    # Check generate mock history
    assert flow.client.generate.call_count == 4
    called_prompt_3 = flow.client.generate.call_args_list[2][0][0]
    assert "MANDATORY PLURALITY REQUIREMENT" in called_prompt_3
    assert "Primary claim: liquidity absorption" in called_prompt_3
    
    print("✓ process_multiple successfully generated two sibling candidate theories with shared group ID.")

if __name__ == "__main__":
    test_process_multiple_generates_sibling_candidates()
