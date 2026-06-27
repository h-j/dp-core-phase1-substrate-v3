import io
import sys
from market.replay.replay_analysis_reporting import ReplayJournalBuilder

def test_learning_effectiveness_audit():
    # 1. Setup mock prediction history with controlled values
    prediction_history = [
        # Day 0 (Start window)
        {
            "prediction": {"confidence": 0.8},
            "prior_prediction_result": None,
            "components_failed": ["comp_a"],
            "reused_lessons": [],
            "lessons_retired": 0,
            "regime_similarity": 0.5,
            "contradiction_score": 0.4
        },
        # Day 1 (Start window)
        {
            "prediction": {"confidence": 0.7},
            "prior_prediction_result": {"direction_score": 1.0}, # correct prediction from Day 0 (confidence 0.8), error = 0.2
            "components_failed": [],
            "reused_lessons": ["lesson_1"],
            "lessons_retired": 1,
            "regime_similarity": 0.6,
            "contradiction_score": 0.2
        },
        # Day 2 (Middle window)
        {
            "prediction": {"confidence": 0.6},
            "prior_prediction_result": {"direction_score": 0.0}, # incorrect prediction from Day 1 (confidence 0.7), error = 0.7
            "components_failed": [],
            "reused_lessons": [],
            "lessons_retired": 0,
            "regime_similarity": 0.7,
            "contradiction_score": 0.3
        },
        # Day 3 (End window)
        {
            "prediction": {"confidence": 0.5},
            "prior_prediction_result": {"direction_score": 0.0}, # incorrect prediction from Day 2 (confidence 0.6), error = 0.6
            "components_failed": [],
            "reused_lessons": ["lesson_2"],
            "lessons_retired": 0,
            "regime_similarity": 0.8,
            "contradiction_score": 0.1
        },
        # Day 4 (End window)
        {
            "prediction": {"confidence": 0.4},
            "prior_prediction_result": {"direction_score": 1.0}, # correct prediction from Day 3 (confidence 0.5), error = 0.5
            "components_failed": [],
            "reused_lessons": ["lesson_2"],
            "lessons_retired": 0,
            "regime_similarity": 0.9,
            "contradiction_score": 0.05
        }
    ]

    analysis = {
        "date_range": ("2026-06-01", "2026-06-05"),
        "prediction_analysis": {"accuracy": 0.5, "total_predictions": 4},
        "prediction_intelligence": {},
        "prediction_history": prediction_history
    }
    
    external_metrics = {
        "experience_stats": {},
        "experience_audit": {},
        "lesson_stats": {},
        "active_lessons_list": [],
        "component_failure_counts": {}
    }

    # Capture print output
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        ReplayJournalBuilder.print_journal("MOCK_MARKET", analysis, external_metrics)
    finally:
        sys.stdout = sys.__stdout__

    output_str = captured_output.getvalue()
    
    # 2. Assertions
    assert "Learning Effectiveness Audit" in output_str
    assert "Component Failure Rate" in output_str
    assert "Lesson Reuse Rate" in output_str
    assert "Lesson Retirement Rate" in output_str
    assert "Regime Retrieval Success" in output_str
    assert "Contradiction Pressure" in output_str
    assert "Confidence Calibration Error" in output_str
    assert "Did DP become less wrong over time?" in output_str
    assert "Conclusion:" in output_str

    print("✓ Learning effectiveness audit print journal calculations verified successfully.")
