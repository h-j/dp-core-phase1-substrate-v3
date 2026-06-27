import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from market.replay.replay_analysis import extract_usefulness_score


def generate_visualizations(analysis, logs, tp_history, output_dir):
    """v1.6 Visualization Layer - Generates calibration and capital charts."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("fast")  # Matplotlib only, no seaborn

    # 1. Actual vs Predicted Curve
    def plot_actual_vs_predicted():
        plt.figure(figsize=(12, 6))
        hist = analysis.get("prediction_history", [])
        dates = [r["date"] for r in hist]

        mapping = {"higher": 1, "lower": -1, "range_bound": 0, "uncertain": 0}
        pred_vals = [mapping.get(r["prediction"].get("direction"), 0) for r in hist]
        act_vals = [
            mapping.get(r["prior_prediction_result"].get("actual_direction"), 0)
            for r in hist
        ]

        plt.step(
            dates,
            act_vals,
            label="Actual Market Direction",
            color="gray",
            alpha=0.5,
            where="post",
        )
        plt.step(
            dates,
            pred_vals,
            label="Predicted Direction",
            color="blue",
            linewidth=2,
            where="post",
        )

        # Marks
        for i, r in enumerate(hist):
            if r.get("prior_prediction_result"):
                score = r["prior_prediction_result"].get("direction_score", 0)
                if score == 1.0:
                    plt.scatter(dates[i], pred_vals[i], color="green", s=30)
                elif score == 0.0:
                    plt.scatter(dates[i], pred_vals[i], color="red", s=30)

        plt.title("Actual vs Predicted Direction Curve")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "actual_vs_predicted_curve.png")
        plt.close()

    # 2. Policy Capital Comparison
    def plot_policy_capital_comparison():
        plt.figure(figsize=(12, 6))
        dates = [l["date"] for l in logs]

        # Backward compatibility check for v1.7 structure
        if logs and "policies" in logs[0]:
            policies = ["baseline", "high_conviction", "breakout"]
            colors = {
                "baseline": "forestgreen",
                "high_conviction": "blue",
                "breakout": "purple",
            }
            for p in policies:
                if p in logs[0]["policies"]:
                    caps = [
                        l["policies"].get(p, {}).get("capital_after", 10000.0)
                        for l in logs
                    ]
                    plt.plot(
                        dates,
                        caps,
                        label=p.replace("_", " ").title(),
                        color=colors.get(p),
                        linewidth=2,
                    )
        elif logs and "capital_after" in logs[0]:
            caps = [l.get("capital_after", 10000.0) for l in logs]
            plt.plot(
                dates, caps, color="forestgreen", label="Legacy Capital", linewidth=2
            )

        plt.axhline(
            y=10000, color="red", linestyle="--", alpha=0.5, label="Starting Capital"
        )
        plt.title("Policy Capital Comparison (Start: ₹10,000)")
        plt.ylabel("Capital (₹)")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "policy_capital_comparison.png")
        plt.close()

    # 3. Confidence Calibration
    def plot_calibration():
        plt.figure(figsize=(8, 8))
        p = analysis.get("prediction_analysis", {})
        buckets = p.get("accuracy_by_confidence_bucket", {})

        x_vals = []
        y_vals = []
        for b in sorted(buckets.keys()):
            x_vals.append(buckets[b]["avg_confidence"])
            y_vals.append(buckets[b]["actual_accuracy"])

        plt.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect Calibration")
        plt.scatter(x_vals, y_vals, color="blue", s=100)
        plt.plot(x_vals, y_vals, "b-", alpha=0.3)

        plt.xlabel("Average Confidence")
        plt.ylabel("Actual Accuracy")
        plt.title("Confidence Calibration Curve")
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "confidence_calibration.png")
        plt.close()

    # 4. Transition Pressure Timeline
    def plot_transition_pressure():
        plt.figure(figsize=(12, 4))
        dates = [d["date"] for d in tp_history]
        scores = [d["pressure_score"] for d in tp_history]

        plt.plot(dates, scores, color="purple", label="Pressure Score")
        risk_dates = [d["date"] for d in tp_history if d.get("breakout_risk")]
        risk_scores = [
            d["pressure_score"] for d in tp_history if d.get("breakout_risk")
        ]
        plt.scatter(risk_dates, risk_scores, color="red", label="Breakout Risk")

        plt.title("Transition Pressure Timeline")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "transition_pressure_timeline.png")
        plt.close()

    # 5. Policy Trade Frequency
    def plot_policy_trade_frequency():
        plt.figure(figsize=(10, 6))
        cap_analysis = analysis.get("capital_simulation_analysis", {})

        policies = ["baseline", "high_conviction", "breakout"]
        labels = [p.replace("_", " ").title() for p in policies if p in cap_analysis]

        if not labels:
            return

        trades = [
            cap_analysis.get(p, {}).get("trade_count", 0)
            for p in policies
            if p in cap_analysis
        ]
        skipped = [
            cap_analysis.get(p, {}).get("skipped_days", 0)
            for p in policies
            if p in cap_analysis
        ]

        x = list(range(len(labels)))
        width = 0.35

        plt.bar(
            [i - width / 2 for i in x], trades, width, label="Trades", color="skyblue"
        )
        plt.bar(
            [i + width / 2 for i in x],
            skipped,
            width,
            label="Skipped Days",
            color="lightcoral",
        )

        plt.ylabel("Count")
        plt.title("Trade Frequency by Policy")
        plt.xticks(x, labels)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "policy_trade_frequency.png")
        plt.close()

    # 6. Dashboard
    def generate_dashboard():
        plt.figure(figsize=(16, 12))

        # Panel 1: Prediction Accuracy (Actual vs Predicted)
        plt.subplot(2, 2, 1)
        hist = analysis.get("prediction_history", [])
        dates = [r["date"] for r in hist]
        mapping = {"higher": 1, "lower": -1, "range_bound": 0, "uncertain": 0}
        pred_vals = [mapping.get(r["prediction"].get("direction"), 0) for r in hist]
        act_vals = [
            mapping.get(r["prior_prediction_result"].get("actual_direction"), 0)
            for r in hist
        ]
        plt.step(dates, act_vals, label="Actual", color="gray", alpha=0.5, where="post")
        plt.step(
            dates, pred_vals, label="Pred", color="blue", linewidth=1.5, where="post"
        )
        plt.title("Prediction Accuracy")
        plt.xticks(rotation=45, fontsize=8)
        plt.legend(prop={"size": 8})

        # Panel 2: Policy Comparison (Capital Curves)
        plt.subplot(2, 2, 2)
        dates = [l["date"] for l in logs]
        if logs and "policies" in logs[0]:
            for p in ["baseline", "high_conviction", "breakout"]:
                if p in logs[0]["policies"]:
                    caps = [
                        l["policies"].get(p, {}).get("capital_after", 10000.0)
                        for l in logs
                    ]
                    plt.plot(dates, caps, label=p.replace("_", " ").title())
        elif logs and "capital_after" in logs[0]:
            caps = [l.get("capital_after", 10000.0) for l in logs]
            plt.plot(dates, caps, label="Legacy")
        plt.title("Policy Capital Comparison")
        plt.xticks(rotation=45, fontsize=8)
        plt.legend(prop={"size": 8})

        # Panel 3: Confidence Calibration
        plt.subplot(2, 2, 3)
        p_an = analysis.get("prediction_analysis", {})
        buckets = p_an.get("accuracy_by_confidence_bucket", {})
        x_v = [buckets[b]["avg_confidence"] for b in sorted(buckets.keys())]
        y_v = [buckets[b]["actual_accuracy"] for b in sorted(buckets.keys())]
        plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
        plt.scatter(x_v, y_v, color="blue", s=40)
        plt.title("Confidence Calibration")
        plt.xlabel("Confidence")
        plt.ylabel("Accuracy")

        # Panel 4: Transition Pressure
        plt.subplot(2, 2, 4)
        tp_dates = [d["date"] for d in tp_history]
        tp_scores = [d["pressure_score"] for d in tp_history]
        plt.plot(tp_dates, tp_scores, color="purple", label="Pressure")
        plt.title("Transition Pressure Timeline")
        plt.xticks(rotation=45, fontsize=8)

        plt.suptitle("Combined Replay Cognition Dashboard", fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(output_dir / "combined_dashboard.png")
        plt.close()

    plot_actual_vs_predicted()
    plot_policy_capital_comparison()
    plot_calibration()
    plot_transition_pressure()
    plot_policy_trade_frequency()
    generate_dashboard()


def _prediction_dataframe(analysis: dict) -> pd.DataFrame:
    rows = analysis.get("prediction_history", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if "prior_prediction_result" in df.columns:
        df["actual_direction"] = df["prior_prediction_result"].apply(
            lambda x: x.get("actual_direction") if isinstance(x, dict) else None
        )
    else:
        df["actual_direction"] = None

    df["prediction_direction"] = df["prediction"].apply(
        lambda x: x.get("direction") if isinstance(x, dict) else None
    )
    df["direction_score"] = df["prior_prediction_result"].apply(
        lambda x: x.get("direction_score") if isinstance(x, dict) else None
    )
    if "theory_usefulness" in df.columns:
        df["theory_usefulness"] = df["theory_usefulness"].apply(
            extract_usefulness_score
        )
    df["confidence"] = df["prediction"].apply(
        lambda x: x.get("confidence", 0.0) if isinstance(x, dict) else 0.0
    )
    return df


def _market_summary(analysis: dict) -> dict:
    pa = analysis.get("prediction_analysis", {})
    return {
        "market_name": analysis.get("market_name", "UNKNOWN"),
        "accuracy": pa.get("accuracy", 0.0),
        "partial_accuracy": pa.get("partial_accuracy", 0.0),
        "mean_confidence": pa.get("mean_confidence", 0.0),
        "uncertain_rate": pa.get("uncertain_rate", 0.0),
    }


def _top_missed_signal(df: pd.DataFrame) -> str:
    if df.empty:
        return "none"
    missed = df[df["direction_score"] != 1.0]
    if missed.empty:
        return "none"
    signal_counts = (
        missed["participation_confirmation"].fillna("unknown").value_counts()
    )
    return signal_counts.index[0] if not signal_counts.empty else "unknown"


def _generate_failure_json(
    base_output_dir: Path,
    primary_metrics: dict,
    secondary_metrics: dict,
    primary_df: pd.DataFrame,
    secondary_df: pd.DataFrame,
):
    summary = {
        "primary_market": primary_metrics["market_name"],
        "secondary_market": secondary_metrics["market_name"],
        "primary_accuracy": primary_metrics["accuracy"],
        "secondary_accuracy": secondary_metrics["accuracy"],
        "primary_divergence_hit_rate": 0.0,
        "secondary_divergence_hit_rate": 0.0,
        "primary_top_missed_signal": _top_missed_signal(primary_df),
        "secondary_top_missed_signal": _top_missed_signal(secondary_df),
        "top_high_confidence_misses": [],
    }

    def divergence_rate(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        divergence = df[df["participation_confirmation"] == "divergence"]
        if divergence.empty:
            return 0.0
        hits = divergence[divergence["direction_score"] == 1.0]
        return float(len(hits) / len(divergence))

    summary["primary_divergence_hit_rate"] = divergence_rate(primary_df)
    summary["secondary_divergence_hit_rate"] = divergence_rate(secondary_df)

    combined_misses = pd.concat([primary_df, secondary_df], ignore_index=True)
    combined_misses = combined_misses[combined_misses["direction_score"] != 1.0]
    combined_misses = combined_misses.sort_values("confidence", ascending=False).head(
        10
    )
    for _, row in combined_misses.iterrows():
        summary["top_high_confidence_misses"].append(
            {
                "date": row.get("date"),
                "market": row.get("market_name"),
                "confidence": float(row.get("confidence", 0.0)),
                "prediction_direction": row.get("prediction_direction"),
                "actual_direction": row.get("actual_direction"),
                "participation_confirmation": row.get("participation_confirmation"),
                "direction_score": row.get("direction_score"),
            }
        )

    file_path = base_output_dir / "cross_asset_failure_summary.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        import json

        json.dump(summary, f, indent=2)

    return summary


def generate_cross_asset_visualizations(
    base_output_dir, primary_analysis: dict, secondary_analysis: dict
):
    os.makedirs(base_output_dir, exist_ok=True)

    primary_df = _prediction_dataframe(primary_analysis)
    secondary_df = _prediction_dataframe(secondary_analysis)
    primary_metrics = _market_summary(primary_analysis)
    secondary_metrics = _market_summary(secondary_analysis)

    labels = ["accuracy", "partial_accuracy", "mean_confidence", "uncertain_rate"]
    x = range(len(labels))
    primary_vals = [primary_metrics[label] for label in labels]
    secondary_vals = [secondary_metrics[label] for label in labels]

    plt.figure(figsize=(10, 6))
    width = 0.35
    plt.bar(
        [i - width / 2 for i in x],
        primary_vals,
        width,
        label=primary_metrics["market_name"],
        color="steelblue",
    )
    plt.bar(
        [i + width / 2 for i in x],
        secondary_vals,
        width,
        label=secondary_metrics["market_name"],
        color="darkorange",
    )
    plt.ylim(0, 1)
    plt.xticks(x, [l.replace("_", " ").title() for l in labels])
    plt.ylabel("Normalized Value")
    plt.title("Normalized NIFTY vs RELIANCE Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(base_output_dir / "nifty_vs_reliance_comparison.png")
    plt.close()

    def _plot_market_confusion(ax, df: pd.DataFrame, market_name: str):
        directions = ["higher", "lower", "range_bound", "uncertain"]
        matrix = pd.DataFrame(0, index=directions, columns=directions)
        scored = df[df["direction_score"].notnull() & df["actual_direction"].notnull()]
        for _, row in scored.iterrows():
            actual = row["actual_direction"] or "uncertain"
            predicted = row["prediction_direction"] or "uncertain"
            if actual not in matrix.index:
                actual = "uncertain"
            if predicted not in matrix.columns:
                predicted = "uncertain"
            matrix.at[actual, predicted] += 1

        im = ax.imshow(matrix, cmap="Reds", interpolation="nearest")
        ax.set_xticks(range(len(directions)))
        ax.set_yticks(range(len(directions)))
        ax.set_xticklabels([d.title() for d in directions], rotation=45)
        ax.set_yticklabels([d.title() for d in directions])
        ax.set_title(f"{market_name} Actual vs Predicted")
        for i in range(len(directions)):
            for j in range(len(directions)):
                ax.text(
                    j, i, int(matrix.iat[i, j]), ha="center", va="center", color="black"
                )
        return im

    plt.figure(figsize=(14, 6))
    ax1 = plt.subplot(1, 2, 1)
    ax2 = plt.subplot(1, 2, 2)
    if not primary_df.empty:
        _plot_market_confusion(ax1, primary_df, primary_metrics["market_name"])
    if not secondary_df.empty:
        _plot_market_confusion(ax2, secondary_df, secondary_metrics["market_name"])
    plt.suptitle("Prediction Failure Heatmap")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(base_output_dir / "prediction_failure_heatmap.png")
    plt.close()

    if primary_df.empty and secondary_df.empty:
        _generate_failure_json(
            base_output_dir,
            primary_metrics,
            secondary_metrics,
            primary_df,
            secondary_df,
        )
        return

    combined = pd.concat([primary_df, secondary_df], ignore_index=True)
    divergence = combined[combined["participation_confirmation"] == "divergence"].copy()
    if not divergence.empty:
        divergence["hit"] = divergence["direction_score"] == 1.0
        divergence["date"] = pd.to_datetime(divergence["date"], errors="coerce")
        divergence = divergence.sort_values("date")
        mark_map = {True: "green", False: "red"}
        market_positions = {
            primary_metrics["market_name"]: 1,
            secondary_metrics["market_name"]: 0,
        }
        plt.figure(figsize=(12, 5))
        for market_name, group in divergence.groupby("market_name"):
            y = market_positions.get(market_name, 0)
            plt.scatter(
                group["date"],
                [y] * len(group),
                c=[mark_map[hit] for hit in group["hit"]],
                s=80,
                label=f"{market_name} divergence",
                edgecolor="black",
                alpha=0.7,
            )
        plt.yticks(
            [0, 1], [secondary_metrics["market_name"], primary_metrics["market_name"]]
        )
        plt.xlabel("Date")
        plt.title("Cross-Asset Divergence Timeline")
        plt.legend()
        plt.tight_layout()
        plt.savefig(base_output_dir / "cross_asset_divergence_timeline.png")
        plt.close()

    _generate_failure_json(
        base_output_dir, primary_metrics, secondary_metrics, primary_df, secondary_df
    )
