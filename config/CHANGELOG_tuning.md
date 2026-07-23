# Cognition Tuning CHANGELOG

All parameter changes to `cognition_tuning.yaml` must be logged here
with date, parameter name, old value, new value, and scientific rationale.

## v2.9 — 2026-07-23

Pre-Registered Minimum Meaningful Effect (MME) Thresholds for Milestones 5, 6, and 7 verification gates (PROMPT R3 / SD-006 retirement).

| Milestone | Metric | MME Threshold | Min Sample | Rationale |
|---|---|---|---|---|
| M5 Selection | `causal_selection_rate_lift_vs_matched_random` | >= +0.10 (+10pp) | n >= 50 | Selection engine must outperform MatchedRandom by 10pp |
| M6 Beliefs | `median_steps_to_weakened` / `collateral` | <= 20 days / 0 | n >= 5 | Weaken dead rules within 20 days without collateral retirement |
| M7 Pruning | `family_a_stable_lift` / `family_b_degradation` | >= +0.10 / >= -0.10 | n >= 50 | Improve by 10pp under stability and degrade by <= 10pp under shift |

## v2.8 — 2026-07-23


Scored Confidence Engine replacing keyword-based confidence evolution engine (PROMPT R1).

| Parameter | Source File | Old Value | New Value | Scientific Rationale |
|---|---|---|---|---|
| `k_falsify` | scored_confidence_engine.py | N/A | 3.0 | Weight penalty on Beta posterior for CONTRADICTED predicate validation outcomes |
| `lambda` | scored_confidence_engine.py | N/A | 0.01 | Daily staleness decay factor for Beta posterior parameters alpha and beta when no evidence received |

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
