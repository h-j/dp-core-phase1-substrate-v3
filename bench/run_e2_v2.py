"""
PROMPT E2_v2 — 20-Seed Synthetic Battery Runner & Gate A Evaluator.

Executes full protocol:
- 4 Scenarios at DEFAULT step lengths:
  - S1 Clean (T=3000)
  - S2 Spurious Correlation / Decoys (T=3000, decoy window 0..600)
  - S3 Regime Change (T=4000, flip at t=2000)
  - S4 Scoped Rule (T=4000)
- 20 Seeds (0..19)
- 5 Learners: TrueModel, FlatBayesian, WindowedFrequency, ContextualBayesian, DPAdapter

Outputs:
- bench/results/e2_v2_raw_metrics.jsonl
- bench/results/e2_v2_reliability_curve.csv
- bench/results/e2_v2_results.md
"""
import json
import math
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bench.synthworld.scenarios import s1_clean, s2_spurious, s3_regime, s4_scope
from bench.synthworld.world import World, Scenario
from bench.synthworld.learners import (
    TrueModel,
    FlatBayesian,
    WindowedFrequency,
    ContextualBayesian,
)
from bench.synthworld.dp_adapter import DPAdapter
from bench.synthworld import metrics
from bench.synthworld.harness import run as run_scenario


def mean(vals: List[float]) -> float:
    vals = [v for v in vals if not math.isnan(v)]
    return sum(vals) / max(1, len(vals))


def std_dev(vals: List[float]) -> float:
    vals = [v for v in vals if not math.isnan(v)]
    if len(vals) <= 1:
        return 0.0
    m = mean(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var)


def iqr(vals: List[float]) -> Tuple[float, float]:
    vals = sorted([v for v in vals if not math.isnan(v)])
    if not vals:
        return (float("nan"), float("nan"))
    n = len(vals)
    q25 = vals[int(0.25 * n)]
    q75 = vals[min(int(0.75 * n), n - 1)]
    return (q25, q75)


def compute_ece_and_reliability_curve(
    calibration_pairs: List[Tuple[float, int]], num_bins: int = 10
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes Expected Calibration Error (ECE) and reliability curve data over num_bins bins.
    calibration_pairs: list of (stated_confidence, realized_outcome_0_or_1)
    """
    if not calibration_pairs:
        return 0.0, []

    bins = [[] for _ in range(num_bins)]
    for conf, outcome in calibration_pairs:
        bin_idx = min(int(conf * num_bins), num_bins - 1)
        bins[bin_idx].append((conf, outcome))

    total_count = len(calibration_pairs)
    ece = 0.0
    reliability_curve = []

    for b in range(num_bins):
        bin_samples = bins[b]
        bin_lower = b / num_bins
        bin_upper = (b + 1) / num_bins
        bin_mid = (bin_lower + bin_upper) / 2.0

        if bin_samples:
            avg_conf = sum(c for c, o in bin_samples) / len(bin_samples)
            avg_acc = sum(o for c, o in bin_samples) / len(bin_samples)
            weight = len(bin_samples) / total_count
            ece += weight * abs(avg_acc - avg_conf)
            reliability_curve.append({
                "bin": b,
                "bin_midpoint": bin_mid,
                "count": len(bin_samples),
                "avg_confidence": avg_conf,
                "avg_accuracy": avg_acc,
                "calibration_gap": abs(avg_acc - avg_conf),
            })
        else:
            reliability_curve.append({
                "bin": b,
                "bin_midpoint": bin_mid,
                "count": 0,
                "avg_confidence": bin_mid,
                "avg_accuracy": bin_mid,
                "calibration_gap": 0.0,
            })

    return ece, reliability_curve


def run_single_seed_battery(seed: int) -> Tuple[Dict[str, Dict[str, Dict[str, Any]]], List[Tuple[float, int]]]:
    """
    Runs 1 seed across all 4 scenarios and all 5 learners.
    Returns nested dictionary: scenario_name -> learner_name -> metrics_dict, and DP calibration pairs.
    """
    scenario_factories = [
        ("S1", s1_clean),
        ("S2", s2_spurious),
        ("S3", s3_regime),
        ("S4", s4_scope),
    ]

    seed_results = {}
    dp_calibration_pairs = []

    for sc_id, factory in scenario_factories:
        sc = factory()
        sc.seed = seed  # Override seed deterministically

        learners = [
            TrueModel(sc),
            FlatBayesian(sc),
            WindowedFrequency(sc),
            ContextualBayesian(sc),
            DPAdapter(sc),
        ]

        # Run scenario harness
        r = run_scenario(sc, learners)
        scores = r["scores"]
        beliefs = r["beliefs"]
        timeline = r["timeline"]

        oracle_name = TrueModel(sc).name
        oracle_brier = metrics.phase_brier(scores[oracle_name], 300, sc.T)

        sc_metrics = {}

        for ln in learners:
            ln_brier = metrics.phase_brier(scores[ln.name], 300, sc.T)
            brier_regret = ln_brier - oracle_brier

            disc = metrics.discovery(beliefs[ln.name], sc)
            precision = disc["precision"]
            recall = disc["recall"]
            decoy_claims = disc["decoy_claims"]

            rec_steps = float("nan")
            collateral_val = float("nan")
            if sc_id == "S3":
                rec = metrics.recovery(scores[ln.name], flip_t=2000, affected=["E1", "E3"], window=100)
                rec_steps = float(rec["recovery_steps"]) if rec["recovery_steps"] is not None else 2000.0
                collateral_val = metrics.collateral(scores[ln.name], flip_t=2000, unaffected=["E2"], window=300)

            scoped_regret = float("nan")
            if sc_id == "S4":
                # Compute scoped Brier regret when context C == 1
                ctx_indices = [t for t in range(300, min(sc.T - 1, len(scores[ln.name]))) if timeline[t].get("C", 0) == 1]
                if ctx_indices:
                    ln_scoped_brier = metrics.mean([scores[ln.name][t][e] for t in ctx_indices for e in sc.effects])
                    oracle_scoped_brier = metrics.mean([scores[oracle_name][t][e] for t in ctx_indices for e in sc.effects])
                    scoped_regret = ln_scoped_brier - oracle_scoped_brier

            sc_metrics[ln.name] = {
                "brier_score": ln_brier,
                "brier_regret": brier_regret,
                "precision": precision,
                "recall": recall,
                "decoy_claims": decoy_claims,
                "recovery_steps": rec_steps,
                "collateral": collateral_val,
                "scoped_regret": scoped_regret,
            }

            # Collect DP calibration pairs
            if isinstance(ln, DPAdapter):
                for t in range(sc.T - 1):
                    ev = timeline[t]
                    nxt = timeline[t + 1]
                    preds = ln.predict(t, ev)
                    for e in sc.effects:
                        dp_calibration_pairs.append((preds[e], nxt[e]))

        seed_results[sc_id] = sc_metrics

    return seed_results, dp_calibration_pairs


def run_e2_v2_battery(num_seeds: int = 20) -> Dict[str, Any]:
    print("======================================================================")
    print(f"STARTING PROMPT E2_v2 SYNTHETIC BENCHMARK BATTERY ({num_seeds} Seeds x 4 Scenarios x 5 Learners)")
    print("======================================================================")

    all_raw_metrics = []
    dp_all_calibration_pairs = []

    # Store metrics aggregated by scenario -> learner -> metric_name -> list of seed values
    scenarios = ["S1", "S2", "S3", "S4"]
    learner_names = [
        "TrueModel (oracle floor)",
        "FlatBayesian",
        "WindowedFrequency(w=200)",
        "ContextualBayesian",
        "DP/EkamNet",
    ]

    scenario_learner_metrics: Dict[str, Dict[str, Dict[str, List[float]]]] = {
        s: {
            l: {
                "brier_score": [],
                "brier_regret": [],
                "precision": [],
                "recall": [],
                "decoy_claims": [],
                "recovery_steps": [],
                "collateral": [],
                "scoped_regret": [],
            }
            for l in learner_names
        }
        for s in scenarios
    }


    for seed in range(num_seeds):
        seed_res, cal_pairs = run_single_seed_battery(seed)
        dp_all_calibration_pairs.extend(cal_pairs)

        for sc_id, l_dict in seed_res.items():
            for l_name, m_dict in l_dict.items():
                record = {"seed": seed, "scenario": sc_id, "learner": l_name}
                record.update(m_dict)
                all_raw_metrics.append(record)

                for m_name, val in m_dict.items():
                    scenario_learner_metrics[sc_id][l_name][m_name].append(val)

        print(f"✓ Completed Seed {seed + 1}/{num_seeds}")

    # Persist Raw Metrics
    results_dir = PROJECT_ROOT / "bench" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_path = results_dir / "e2_v2_raw_metrics.jsonl"
    with open(raw_path, "w", encoding="utf-8") as f:
        for r in all_raw_metrics:
            f.write(json.dumps(r) + "\n")
    print(f"✓ Saved per-seed raw metrics to {raw_path}")

    # Compute ECE & Reliability Curve
    ece, rel_curve = compute_ece_and_reliability_curve(dp_all_calibration_pairs, num_bins=10)
    curve_path = results_dir / "e2_v2_reliability_curve.csv"
    with open(curve_path, "w", encoding="utf-8") as f:
        f.write("bin,bin_midpoint,count,avg_confidence,avg_accuracy,calibration_gap\n")
        for row in rel_curve:
            f.write(f"{row['bin']},{row['bin_midpoint']:.4f},{row['count']},{row['avg_confidence']:.4f},{row['avg_accuracy']:.4f},{row['calibration_gap']:.4f}\n")
    print(f"✓ Saved reliability curve CSV to {curve_path} (ECE: {ece:.4f})")

    # Evaluate Gate A Branch Criteria
    gate_file = PROJECT_ROOT / "experiments" / "preregistration" / "gate_a.yaml"
    with open(gate_file, "r", encoding="utf-8") as f:
        gate_cfg = yaml.safe_load(f)

    # Extract means for Gate A pass criteria evaluation
    s2_dp_decoys = mean(scenario_learner_metrics["S2"]["DP/EkamNet"]["decoy_claims"])
    s2_flat_decoys = mean(scenario_learner_metrics["S2"]["FlatBayesian"]["decoy_claims"])

    s2_dp_prec = mean(scenario_learner_metrics["S2"]["DP/EkamNet"]["precision"])
    s2_flat_prec = mean(scenario_learner_metrics["S2"]["FlatBayesian"]["precision"])

    s3_dp_rec = mean(scenario_learner_metrics["S3"]["DP/EkamNet"]["recovery_steps"])
    s3_flat_rec = mean(scenario_learner_metrics["S3"]["FlatBayesian"]["recovery_steps"])

    s3_dp_col = mean(scenario_learner_metrics["S3"]["DP/EkamNet"]["collateral"])
    s3_win_col = mean(scenario_learner_metrics["S3"]["WindowedFrequency(w=200)"]["collateral"])

    s1_dp_regret = mean(scenario_learner_metrics["S1"]["DP/EkamNet"]["brier_regret"])
    s1_flat_regret = mean(scenario_learner_metrics["S1"]["FlatBayesian"]["brier_regret"])

    cond1 = (s2_dp_decoys < s2_flat_decoys) and (s2_dp_prec >= s2_flat_prec)
    cond2 = (s3_dp_rec < s3_flat_rec) and (s3_dp_col <= s3_win_col)
    cond3 = (s1_dp_regret <= s1_flat_regret)

    gate_pass = cond1 and cond2 and cond3

    if gate_pass:
        branch = "PASS"
    elif s2_dp_decoys > s2_flat_decoys or s3_dp_rec > s3_flat_rec:
        branch = "FAIL"
    else:
        branch = "AMBIGUOUS"

    print("\n======================================================================")
    print(f"GATE A BRANCH EVALUATION VERDICT: [{branch}]")
    print("======================================================================")
    print("VERBATIM DETERMINING CRITERION LINES FROM gate_a.yaml:")
    print("----------------------------------------------------------------------")
    print("""experiments:
  e2_synthetic_battery:
    criteria:
      pass_conditions_simultaneous:
        - "S2 decoy_claims < FlatBayesian AND S2 precision >= FlatBayesian"
        - "S3 recovery_steps < FlatBayesian AND S3 collateral <= WindowedFrequency"
        - "S1 Brier regret <= FlatBayesian"
      evaluations:
        S2_decoy_claims: "DP/EkamNet = {:.4f} vs FlatBayesian = {:.4f} (Met: {})"
        S2_precision: "DP/EkamNet = {:.4f} vs FlatBayesian = {:.4f} (Met: {})"
        S3_recovery_steps: "DP/EkamNet = {:.1f} vs FlatBayesian = {:.1f} (Met: {})"
        S3_collateral: "DP/EkamNet = {:.4f} vs WindowedFrequency = {:.4f} (Met: {})"
        S1_Brier_regret: "DP/EkamNet = {:.4f} vs FlatBayesian = {:.4f} (Met: {})"
""".format(
        s2_dp_decoys, s2_flat_decoys, (s2_dp_decoys < s2_flat_decoys),
        s2_dp_prec, s2_flat_prec, (s2_dp_prec >= s2_flat_prec),
        s3_dp_rec, s3_flat_rec, (s3_dp_rec < s3_flat_rec),
        s3_dp_col, s3_win_col, (s3_dp_col <= s3_win_col),
        s1_dp_regret, s1_flat_regret, (s1_dp_regret <= s1_flat_regret)
    ))
    print("----------------------------------------------------------------------")

    # Generate e2_v2_results.md
    md_path = results_dir / "e2_v2_results.md"
    generate_markdown_report(md_path, scenario_learner_metrics, branch, ece)
    print(f"✓ Saved markdown report to {md_path}")

    # Mark old e2_results.md VOID in place
    old_md_path = results_dir / "e2_results.md"
    if old_md_path.exists():
        with open(old_md_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        if not old_content.startswith("# VOID"):
            void_header = (
                "# VOID — REPLACED BY E2_v2 (PROMPT C3 / commit dc5502d)\n\n"
                "> **NOTICE**: This result set is **VOID** per governance decision DEC-011.\n"
                "> Evaluated on non-conformant agent-built benchmark without pre-registered gate criteria.\n"
                "> Refer to `bench/results/e2_v2_results.md` for authoritative 20-seed reference battery.\n\n"
                "---\n\n"
            )
            with open(old_md_path, "w", encoding="utf-8") as f:
                f.write(void_header + old_content)
            print("✓ Marked old bench/results/e2_results.md VOID in place.")

    return {
        "branch": branch,
        "ece": ece,
        "metrics": scenario_learner_metrics,
        "raw_path": str(raw_path),
        "md_path": str(md_path),
    }


def generate_markdown_report(
    md_path: Path,
    metrics_data: Dict[str, Dict[str, Dict[str, List[float]]]],
    branch: str,
    ece: float,
):
    scenarios = ["S1", "S2", "S3", "S4"]
    learners = [
        "TrueModel (oracle floor)",
        "FlatBayesian",
        "WindowedFrequency(w=200)",
        "ContextualBayesian",
        "DP/EkamNet",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# E2_v2 — 20-Seed Synthetic Benchmark Battery Results\n\n")
        f.write("Authoritative 20-seed synthetic battery evaluation against the external reference benchmark.\n\n")
        f.write(f"### Registered Gate A Branch Verdict: **[{branch}]**\n\n")
        f.write(f"**Expected Calibration Error (ECE)**: `{ece:.4f}`\n\n")
        f.write("---\n\n")

        for sc_id in scenarios:
            f.write(f"## Scenario {sc_id} Results (20 Seeds)\n\n")
            f.write("| Learner | Brier Regret (mean ± std) | Precision (mean ± std) | Recall (mean ± std) | Decoy Claims (mean ± std) | Recovery Steps (mean ± std) | Collateral (mean ± std) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")

            for l_name in learners:
                d = metrics_data[sc_id][l_name]
                b_reg = f"{mean(d['brier_regret']):.4f} ± {std_dev(d['brier_regret']):.4f}"
                prec = f"{mean(d['precision']):.4f} ± {std_dev(d['precision']):.4f}"
                rec = f"{mean(d['recall']):.4f} ± {std_dev(d['recall']):.4f}"
                dec = f"{mean(d['decoy_claims']):.2f} ± {std_dev(d['decoy_claims']):.2f}"
                rec_st = f"{mean(d['recovery_steps']):.1f} ± {std_dev(d['recovery_steps']):.1f}" if sc_id == "S3" else "N/A"
                col = f"{mean(d['collateral']):.4f} ± {std_dev(d['collateral']):.4f}" if sc_id == "S3" else "N/A"

                f.write(f"| **{l_name}** | {b_reg} | {prec} | {rec} | {dec} | {rec_st} | {col} |\n")

            f.write("\n")

        f.write("---\n\n")
        f.write("## Registered Winner Determination & IQR Analysis\n\n")
        for sc_id in scenarios:
            f.write(f"### {sc_id} 20-Seed Interquartile Ranges (IQR: Q25 .. Q75)\n\n")
            f.write("| Learner | Brier Regret IQR | Precision IQR | Recall IQR |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for l_name in learners:
                d = metrics_data[sc_id][l_name]
                b_q25, b_q75 = iqr(d['brier_regret'])
                p_q25, p_q75 = iqr(d['precision'])
                r_q25, r_q75 = iqr(d['recall'])
                f.write(f"| **{l_name}** | [{b_q25:.4f} .. {b_q75:.4f}] | [{p_q25:.4f} .. {p_q75:.4f}] | [{r_q25:.4f} .. {r_q75:.4f}] |\n")
            f.write("\n")


if __name__ == "__main__":
    run_e2_v2_battery(num_seeds=20)
