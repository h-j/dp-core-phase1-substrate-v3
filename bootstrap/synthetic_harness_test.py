from flows.synthetic_experiment.agents import AgentE
from flows.synthetic_experiment.schemas import CandidateProposition, Experience
from flows.synthetic_experiment.synthetic_harness import (
    SyntheticEnvironmentGenerator, compute_evidence, generate_candidates)


def test_synthetic_generator_produces_correct_schema():
    generator = SyntheticEnvironmentGenerator(
        signal_strength=0.8,
        base_rate=0.5,
        noise_level=0.0,  # No noise to ensure deterministic properties
        regime_persistence=1.0,  # Keep regime A
        regime_shifts=[500],
        sample_size=100,
        random_seed=42,
    )
    experiences = generator.generate()

    assert len(experiences) == 100
    assert all(isinstance(e, Experience) for e in experiences)
    for e in experiences:
        assert e.regime == "A"
        assert "signal" in e.features
        assert "spurious_signal" in e.features
        assert e.outcome in ["UP", "DOWN"]


def test_candidate_generation_bounds():
    candidates = generate_candidates(50)
    assert len(candidates) == 50
    assert all(isinstance(c, CandidateProposition) for c in candidates)

    # Validate proposition ids are unique
    ids = [c.proposition_id for c in candidates]
    assert len(set(ids)) == 50


def test_evidence_compilation_precision():
    generator = SyntheticEnvironmentGenerator(
        signal_strength=0.8,
        base_rate=0.5,
        noise_level=0.0,
        regime_persistence=1.0,
        regime_shifts=[500],
        sample_size=200,
        random_seed=42,
    )
    experiences = generator.generate()
    candidates = generate_candidates(10)
    evidence = compute_evidence(experiences, candidates)

    assert len(evidence) == 10
    evidence_map = {e.proposition_id: e for e in evidence}

    # prop_signal_up should have activation count > 0 and positive lift
    assert "prop_signal_up" in evidence_map
    sig_up = evidence_map["prop_signal_up"]
    assert sig_up.activation_count > 0
    # True relation p_conditional should be around 0.8, lift should be positive
    assert sig_up.conditional_probability > sig_up.unconditional_base_rate
    assert sig_up.signed_lift > 0.0


def test_counterfactual_inversion_behavior():
    candidates = generate_candidates(10)
    generator = SyntheticEnvironmentGenerator(
        signal_strength=0.8,
        base_rate=0.5,
        noise_level=0.0,
        regime_persistence=1.0,
        regime_shifts=[500],
        sample_size=100,
        random_seed=42,
    )
    experiences = generator.generate()
    evidence = compute_evidence(experiences, candidates)

    agent_e = AgentE(mock_llm=True, seed=42, manipulation="invert")
    manipulated = agent_e.manipulate_evidence(evidence)

    evidence_map = {e.proposition_id: e for e in evidence}
    manip_map = {e.proposition_id: e for e in manipulated}

    # Verify lift and counts are inverted
    orig = evidence_map["prop_signal_up"]
    manip = manip_map["prop_signal_up"]

    assert manip.activation_count == orig.activation_count
    assert manip.support_count == orig.contradiction_count
    assert manip.contradiction_count == orig.support_count
    assert manip.signed_lift == -orig.signed_lift
    assert manip.conditional_probability == 1.0 - orig.conditional_probability
