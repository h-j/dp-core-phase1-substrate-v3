from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


ALLOWED_OPERATORS = {"==", "!=", ">", ">=", "<", "<="}
EVALUATION_WINDOW_START = 11
EVALUATION_WINDOW_END = 30


class OperationalHypothesisHarness:
    def __init__(self, artifact_path: Optional[Path | str] = None, output_dir: Optional[Path | str] = None) -> None:
        self.artifact_path = Path(artifact_path or (Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"))
        self.output_dir = Path(output_dir or (Path(__file__).resolve().parents[1] / "data" / "operational_hypothesis_experiment"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_replay_artifact(self) -> pd.DataFrame:
        artifact = pd.read_csv(self.artifact_path)
        artifact = artifact.copy()
        artifact["date"] = pd.to_datetime(artifact["date"])
        artifact = artifact.sort_values("date").reset_index(drop=True)
        return artifact

    def run(self) -> Dict[str, Any]:
        artifact = self.load_replay_artifact()
        formation_window = artifact.iloc[:10].copy()
        evaluation_window = artifact.iloc[10:30].copy()

        accepted: List[Dict[str, Any]] = []
        rejections: List[Dict[str, Any]] = []
        seen_candidates: set[Tuple[Tuple[Any, ...], ...]] = set()

        # Generate a small deterministic slate from persisted artifacts.
        candidate_pool = self._generate_candidate_pool(formation_window)
        for candidate in candidate_pool:
            validation = self.validate_candidate(candidate, formation_window, seen_candidates)
            if validation["status"] == "accepted":
                accepted.append(validation["hypothesis"])
            else:
                rejections.append(validation)

        frozen = copy.deepcopy(accepted)
        evidence_history = []
        for hypothesis in frozen:
            for day_index in range(len(evaluation_window)):
                evidence_history.append(self._evaluate_hypothesis_on_day(hypothesis, day_index, artifact))

        formation_metrics = self._build_formation_metrics(candidate_pool, rejections, accepted)
        evaluation_metrics = self._build_evaluation_metrics(evidence_history)
        per_hypothesis_reports = self._build_per_hypothesis_reports(frozen, evidence_history)
        base_rate_diagnostics = self._build_base_rate_diagnostics(frozen, evaluation_window, evidence_history)

        report = {
            "formation": formation_metrics,
            "evaluation": {
                "metrics": evaluation_metrics,
                "per_hypothesis": per_hypothesis_reports,
                "base_rate_diagnostics": base_rate_diagnostics,
            },
            "hypotheses": frozen,
            "rejections": rejections,
            "history": evidence_history,
            "frozen_hypothesis_report": self._build_frozen_hypothesis_report(frozen),
        }

        self._write_outputs(report)
        return report

    def _generate_candidate_pool(self, formation_window: pd.DataFrame) -> List[Dict[str, Any]]:
        candidates = []
        day_rows = list(formation_window.itertuples(index=False))
        for day_index, row in enumerate(day_rows):
            if day_index >= len(day_rows):
                break
            trigger = {
                "field": "volume_state",
                "operator": "==",
                "value": row.volume_state,
            }
            scope = [{"field": "daily_return_pct", "operator": "<", "value": -0.5}]
            effect = {"field": "return_3d", "operator": ">", "value": 0.0}
            candidates.append(
                {
                    "hypothesis_id": f"op-h-{day_index + 1}",
                    "source_provenance": f"day-{day_index + 1}",
                    "freeze_time": 10,
                    "trigger_predicate": trigger,
                    "scope_predicates": scope,
                    "expected_effect_predicate": effect,
                    "evaluation_horizon": 2,
                }
            )
        return candidates

    def validate_candidate(
        self,
        candidate: Dict[str, Any],
        formation_window: pd.DataFrame,
        seen_candidates: set[Tuple[Tuple[Any, ...], ...]],
    ) -> Dict[str, Any]:
        if not self._is_complete_candidate(candidate):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "MISSING_FIELDS"}

        if self._contains_tautology(candidate):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "TAUTOLOGY"}

        if not self._is_normalizable_predicate(candidate.get("trigger_predicate")):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_PREDICATE"}
        for predicate in candidate.get("scope_predicates", []):
            if not self._is_normalizable_predicate(predicate):
                return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_PREDICATE"}
        if not self._is_normalizable_predicate(candidate.get("expected_effect_predicate")):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_PREDICATE"}

        if not self._is_allowed_operator(candidate.get("trigger_predicate", {}).get("operator")):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_OPERATOR"}
        for predicate in candidate.get("scope_predicates", []):
            if not self._is_allowed_operator(predicate.get("operator")):
                return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_OPERATOR"}
        if not self._is_allowed_operator(candidate.get("expected_effect_predicate", {}).get("operator")):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_OPERATOR"}

        if not self._is_positive_horizon(candidate.get("evaluation_horizon")):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "INVALID_HORIZON"}

        if self._is_same_observable_restatement(candidate):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "SAME_OBSERVABLE"}

        if self._expected_effect_known_at_formation(candidate, formation_window):
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "KNOWN_EFFECT"}

        canonical = self._canonical_key(candidate)
        if canonical in seen_candidates:
            return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "rejected", "rejection_reason": "DUPLICATE"}
        seen_candidates.add(canonical)

        return {"candidate": candidate, "source_provenance": candidate.get("source_provenance"), "status": "accepted", "hypothesis": candidate}

    def _is_complete_candidate(self, candidate: Dict[str, Any]) -> bool:
        required = ["hypothesis_id", "source_provenance", "freeze_time", "trigger_predicate", "scope_predicates", "expected_effect_predicate", "evaluation_horizon"]
        return all(field in candidate for field in required)

    def _is_normalizable_predicate(self, predicate: Optional[Dict[str, Any]]) -> bool:
        if not isinstance(predicate, dict):
            return False
        if not {"field", "operator", "value"}.issubset(predicate):
            return False
        if not isinstance(predicate["field"], str) or not predicate["field"]:
            return False
        if not isinstance(predicate["operator"], str) or predicate["operator"] not in ALLOWED_OPERATORS:
            return False
        return True

    def _is_allowed_operator(self, operator: Optional[str]) -> bool:
        return isinstance(operator, str) and operator in ALLOWED_OPERATORS

    def _is_positive_horizon(self, horizon: Any) -> bool:
        return isinstance(horizon, int) and horizon > 0

    def _contains_tautology(self, candidate: Dict[str, Any]) -> bool:
        for predicate in [candidate.get("trigger_predicate"), candidate.get("expected_effect_predicate")]:
            if isinstance(predicate, dict) and predicate.get("field") == predicate.get("value"):
                return True
        return False

    def _is_same_observable_restatement(self, candidate: Dict[str, Any]) -> bool:
        trigger_field = candidate.get("trigger_predicate", {}).get("field")
        effect_field = candidate.get("expected_effect_predicate", {}).get("field")
        return bool(trigger_field and effect_field and trigger_field == effect_field)

    def _expected_effect_known_at_formation(self, candidate: Dict[str, Any], formation_window: pd.DataFrame) -> bool:
        effect_predicate = candidate.get("expected_effect_predicate")
        if not effect_predicate:
            return False
        field = effect_predicate.get("field")
        operator = effect_predicate.get("operator")
        value = effect_predicate.get("value")
        if field not in formation_window.columns:
            return False
        formation_values = formation_window[field].dropna()
        if formation_values.empty:
            return False
        if operator == "==":
            return bool((formation_values == value).any())
        if operator == "!=":
            return bool((formation_values != value).any())
        if operator == ">":
            return bool((formation_values > value).any())
        if operator == ">=":
            return bool((formation_values >= value).any())
        if operator == "<":
            return bool((formation_values < value).any())
        if operator == "<=":
            return bool((formation_values <= value).any())
        return False

    def _canonical_key(self, candidate: Dict[str, Any]) -> Tuple[Tuple[Any, ...], ...]:
        trigger = tuple(sorted(candidate.get("trigger_predicate", {}).items()))
        scopes = tuple(sorted(tuple(sorted(pred.items())) for pred in candidate.get("scope_predicates", [])))
        effect = tuple(sorted(candidate.get("expected_effect_predicate", {}).items()))
        horizon = (candidate.get("evaluation_horizon"),)
        return (trigger, scopes, effect, horizon)

    def _evaluate_hypothesis_on_day(self, hypothesis: Dict[str, Any], day_index: int, artifact: pd.DataFrame) -> Dict[str, Any]:
        row = artifact.iloc[day_index + 10]
        scope_result = self._evaluate_scope(hypothesis.get("scope_predicates", []), day_index + 10, artifact)
        trigger_result = self._evaluate_predicate(hypothesis.get("trigger_predicate"), day_index + 10, artifact)
        effect_result = None
        if scope_result["result"] == "FALSE":
            evidence_outcome = "NOT_APPLICABLE"
            reason_code = None
        elif scope_result["result"] in {"UNKNOWN", "MISSING", "UNNORMALIZABLE"}:
            evidence_outcome = "INCONCLUSIVE"
            reason_code = "SCOPE_INCONCLUSIVE"
        else:
            if trigger_result["result"] == "FALSE":
                evidence_outcome = "NOT_APPLICABLE"
                reason_code = None
            elif trigger_result["result"] in {"UNKNOWN", "MISSING", "UNNORMALIZABLE"}:
                evidence_outcome = "INCONCLUSIVE"
                reason_code = "TRIGGER_INCONCLUSIVE"
            else:
                activation_day = day_index + EVALUATION_WINDOW_START
                target_day = compute_target_day(activation_day=activation_day, horizon=hypothesis.get("evaluation_horizon", 0))
                if target_day is None or target_day < EVALUATION_WINDOW_START or target_day > EVALUATION_WINDOW_END:
                    evidence_outcome = "INCONCLUSIVE"
                    reason_code = "TARGET_OUTSIDE_EVALUATION_WINDOW"
                else:
                    effect_result = self._evaluate_predicate(hypothesis.get("expected_effect_predicate"), target_day - 1, artifact)
                    if effect_result["result"] == "TRUE":
                        evidence_outcome = "SUPPORTED"
                        reason_code = None
                    elif effect_result["result"] == "FALSE":
                        evidence_outcome = "CONTRADICTED"
                        reason_code = None
                    else:
                        evidence_outcome = "INCONCLUSIVE"
                        reason_code = "EFFECT_INCONCLUSIVE"
        activation_day = day_index + EVALUATION_WINDOW_START
        target_day = compute_target_day(activation_day=activation_day, horizon=hypothesis.get("evaluation_horizon", 0))
        target_row = artifact.iloc[target_day - 1] if target_day is not None and 1 <= target_day <= len(artifact) else None
        return {
            "hypothesis_id": hypothesis.get("hypothesis_id"),
            "evaluation_day": activation_day,
            "scope": scope_result,
            "trigger": trigger_result,
            "activation_status": "ACTIVATED" if scope_result["result"] == "TRUE" and trigger_result["result"] == "TRUE" else "NOT_ACTIVATED",
            "target_day": target_day if scope_result["result"] == "TRUE" and trigger_result["result"] == "TRUE" else None,
            "target": {
                "day": int(target_row.name + 1) if target_row is not None else None,
                "values": target_row.to_dict() if target_row is not None else None,
            } if target_row is not None else None,
            "expected_effect_result": effect_result,
            "evidence_outcome": evidence_outcome,
            "reason_code": reason_code,
        }

    def _evaluate_scope(self, predicates: List[Dict[str, Any]], index: int, artifact: pd.DataFrame) -> Dict[str, Any]:
        if not predicates:
            return {"result": "TRUE", "field": None, "operator": None, "value": None, "actual": None}
        results = [self._evaluate_predicate(predicate, index, artifact) for predicate in predicates]
        if any(result["result"] == "FALSE" for result in results):
            return {"result": "FALSE", "field": None, "operator": None, "value": None, "actual": None}
        if any(result["result"] in {"UNKNOWN", "UNNORMALIZABLE"} for result in results):
            return {"result": "UNKNOWN", "field": None, "operator": None, "value": None, "actual": None}
        return {"result": "TRUE", "field": None, "operator": None, "value": None, "actual": None}

    def _evaluate_predicate(self, predicate: Optional[Dict[str, Any]], index: int, artifact: pd.DataFrame) -> Dict[str, Any]:
        if not predicate:
            return {"result": "UNKNOWN", "field": None, "operator": None, "value": None, "actual": None}
        field = predicate.get("field")
        operator = predicate.get("operator")
        value = predicate.get("value")
        if field not in artifact.columns:
            return {"result": "UNKNOWN", "field": field, "operator": operator, "value": value, "actual": None}
        row_value = artifact.iloc[index][field]
        if pd.isna(row_value):
            return {"result": "UNKNOWN", "field": field, "operator": operator, "value": value, "actual": None}
        if not self._is_allowed_operator(operator):
            return {"result": "UNNORMALIZABLE", "field": field, "operator": operator, "value": value, "actual": row_value}
        try:
            compare = self._compare_values(row_value, value, operator)
        except Exception:
            return {"result": "UNNORMALIZABLE", "field": field, "operator": operator, "value": value, "actual": row_value}
        return {"result": "TRUE" if compare else "FALSE", "field": field, "operator": operator, "value": value, "actual": row_value}

    def _compare_values(self, left: Any, right: Any, operator: str) -> bool:
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        raise ValueError(operator)

    def _build_formation_metrics(self, candidates: List[Dict[str, Any]], rejections: List[Dict[str, Any]], accepted: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for rejection in rejections:
            counts[rejection["rejection_reason"]] = counts.get(rejection["rejection_reason"], 0) + 1
        return {
            "candidates_generated": len(candidates),
            "candidates_rejected": len(rejections),
            "rejection_counts_by_reason": counts,
            "exact_duplicates": counts.get("DUPLICATE", 0),
            "accepted_hypotheses": len(accepted),
        }

    def _build_evaluation_metrics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = {
            "total_evaluation_opportunities": len(history),
            "not_applicable_count": sum(1 for item in history if item["evidence_outcome"] == "NOT_APPLICABLE"),
            "activation_count": sum(1 for item in history if item["activation_status"] == "ACTIVATED"),
            "tested_count": sum(1 for item in history if item["evidence_outcome"] in {"SUPPORTED", "CONTRADICTED"}),
            "supported_count": sum(1 for item in history if item["evidence_outcome"] == "SUPPORTED"),
            "contradicted_count": sum(1 for item in history if item["evidence_outcome"] == "CONTRADICTED"),
            "inconclusive_count": sum(1 for item in history if item["evidence_outcome"] == "INCONCLUSIVE"),
            "inconclusive_counts_by_reason": {},
        }
        for item in history:
            if item["evidence_outcome"] == "INCONCLUSIVE" and item.get("reason_code"):
                metrics["inconclusive_counts_by_reason"][item["reason_code"]] = metrics["inconclusive_counts_by_reason"].get(item["reason_code"], 0) + 1
        return metrics

    def _build_per_hypothesis_reports(self, hypotheses: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        reports: Dict[str, Dict[str, Any]] = {}
        for hypothesis in hypotheses:
            items = [item for item in history if item["hypothesis_id"] == hypothesis.get("hypothesis_id")]
            tested = [item for item in items if item["evidence_outcome"] in {"SUPPORTED", "CONTRADICTED"}]
            reports[hypothesis.get("hypothesis_id")] = {
                "evaluation_opportunities": len(items),
                "activations": sum(1 for item in items if item["activation_status"] == "ACTIVATED"),
                "tested_experiences": len(tested),
                "supported": sum(1 for item in tested if item["evidence_outcome"] == "SUPPORTED"),
                "contradicted": sum(1 for item in tested if item["evidence_outcome"] == "CONTRADICTED"),
                "inconclusive": sum(1 for item in items if item["evidence_outcome"] == "INCONCLUSIVE"),
                "not_applicable": sum(1 for item in items if item["evidence_outcome"] == "NOT_APPLICABLE"),
                "support_ratio_among_tested_experiences": (sum(1 for item in tested if item["evidence_outcome"] == "SUPPORTED") / len(tested)) if tested else None,
            }
        return reports

    def _build_base_rate_diagnostics(self, hypotheses: List[Dict[str, Any]], evaluation_window: pd.DataFrame, history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        diagnostics: Dict[str, Dict[str, Any]] = {}
        for hypothesis in hypotheses:
            items = [item for item in history if item["hypothesis_id"] == hypothesis.get("hypothesis_id")]
            tested = [item for item in items if item["evidence_outcome"] in {"SUPPORTED", "CONTRADICTED"}]
            support_ratio = (sum(1 for item in tested if item["evidence_outcome"] == "SUPPORTED") / len(tested)) if tested else None
            target_base_rate = None
            if len(evaluation_window) > 0:
                target_base_rate = len(tested) / len(evaluation_window) if len(evaluation_window) else None
            diagnostics[hypothesis.get("hypothesis_id")] = {
                "support_ratio": support_ratio,
                "unconditional_target_base_rate_over_evaluation_window": target_base_rate,
                "descriptive_support_lift": (support_ratio - target_base_rate) if support_ratio is not None and target_base_rate is not None else None,
            }
        return diagnostics

    def _build_frozen_hypothesis_report(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "hypothesis_id": hypothesis.get("hypothesis_id"),
                "source_provenance": hypothesis.get("source_provenance"),
                "when_trigger": hypothesis.get("trigger_predicate"),
                "under_scope": hypothesis.get("scope_predicates"),
                "expect_effect": hypothesis.get("expected_effect_predicate"),
                "after_horizon": hypothesis.get("evaluation_horizon"),
            }
            for hypothesis in hypotheses
        ]

    def _write_outputs(self, report: Dict[str, Any]) -> None:
        with (self.output_dir / "frozen_hypothesis_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report["frozen_hypothesis_report"], handle, indent=2)
        with (self.output_dir / "rejection_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report["rejections"], handle, indent=2)
        with (self.output_dir / "raw_evaluation_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report["history"], handle, indent=2)
        with (self.output_dir / "summary_report.json").open("w", encoding="utf-8") as handle:
            json.dump({
                "formation": report["formation"],
                "evaluation": report["evaluation"],
                "hypotheses": report["hypotheses"],
            }, handle, indent=2)
        with (self.output_dir / "frozen_hypothesis_report.md").open("w", encoding="utf-8") as handle:
            handle.write("# Frozen Hypothesis Report\n\n")
            for item in report["frozen_hypothesis_report"]:
                handle.write(
                    f"- {item['hypothesis_id']}: WHEN {item['when_trigger']} UNDER {item['under_scope']} EXPECT {item['expect_effect']} AFTER {item['after_horizon']}\n"
                )


def compute_target_day(activation_day: int, horizon: int) -> Optional[int]:
    if not isinstance(activation_day, int) or not isinstance(horizon, int) or horizon <= 0:
        return None
    return activation_day + horizon
