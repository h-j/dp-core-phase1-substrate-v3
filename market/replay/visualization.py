import matplotlib.pyplot as plt
import os
from pathlib import Path
import pandas as pd

def generate_visualizations(analysis, logs, tp_history, output_dir):
    """v1.6 Visualization Layer - Generates calibration and capital charts."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('fast') # Matplotlib only, no seaborn

    # 1. Actual vs Predicted Curve
    def plot_actual_vs_predicted():
        plt.figure(figsize=(12, 6))
        hist = analysis.get("prediction_history", [])
        dates = [r["date"] for r in hist]
        
        mapping = {"higher": 1, "lower": -1, "range_bound": 0, "uncertain": 0}
        pred_vals = [mapping.get(r["prediction"].get("direction"), 0) for r in hist]
        act_vals = [mapping.get(r["prior_prediction_result"].get("actual_direction"), 0) for r in hist]

        plt.step(dates, act_vals, label="Actual Market Direction", color="gray", alpha=0.5, where='post')
        plt.step(dates, pred_vals, label="Predicted Direction", color="blue", linewidth=2, where='post')
        
        # Marks
        for i, r in enumerate(hist):
            if r.get("prior_prediction_result"):
                score = r["prior_prediction_result"].get("direction_score", 0)
                if score == 1.0: plt.scatter(dates[i], pred_vals[i], color="green", s=30)
                elif score == 0.0: plt.scatter(dates[i], pred_vals[i], color="red", s=30)

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
            colors = {"baseline": "forestgreen", "high_conviction": "blue", "breakout": "purple"}
            for p in policies:
                if p in logs[0]["policies"]:
                    caps = [l["policies"].get(p, {}).get("capital_after", 10000.0) for l in logs]
                    plt.plot(dates, caps, label=p.replace("_", " ").title(), color=colors.get(p), linewidth=2)
        elif logs and "capital_after" in logs[0]:
            caps = [l.get("capital_after", 10000.0) for l in logs]
            plt.plot(dates, caps, color="forestgreen", label="Legacy Capital", linewidth=2)

        plt.axhline(y=10000, color="red", linestyle="--", alpha=0.5, label="Starting Capital")
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
            
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.5, label="Perfect Calibration")
        plt.scatter(x_vals, y_vals, color="blue", s=100)
        plt.plot(x_vals, y_vals, 'b-', alpha=0.3)
        
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
        risk_scores = [d["pressure_score"] for d in tp_history if d.get("breakout_risk")]
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

        trades = [cap_analysis.get(p, {}).get("trade_count", 0) for p in policies if p in cap_analysis]
        skipped = [cap_analysis.get(p, {}).get("skipped_days", 0) for p in policies if p in cap_analysis]

        x = list(range(len(labels)))
        width = 0.35

        plt.bar([i - width/2 for i in x], trades, width, label='Trades', color='skyblue')
        plt.bar([i + width/2 for i in x], skipped, width, label='Skipped Days', color='lightcoral')

        plt.ylabel('Count')
        plt.title('Trade Frequency by Policy')
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
        act_vals = [mapping.get(r["prior_prediction_result"].get("actual_direction"), 0) for r in hist]
        plt.step(dates, act_vals, label="Actual", color="gray", alpha=0.5, where='post')
        plt.step(dates, pred_vals, label="Pred", color="blue", linewidth=1.5, where='post')
        plt.title("Prediction Accuracy")
        plt.xticks(rotation=45, fontsize=8)
        plt.legend(prop={'size': 8})

        # Panel 2: Policy Comparison (Capital Curves)
        plt.subplot(2, 2, 2)
        dates = [l["date"] for l in logs]
        if logs and "policies" in logs[0]:
            for p in ["baseline", "high_conviction", "breakout"]:
                if p in logs[0]["policies"]:
                    caps = [l["policies"].get(p, {}).get("capital_after", 10000.0) for l in logs]
                    plt.plot(dates, caps, label=p.replace("_", " ").title())
        elif logs and "capital_after" in logs[0]:
            caps = [l.get("capital_after", 10000.0) for l in logs]
            plt.plot(dates, caps, label="Legacy")
        plt.title("Policy Capital Comparison")
        plt.xticks(rotation=45, fontsize=8)
        plt.legend(prop={'size': 8})

        # Panel 3: Confidence Calibration
        plt.subplot(2, 2, 3)
        p_an = analysis.get("prediction_analysis", {})
        buckets = p_an.get("accuracy_by_confidence_bucket", {})
        x_v = [buckets[b]["avg_confidence"] for b in sorted(buckets.keys())]
        y_v = [buckets[b]["actual_accuracy"] for b in sorted(buckets.keys())]
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
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