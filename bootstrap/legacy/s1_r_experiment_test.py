from flows.synthetic_experiment.s1_r_experiment import (
    S1REnvironmentGenerator, check_epistemic_complexity,
    generate_s1_r_candidates, pearson_correlation)
from flows.synthetic_experiment.schemas import CandidateProposition, Experience


def test_s1_r_generator_produces_correct_schema():
    generator = S1REnvironmentGenerator(
        signal_strength=0.8,
        base_rate=0.5,
        noise_level=0.1,
        regime_persistence=0.9,
        sample_size=100,
        random_seed=42,
    )
    experiences = generator.generate()

    assert len(experiences) == 100
    assert all(isinstance(e, Experience) for e in experiences)
    for e in experiences:
        assert "signal_stable" in e.features
        assert "signal_small_sample" in e.features
        assert "signal_deteriorating" in e.features
        assert "signal_regime_mismatch" in e.features
        assert "signal_weak" in e.features
        assert "signal_inverse" in e.features
        assert e.outcome in ["UP", "DOWN"]


def test_pearson_correlation_calculation():
    # Deterministic test values
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert abs(pearson_correlation(x, y) - 1.0) < 1e-7

    y_inv = [10.0, 8.0, 6.0, 4.0, 2.0]
    assert abs(pearson_correlation(x, y_inv) - (-1.0)) < 1e-7

    y_noise = [2.0, 3.0, 1.0, 5.0, 4.0]
    corr = pearson_correlation(x, y_noise)
    assert -1.0 <= corr <= 1.0


def test_s1_r_candidate_generation_bounds():
    candidates = generate_s1_r_candidates(50)
    assert len(candidates) == 50
    assert all(isinstance(c, CandidateProposition) for c in candidates)

    ids = [c.proposition_id for c in candidates]
    assert len(set(ids)) == 50
