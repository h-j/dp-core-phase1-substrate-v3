# Experiment S1: Synthetic Belief Learning Harness Report

- **Total Worlds**: 10
- **Seeds per World**: 30
- **Total Simulation Runs**: 1500
- **LLM Execution Mode**: Mock Mode

## Overall Agent Performance

| Agent Condition | Mean Precision (P@K) | Mean Realized Lift (OOS) |
| --- | --- | --- |
| Agent A (Raw Experience) | 0.1573 | 0.0175 |
| Agent B (Heuristic Lift) | 0.2513 | 0.0294 |
| Agent C (Evidence Representation) | 0.2167 | 0.0252 |
| Agent D (Matched Random) | 0.0533 | -0.0009 |
| Agent E (Counterfactual Inverted) | 0.1087 | -0.0252 |

## Statistical ANOVA Results

### Metric: Precision
- **F-Statistic**: 122.2569
- **p-value**: 1e-16
- **Degrees of Freedom**: Between=4, Within=1495

#### Group Means:
  - **Agent A (Raw Experience)**: 0.1573
  - **Agent B (Heuristic Lift)**: 0.2513
  - **Agent C (Evidence Representation)**: 0.2167
  - **Agent D (Matched Random)**: 0.0533
  - **Agent E (Counterfactual Inverted)**: 0.1087

### Metric: Mean_lift
- **F-Statistic**: 140.5975
- **p-value**: 1e-16
- **Degrees of Freedom**: Between=4, Within=1495

#### Group Means:
  - **Agent A (Raw Experience)**: 0.0175
  - **Agent B (Heuristic Lift)**: 0.0294
  - **Agent C (Evidence Representation)**: 0.0252
  - **Agent D (Matched Random)**: -0.0009
  - **Agent E (Counterfactual Inverted)**: -0.0252

