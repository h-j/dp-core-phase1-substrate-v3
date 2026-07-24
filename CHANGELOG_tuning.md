# Cognition Parameter & Gate Registration Tuning Changelog

All hyperparameter changes, threshold updates, and gate registrations must be logged in this file prior to execution.

---

## [1.0.0] - 2026-07-24

### Registered
- **Gate A Pre-Registration (`experiments/preregistration/gate_a.yaml`)**:
  - Registered formal E1 counterfactual influence gate criteria:
    - Preconditions: Ablation target Beta confidence > 0.65 with `evidence_count >= 5`; `substitution_count` and `reinvocation_count` must be reported.
    - PASS: `unpredicted_divergence` empty AND `verified_influence` non-empty.
    - INSTRUMENTATION_FAIL: `unpredicted_divergence` non-empty.
    - NULL: `observed_divergence` empty.
  - Registered formal E2 synthetic benchmark battery criteria:
    - Simultaneously requires: S2 `decoy_claims` rate < `FlatBayesian`'s AND S2 `discovery_precision` >= `FlatBayesian`'s; AND S3 `recovery_steps` < `FlatBayesian`'s AND S3 `collateral` <= `WindowedFrequency`'s; AND S1 Brier regret <= `FlatBayesian`'s.
    - Three-branch interpretation table registered verbatim (`PASS` / `FAIL` / `AMBIGUOUS`).
