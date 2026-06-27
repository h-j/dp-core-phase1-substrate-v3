from collections import defaultdict
from datetime import UTC, datetime
from typing import Dict, List


class TheorySurvivalTracker:
    """
    Tracks recurring theories over time.

    Identifies:
    - Strengthening theories
    - Weakening theories
    - Unstable assumptions
    - Recurring failures
    """

    def __init__(self):
        self.theory_tracker = defaultdict(
            lambda: {
                "count": 0,
                "validations": [],
                "failures": 0,
                "last_seen": None,
                "validation_scores": [],
                "assumptions": [],
            }
        )

    def track(self, theory, validation_result):
        """Track theory performance over time."""

        thesis_key = self._normalize_thesis(theory.thesis)

        entry = self.theory_tracker[thesis_key]
        entry["count"] += 1
        entry["last_seen"] = datetime.now(UTC)
        entry["validations"].append(validation_result["validation_score"])
        entry["validation_scores"].append(validation_result["validation_score"])
        entry["assumptions"] = theory.assumptions

        if validation_result["validation_score"] < 0.4:
            entry["failures"] += 1

    def analyze_trends(self) -> Dict:
        """Analyze recurring patterns in theory survival."""

        strengthening = []
        weakening = []
        unstable = []
        failing = []

        for thesis_key, data in self.theory_tracker.items():

            if data["count"] < 2:
                continue

            avg_score = sum(data["validation_scores"]) / len(data["validation_scores"])

            recent_scores = data["validation_scores"][-3:]
            recent_avg = sum(recent_scores) / len(recent_scores)

            trend = recent_avg - avg_score

            if trend > 0.1:
                strengthening.append(
                    {
                        "thesis": thesis_key,
                        "occurrences": data["count"],
                        "avg_score": avg_score,
                        "recent_trend": trend,
                        "failure_rate": data["failures"] / data["count"],
                    }
                )

            elif trend < -0.1:
                weakening.append(
                    {
                        "thesis": thesis_key,
                        "occurrences": data["count"],
                        "avg_score": avg_score,
                        "recent_trend": trend,
                        "failure_rate": data["failures"] / data["count"],
                    }
                )

            else:
                if avg_score < 0.5:
                    unstable.append(
                        {
                            "thesis": thesis_key,
                            "occurrences": data["count"],
                            "avg_score": avg_score,
                            "failure_rate": data["failures"] / data["count"],
                        }
                    )

            if data["failures"] / data["count"] > 0.5:
                failing.append(
                    {
                        "thesis": thesis_key,
                        "occurrences": data["count"],
                        "failure_rate": data["failures"] / data["count"],
                        "last_seen": data["last_seen"],
                    }
                )

        return {
            "strengthening_theories": strengthening,
            "weakening_theories": weakening,
            "unstable_theories": unstable,
            "recurring_failures": failing,
        }

    def generate_survival_summary(self) -> str:
        """Generate human-readable survival summary."""

        trends = self.analyze_trends()

        summary = ""

        if trends["strengthening_theories"]:
            summary += "Strengthening theories: "
            for theory in trends["strengthening_theories"][:2]:
                summary += (
                    f"{theory['thesis']} "
                    f"({theory['occurrences']} validations, "
                    f"avg {theory['avg_score']:.2f}). "
                )

        if trends["weakening_theories"]:
            summary += "Weakening theories: "
            for theory in trends["weakening_theories"][:2]:
                summary += (
                    f"{theory['thesis']} "
                    f"(deteriorating, {theory['failure_rate']:.0%} failures). "
                )

        if trends["recurring_failures"]:
            summary += "Recurring failures: "
            for theory in trends["recurring_failures"][:2]:
                summary += (
                    f"{theory['thesis']} "
                    f"({theory['failure_rate']:.0%} failure rate). "
                )

        return summary

    def identify_unstable_assumptions(self) -> List[str]:
        """Identify assumptions that appear in failing theories."""

        trends = self.analyze_trends()

        unstable_assumptions = []

        for theory in trends["recurring_failures"]:
            for data in self.theory_tracker.values():
                if self._normalize_thesis(data["assumptions"]) == theory["thesis"]:
                    unstable_assumptions.extend(data["assumptions"])

        return list(set(unstable_assumptions))

    def _normalize_thesis(self, thesis) -> str:
        """Normalize thesis for comparison."""

        if isinstance(thesis, list):
            return str(thesis[:50])
        return thesis[:100]
