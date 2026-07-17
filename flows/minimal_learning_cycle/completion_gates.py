import json
import math
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, model_validator


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INDETERMINATE = "INDETERMINATE"


class ClaimStatus(str, Enum):
    CLAIM_SUPPORTED = "CLAIM_SUPPORTED"
    CLAIM_CONTRADICTED = "CLAIM_CONTRADICTED"
    CLAIM_NOT_DEMONSTRATED = "CLAIM_NOT_DEMONSTRATED"
    CLAIM_INDETERMINATE = "CLAIM_INDETERMINATE"
    NEUTRAL_EFFECT_DEMONSTRATED = "NEUTRAL_EFFECT_DEMONSTRATED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INSUFFICIENTLY_POWERED = "INSUFFICIENTLY_POWERED"
    INDETERMINATE_NO_POWER_TARGET_DEFINED = "INDETERMINATE_NO_POWER_TARGET_DEFINED"
    NO_DIFFERENCE = "NO_DIFFERENCE"


class ClaimType(str, Enum):
    POSITIVE_IMPROVEMENT = "positive_improvement"
    HARM_DEGRADATION = "harm_degradation"
    NO_DIFFERENCE = "no_difference"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENTLY_POWERED = "insufficiently_powered"
    CLAIM_CONTRADICTED = "claim_contradicted"
    INDETERMINATE_NO_POWER_TARGET_DEFINED = "indeterminate_no_power_target_defined"


class ClaimSpecification(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    minimum_meaningful_effect: float | None = None
    expected_baseline_proportion: float | None = None
    confidence_level: float = 0.95
    target_power: float = 0.80


class MilestoneCompletionGates(BaseModel):
    milestone_id: str
    ISOLATION_GATE_STATUS: GateStatus = GateStatus.INDETERMINATE
    CAUSAL_NECESSITY_GATE_STATUS: GateStatus = GateStatus.INDETERMINATE
    MECHANISM_STRENGTH_GATE_STATUS: GateStatus = GateStatus.INDETERMINATE
    DIAGNOSTIC_PRIMARY_SEPARATION_STATUS: GateStatus = GateStatus.INDETERMINATE
    RESOURCE_CONTAMINATION_STATUS: GateStatus = GateStatus.INDETERMINATE
    SAFEGUARD_BENEFIT_STATUS: GateStatus = GateStatus.INDETERMINATE
    SAFEGUARD_COST_STATUS: GateStatus = GateStatus.INDETERMINATE
    COMPLETE_LIFECYCLE_ACCOUNTING_STATUS: GateStatus = GateStatus.INDETERMINATE
    CLAIM_SCOPE_STATUS: GateStatus = GateStatus.INDETERMINATE
    REGRESSION_SAFETY_STATUS: GateStatus = GateStatus.INDETERMINATE

    # Epoch 9 Completion Gates
    CANONICAL_STATE_CORRECTION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    REPOSITORY_REALITY_INSPECTION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    PERSISTENT_PRE_REGISTRATION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    SEED_OVERLAP_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    FUTURE_DATA_ISOLATION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    PRIMARY_BEHAVIORAL_METRIC_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    PRIMARY_EPISTEMIC_METRIC_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    PRIMARY_EPISTEMIC_METRIC_MEASUREMENT_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    EVIDENCE_SUFFICIENCY_REQUIREMENT_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    EVIDENCE_SUFFICIENCY_SATISFACTION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    MEMORY_INFLUENCE_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    CAUSAL_ATTRIBUTION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    FAMILY_A_RESULT_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    FAMILY_B_RESULT_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    NEGATIVE_MEMORY_OVERGENERALIZATION_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    RESOURCE_METRIC_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    CLAIM_EVIDENCE_GATE_REPAIR_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    CLAIM_EVIDENCE_CONSISTENCY_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    MILESTONE_SCIENTIFIC_CLOSURE_STATUS: GateStatus = GateStatus.NOT_APPLICABLE
    VERDICT_INTEGRITY_STATUS: GateStatus = GateStatus.NOT_APPLICABLE

    @model_validator(mode="after")
    def validate_milestone_gates(self) -> "MilestoneCompletionGates":
        """
        Ensures that if any gate is FAIL or INDETERMINATE, the milestone cannot be closed.
        Exception is if the gate is explicitly marked as NOT_APPLICABLE.
        """
        gates = [
            ("ISOLATION_GATE_STATUS", self.ISOLATION_GATE_STATUS),
            ("CAUSAL_NECESSITY_GATE_STATUS", self.CAUSAL_NECESSITY_GATE_STATUS),
            ("MECHANISM_STRENGTH_GATE_STATUS", self.MECHANISM_STRENGTH_GATE_STATUS),
            (
                "DIAGNOSTIC_PRIMARY_SEPARATION_STATUS",
                self.DIAGNOSTIC_PRIMARY_SEPARATION_STATUS,
            ),
            ("RESOURCE_CONTAMINATION_STATUS", self.RESOURCE_CONTAMINATION_STATUS),
            ("SAFEGUARD_BENEFIT_STATUS", self.SAFEGUARD_BENEFIT_STATUS),
            ("SAFEGUARD_COST_STATUS", self.SAFEGUARD_COST_STATUS),
            (
                "COMPLETE_LIFECYCLE_ACCOUNTING_STATUS",
                self.COMPLETE_LIFECYCLE_ACCOUNTING_STATUS,
            ),
            ("CLAIM_SCOPE_STATUS", self.CLAIM_SCOPE_STATUS),
            ("REGRESSION_SAFETY_STATUS", self.REGRESSION_SAFETY_STATUS),
            (
                "CANONICAL_STATE_CORRECTION_STATUS",
                self.CANONICAL_STATE_CORRECTION_STATUS,
            ),
            (
                "REPOSITORY_REALITY_INSPECTION_STATUS",
                self.REPOSITORY_REALITY_INSPECTION_STATUS,
            ),
            (
                "PERSISTENT_PRE_REGISTRATION_STATUS",
                self.PERSISTENT_PRE_REGISTRATION_STATUS,
            ),
            ("SEED_OVERLAP_STATUS", self.SEED_OVERLAP_STATUS),
            ("FUTURE_DATA_ISOLATION_STATUS", self.FUTURE_DATA_ISOLATION_STATUS),
            ("PRIMARY_BEHAVIORAL_METRIC_STATUS", self.PRIMARY_BEHAVIORAL_METRIC_STATUS),
            ("PRIMARY_EPISTEMIC_METRIC_STATUS", self.PRIMARY_EPISTEMIC_METRIC_STATUS),
            (
                "PRIMARY_EPISTEMIC_METRIC_MEASUREMENT_STATUS",
                self.PRIMARY_EPISTEMIC_METRIC_MEASUREMENT_STATUS,
            ),
            (
                "EVIDENCE_SUFFICIENCY_REQUIREMENT_STATUS",
                self.EVIDENCE_SUFFICIENCY_REQUIREMENT_STATUS,
            ),
            (
                "EVIDENCE_SUFFICIENCY_SATISFACTION_STATUS",
                self.EVIDENCE_SUFFICIENCY_SATISFACTION_STATUS,
            ),
            ("MEMORY_INFLUENCE_STATUS", self.MEMORY_INFLUENCE_STATUS),
            ("CAUSAL_ATTRIBUTION_STATUS", self.CAUSAL_ATTRIBUTION_STATUS),
            ("FAMILY_A_RESULT_STATUS", self.FAMILY_A_RESULT_STATUS),
            ("FAMILY_B_RESULT_STATUS", self.FAMILY_B_RESULT_STATUS),
            (
                "NEGATIVE_MEMORY_OVERGENERALIZATION_STATUS",
                self.NEGATIVE_MEMORY_OVERGENERALIZATION_STATUS,
            ),
            ("RESOURCE_METRIC_STATUS", self.RESOURCE_METRIC_STATUS),
            (
                "CLAIM_EVIDENCE_GATE_REPAIR_STATUS",
                self.CLAIM_EVIDENCE_GATE_REPAIR_STATUS,
            ),
            (
                "CLAIM_EVIDENCE_CONSISTENCY_STATUS",
                self.CLAIM_EVIDENCE_CONSISTENCY_STATUS,
            ),
            (
                "MILESTONE_SCIENTIFIC_CLOSURE_STATUS",
                self.MILESTONE_SCIENTIFIC_CLOSURE_STATUS,
            ),
            ("VERDICT_INTEGRITY_STATUS", self.VERDICT_INTEGRITY_STATUS),
        ]

        failures = []
        for name, status in gates:
            if status in (GateStatus.FAIL, GateStatus.INDETERMINATE):
                failures.append(f"{name} is {status}")

        if failures:
            raise ValueError(
                f"Scientific Completion Gate Failure for {self.milestone_id}: "
                f"The following gates did not pass: {', '.join(failures)}"
            )

        return self


def probit(p: float) -> float:
    """
    Inverse normal CDF (probit function) using the Beasley-Springer-Moro rational approximation.
    Accurate to 1e-4 for probability ranges [1e-9, 1-1e-9].
    """
    if p <= 0.0 or p >= 1.0:
        raise ValueError("Probability p must be in (0, 1) exclusive.")

    # Fast lookup for common statistical values
    lookups = {
        0.90: 1.28155,
        0.95: 1.64485,
        0.975: 1.95996,
        0.99: 2.32635,
        0.995: 2.57583,
        0.80: 0.84162,
        0.50: 0.0,
    }
    for k, v in lookups.items():
        if abs(p - k) < 1e-4:
            return v

    y = p - 0.5
    if abs(y) < 0.42:
        r = y * y
        num = (
            ((-2.549732777849e1 * r + 5.127818090947e1) * r - 3.487039050749e1) * r
            + 7.828524756583e0
        ) * y
        den = (
            ((1.661839254620e1 * r - 5.078404561586e1) * r + 4.904612123469e1) * r
            - 1.655562035952e1
        ) * r + 1.0
        return num / den
    else:
        r = p if y < 0 else 1.0 - p
        s = math.log(-math.log(r))
        t = (
            ((-3.222384921989e-3 * s - 3.422420885551e-2) * s - 2.043228511497e-1) * s
            - 4.536400293207e-1
        ) * s - 2.132285047353e-1
        u = (
            ((9.938761102624e-5 * s + 3.215878036308e-3) * s + 3.551375231584e-2) * s
            + 1.189771618774e-1
        ) * s + 1.0
        z_val = t / u
        return z_val if y < 0 else -z_val


class ClaimEvidenceConsistencyGate(BaseModel):
    claim_id: str
    claim_text: str
    status: ClaimStatus = ClaimStatus.CLAIM_INDETERMINATE
    sample_size: int | None = None
    observed_diff: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    n_required: int | None = None

    @staticmethod
    def evaluate_claim_consistency(
        results: Dict[str, Any], spec: ClaimSpecification
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Calculates exact confidence intervals and sample size requirements based on MME
        to validate claims across POSITIVE_IMPROVEMENT, HARM_DEGRADATION, and NO_DIFFERENCE types.

        CRITICAL: The N_required power calculation relies on pre-registered MME and expected/conservative baseline,
        completely independent of the observed rates in results.
        """
        if spec.minimum_meaningful_effect is None:
            return ClaimEvidenceConsistencyGate(
                claim_id=spec.claim_id,
                claim_text=spec.claim_text,
                status=ClaimStatus.INDETERMINATE_NO_POWER_TARGET_DEFINED,
            )

        family_key = None
        if "family a" in spec.claim_text.lower():
            family_key = "family_a"
        elif (
            "family b" in spec.claim_text.lower()
            or "overgeneralization" in spec.claim_text.lower()
        ):
            family_key = "family_b"

        family_results = (
            results.get(family_key, results)
            if family_key and family_key in results
            else results
        )

        N = family_results.get("sample_size", family_results.get("triggered_events", 0))
        p_c = family_results.get(
            "condition_c_rate", family_results.get("baseline_rate", 0.0)
        )
        p_d = family_results.get(
            "condition_d_rate", family_results.get("treatment_rate", 0.0)
        )
        diff = family_results.get("epistemic_metric_diff", p_d - p_c)

        # 1. CI calculation uses observed rates (descriptive error bounds)
        z = probit(0.5 + spec.confidence_level / 2.0)
        z_power = probit(spec.target_power)

        obs_variance = p_c * (1 - p_c) + p_d * (1 - p_d)
        if obs_variance == 0.0:
            obs_variance = 0.25  # Fallback for CI calculations only
        se = math.sqrt(obs_variance / N) if N > 0 else 0.0
        ci_lower = diff - z * se
        ci_upper = diff + z * se

        # 2. Power calculation uses expected baseline or conservative 0.5 baseline (independent of results)
        p_b = (
            spec.expected_baseline_proportion
            if spec.expected_baseline_proportion is not None
            else 0.5
        )
        p_t = max(0.0, min(1.0, p_b + spec.minimum_meaningful_effect))

        expected_variance = p_b * (1 - p_b) + p_t * (1 - p_t)
        mme = abs(spec.minimum_meaningful_effect)
        n_required = math.ceil(((z + z_power) ** 2) * expected_variance / (mme**2))

        # Determine status
        if N >= n_required:
            if spec.claim_type == ClaimType.POSITIVE_IMPROVEMENT and ci_upper < 0:
                status = ClaimStatus.CLAIM_CONTRADICTED
            elif spec.claim_type == ClaimType.HARM_DEGRADATION and ci_lower > 0:
                status = ClaimStatus.CLAIM_CONTRADICTED
            elif spec.claim_type == ClaimType.POSITIVE_IMPROVEMENT:
                if ci_lower > 0:
                    status = ClaimStatus.CLAIM_SUPPORTED
                else:
                    status = ClaimStatus.NO_DIFFERENCE
            elif spec.claim_type == ClaimType.HARM_DEGRADATION:
                if ci_upper < 0:
                    status = ClaimStatus.CLAIM_SUPPORTED
                else:
                    status = ClaimStatus.NO_DIFFERENCE
            else:
                if ci_lower <= 0 <= ci_upper:
                    status = ClaimStatus.NO_DIFFERENCE
                else:
                    status = ClaimStatus.CLAIM_CONTRADICTED
        else:
            if ci_lower <= 0 <= ci_upper:
                status = ClaimStatus.INCONCLUSIVE
            else:
                if spec.claim_type == ClaimType.POSITIVE_IMPROVEMENT and ci_upper < 0:
                    status = ClaimStatus.CLAIM_CONTRADICTED
                elif spec.claim_type == ClaimType.HARM_DEGRADATION and ci_lower > 0:
                    status = ClaimStatus.CLAIM_CONTRADICTED
                else:
                    status = ClaimStatus.INSUFFICIENTLY_POWERED

        return ClaimEvidenceConsistencyGate(
            claim_id=spec.claim_id,
            claim_text=spec.claim_text,
            status=status,
            sample_size=N,
            observed_diff=diff,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_required=n_required,
        )

    @staticmethod
    def evaluate_false_admission_reduction(
        baseline_rate: float, treatment_rate: float, claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Legacy Regression Case 1 Validator:
        """
        if (
            "reduced false admissions" in claim_text.lower()
            or "reduction" in claim_text.lower()
        ):
            if treatment_rate < baseline_rate:
                status = ClaimStatus.CLAIM_SUPPORTED
            elif treatment_rate > baseline_rate:
                status = ClaimStatus.CLAIM_CONTRADICTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        elif (
            "did not reduce" in claim_text.lower()
            or "no reduction" in claim_text.lower()
        ):
            if treatment_rate == baseline_rate:
                status = ClaimStatus.CLAIM_SUPPORTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M5_FALSE_ADMISSION_CLAIM", claim_text=claim_text, status=status
        )

    @staticmethod
    def evaluate_order_sensitivity(
        sequences: Dict[str, Any], claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Legacy Regression Case 2 Validator:
        """
        if (
            "order sensitivity" in claim_text.lower()
            or "order_sensitivity" in claim_text.lower()
        ):
            if "order_a" in sequences and "order_b" in sequences:
                if sequences["order_a"] != sequences["order_b"]:
                    status = ClaimStatus.CLAIM_SUPPORTED
                else:
                    status = ClaimStatus.CLAIM_CONTRADICTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        elif "absorbing" in claim_text.lower() or "retirement" in claim_text.lower():
            if (
                sequences.get("sequence_b_contradiction", [])[-1] == "RETIRED_BELIEF"
                or sequences.get("order_a") == "RETIRED_BELIEF"
                or sequences.get("sequence_d_order_sensitivity", {}).get("order_a")
                == "RETIRED_BELIEF"
            ):
                status = ClaimStatus.CLAIM_SUPPORTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M6_ORDER_SENSITIVITY_CLAIM", claim_text=claim_text, status=status
        )

    @staticmethod
    def evaluate_minimal_causal_learning(
        results: Dict[str, Any], claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Legacy Milestone 7 Repaired Validator:
        """
        if (
            "minimal causal learning demonstrated" in claim_text.lower()
            or "minimal_causal_learning" in claim_text.lower()
            or "positive epistemic effect" in claim_text.lower()
        ):
            if (
                not results.get("epistemic_metric_measured", False)
                or "primary_epistemic_metric" not in results
            ):
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
            elif not results.get("evidence_sufficiency_satisfied", True):
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
            else:
                diff = results.get("epistemic_metric_diff", 0.0)
                if diff > 0.0:
                    status = ClaimStatus.CLAIM_SUPPORTED
                elif diff < 0.0:
                    status = ClaimStatus.CLAIM_CONTRADICTED
                else:
                    if results.get("neutrality_criterion_satisfied", False):
                        status = ClaimStatus.NEUTRAL_EFFECT_DEMONSTRATED
                    else:
                        status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M7_MINIMAL_CAUSAL_LEARNING", claim_text=claim_text, status=status
        )


class MilestoneScientificClosure(BaseModel):
    milestone_id: str
    methodology_gates: MilestoneCompletionGates
    claims: List[ClaimEvidenceConsistencyGate]

    # Validation Invariants
    primary_epistemic_metric_measured: bool = True
    evidence_sufficiency_satisfied: bool = True
    diagnostic_primary_separation: bool = True
    condition_isolation: bool = True
    causal_necessity_satisfied: bool = True
    claim_evidence_consistency: bool = True
    final_verdict_exceeds_evidence: bool = False

    @model_validator(mode="after")
    def validate_scientific_closure(self) -> "MilestoneScientificClosure":
        if not self.primary_epistemic_metric_measured:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: PRIMARY_EPISTEMIC_METRIC_NOT_MEASURED"
            )
        if not self.evidence_sufficiency_satisfied:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: EVIDENCE_SUFFICIENCY_REQUIREMENT_NOT_SATISFIED"
            )
        if not self.diagnostic_primary_separation:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: DIAGNOSTIC_PRIMARY_SEPARATION_FAILED"
            )
        if not self.condition_isolation:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: CONDITION_ISOLATION_FAILED"
            )
        if not self.causal_necessity_satisfied:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: CAUSAL_NECESSITY_FAILED"
            )
        if not self.claim_evidence_consistency:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: CLAIM_EVIDENCE_CONSISTENCY_FAILED"
            )
        if self.final_verdict_exceeds_evidence:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: FINAL_VERDICT_EXCEEDS_EVIDENCE"
            )

        undemonstrated = []
        contradicted = []
        for claim in self.claims:
            if claim.status in (
                ClaimStatus.CLAIM_NOT_DEMONSTRATED,
                ClaimStatus.INSUFFICIENTLY_POWERED,
                ClaimStatus.INCONCLUSIVE,
                ClaimStatus.CLAIM_INDETERMINATE,
                ClaimStatus.INDETERMINATE_NO_POWER_TARGET_DEFINED,
            ):
                undemonstrated.append(f"{claim.claim_text} ({claim.status.value})")
            elif claim.status == ClaimStatus.CLAIM_CONTRADICTED:
                contradicted.append(claim.claim_text)

        errors = []
        if contradicted:
            errors.append(f"Contradicted claims: {', '.join(contradicted)}")
        if undemonstrated:
            errors.append(f"Undemonstrated claims: {', '.join(undemonstrated)}")

        if errors:
            raise ValueError(
                f"Scientific Closure Failure for {self.milestone_id}: "
                f"{'; '.join(errors)}"
            )

        return self


class EpistemicValidationManifest(BaseModel):
    model_config = {"extra": "forbid"}

    milestone_5: MilestoneCompletionGates | None = None
    milestone_6: MilestoneCompletionGates | None = None
    milestone_7: MilestoneCompletionGates | None = None
    milestone_7_closure: MilestoneScientificClosure | None = None
    claims: List[ClaimSpecification] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    evaluated_claims: List[ClaimEvidenceConsistencyGate] = Field(default_factory=list)

    @model_validator(mode="after")
    def run_gate_checks(self) -> "EpistemicValidationManifest":
        evaluated = []
        for spec in self.claims:
            gate = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(
                self.results, spec
            )
            evaluated.append(gate)
        self.evaluated_claims = evaluated
        return self


class ValidationStorageManager:
    @staticmethod
    def save_manifest(manifest: EpistemicValidationManifest, filepath: str):
        with open(filepath, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)


class EpistemicValidationManifestReader:
    @staticmethod
    def load_manifest(filepath: str) -> EpistemicValidationManifest:
        with open(filepath, "r") as f:
            data = json.load(f)

        manifest = EpistemicValidationManifest.model_validate(data)

        # Consumption-side check: raise on CONTRADICTED or INSUFFICIENTLY_POWERED
        for claim in manifest.evaluated_claims:
            if claim.status in (
                ClaimStatus.CLAIM_CONTRADICTED,
                ClaimStatus.INSUFFICIENTLY_POWERED,
            ):
                raise ValueError(
                    f"Consumption Blocked: Manifest contains failed/underpowered status: "
                    f"[{claim.claim_id}] -> {claim.status}"
                )
        return manifest
