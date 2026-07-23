"""
Synthworld Benchmark Harness.
"""
from typing import Dict, List, Any
from bench.synthworld.world import SynthWorldScenario
from bench.synthworld.learners import Learner
from bench.synthworld.metrics import evaluate_learner_performance


class BenchmarkHarness:
    def __init__(self, scenario: SynthWorldScenario, steps: int = 200):
        self.scenario = scenario
        self.steps = steps

    def run_learner(self, learner: Learner) -> Dict[str, Any]:
        predictions: List[Dict[str, float]] = []
        actuals: List[Dict[str, int]] = []

        prior_events = None
        for t in range(self.steps):
            events = self.scenario.generate_step(t, prior_events=prior_events)

            # Predict P(effect at t+1) given current step events
            pred = learner.predict(t, events)
            predictions.append(pred)

            # Ingest experience
            learner.observe(t, events)

            actuals.append(events)
            prior_events = events

        # Measure performance using shift prediction/actual offset
        shifted_predictions = predictions[:-1]
        shifted_actuals = actuals[1:]

        final_beliefs = learner.beliefs()
        metrics = evaluate_learner_performance(
            self.scenario, shifted_predictions, shifted_actuals, final_beliefs, self.steps - 1
        )
        metrics["steps_run"] = self.steps
        return metrics
