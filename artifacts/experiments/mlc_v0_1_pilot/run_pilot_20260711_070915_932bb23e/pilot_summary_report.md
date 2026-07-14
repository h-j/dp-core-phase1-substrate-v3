# MLC v0.1 Pilot Experiment Summary Report

## Pilot Execution Verdict
**VERDICT: MLC_V0_1_PILOT_INVALID_IMPLEMENTATION**

### Run Metadata
- **Run ID**: `run_pilot_20260711_070915_932bb23e`
- **Timestamp**: `2026-07-11T01:39:15.390876Z`
- **World Count**: 100
- **Configuration Hash**: `8bcece76360f39e8e603e94b9e9b160fdbe7982fdec2a6c13b2ec3cd1622bccc`
- **World Registry Hash**: `a6264ea2fe8f58a4bb63afad933ad72194ebd9bc44211d4de1996f72f08b5d19`

### 1. Validity Gates
| Validity Gate | Status | Evidence |
| --- | --- | --- |
| `PILOT_GATE_1_WORLD_COUNT` | PASS | Registry has 100 worlds. Decided 100 worlds. |
| `PILOT_GATE_2_ZONE_COMPOSITION` | PASS | Zones: Clear=30, Boundary=50, Evidence-Limited=20. |
| `PILOT_GATE_3_BOUNDARY_MAPPING` | PASS | Verified boundary effect to ground truth mapping consistency. |
| `PILOT_GATE_4_MULTIPLE_SEEDS` | PASS | Boundary effect seed counts: {-0.08: 7, -0.04: 7, 0.0: 7, 0.05: 8, 0.12: 7, 0.16: 7, 0.2: 7}. |
| `PILOT_GATE_5_REGISTRY_FREEZE` | PASS | Stored hash: a6264ea2fe8f58a4bb63afad933ad72194ebd9bc44211d4de1996f72f08b5d19, Computed hash: a6264ea2fe8f58a4bb63afad933ad72194ebd9bc44211d4de1996f72f08b5d19. |
| `PILOT_GATE_6_THRESHOLD_FREEZE` | PASS | Admit=0.15, Reject=-0.05. |
| `PILOT_GATE_7_NO_SCIENTIFIC_MUTATION` | PASS | No mutation of scientific thresholds detected. |
| `PILOT_GATE_8_ARTIFACT_COMPLETENESS` | PASS | To be evaluated during runner finalization. |
| `PILOT_GATE_9_PAIRED_COMPARISON_COMPLETENESS` | PASS | MLC=100, B2=100, B3=100 decisions matched. |
| `PILOT_GATE_10_ZONE_METRIC_COMPLETENESS` | PASS | Found metric sections: ['pooled', 'clear_zone', 'boundary_zone', 'evidence_limited_zone']. |
| `PILOT_GATE_11_CATASTROPHIC_DECOMPOSITION` | FAIL | Found H4 sections: []. |
| `PILOT_GATE_12_POWER_REPORT_COMPLETENESS` | FAIL | All required power fields exist for H2, H3, and H4. |

### 2. Statistical Comparisons and Power Analysis
The provisional minimum meaningful paired effect is **5 percentage points (0.05)**. Target power is **80%**.

| Hypothesis | Observed Mean Diff | Observed Variance | Observed Std Dev | 95% Confidence Interval | Estimated Power (n=500) | Required n for 80% Power | Adequately Powered? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H2**: MLC vs B3 | 0.5100 | 0.393838 | 0.6276 | [0.387, 0.633] | 42.93% | 1237 | No |
| **H3**: MLC vs B2 | -0.0100 | 0.232222 | 0.4819 | [-0.1045, 0.0845] | 64.06% | 730 | No |
| **H4**: MLC vs B2 safety | 0.0000 | 0.020202 | 0.1421 | [-0.0279, 0.0279] | 100.00% | 64 | Yes |

### 3. Mandatory Disaggregated Zone Performance
| Zone | Worlds | MLC Accuracy | B2 Retro Accuracy | B3 Random Accuracy | B4 Oracle Accuracy | MLC vs B2 Diff | MLC vs B3 Diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Pooled** | 100 | 0.8600 | 0.8700 | 0.3500 | 1.0000 | -0.0100 | 0.5100 |
| **Clear Zone** | 30 | 1.0000 | 1.0000 | 0.3333 | 1.0000 | 0.0000 | 0.6667 |
| **Boundary Zone** | 50 | 0.7200 | 0.7400 | 0.3400 | 1.0000 | -0.0200 | 0.3800 |
| **Evidence-Limited** | 20 | 1.0000 | 1.0000 | 0.4000 | 1.0000 | 0.0000 | 0.6000 |

### 4. Safety H4 Decomposition
- **Pooled CFA Rate**: MLC: 0.0200 (2 worlds) vs B2: 0.0200 (2 worlds)
- **CFA Reject**: MLC: 0.0000 vs B2: 0.0000
- **CFA Evidence-Limited**: MLC: 0.0000 vs B2: 0.0000
- **CFA Effect Ambiguous**: MLC: 0.0200 vs B2: 0.0200

### 5. H5 Calibration Metrics
- **DEFER Precision**: 0.8431
- **DEFER Recall**: 0.8776
- **EVIDENCE_LIMITED Subtype Accuracy**: 0.0000
- **EFFECT_AMBIGUITY Subtype Accuracy**: 0.7931

#### Confusion Matrix (Actual vs Predicted)
| Ground Truth | Predicted ADMIT | Predicted REJECT | Predicted DEFER |
| --- | --- | --- | --- |
| **ADMIT** | 23 | 0 | 6 |
| **REJECT** | 0 | 20 | 2 |
| **DEFER** | 2 | 4 | 43 |

### 6. Design Verification Decision Support
Based on the pilot observations:
- **H2 (MLC vs Matched Random)**: UNDERPOWERED at n=500 (power: 42.93%). Required n for 80% power: 1237.
- **H3 (MLC vs Retrospective Baseline)**: UNDERPOWERED at n=500 (power: 64.06%). Required n for 80% power: 730.
- **H4 (Safety Comparison)**: Adequately powered at n=500 (power: 100.00%). Required n for 80% power: 64.
