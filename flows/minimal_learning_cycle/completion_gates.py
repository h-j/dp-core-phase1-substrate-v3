from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, model_validator


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
            ("DIAGNOSTIC_PRIMARY_SEPARATION_STATUS", self.DIAGNOSTIC_PRIMARY_SEPARATION_STATUS),
            ("RESOURCE_CONTAMINATION_STATUS", self.RESOURCE_CONTAMINATION_STATUS),
            ("SAFEGUARD_BENEFIT_STATUS", self.SAFEGUARD_BENEFIT_STATUS),
            ("SAFEGUARD_COST_STATUS", self.SAFEGUARD_COST_STATUS),
            ("COMPLETE_LIFECYCLE_ACCOUNTING_STATUS", self.COMPLETE_LIFECYCLE_ACCOUNTING_STATUS),
            ("CLAIM_SCOPE_STATUS", self.CLAIM_SCOPE_STATUS),
            ("REGRESSION_SAFETY_STATUS", self.REGRESSION_SAFETY_STATUS),
            ("CANONICAL_STATE_CORRECTION_STATUS", self.CANONICAL_STATE_CORRECTION_STATUS),
            ("REPOSITORY_REALITY_INSPECTION_STATUS", self.REPOSITORY_REALITY_INSPECTION_STATUS),
            ("PERSISTENT_PRE_REGISTRATION_STATUS", self.PERSISTENT_PRE_REGISTRATION_STATUS),
            ("SEED_OVERLAP_STATUS", self.SEED_OVERLAP_STATUS),
            ("FUTURE_DATA_ISOLATION_STATUS", self.FUTURE_DATA_ISOLATION_STATUS),
            ("PRIMARY_BEHAVIORAL_METRIC_STATUS", self.PRIMARY_BEHAVIORAL_METRIC_STATUS),
            ("PRIMARY_EPISTEMIC_METRIC_STATUS", self.PRIMARY_EPISTEMIC_METRIC_STATUS),
            ("PRIMARY_EPISTEMIC_METRIC_MEASUREMENT_STATUS", self.PRIMARY_EPISTEMIC_METRIC_MEASUREMENT_STATUS),
            ("EVIDENCE_SUFFICIENCY_REQUIREMENT_STATUS", self.EVIDENCE_SUFFICIENCY_REQUIREMENT_STATUS),
            ("EVIDENCE_SUFFICIENCY_SATISFACTION_STATUS", self.EVIDENCE_SUFFICIENCY_SATISFACTION_STATUS),
            ("MEMORY_INFLUENCE_STATUS", self.MEMORY_INFLUENCE_STATUS),
            ("CAUSAL_ATTRIBUTION_STATUS", self.CAUSAL_ATTRIBUTION_STATUS),
            ("FAMILY_A_RESULT_STATUS", self.FAMILY_A_RESULT_STATUS),
            ("FAMILY_B_RESULT_STATUS", self.FAMILY_B_RESULT_STATUS),
            ("NEGATIVE_MEMORY_OVERGENERALIZATION_STATUS", self.NEGATIVE_MEMORY_OVERGENERALIZATION_STATUS),
            ("RESOURCE_METRIC_STATUS", self.RESOURCE_METRIC_STATUS),
            ("CLAIM_EVIDENCE_GATE_REPAIR_STATUS", self.CLAIM_EVIDENCE_GATE_REPAIR_STATUS),
            ("CLAIM_EVIDENCE_CONSISTENCY_STATUS", self.CLAIM_EVIDENCE_CONSISTENCY_STATUS),
            ("MILESTONE_SCIENTIFIC_CLOSURE_STATUS", self.MILESTONE_SCIENTIFIC_CLOSURE_STATUS),
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


class ClaimEvidenceConsistencyGate(BaseModel):
    claim_id: str
    claim_text: str
    status: ClaimStatus = ClaimStatus.CLAIM_INDETERMINATE

    @staticmethod
    def evaluate_false_admission_reduction(
        baseline_rate: float, treatment_rate: float, claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Regression Case 1 Validator:
        - baseline_rate: false admission rate in Condition B.
        - treatment_rate: false admission rate in Condition C.
        """
        if "reduced false admissions" in claim_text.lower() or "reduction" in claim_text.lower():
            if treatment_rate < baseline_rate:
                status = ClaimStatus.CLAIM_SUPPORTED
            elif treatment_rate > baseline_rate:
                status = ClaimStatus.CLAIM_CONTRADICTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        elif "did not reduce" in claim_text.lower() or "no reduction" in claim_text.lower():
            if treatment_rate == baseline_rate:
                status = ClaimStatus.CLAIM_SUPPORTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M5_FALSE_ADMISSION_CLAIM",
            claim_text=claim_text,
            status=status
        )

    @staticmethod
    def evaluate_order_sensitivity(
        sequences: Dict[str, Any], claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Regression Case 2 Validator:
        - sequences: dictionary containing the results of order comparison.
        """
        if "order sensitivity" in claim_text.lower() or "order_sensitivity" in claim_text.lower():
            if "order_a" in sequences and "order_b" in sequences:
                if sequences["order_a"] != sequences["order_b"]:
                    status = ClaimStatus.CLAIM_SUPPORTED
                else:
                    status = ClaimStatus.CLAIM_CONTRADICTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        elif "absorbing" in claim_text.lower() or "retirement" in claim_text.lower():
            if (
                sequences.get("sequence_b_contradiction", [])[-1] == "RETIRED_BELIEF" or
                sequences.get("order_a") == "RETIRED_BELIEF" or
                sequences.get("sequence_d_order_sensitivity", {}).get("order_a") == "RETIRED_BELIEF"
            ):
                status = ClaimStatus.CLAIM_SUPPORTED
            else:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M6_ORDER_SENSITIVITY_CLAIM",
            claim_text=claim_text,
            status=status
        )

    @staticmethod
    def evaluate_minimal_causal_learning(
        results: Dict[str, Any], claim_text: str
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Milestone 7 Repaired Validator:
        - results: dictionary containing the results of the learning loop experiment.
        """
        if "minimal causal learning demonstrated" in claim_text.lower() or "minimal_causal_learning" in claim_text.lower() or "positive epistemic effect" in claim_text.lower():
            # Check Case A: No epistemic performance metric measured
            if not results.get("epistemic_metric_measured", False) or "primary_epistemic_metric" not in results:
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
            # Check Evidence Sufficiency
            elif not results.get("evidence_sufficiency_satisfied", True):
                status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
            else:
                diff = results.get("epistemic_metric_diff", 0.0)
                if diff > 0.0:
                    status = ClaimStatus.CLAIM_SUPPORTED  # Case C: improves
                elif diff < 0.0:
                    status = ClaimStatus.CLAIM_CONTRADICTED  # Case B: degrades
                else:
                    if results.get("neutrality_criterion_satisfied", False):
                        status = ClaimStatus.NEUTRAL_EFFECT_DEMONSTRATED  # Case D: neutral
                    else:
                        status = ClaimStatus.CLAIM_NOT_DEMONSTRATED
        else:
            status = ClaimStatus.CLAIM_INDETERMINATE

        return ClaimEvidenceConsistencyGate(
            claim_id="M7_MINIMAL_CAUSAL_LEARNING",
            claim_text=claim_text,
            status=status
        )


class MilestoneScientificClosure(BaseModel):
    milestone_id: str
    methodology_gates: MilestoneCompletionGates
    claims: List[ClaimEvidenceConsistencyGate]
    
    # Validation Invariants (Epoch 9)
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
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: PRIMARY_EPISTEMIC_METRIC_NOT_MEASURED")
        if not self.evidence_sufficiency_satisfied:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: EVIDENCE_SUFFICIENCY_REQUIREMENT_NOT_SATISFIED")
        if not self.diagnostic_primary_separation:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: DIAGNOSTIC_PRIMARY_SEPARATION_FAILED")
        if not self.condition_isolation:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: CONDITION_ISOLATION_FAILED")
        if not self.causal_necessity_satisfied:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: CAUSAL_NECESSITY_FAILED")
        if not self.claim_evidence_consistency:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: CLAIM_EVIDENCE_CONSISTENCY_FAILED")
        if self.final_verdict_exceeds_evidence:
            raise ValueError(f"Scientific Closure Failure for {self.milestone_id}: FINAL_VERDICT_EXCEEDS_EVIDENCE")

        undemonstrated = []
        contradicted = []
        for claim in self.claims:
            if claim.status == ClaimStatus.CLAIM_NOT_DEMONSTRATED:
                undemonstrated.append(claim.claim_text)
            elif claim.status == ClaimStatus.CLAIM_CONTRADICTED:
                contradicted.append(claim.claim_text)
            elif claim.status == ClaimStatus.CLAIM_INDETERMINATE:
                undemonstrated.append(claim.claim_text + " (INDETERMINATE)")
                
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
