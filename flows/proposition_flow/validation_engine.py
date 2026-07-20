import logging
from datetime import datetime, timezone
from typing import Any, Tuple
from uuid import uuid4

import pandas as pd

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord

logger = logging.getLogger(__name__)


class ValidationEngine:
    VERSION = "1.0.0"

    def validate(
        self,
        compiled_prop: CompiledProposition,
        history_df: pd.DataFrame,
        current_step: int,
        confidence_before: float = 0.5,
        confidence_after: float = 0.5,
        uncertainty_before: float = 0.5,
        uncertainty_after: float = 0.5,
        regime: str = "neutral",
        market_context: dict = None,
    ) -> ValidationRecord:
        """Deterministically evaluates a grounded CompiledProposition against observed reality."""
        validation_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)

        # Base properties for provenance
        base_record = {
            "proposition_id": getattr(compiled_prop, "id", "N/A"),
            "canonical_proposition_id": getattr(
                compiled_prop, "canonical_proposition_id", "N/A"
            ),
            "theory_id": getattr(compiled_prop, "theory_id", "N/A"),
            "lineage_id": getattr(compiled_prop, "lineage_id", "N/A"),
            "mechanism_ids": getattr(compiled_prop, "mechanism_ids", []),
            "timestamp": timestamp,
            "replay_step": current_step,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "confidence_delta": confidence_after - confidence_before,
            "uncertainty_before": uncertainty_before,
            "uncertainty_after": uncertainty_after,
            "uncertainty_delta": uncertainty_after - uncertainty_before,
            "regime": regime,
            "market_context": market_context,
            "grounding_version": "1.7.0",
            "compiler_version": "1.7.0",
            "validation_engine_version": self.VERSION,
            "notes": None,
        }

        if getattr(compiled_prop, "compilation_status", "") != "SUCCESS":
            return self._create_record(
                validation_id=validation_id,
                validation_state="GROUNDED",
                validation_trace={
                    "error": "Proposition compilation status is not SUCCESS"
                },
                base_record=base_record,
            )

        try:
            # 1. Evaluate Trigger
            trigger_def = compiled_prop.trigger_definition
            if not trigger_def:
                return self._create_record(
                    validation_id=validation_id,
                    validation_state="UNTRIGGERED",
                    validation_trace={"trigger": "Missing trigger definition"},
                    base_record=base_record,
                )

            trigger_met, trigger_val, trigger_trace = self._evaluate_condition(
                trigger_def, history_df, current_step
            )

            if not trigger_met:
                return self._create_record(
                    validation_id=validation_id,
                    validation_state="UNTRIGGERED",
                    validation_trace={
                        "trigger_evaluated": trigger_trace,
                        "trigger_val": trigger_val,
                        "status": "Trigger condition not met",
                    },
                    base_record=base_record,
                )

            # 2. Evaluate Scope Constraints
            scope_defs = compiled_prop.scope_definition or []
            scope_met = True
            scope_traces = []
            for scope_def in scope_defs:
                sc_met, sc_val, sc_trace = self._evaluate_condition(
                    scope_def, history_df, current_step
                )
                scope_traces.append(
                    {
                        "definition": scope_def,
                        "evaluated": sc_trace,
                        "val": sc_val,
                        "met": sc_met,
                    }
                )
                if not sc_met:
                    scope_met = False

            if not scope_met:
                return self._create_record(
                    validation_id=validation_id,
                    validation_state="UNTRIGGERED",
                    validation_trace={
                        "trigger_evaluated": trigger_trace,
                        "trigger_val": trigger_val,
                        "scope_evaluated": scope_traces,
                        "status": "Scope constraint mismatch",
                    },
                    base_record=base_record,
                )

            # 3. Evaluate Target (Lookahead Step)
            target_def = compiled_prop.target_definition
            if not target_def:
                return self._create_record(
                    validation_id=validation_id,
                    validation_state="TRIGGERED",
                    validation_trace={
                        "trigger_evaluated": trigger_trace,
                        "trigger_val": trigger_val,
                        "scope_evaluated": scope_traces,
                        "status": "No target definition found",
                    },
                    base_record=base_record,
                )

            # Standard lookahead target step is step + 1
            target_step = current_step + 1
            if target_step >= len(history_df):
                # Out of bounds - target has not yet realized in the backtest replay
                return self._create_record(
                    validation_id=validation_id,
                    validation_state="TRIGGERED",
                    validation_trace={
                        "trigger_evaluated": trigger_trace,
                        "trigger_val": trigger_val,
                        "scope_evaluated": scope_traces,
                        "status": "Target step is in the future",
                    },
                    base_record=base_record,
                )

            target_met, target_val, target_trace = self._evaluate_condition(
                target_def, history_df, target_step, prev_idx=current_step
            )

            state = "SUPPORTED" if target_met else "CONTRADICTED"
            evidence_dict = {
                "evaluated": target_trace,
                "val": target_val,
                "step": target_step,
            }

            return self._create_record(
                validation_id=validation_id,
                validation_state=state,
                supporting_evidence=evidence_dict if target_met else None,
                contradicting_evidence=None if target_met else evidence_dict,
                validation_trace={
                    "trigger_evaluated": trigger_trace,
                    "trigger_val": trigger_val,
                    "scope_evaluated": scope_traces,
                    "target_evaluated": target_trace,
                    "target_val": target_val,
                },
                base_record=base_record,
            )

        except Exception as e:
            logger.error(f"Validation Engine evaluation error: {e}", exc_info=True)
            return self._create_record(
                validation_id=validation_id,
                validation_state="GROUNDED",
                validation_trace={"error": f"Evaluation exception: {str(e)}"},
                base_record=base_record,
            )

    def _create_record(
        self,
        validation_id: str,
        validation_state: str,
        validation_trace: dict,
        base_record: dict,
        supporting_evidence: dict = None,
        contradicting_evidence: dict = None,
    ) -> ValidationRecord:
        """Helper to recursively sanitize types and return a clean ValidationRecord."""
        return ValidationRecord(
            id=validation_id,
            validation_state=validation_state,
            validation_trace=self._to_native(validation_trace),
            supporting_evidence=self._to_native(supporting_evidence),
            contradicting_evidence=self._to_native(contradicting_evidence),
            **{k: self._to_native(v) for k, v in base_record.items()},
        )

    def _to_native(self, val: Any) -> Any:
        """Recursively converts numpy and pandas types to standard Python native types."""
        if hasattr(val, "item") and callable(getattr(val, "item")):
            try:
                return val.item()
            except Exception:
                pass
        if isinstance(val, dict):
            return {k: self._to_native(v) for k, v in val.items()}
        if isinstance(val, list):
            return [self._to_native(x) for x in val]
        if isinstance(val, tuple):
            return tuple(self._to_native(x) for x in val)
        # Check for pandas/numpy int/float types explicitly
        if type(val).__name__ in ["int64", "int32", "long"]:
            return int(val)
        if type(val).__name__ in ["float64", "float32"]:
            return float(val)
        return val

    def _evaluate_condition(
        self,
        cond: dict,
        history_df: pd.DataFrame,
        idx: int,
        prev_idx: int = None,
    ) -> Tuple[bool, Any, str]:
        """Evaluates a single condition dictionary against history_df at index idx."""
        if "operand_left" in cond and "operand_right" in cond:
            left_operand = cond["operand_left"]
            right_operand = cond["operand_right"]
            op = cond["operator"]

            left_val, left_trace = self._resolve_operand(left_operand, history_df, idx)
            right_val, right_trace = self._resolve_operand(
                right_operand, history_df, idx
            )

            if left_val is None or right_val is None:
                return (
                    False,
                    None,
                    f"Operand evaluation failed: left={left_trace}, right={right_trace}",
                )

            is_met = self._apply_operator(left_val, op, right_val)
            desc = (
                f"Relative: {left_trace} ({left_val}) {op} {right_trace} ({right_val})"
            )
            return is_met, left_val, desc

        elif "field" in cond:
            field = cond["field"]
            op = cond["operator"]
            expected_val = cond.get("value")

            if field == "outcome":
                # Special evaluation of daily outcome close vs close at prev_idx
                ref_idx = prev_idx if prev_idx is not None else idx - 1
                if ref_idx < 0 or ref_idx >= len(history_df) or idx >= len(history_df):
                    return (
                        False,
                        None,
                        f"Outcome out of bounds: ref={ref_idx}, idx={idx}",
                    )
                close_prev = history_df["close"].iloc[ref_idx]
                close_curr = history_df["close"].iloc[idx]
                ret = (close_curr / close_prev - 1.0) if close_prev > 0 else 0.0
                if ret > 0.0005:
                    actual_dir = "up"
                elif ret < -0.0005:
                    actual_dir = "down"
                else:
                    actual_dir = "flat"

                is_met = self._apply_operator(actual_dir, op, expected_val)
                desc = f"Outcome: actual={actual_dir} {op} expected={expected_val} (return={ret:.4f})"
                return is_met, actual_dir, desc

            else:
                if field not in history_df.columns:
                    return (
                        False,
                        None,
                        f"Missing field in dataset: field={field}",
                    )
                lag = cond.get("lag", 0)
                target_idx = idx - lag
                if target_idx < 0 or target_idx >= len(history_df):
                    return (
                        False,
                        None,
                        f"Field index out of bounds: field={field}, idx={target_idx}",
                    )

                actual_val = history_df[field].iloc[target_idx]
                # If target is string, compare string representations lower case
                if isinstance(actual_val, str) and isinstance(expected_val, str):
                    is_met = self._apply_operator(
                        actual_val.lower(), op, expected_val.lower()
                    )
                else:
                    is_met = self._apply_operator(actual_val, op, expected_val)

                desc = f"Field: {field}[t-{lag}] ({actual_val}) {op} {expected_val}"
                return is_met, actual_val, desc

        return False, None, f"Invalid condition specification: {cond}"

    def _resolve_operand(
        self, operand: dict, history_df: pd.DataFrame, idx: int
    ) -> Tuple[Any, str]:
        field = operand.get("field")
        if not field or field not in history_df.columns:
            return None, f"{field} (Missing Column)"
        offset = operand.get("time_offset", 0)
        target_idx = idx + offset

        if target_idx < 0 or target_idx >= len(history_df):
            return None, f"{field}[t+{offset}] (Out of Bounds)"

        transform = operand.get("transform")
        if transform == "ROLLING_MEAN":
            window = operand.get("window_size", 20)
            start_idx = max(0, target_idx - window + 1)
            subset = history_df[field].iloc[start_idx : target_idx + 1]
            val = subset.mean()
            trace = f"rolling_mean({field}, {window})[t+{offset}]"
            return val, trace

        val = history_df[field].iloc[target_idx]
        trace = f"{field}[t+{offset}]"
        return val, trace


    def _apply_operator(self, left: Any, op: str, right: Any) -> bool:
        try:
            if op == ">":
                return float(left) > float(right)
            if op == "<":
                return float(left) < float(right)
            if op == "==":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) == str(right)
                return float(left) == float(right)
            if op == ">=":
                return float(left) >= float(right)
            if op == "<=":
                return float(left) <= float(right)
            if op == "!=":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) != str(right)
                return float(left) != float(right)
        except Exception:
            return left == right
        return False
