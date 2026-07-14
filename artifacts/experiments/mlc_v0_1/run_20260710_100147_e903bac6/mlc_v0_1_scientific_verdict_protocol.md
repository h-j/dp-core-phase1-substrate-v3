# MLC v0.1 Scientific Verdict Protocol

This protocol formally defines the evaluation framework for the Minimal Learning Cycle v0.1 (MLC v0.1) experiment.

## Hypotheses Mappings & Metrics

### H1: Lifecycle Fidelity
- **Question**: Did MLC v0.1 execute the intended epistemic lifecycle without violating architectural validity gates?
- **Sensing**: validity Gates 1–10.
- **PASS**: All validity gates report PASS.
- **FAIL**: Any gate reports FAIL. Short-circuits all downstream evaluation.

### H2: Above-Random Decision Value
- **Question**: Does MLC v0.1 provide decision value above the matched random baseline?
- **Comparison**: MLC vs B3 Matched Random decision accuracy (evaluated epistemic propositions only).
- **Outcome States**: PASS, FAIL, INCONCLUSIVE.

### H3: Prospective Accuracy Value
- **Question**: Does prospective validation improve decision accuracy over the matched retrospective-only B2 ablation?
- **Comparison**: MLC vs B2 Retrospective Effect Only accuracy.
- **Outcome States**: IMPROVED, NO_DIFFERENCE, DEGRADED, INCONCLUSIVE.

### H4: Safety Value
- **Question**: Does prospective validation reduce catastrophic false admission relative to B2?
- **Decomposition**: 
  - FALSE_ADMIT_REJECT (Admitted when expected is REJECT)
  - FALSE_ADMIT_EVIDENCE_LIMITED (Admitted when expected is DEFER_EVIDENCE_LIMITED)
  - FALSE_ADMIT_EFFECT_AMBIGUOUS (Admitted when expected is DEFER_EFFECT_AMBIGUITY)
- **Outcome States**: IMPROVED, NO_DIFFERENCE, DEGRADED, INCONCLUSIVE.

### H5: Defer Calibration
- **Question**: Does MLC correctly identify propositions that should remain deferred?
- **Targets**: DEFER Precision >= 0.80, DEFER Recall >= 0.70.
- **Outcome States**: PASS, FAIL, INCONCLUSIVE.

## Scientific Parameter Declarations
- **ADMIT_THRESHOLD**: 0.15 (Experimental design parameter)
- **REJECT_THRESHOLD**: -0.05 (Experimental design parameter)
- **Statistical Significance Alpha / Lift thresholds**: Unresolved (exploratory phase).
