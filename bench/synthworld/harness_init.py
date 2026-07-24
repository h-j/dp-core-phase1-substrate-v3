"""Learner roster for the benchmark. Add DPAdapter here once wired."""
from .learners import TrueModel, FlatBayesian, WindowedFrequency, ContextualBayesian
from .dp_adapter import DPAdapter


def make_learners(scenario):
    return [
        TrueModel(scenario),
        FlatBayesian(scenario),
        WindowedFrequency(scenario),
        ContextualBayesian(scenario),
        DPAdapter(scenario),
    ]

