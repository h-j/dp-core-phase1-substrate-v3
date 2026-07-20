# Cognition Tuning CHANGELOG

All parameter changes to `cognition_tuning.yaml` must be logged here
with date, parameter name, old value, new value, and scientific rationale.

## v1.0 — 2026-07-20

**Phase 5 of 9-phase remediation (2026-07-20)**

Initial extraction of all tunable weights from inline code literals.
No parameter values were changed — this is a pure relocation.

| Parameter | Source File | Value |
|---|---|---|
| `outcome_high_threshold` | confidence_evolution_engine.py | 0.7 |
| `outcome_mid_threshold` | confidence_evolution_engine.py | 0.4 |
| `empirical_delta_high_support` | confidence_evolution_engine.py | 0.08 |
| `max_score_weight` | contradiction_detector.py CONFIG | 0.7 |
| `threshold_synthesis` | contradiction_detector.py CONFIG | 0.38 |
| *(and remaining parameters)* | both files | see YAML |
