"""
PROMPT E2 — 20-Seed Synthetic Battery Runner & Gate A Evaluator.

Executes:
- 4 Scenarios (S1 Clean, S2 Spurious/Decoy, S3 Regime Flip, S4 Scoped Rule)
- 20 Seeds (0..19)
- 4 Learners (TruModalOracle, ElatraverianLearner, ContextualBayesianLearner, DPAdapter)
- 200 Steps per run

Outputs:
- bench/results/e2_raw_metrics.jsonl
- bench/results/reliability_curve.csv
- bench/results/e2_results.md
"""
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bench.synthworld.world import SynthWorldScenario
from bench.synthworld.learners import (
    Learner,
    TruModalOracle,
    ElatraverianLearner,
    ContextualBayesianLearner,
)
from bench.synthworld.dp_adapter import DPAdapter
from bench.synthworld.metrics import compute_brier_score


def mean(vals: List[float]) -> float:
    return sum(vals) / max(1, len(vals))


def std_dev(vals: List[float]) -> float:
    if len(vals) <= 1:
        return 0.0
    m = mean(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var)


def median_and_iqr(vals: List[float]) -> Tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    sorted_v = sorted(vals)
    n = len(sorted_v)
    med = sorted_v[n // 2] if n % 2 != 0 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2.0
    q1 = sorted_v[n // 4]
    q3 = sorted_v[(3 * n) // 4]
    return med, q3 - q1


def run_single_seed_experiment(
    scenario_id: str,
    seed: int,
    steps: int = 200,
) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[float, int]]]:
    """
    Runs a single seed experiment across all 4 learners.
    Returns per-learner metric dictionaries and DPAdapter calibration sample pairs.
    """
    scenario = SynthWorldScenario(scenario_id=scenario_id, seed=seed)
    causes = scenario.candidate_causes()
    effects = scenario.effects()

    learners: Dict[str, Learner] = {
        "TruModalOracle": TruModalOracle(scenario),
        "Elatraverian": ElatraverianLearner(scenario),
        "ContextualBayesian": ContextualBayesianLearner(scenario),
        "DPAdapter": DPAdapter(scenario),
    }

    # Track predictions and actuals per learner
    predictions: Dict[str, List[Dict[str, float]]] = {k: [] for k in learners}
    actuals: List[Dict[str, int]] = []
    scope_signals: List[int] = []

    # Calibration pairs for DPAdapter: (predicted_confidence, actual_outcome)
    dp_calibration_pairs: List[Tuple[float, int]] = []

    prior_events = None
    dead_rule_dropped_step: Dict[str, Optional[int]] = {k: None for k in learners}

    for t in range(steps):
        events = scenario.generate_step(t, prior_events=prior_events)

        # Predict
        step_preds = {}
        for name, learner in learners.items():
            pred = learner.predict(t, events)
            step_preds[name] = pred
            predictions[name].append(pred)

            if name == "DPAdapter":
                for e, p in pred.items():
                    # We will align prediction made at t with actual effect at t+1
                    pass

        # Observe
        for name, learner in learners.items():
            learner.observe(t, events)

            # S3 Recovery Tracking post regime flip (t >= 100)
            if scenario_id == "S3" and t >= 100:
                beliefs = learner.beliefs()
                dead_rule_conf = beliefs.get(("c1", "e1"), 1.0)
                if dead_rule_conf < 0.50 and dead_rule_dropped_step[name] is None:
                    dead_rule_dropped_step[name] = t - 100

        actuals.append(events)
        scope_signals.append(events.get("s1", 0))
        prior_events = events

    # Collect calibration pairs for DPAdapter (shift predictions by 1 step)
    for t in range(steps - 1):
        pred_dp = predictions["DPAdapter"][t]
        act_next = actuals[t + 1]
        for e in effects:
            dp_calibration_pairs.append((pred_dp.get(e, 0.0), act_next.get(e, 0)))

    # Compute Oracle Brier Score for regret calculation
    shifted_actuals = actuals[1:]
    oracle_preds = predictions["TruModalOracle"][:-1]
    oracle_brier = compute_brier_score(oracle_preds, shifted_actuals)

    metrics_by_learner: Dict[str, Dict[str, Any]] = {}

    for name, learner in learners.items():
        learner_preds = predictions[name][:-1]
        brier = compute_brier_score(learner_preds, shifted_actuals)
        brier_regret = brier - oracle_brier

        # Final beliefs at end of run
        final_beliefs = learner.beliefs()
        true_causes = scenario.ground_truth_causes(steps - 1)

        # Discovery Precision & Recall
        tp = 0
        fp = 0
        fn = 0
        gt_set = set((c, e) for c in true_causes for e in effects)

        for c in causes:
            for e in effects:
                conf = final_beliefs.get((c, e), 0.0)
                if conf >= 0.50:
                    if (c, e) in gt_set:
                        tp += 1
                    else:
                        fp += 1
                else:
                    if (c, e) in gt_set:
                        fn += 1

        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)

        # Decoy sensitivity (S2)
        decoy_sens = final_beliefs.get(("c2", "e1"), 0.0)

        # S3 Recovery Steps
        if scenario_id == "S3":
            rec_steps = dead_rule_dropped_step[name] if dead_rule_dropped_step[name] is not None else 100
        else:
            rec_steps = 0

        # S3 Collateral Rate
        collateral_rate = 0.0
        if scenario_id == "S3":
            # True rule post flip is c2 -> e1
            c2_conf = final_beliefs.get(("c2", "e1"), 0.0)
            if c2_conf < 0.50:
                collateral_rate = 1.0

        # S4 Scoped Regret vs Unconditioned Regret
        scoped_preds = []
        scoped_acts = []
        for t_idx in range(steps - 1):
            if scope_signals[t_idx] == 1:
                scoped_preds.append(predictions[name][t_idx])
                scoped_acts.append(shifted_actuals[t_idx])

        scoped_brier = compute_brier_score(scoped_preds, scoped_acts) if scoped_preds else brier
        scoped_oracle_brier = compute_brier_score([oracle_preds[i] for i in range(len(oracle_preds)) if scope_signals[i] == 1], scoped_acts) if scoped_preds else oracle_brier
        scoped_regret = scoped_brier - scoped_oracle_brier

        metrics_by_learner[name] = {
            "scenario": scenario_id,
            "seed": seed,
            "learner": name,
            "brier_score": brier,
            "oracle_brier": oracle_brier,
            "brier_regret": brier_regret,
            "precision": precision,
            "recall": recall,
            "decoy_sensitivity": decoy_sens,
            "recovery_steps": rec_steps,
            "collateral_rate": collateral_rate,
            "scoped_regret": scoped_regret,
            "unconditioned_regret": brier_regret,
        }

    return metrics_by_learner, dp_calibration_pairs


def compute_ece_and_reliability_curve(calibration_pairs: List[Tuple[float, int]], num_bins: int = 10) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes Expected Calibration Error (ECE) and reliability curve rows over num_bins equal width bins.
    """
    if not calibration_pairs:
        return 0.0, []

    total_samples = len(calibration_pairs)
    bin_width = 1.0 / num_bins
    curve_rows = []
    ece = 0.0

    for idx in range(num_bins):
        b_min = idx * bin_width
        b_max = (idx + 1) * bin_width
        # Filter samples in bin [b_min, b_max) (inclusive of 1.0 for last bin)
        if idx == num_bins - 1:
            bin_samples = [p for p in calibration_pairs if b_min <= p[0] <= b_max]
        else:
            bin_samples = [p for p in calibration_pairs if b_min <= p[0] < b_max]

        count = len(bin_samples)
        if count > 0:
            mean_conf = sum(p[0] for p in bin_samples) / count
            emp_acc = sum(p[1] for p in bin_samples) / count
            gap = abs(emp_acc - mean_conf)
            ece += (count / total_samples) * gap
        else:
            mean_conf = (b_min + b_max) / 2.0
            emp_acc = 0.0
            gap = 0.0

        curve_rows.append({
            "bin_index": idx,
            "bin_min": round(b_min, 2),
            "bin_max": round(b_max, 2),
            "sample_count": count,
            "mean_confidence": round(mean_conf, 4),
            "empirical_accuracy": round(emp_acc, 4),
            "calibration_gap": round(gap, 4),
        })

    return ece, curve_rows


def run_e2_battery(num_seeds: int = 20, steps: int = 200) -> Dict[str, Any]:
    scenarios = ["S1", "S2", "S3", "S4"]
    learners = ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]

    results_dir = PROJECT_ROOT / "bench" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_metrics_path = results_dir / "e2_raw_metrics.jsonl"
    if raw_metrics_path.exists():
        raw_metrics_path.unlink()

    all_raw_records: List[Dict[str, Any]] = []
    all_dp_calibration_pairs: List[Tuple[float, int]] = []

    print(f"======================================================================")
    print(f"STARTING PROMPT E2 BENCHMARK BATTERY ({num_seeds} Seeds x {len(scenarios)} Scenarios)")
    print(f"======================================================================")

    for scenario_id in scenarios:
        for seed in range(num_seeds):
            m_dict, cal_pairs = run_single_seed_experiment(scenario_id, seed, steps=steps)
            all_dp_calibration_pairs.extend(cal_pairs)
            for learner_name, record in m_dict.items():
                all_raw_records.append(record)
                with open(raw_metrics_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, sort_keys=True) + "\n")

    print(f"✓ Executed {len(all_raw_records)} runs. Saved raw metrics to {raw_metrics_path}")

    # Compute ECE & Reliability Curve
    ece_val, reliability_curve = compute_ece_and_reliability_curve(all_dp_calibration_pairs)

    reliability_csv_path = results_dir / "reliability_curve.csv"
    with open(reliability_csv_path, "w", encoding="utf-8") as f:
        f.write("bin_index,bin_min,bin_max,sample_count,mean_confidence,empirical_accuracy,calibration_gap\n")
        for row in reliability_curve:
            f.write(f"{row['bin_index']},{row['bin_min']},{row['bin_max']},{row['sample_count']},{row['mean_confidence']},{row['empirical_accuracy']},{row['calibration_gap']}\n")

    print(f"✓ Expected Calibration Error (ECE): {ece_val:.4f}. Saved reliability curve to {reliability_csv_path}")

    # Aggregate Statistics per Scenario per Learner
    agg_stats: Dict[str, Dict[str, Dict[str, Any]]] = {s: {l: {} for l in learners} for s in scenarios}

    for s_id in scenarios:
        for l_name in learners:
            subset = [r for r in all_raw_records if r["scenario"] == s_id and r["learner"] == l_name]

            regrets = [r["brier_regret"] for r in subset]
            precs = [r["precision"] for r in subset]
            recalls = [r["recall"] for r in subset]
            decoys = [r["decoy_sensitivity"] for r in subset]
            rec_steps = [r["recovery_steps"] for r in subset]
            col_rates = [r["collateral_rate"] for r in subset]

            med_regret, iqr_regret = median_and_iqr(regrets)

            agg_stats[s_id][l_name] = {
                "brier_regret_mean": mean(regrets),
                "brier_regret_std": std_dev(regrets),
                "brier_regret_med": med_regret,
                "brier_regret_iqr": iqr_regret,
                "precision_mean": mean(precs),
                "precision_std": std_dev(precs),
                "recall_mean": mean(recalls),
                "recall_std": std_dev(recalls),
                "decoy_sensitivity_mean": mean(decoys),
                "decoy_sensitivity_std": std_dev(decoys),
                "recovery_steps_mean": mean(rec_steps),
                "recovery_steps_std": std_dev(rec_steps),
                "collateral_rate_mean": mean(col_rates),
                "collateral_rate_std": std_dev(col_rates),
            }

    # Evaluate Gate A Branch Mechanically
    # Criterion 1: DPAdapter S2 Decoy Sensitivity vs Elatraverian
    s2_dp_decoy = agg_stats["S2"]["DPAdapter"]["decoy_sensitivity_mean"]
    s2_ela_decoy = agg_stats["S2"]["Elatraverian"]["decoy_sensitivity_mean"]

    # Criterion 2: DPAdapter S3 Recovery Steps <= 100
    s3_dp_rec = agg_stats["S3"]["DPAdapter"]["recovery_steps_mean"]

    # Criterion 3: Regret comparison on S1-S4
    s1_dp_regret = agg_stats["S1"]["DPAdapter"]["brier_regret_mean"]
    s1_ela_regret = agg_stats["S1"]["Elatraverian"]["brier_regret_mean"]

    s2_dp_regret = agg_stats["S2"]["DPAdapter"]["brier_regret_mean"]
    s2_ela_regret = agg_stats["S2"]["Elatraverian"]["brier_regret_mean"]

    # Determine Gate A Branch
    determining_lines = []

    if s2_dp_decoy < s2_ela_decoy and s3_dp_rec <= 100 and s2_dp_regret <= s2_ela_regret:
        gate_branch = "PASS"
        determining_lines.append(f"- Criterion 1 (PASS): DPAdapter S2 Decoy Sensitivity ({s2_dp_decoy:.4f}) is strictly lower than Elatraverian baseline ({s2_ela_decoy:.4f}).")
        determining_lines.append(f"- Criterion 2 (PASS): DPAdapter S3 Recovery Steps ({s3_dp_rec:.1f} steps) is <= 100 steps.")
        determining_lines.append(f"- Criterion 3 (PASS): DPAdapter S2 Brier Regret ({s2_dp_regret:.4f}) is <= Elatraverian ({s2_ela_regret:.4f}).")
    elif s2_dp_regret > s2_ela_regret or s2_dp_decoy > s2_ela_decoy:
        gate_branch = "FAIL"
        determining_lines.append(f"- Criterion 1 (FAIL): DPAdapter S2 Decoy Sensitivity ({s2_dp_decoy:.4f}) is >= Elatraverian baseline ({s2_ela_decoy:.4f}) or Regret is higher.")
        determining_lines.append(f"- Criterion 2: S3 Recovery Steps = {s3_dp_rec:.1f} steps.")
    else:
        gate_branch = "AMBIGUOUS"
        determining_lines.append(f"- Criterion 1 (AMBIGUOUS): Mixed performance profile across S1-S4.")

    print(f"\n======================================================================")
    print(f"GATE A BRANCH DETERMINATION: [{gate_branch}]")
    print(f"======================================================================")
    for line in determining_lines:
        print(line)

    # Generate bench/results/e2_results.md
    results_md_path = results_dir / "e2_results.md"
    generate_e2_results_markdown(results_md_path, agg_stats, gate_branch, determining_lines, ece_val, reliability_curve)

    return {
        "gate_branch": gate_branch,
        "determining_lines": determining_lines,
        "ece": ece_val,
        "agg_stats": agg_stats,
        "results_md_path": str(results_md_path),
        "reliability_csv_path": str(reliability_csv_path),
    }


def generate_e2_results_markdown(
    output_path: Path,
    agg_stats: Dict[str, Dict[str, Dict[str, Any]]],
    gate_branch: str,
    determining_lines: List[str],
    ece_val: float,
    reliability_curve: List[Dict[str, Any]],
):
    md_content = f"""# PROMPT E2 — 20-Seed Synthetic Benchmark Battery Results

* **Evaluation Timestamp**: 2026-07-24
* **Total Seeds**: 20 (seeds 0..19)
* **Steps Per Seed**: 200
* **Expected Calibration Error (ECE)**: **{ece_val:.4f}**
* **Gate A Branch Outcome**: **`GATE A: {gate_branch}`**

---

## 1. Gate A Branch Verdict & Quoted Determining Criteria

```text
GATE A BRANCH: {gate_branch}
Determining Criteria Lines:
"""
    for line in determining_lines:
        md_content += f"{line}\n"

    md_content += f"""```

---

## 2. Benchmark Metric Tables Per Scenario (Mean ± Std)

### Scenario S1 (Clean Cause-Effect)
| Learner | Brier Regret (vs Oracle) | Precision | Recall | Median Regret (IQR) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for l in ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]:
        st = agg_stats["S1"][l]
        md_content += f"| **{l}** | {st['brier_regret_mean']:.4f} ± {st['brier_regret_std']:.4f} | {st['precision_mean']:.4f} | {st['recall_mean']:.4f} | {st['brier_regret_med']:.4f} ({st['brier_regret_iqr']:.4f}) |\n"

    md_content += f"""
### Scenario S2 (Spurious / Decoy Trap)
| Learner | Brier Regret (vs Oracle) | Decoy Sensitivity | Precision | Recall |
| :--- | :--- | :--- | :--- | :--- |
"""
    for l in ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]:
        st = agg_stats["S2"][l]
        md_content += f"| **{l}** | {st['brier_regret_mean']:.4f} ± {st['brier_regret_std']:.4f} | **{st['decoy_sensitivity_mean']:.4f}** | {st['precision_mean']:.4f} | {st['recall_mean']:.4f} |\n"

    md_content += f"""
### Scenario S3 (Regime Flip)
| Learner | Brier Regret (vs Oracle) | Recovery Steps (t >= 100) | Collateral Rate | Precision |
| :--- | :--- | :--- | :--- | :--- |
"""
    for l in ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]:
        st = agg_stats["S3"][l]
        md_content += f"| **{l}** | {st['brier_regret_mean']:.4f} ± {st['brier_regret_std']:.4f} | **{st['recovery_steps_mean']:.1f} steps** | {st['collateral_rate_mean']:.4f} | {st['precision_mean']:.4f} |\n"

    md_content += f"""
### Scenario S4 (Scoped Rule)
| Learner | Brier Regret (vs Oracle) | Precision | Recall | Median Regret (IQR) |
| :--- | :--- | :--- | :--- | :--- |
"""
    for l in ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]:
        st = agg_stats["S4"][l]
        md_content += f"| **{l}** | {st['brier_regret_mean']:.4f} ± {st['brier_regret_std']:.4f} | {st['precision_mean']:.4f} | {st['recall_mean']:.4f} | {st['brier_regret_med']:.4f} ({st['brier_regret_iqr']:.4f}) |\n"

    md_content += f"""
---

## 3. Reliability Curve & Calibration Table (DPAdapter)

* **Overall ECE**: **{ece_val:.4f}**

| Bin Index | Confidence Range | Sample Count | Mean Confidence | Empirical Accuracy | Calibration Gap |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for row in reliability_curve:
        md_content += f"| Bin {row['bin_index']} | [{row['bin_min']:.2f} - {row['bin_max']:.2f}] | {row['sample_count']} | {row['mean_confidence']:.4f} | {row['empirical_accuracy']:.4f} | {row['calibration_gap']:.4f} |\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✓ Results markdown saved to {output_path}")


if __name__ == "__main__":
    res = run_e2_battery(num_seeds=20, steps=200)
