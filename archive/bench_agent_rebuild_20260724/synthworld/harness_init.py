"""
Synthworld Harness Initialization and Learner Registry.

Registers available benchmark learners:
- TruModalOracle
- ElatraverianLearner
- ContextualBayesianLearner
- DPAdapter
"""
from typing import Dict, Type
from bench.synthworld.learners import (
    Learner,
    TruModalOracle,
    ElatraverianLearner,
    ContextualBayesianLearner,
)
from bench.synthworld.dp_adapter import DPAdapter
from bench.synthworld.world import SynthWorldScenario


LEARNER_REGISTRY: Dict[str, Type[Learner]] = {
    "oracle": TruModalOracle,
    "elatraverian": ElatraverianLearner,
    "contextual_bayesian": ContextualBayesianLearner,
    "dp_adapter": DPAdapter,
}


def get_learner(learner_name: str, scenario: SynthWorldScenario) -> Learner:
    """Instantiates a learner by name for the given scenario."""
    if learner_name not in LEARNER_REGISTRY:
        raise ValueError(f"Unknown learner '{learner_name}'. Available: {list(LEARNER_REGISTRY.keys())}")
    return LEARNER_REGISTRY[learner_name](scenario)
