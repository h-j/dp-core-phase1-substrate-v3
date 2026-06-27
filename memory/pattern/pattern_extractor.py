from typing import Dict, List, Tuple

from cognition.schemas.experience.experience import Experience
from cognition.schemas.pattern.pattern import Pattern
from memory.experience.experience_repository import ExperienceRepository
from memory.pattern.pattern_repository import PatternRepository


class PatternExtractor:
    """
    Scans and extracts recurring causal failure sequences across experiences.
    Requires evidence from multiple experiences.
    """

    def __init__(
        self, experience_repo: ExperienceRepository, pattern_repo: PatternRepository
    ):
        self.experience_repo = experience_repo
        self.pattern_repo = pattern_repo

    def extract_patterns(self) -> List[Pattern]:
        """
        Scans all experiences, groups by failure signature, and saves extracted patterns.
        """
        experiences = self.experience_repo.get_all()

        # Group experiences by: (failed_component, root_cause, contradiction_signatures_tuple)
        groups: Dict[Tuple[str, str, Tuple[str, ...]], List[Experience]] = {}

        for exp in experiences:
            # Experience contradictions as signature list
            contra_sig = tuple(sorted(exp.contradictions)) if exp.contradictions else ()

            # Look for failure events in causal_events
            events = getattr(exp, "causal_events", []) or []
            if isinstance(exp, dict):
                events = exp.get("causal_events", []) or []

            for event in events:
                # We care about validation failures
                components_failed = event.get("components_failed") or []
                root_cause = event.get("root_cause")

                if components_failed and root_cause:
                    for comp in components_failed:
                        key = (comp, root_cause, contra_sig)
                        if key not in groups:
                            groups[key] = []
                        if exp.experience_id not in [
                            e.experience_id for e in groups[key]
                        ]:
                            groups[key].append(exp)

        extracted_patterns = []

        for (comp, root_cause, contra_tuple), exps in groups.items():
            # Requirement: Require evidence from multiple experiences (>= 2)
            if len(exps) < 2:
                continue

            # Build unique pattern id based on components
            pattern_id = f"pat_{comp}_{root_cause}"
            pattern_id = "".join(
                c if c.isalnum() or c in "_-" else "_" for c in pattern_id
            ).lower()

            # Aggregate regimes and outcomes
            regimes = set()
            for exp in exps:
                if exp.regime_context:
                    regimes.update(exp.regime_context)

            support_count = sum(exp.validation_count for exp in exps)
            contradiction_count = sum(exp.falsification_count for exp in exps)
            total = support_count + contradiction_count
            confidence = support_count / total if total > 0 else 1.0

            # Build lesson text explaining the sequence
            regime_str = ", ".join(sorted(list(regimes))) if regimes else "general"
            contra_str = ", ".join(list(contra_tuple)) if contra_tuple else "none"
            lesson_text = (
                f"Pattern failure repeatedly observed in '{comp}' due to '{root_cause}' "
                f"under contradictions [{contra_str}] in '{regime_str}' regimes. "
                f"Lesson: Adjust logic branches or assumptions to preemptively handle '{root_cause}'."
            )

            pattern = Pattern(
                pattern_id=pattern_id,
                failed_component=comp,
                root_cause=root_cause,
                contradiction_signatures=list(contra_tuple),
                regime_context=list(regimes),
                source_experience_ids=[exp.experience_id for exp in exps],
                support_count=support_count,
                contradiction_count=contradiction_count,
                confidence=confidence,
                lesson_text=lesson_text,
            )
            self.pattern_repo.save(pattern)
            extracted_patterns.append(pattern)

        return extracted_patterns
