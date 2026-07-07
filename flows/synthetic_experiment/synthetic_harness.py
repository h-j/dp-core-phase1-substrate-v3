import random
from typing import Any, Dict, List, Optional

from flows.synthetic_experiment.schemas import (CandidateProposition,
                                                EvidenceObject, Experience,
                                                PlantedRelation, Predicate,
                                                RelationType)


def check_predicate(experience: Experience, predicate: Predicate) -> bool:
    """Helper to check if a predicate matches an experience."""
    field = predicate.field
    val = None
    if field == "regime":
        val = experience.regime
    elif field == "outcome":
        val = experience.outcome
    else:
        val = experience.features.get(field)

    if val is None:
        return False

    op = predicate.operator
    if op == "==":
        return str(val) == str(predicate.value)
    elif op == "!=":
        return str(val) != str(predicate.value)
    try:
        if op == ">":
            return float(val) > float(predicate.value)
        elif op == ">=":
            return float(val) >= float(predicate.value)
        elif op == "<":
            return float(val) < float(predicate.value)
        elif op == "<=":
            return float(val) <= float(predicate.value)
    except (ValueError, TypeError):
        return False
    return False


class SyntheticEnvironmentGenerator:
    def __init__(
        self,
        signal_strength: float = 0.8,
        base_rate: float = 0.5,
        noise_level: float = 0.1,
        regime_persistence: float = 0.9,
        regime_shifts: Optional[List[int]] = None,
        sample_size: int = 1000,
        random_seed: int = 42,
    ) -> None:
        self.signal_strength = signal_strength
        self.base_rate = base_rate
        self.noise_level = noise_level
        self.regime_persistence = regime_persistence
        self.regime_shifts = regime_shifts or [500]
        self.sample_size = sample_size
        self.random_seed = random_seed

    def generate(self) -> List[Experience]:
        random.seed(self.random_seed)
        experiences = []
        regime = "A"

        for t in range(1, self.sample_size + 1):
            # 1. Transition regime
            if t > 1:
                if random.random() > self.regime_persistence:
                    regime = "B" if regime == "A" else "A"

            # 2. Generate features
            signal = "high" if random.random() < 0.3 else "low"
            spurious_signal = "high" if random.random() < 0.3 else "low"
            signal_decay = "high" if random.random() < 0.3 else "low"
            signal_shift = "high" if random.random() < 0.3 else "low"

            features = {
                "signal": signal,
                "spurious_signal": spurious_signal,
                "signal_decay": signal_decay,
                "signal_shift": signal_shift,
            }
            # Add 21 dummy features so total candidate propositions is 50
            for i in range(1, 22):
                features[f"dummy_{i}"] = "high" if random.random() < 0.3 else "low"

            # 3. Determine outcome probability
            p_up = self.base_rate
            if regime == "A":
                if signal == "high":
                    p_up = self.signal_strength
                elif signal_decay == "high":
                    # Decays linearly from signal_strength to base_rate over the run
                    p_up = self.signal_strength - (
                        self.signal_strength - self.base_rate
                    ) * (t / self.sample_size)
                elif signal_shift == "high":
                    # Reverses after regime shift
                    is_shifted = False
                    for shift in self.regime_shifts:
                        if t >= shift:
                            is_shifted = not is_shifted
                    p_up = (
                        (1.0 - self.signal_strength)
                        if is_shifted
                        else self.signal_strength
                    )

            # 4. Generate realized outcome with noise
            if random.random() < self.noise_level:
                outcome = "UP" if random.random() < 0.5 else "DOWN"
            else:
                outcome = "UP" if random.random() < p_up else "DOWN"

            exp = Experience(
                timestamp=t,
                regime=regime,
                features=features,
                outcome=outcome,
            )
            experiences.append(exp)

        return experiences


def generate_candidates(num_candidates: int = 50) -> List[CandidateProposition]:
    """Generates a deterministic pool of candidate propositions using a closed grammar."""
    features = ["signal", "spurious_signal", "signal_decay", "signal_shift"]
    num_dummies = (num_candidates // 2) - len(features)
    for i in range(1, num_dummies + 1):
        features.append(f"dummy_{i}")

    candidates = []
    for feat in features:
        for target_val in ["UP", "DOWN"]:
            prop_id = f"prop_{feat}_{target_val.lower()}"
            cand = CandidateProposition(
                proposition_id=prop_id,
                trigger_predicate=Predicate(field=feat, operator="==", value="high"),
                scope_predicates=[Predicate(field="regime", operator="==", value="A")],
                expected_effect_predicate=Predicate(
                    field="outcome", operator="==", value=target_val
                ),
                evaluation_horizon=1,
            )
            candidates.append(cand)

    return candidates[:num_candidates]


def compute_evidence(
    experiences: List[Experience],
    candidates: List[CandidateProposition],
) -> List[EvidenceObject]:
    """Computes EvidenceObjects for each CandidateProposition over a set of experiences."""
    evidence_objects = []

    for candidate in candidates:
        activations = 0
        supported = 0
        contradicted = 0

        target_value = candidate.expected_effect_predicate.value

        # Calculate base rate of outcome within the scope
        scope_count = 0
        target_in_scope_count = 0

        # Split experiences for stability score calculation
        mid = len(experiences) // 2
        first_half = experiences[:mid]
        second_half = experiences[mid:]

        def compute_subset_lift(subset: List[Experience]) -> float:
            act = 0
            sup = 0
            sc = 0
            tgt_sc = 0
            for exp in subset:
                scope_ok = all(
                    check_predicate(exp, p) for p in candidate.scope_predicates
                )
                if scope_ok:
                    sc += 1
                    if exp.outcome == target_value:
                        tgt_sc += 1
                    if check_predicate(exp, candidate.trigger_predicate):
                        act += 1
                        if exp.outcome == target_value:
                            sup += 1
            cond = (sup / act) if act > 0 else 0.0
            base = (tgt_sc / sc) if sc > 0 else 0.5
            return cond - base

        for exp in experiences:
            scope_ok = all(check_predicate(exp, p) for p in candidate.scope_predicates)
            if not scope_ok:
                continue

            scope_count += 1
            if exp.outcome == target_value:
                target_in_scope_count += 1

            if check_predicate(exp, candidate.trigger_predicate):
                activations += 1
                if exp.outcome == target_value:
                    supported += 1
                else:
                    contradicted += 1

        cond_prob = (supported / activations) if activations > 0 else 0.0
        base_rate = (target_in_scope_count / scope_count) if scope_count > 0 else 0.5
        signed_lift = cond_prob - base_rate
        absolute_lift = abs(signed_lift)
        uncertainty = 1.0 / (activations**0.5) if activations > 0 else 1.0

        lift_1 = compute_subset_lift(first_half)
        lift_2 = compute_subset_lift(second_half)
        stability = 1.0 - abs(lift_1 - lift_2)

        ev = EvidenceObject(
            proposition_id=candidate.proposition_id,
            activation_count=activations,
            support_count=supported,
            contradiction_count=contradicted,
            conditional_probability=cond_prob,
            unconditional_base_rate=base_rate,
            signed_lift=signed_lift,
            absolute_lift=absolute_lift,
            uncertainty_score=uncertainty,
            stability_score=stability,
        )
        evidence_objects.append(ev)

    return evidence_objects
