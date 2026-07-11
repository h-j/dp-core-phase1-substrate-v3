import datetime
import hashlib
import json
import os
import subprocess
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MLCVerdict(str, Enum):
    MLC_V0_1_ARCHITECTURAL_FAILURE = "MLC_V0_1_ARCHITECTURAL_FAILURE"
    MLC_V0_1_VALID_LIFECYCLE_NO_EMPIRICAL_VALUE = (
        "MLC_V0_1_VALID_LIFECYCLE_NO_EMPIRICAL_VALUE"
    )
    MLC_V0_1_PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY = (
        "MLC_V0_1_PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY"
    )
    MLC_V0_1_PROSPECTIVE_VALIDATION_REDUCES_FALSE_ADMISSION = (
        "MLC_V0_1_PROSPECTIVE_VALIDATION_REDUCES_FALSE_ADMISSION"
    )
    MLC_V0_1_PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY = (
        "MLC_V0_1_PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY"
    )
    MLC_V0_1_DEFER_CALIBRATION_FAILURE = "MLC_V0_1_DEFER_CALIBRATION_FAILURE"
    MLC_V0_1_INCONCLUSIVE = "MLC_V0_1_INCONCLUSIVE"


class HypothesisStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    IMPROVED = "IMPROVED"
    NO_DIFFERENCE = "NO_DIFFERENCE"
    DEGRADED = "DEGRADED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_INTERPRETABLE = "NOT_INTERPRETABLE"


class HypothesisResult(BaseModel):
    hypothesis_id: str
    scientific_question: str
    status: HypothesisStatus
    metrics: Dict[str, Any]
    baseline: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    sample_size: int
    excluded_record_count: int
    statistical_metadata: Dict[str, Any]
    interpretation: str
    limitations: str
    # H4 decomposition
    pooled_false_admission: Optional[Dict[str, Any]] = None
    false_admit_reject: Optional[Dict[str, Any]] = None
    false_admit_evidence_limited: Optional[Dict[str, Any]] = None
    false_admit_effect_ambiguous: Optional[Dict[str, Any]] = None
    # H5 calibration
    defer_precision: Optional[float] = None
    defer_recall: Optional[float] = None
    target_status: Optional[str] = None


class ExperimentScientificResult(BaseModel):
    experiment_id: str
    run_id: str
    protocol_version: str
    configuration_hash: str
    git_commit: str
    timestamp: str
    h1_result: HypothesisResult
    h2_result: HypothesisResult
    h3_result: HypothesisResult
    h4_result: HypothesisResult
    h5_result: HypothesisResult
    interpretation_status: str
    derived_summary_label: str
    threshold_disclosures: Dict[str, Any]
    unresolved_scientific_issues: List[str]
    evaluator_version: str


class MLCVerdictEvaluator:
    def __init__(
        self,
        significance_alpha: Optional[float] = None,
        minimum_lift_effect: Optional[float] = None,
        defer_precision_target: Optional[float] = None,
        defer_recall_target: Optional[float] = None,
    ):
        self.significance_alpha = significance_alpha
        self.minimum_lift_effect = minimum_lift_effect
        self.defer_precision_target = defer_precision_target
        self.defer_recall_target = defer_recall_target

        # Legacy placeholder dictionary for backward compatibility (Section 28A checks)
        self.unresolved_verdict_thresholds: Dict[str, Any] = {
            "significance_alpha": significance_alpha,
            "minimum_lift_effect": minimum_lift_effect,
            "precedence_rules": "FROZEN_PROTOCOL_ADDENDUM_V0_1",
            "hypothesis_to_verdict_map": "FROZEN_PROTOCOL_ADDENDUM_V0_1",
        }

    def evaluate_verdict(self, metrics: Dict[str, Any]) -> MLCVerdict:
        """
        Verdict evaluation interface for backward compatibility.
        """
        # Validate that legacy thresholds are resolved (only if manually running legacy path)
        is_resolved = all(
            v is not None for v in self.unresolved_verdict_thresholds.values()
        )
        if not is_resolved:
            raise RuntimeError(
                "Cannot derive verdict: Hypothesis-to-verdict mapping and numerical verdict thresholds are unresolved."
            )
        return MLCVerdict.MLC_V0_1_INCONCLUSIVE

    def evaluate_result(
        self,
        decisions: List[Dict[str, Any]],
        oracle_decisions: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
        frozen_candidates: List[Dict[str, Any]],
        erc_logs: List[Dict[str, Any]],
        validity_gates: Dict[str, Any],
        metrics: Dict[str, Any],
        run_id: str,
        git_commit: Optional[str] = None,
    ) -> ExperimentScientificResult:
        """
        Evaluates H1-H5 structured hypothesis results and returns an ExperimentScientificResult object.
        """
        # Extract git commit
        git_hash = "unavailable"
        if git_commit:
            git_hash = git_commit
        else:
            try:
                git_hash = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
            except Exception:
                pass

        # H1: Lifecycle Fidelity
        h1_passed = (
            all(res.get("status") == "PASS" for res in validity_gates.values())
            if validity_gates
            else False
        )
        h1_status = HypothesisStatus.PASS if h1_passed else HypothesisStatus.FAIL

        # Set up default disclosures & issues
        unresolved_issues = []
        if self.minimum_lift_effect is None:
            unresolved_issues.append(
                "Minimum Lift Effect size is unresolved (exploratory only)."
            )
        if self.significance_alpha is None:
            unresolved_issues.append(
                "Significance alpha threshold is unresolved (exploratory only)."
            )
        if self.defer_precision_target is None:
            unresolved_issues.append("DEFER Precision target threshold is unresolved.")
        if self.defer_recall_target is None:
            unresolved_issues.append("DEFER Recall target threshold is unresolved.")

        config_dict = {"admit_threshold": 0.15, "reject_threshold": -0.05}
        config_hash = hashlib.sha256(
            json.dumps(config_dict, sort_keys=True).encode("utf-8")
        ).hexdigest()

        timestamp_str = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        epistemic_decisions = [
            d for d in decisions if d["decision"] != "COMPILATION_REJECTED"
        ]
        n = len(epistemic_decisions)
        excluded_count = len(decisions) - n

        # Handle H1 short-circuit
        if h1_status == HypothesisStatus.FAIL:
            h1_res = HypothesisResult(
                hypothesis_id="H1",
                scientific_question="Did MLC v0.1 execute the intended epistemic lifecycle without violating architectural validity gates?",
                status=HypothesisStatus.FAIL,
                metrics={"validity_gates": validity_gates},
                sample_size=len(decisions),
                excluded_record_count=0,
                statistical_metadata={},
                interpretation="Validity gates failed. Downstream metrics are not interpretable.",
                limitations="Lifecycle fidelity violation.",
            )

            def make_not_interpretable(h_id: str, q: str) -> HypothesisResult:
                return HypothesisResult(
                    hypothesis_id=h_id,
                    scientific_question=q,
                    status=HypothesisStatus.NOT_INTERPRETABLE,
                    metrics={},
                    sample_size=0,
                    excluded_record_count=excluded_count,
                    statistical_metadata={},
                    interpretation="Not interpretable due to H1 failure.",
                    limitations="H1 fidelity failure.",
                )

            return ExperimentScientificResult(
                experiment_id="MLC_V0_1",
                run_id=run_id,
                protocol_version="0.1.0",
                configuration_hash=config_hash,
                git_commit=git_hash,
                timestamp=timestamp_str,
                h1_result=h1_res,
                h2_result=make_not_interpretable(
                    "H2",
                    "Does MLC v0.1 provide decision value above the matched random baseline?",
                ),
                h3_result=make_not_interpretable(
                    "H3",
                    "Does prospective validation improve decision accuracy over the matched retrospective-only B2 ablation?",
                ),
                h4_result=make_not_interpretable(
                    "H4",
                    "Does prospective validation reduce catastrophic false admission relative to B2?",
                ),
                h5_result=make_not_interpretable(
                    "H5",
                    "Does MLC correctly identify propositions that should remain deferred?",
                ),
                interpretation_status="NOT_INTERPRETABLE",
                derived_summary_label="ARCHITECTURAL_FAILURE",
                threshold_disclosures={
                    "admit_threshold": 0.15,
                    "reject_threshold": -0.05,
                },
                unresolved_scientific_issues=unresolved_issues
                + ["H1 fidelity failure"],
                evaluator_version="0.1.0",
            )

        # H1 result success
        h1_res = HypothesisResult(
            hypothesis_id="H1",
            scientific_question="Did MLC v0.1 execute the intended epistemic lifecycle without violating architectural validity gates?",
            status=HypothesisStatus.PASS,
            metrics={"validity_gates": validity_gates},
            sample_size=len(decisions),
            excluded_record_count=0,
            statistical_metadata={},
            interpretation="All 10 validity gates passed.",
            limitations="Fidelity check passed.",
        )

        oracle_map = {
            o["world_id"]: o.get("expected_decision", o.get("decision"))
            for o in oracle_decisions
        }
        oracle_reason_map = {
            o["world_id"]: o.get("expected_reason", o.get("reason_code"))
            for o in oracle_decisions
        }

        # Evaluate H2
        b3_map = baseline_results.get("b3_decisions", {})
        b3_correct = 0
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if b3_map.get(w_id) == oracle_map.get(w_id):
                b3_correct += 1
        b3_acc = b3_correct / n if n > 0 else 0.0
        mlc_acc = metrics.get("overall_decision_accuracy", 0.0)

        h2_status = HypothesisStatus.INCONCLUSIVE
        h2_interpretation = (
            "Significance criteria and effect size thresholds are unresolved."
        )
        if self.minimum_lift_effect is not None:
            diff = mlc_acc - b3_acc
            if diff >= self.minimum_lift_effect:
                h2_status = HypothesisStatus.PASS
                h2_interpretation = f"MLC accuracy ({mlc_acc:.4f}) is improved over B3 Random ({b3_acc:.4f}) by at least lift target ({self.minimum_lift_effect:.4f})."
            elif diff <= -self.minimum_lift_effect:
                h2_status = HypothesisStatus.FAIL
                h2_interpretation = f"MLC accuracy ({mlc_acc:.4f}) is below or equal to B3 Random ({b3_acc:.4f}) by lift target."
            else:
                h2_status = HypothesisStatus.INCONCLUSIVE
                h2_interpretation = f"Accuracy difference ({diff:.4f}) does not meet lift target ({self.minimum_lift_effect:.4f})."

        h2_res = HypothesisResult(
            hypothesis_id="H2",
            scientific_question="Does MLC v0.1 provide decision value above the matched random baseline?",
            status=h2_status,
            metrics={"mlc_accuracy": mlc_acc, "b3_accuracy": b3_acc},
            baseline={"b3_matched_random_accuracy": b3_acc},
            comparison={"accuracy_lift_over_random": mlc_acc - b3_acc},
            sample_size=n,
            excluded_record_count=excluded_count,
            statistical_metadata={
                "significance_alpha": self.significance_alpha,
                "minimum_lift_effect": self.minimum_lift_effect,
            },
            interpretation=h2_interpretation,
            limitations="Assumes uniform random baseline choice distribution.",
        )

        # Evaluate H3
        b2_acc = metrics.get("b2_decision_accuracy", 0.0)
        h3_status = HypothesisStatus.INCONCLUSIVE
        h3_interpretation = "Accuracy comparison criteria are unresolved."
        if self.minimum_lift_effect is not None:
            diff = mlc_acc - b2_acc
            if diff >= self.minimum_lift_effect:
                h3_status = HypothesisStatus.IMPROVED
                h3_interpretation = f"MLC accuracy ({mlc_acc:.4f}) is improved over B2 Retro ({b2_acc:.4f}) by at least lift target ({self.minimum_lift_effect:.4f})."
            elif diff <= -self.minimum_lift_effect:
                h3_status = HypothesisStatus.DEGRADED
                h3_interpretation = f"MLC accuracy ({mlc_acc:.4f}) is degraded compared to B2 Retro ({b2_acc:.4f}) by lift target."
            else:
                h3_status = HypothesisStatus.NO_DIFFERENCE
                h3_interpretation = f"Accuracy difference ({diff:.4f}) does not meet lift target ({self.minimum_lift_effect:.4f})."

        h3_res = HypothesisResult(
            hypothesis_id="H3",
            scientific_question="Does prospective validation improve decision accuracy over the matched retrospective-only B2 ablation?",
            status=h3_status,
            metrics={"mlc_accuracy": mlc_acc, "b2_accuracy": b2_acc},
            baseline={"b2_retro_accuracy": b2_acc},
            comparison={"accuracy_lift_over_b2": mlc_acc - b2_acc},
            sample_size=n,
            excluded_record_count=excluded_count,
            statistical_metadata={"minimum_lift_effect": self.minimum_lift_effect},
            interpretation=h3_interpretation,
            limitations="Oracle evaluation treats C1 and C2 as collapsed DEFER decisions.",
        )

        # Evaluate H4
        mlc_cat_rate = metrics.get("catastrophic_false_admission_rate", 0.0)
        b2_cat_rate = metrics.get("b2_catastrophic_false_admission_rate", 0.0)

        mlc_fa_reject = 0
        mlc_fa_ev_lim = 0
        mlc_fa_eff_amb = 0
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if d["decision"] == "ADMIT":
                gt_dec = oracle_map.get(w_id)
                gt_reason = oracle_reason_map.get(w_id)
                if gt_dec == "REJECT":
                    mlc_fa_reject += 1
                elif gt_dec == "DEFER":
                    if (
                        gt_reason == "ORACLE_DEFER_EVIDENCE_LIMITED"
                        or gt_reason == "EVIDENCE_LIMITED"
                    ):
                        mlc_fa_ev_lim += 1
                    elif (
                        gt_reason == "ORACLE_DEFER_EFFECT_AMBIGUITY"
                        or gt_reason == "EFFECT_AMBIGUITY"
                    ):
                        mlc_fa_eff_amb += 1

        b2_fa_reject = 0
        b2_fa_ev_lim = 0
        b2_fa_eff_amb = 0
        b2_map = baseline_results.get("b2_decisions", {})
        for d in epistemic_decisions:
            w_id = d["world_id"]
            if b2_map.get(w_id) == "ADMIT":
                gt_dec = oracle_map.get(w_id)
                gt_reason = oracle_reason_map.get(w_id)
                if gt_dec == "REJECT":
                    b2_fa_reject += 1
                elif gt_dec == "DEFER":
                    if (
                        gt_reason == "ORACLE_DEFER_EVIDENCE_LIMITED"
                        or gt_reason == "EVIDENCE_LIMITED"
                    ):
                        b2_fa_ev_lim += 1
                    elif (
                        gt_reason == "ORACLE_DEFER_EFFECT_AMBIGUITY"
                        or gt_reason == "EFFECT_AMBIGUITY"
                    ):
                        b2_fa_eff_amb += 1

        mlc_fa_rej_rate = mlc_fa_reject / n if n > 0 else 0.0
        mlc_fa_ev_rate = mlc_fa_ev_lim / n if n > 0 else 0.0
        mlc_fa_eff_rate = mlc_fa_eff_amb / n if n > 0 else 0.0

        b2_fa_rej_rate = b2_fa_reject / n if n > 0 else 0.0
        b2_fa_ev_rate = b2_fa_ev_lim / n if n > 0 else 0.0
        b2_fa_eff_rate = b2_fa_eff_amb / n if n > 0 else 0.0

        h4_status = HypothesisStatus.INCONCLUSIVE
        h4_interpretation = "Safety comparison criteria are unresolved."
        if self.minimum_lift_effect is not None:
            diff = mlc_cat_rate - b2_cat_rate
            if diff <= -self.minimum_lift_effect:
                h4_status = HypothesisStatus.IMPROVED
                h4_interpretation = f"MLC false admission rate ({mlc_cat_rate:.4f}) is reduced compared to B2 ({b2_cat_rate:.4f}) by at least lift target ({self.minimum_lift_effect:.4f})."
            elif diff >= self.minimum_lift_effect:
                h4_status = HypothesisStatus.DEGRADED
                h4_interpretation = f"MLC false admission rate ({mlc_cat_rate:.4f}) is increased compared to B2 ({b2_cat_rate:.4f}) by at least lift target."
            else:
                h4_status = HypothesisStatus.NO_DIFFERENCE
                h4_interpretation = f"False admission rate difference ({diff:.4f}) does not meet lift target ({self.minimum_lift_effect:.4f})."

        h4_res = HypothesisResult(
            hypothesis_id="H4",
            scientific_question="Does prospective validation reduce catastrophic false admission relative to B2?",
            status=h4_status,
            metrics={"mlc_pooled_rate": mlc_cat_rate, "b2_pooled_rate": b2_cat_rate},
            baseline={"b2_pooled_rate": b2_cat_rate},
            comparison={"pooled_reduction": b2_cat_rate - mlc_cat_rate},
            sample_size=n,
            excluded_record_count=excluded_count,
            statistical_metadata={"minimum_lift_effect": self.minimum_lift_effect},
            interpretation=h4_interpretation,
            limitations="Decomposition counts are subject to seeds and world registry definitions.",
            pooled_false_admission={
                "mlc_count": int(mlc_cat_rate * n),
                "mlc_rate": mlc_cat_rate,
                "b2_count": int(b2_cat_rate * n),
                "b2_rate": b2_cat_rate,
            },
            false_admit_reject={
                "mlc_count": mlc_fa_reject,
                "mlc_rate": mlc_fa_rej_rate,
                "b2_count": b2_fa_reject,
                "b2_rate": b2_fa_rej_rate,
            },
            false_admit_evidence_limited={
                "mlc_count": mlc_fa_ev_lim,
                "mlc_rate": mlc_fa_ev_rate,
                "b2_count": b2_fa_ev_lim,
                "b2_rate": b2_fa_ev_rate,
            },
            false_admit_effect_ambiguous={
                "mlc_count": mlc_fa_eff_amb,
                "mlc_rate": mlc_fa_eff_rate,
                "b2_count": b2_fa_eff_amb,
                "b2_rate": b2_fa_eff_rate,
            },
        )

        # Evaluate H5
        defer_prec = metrics.get("defer_precision", 0.0)
        defer_rec = metrics.get("defer_recall", 0.0)

        h5_status = HypothesisStatus.INCONCLUSIVE
        h5_interpretation = "Defer calibration targets are unresolved."
        if (
            self.defer_precision_target is not None
            and self.defer_recall_target is not None
        ):
            if (
                defer_prec >= self.defer_precision_target
                and defer_rec >= self.defer_recall_target
            ):
                h5_status = HypothesisStatus.PASS
                h5_interpretation = f"MLC Defer Precision ({defer_prec:.4f}) and Recall ({defer_rec:.4f}) meet targets."
            else:
                h5_status = HypothesisStatus.FAIL
                h5_interpretation = f"MLC Defer Precision ({defer_prec:.4f}) or Recall ({defer_rec:.4f}) do not meet targets."

        h5_res = HypothesisResult(
            hypothesis_id="H5",
            scientific_question="Does MLC correctly identify propositions that should remain deferred?",
            status=h5_status,
            metrics={"defer_precision": defer_prec, "defer_recall": defer_rec},
            baseline=None,
            comparison=None,
            sample_size=n,
            excluded_record_count=excluded_count,
            statistical_metadata={
                "precision_target": self.defer_precision_target,
                "recall_target": self.defer_recall_target,
            },
            interpretation=h5_interpretation,
            limitations="Assumes clean C1/C2 separation in DGP.",
            defer_precision=defer_prec,
            defer_recall=defer_rec,
            target_status=(
                "PROVISIONAL" if self.defer_precision_target is None else "FROZEN"
            ),
        )

        # Derive summary label
        derived_summary_label = "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
        if (
            h2_status == HypothesisStatus.INCONCLUSIVE
            or h3_status == HypothesisStatus.INCONCLUSIVE
            or h4_status == HypothesisStatus.INCONCLUSIVE
        ):
            derived_summary_label = "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
        elif h2_status == HypothesisStatus.FAIL:
            derived_summary_label = (
                "VALID_LIFECYCLE_WITHOUT_ABOVE_RANDOM_DECISION_VALUE"
            )
        elif h2_status == HypothesisStatus.PASS:
            if (
                h3_status == HypothesisStatus.IMPROVED
                and h4_status == HypothesisStatus.IMPROVED
            ):
                if h5_status == HypothesisStatus.FAIL:
                    derived_summary_label = "PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY_WITH_DEFER_CALIBRATION_WEAKNESS"
                else:
                    derived_summary_label = (
                        "PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY"
                    )
            elif (
                h3_status == HypothesisStatus.IMPROVED
                and h4_status == HypothesisStatus.NO_DIFFERENCE
            ):
                derived_summary_label = "ACCURACY_IMPROVED_WITHOUT_SAFETY_IMPROVEMENT"
            elif (
                h3_status == HypothesisStatus.IMPROVED
                and h4_status == HypothesisStatus.DEGRADED
            ):
                derived_summary_label = "ACCURACY_IMPROVED_SAFETY_DEGRADED"
            elif (
                h3_status == HypothesisStatus.NO_DIFFERENCE
                and h4_status == HypothesisStatus.IMPROVED
            ):
                derived_summary_label = "PROSPECTIVE_VALIDATION_REDUCES_FALSE_ADMISSION_WITHOUT_ACCURACY_GAIN"
            elif (
                h3_status == HypothesisStatus.DEGRADED
                and h4_status == HypothesisStatus.IMPROVED
            ):
                derived_summary_label = "SAFETY_IMPROVED_AT_ACCURACY_COST"

        return ExperimentScientificResult(
            experiment_id="MLC_V0_1",
            run_id=run_id,
            protocol_version="0.1.0",
            configuration_hash=config_hash,
            git_commit=git_hash,
            timestamp=timestamp_str,
            h1_result=h1_res,
            h2_result=h2_res,
            h3_result=h3_res,
            h4_result=h4_res,
            h5_result=h5_res,
            interpretation_status="INTERPRETABLE",
            derived_summary_label=derived_summary_label,
            threshold_disclosures={
                "admit_threshold": 0.15,
                "reject_threshold": -0.05,
                "significance_alpha": self.significance_alpha,
                "minimum_lift_effect": self.minimum_lift_effect,
                "defer_precision_target": self.defer_precision_target,
                "defer_recall_target": self.defer_recall_target,
            },
            unresolved_scientific_issues=unresolved_issues,
            evaluator_version="0.1.0",
        )
