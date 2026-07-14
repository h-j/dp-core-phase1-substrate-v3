# MLC v0.1 Summary Report

## Validity Gate Status
- **GATE_1**: PASS (Found 3 validation authorizations for 3 validated candidates out of 4 total decisions.)
- **GATE_2**: PASS (Family B worlds verify true comparative effect <= REJECT_THRESHOLD.)
- **GATE_3**: PASS (Thresholds are frozen and ordered: REJECT=-0.05 < ADMIT=0.15.)
- **GATE_4**: PASS (Family representation counts: {'A': 1, 'C2': 1, 'B': 1, 'C1': 1}.)
- **GATE_5**: PASS (Contradiction definitions found in all 3 frozen candidates.)
- **GATE_6A**: PASS (Compilation and Attribution use identical imports from measurement.py.)
- **GATE_6B**: PASS (Window 2 and Window 3 share the compute_metrics function in measurement.py.)
- **GATE_6C**: PASS (B2 utilizes same frozen candidate objects as MLC.)
- **GATE_7**: PASS (ERC Authorizations: Compilation=4, Evidence=4 for 3 candidates.)
- **GATE_8**: PASS (SHA-256 hashes of proposition definitions match content_hash records.)
- **GATE_9**: PASS (Verified 4 epistemic decisions are in [ADMIT, REJECT, DEFER] and 0 pre-epistemic rejections are distinct.)
- **GATE_10**: PASS (All decisions map 1-to-1 with persisted belief memory records.)

## Performance Metrics
- **Overall Decision Accuracy**: 100.00%
- **B2 Retrospective Decision Accuracy**: 100.00%
- **Catastrophic False Admission Rate**: 0.00%
- **False Rejection Rate**: 0.00%
- **DEFER Precision**: 100.00%
- **DEFER Recall**: 100.00%
- **Compilation Rejection Count**: 0
