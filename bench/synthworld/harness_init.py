"""Learner roster for the benchmark. Add DPAdapter here once wired."""
from .learners import TrueModel, FlatBayesian, WindowedFrequency, ContextualBayesian


def make_learners(scenario):
    return [
        TrueModel(scenario),
        FlatBayesian(scenario),
        WindowedFrequency(scenario),
        ContextualBayesian(scenario),
    ]
