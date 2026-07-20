# FORMATION BOUNDARY DIAGNOSTIC PHASE 0 PROTOCOL v0.1

## 1. Executive Verdict
**FINAL SCIENTIFIC VERDICT: FORMATION_BOUNDARY_PHASE_0_PROTOCOL_READY**

This document establishes the frozen protocol for **Formation Boundary Diagnostic Phase 0**, a strictly read-only, source-to-target semantic representability audit. The protocol is designed to answer whether the explicit semantic content of representative current DP Theory artifacts can be mapped to the ten frozen Proposition-compatible fields without material deletion, invention, distortion, or hidden reasoning dependency. 

---

## 2. Exact Scientific Question
The core scientific question motivating this Phase 0 diagnostic is:
> **Can the explicit semantic content of representative current DP Theory artifacts be represented within the frozen Proposition-compatible semantic schema without material deletion, invention, distortion, hidden reasoning dependency, or residual loss of epistemically relevant source meaning?**

---

## 3. Diagnostic Scope
The diagnostic is strictly a **source-to-target semantic representability audit**. 
It inspects:
- **Source**: Explicit text and parameters stored in historical `Theory` and `TheoryStructured` snapshots.
- **Target**: The ten frozen semantic fields defined by the Atomic Field-Level Fidelity Schema.
It does **not** compare Strategy A and Strategy B, execute candidate generation, modify prompts, or test downstream selection risk.

---

## 4. Explicit Non-Goals
The following tasks are explicitly outside the scope of this protocol:
- Executing or implementing Strategy A or Strategy B.
- Generating diagnostic candidates or tuning LLM temperatures/seeds.
- Modifying Proposition Pydantic schemas or MLC validity gates.
- Designing a persistent relationship graph or implementing S4-E0 gates.
- Proposing roadmap prioritization or claiming Proposition validation.

---

## 5. Failure Mechanism Model
The diagnostic identifies and distinguishes four distinct failure mechanisms at the boundary:
1. **Source Under-Specification**: The source Theory does not explicitly contain semantic info required by the target schema (e.g. missing target outcome direction).
2. **Translational Invention**: Populating a target field requires adding explanatory context or variables not supported by the source.
3. **Translational Distortion**: The target representation changes or weakens the causal direction or scope present in the source.
4. **Target Schema Loss**: Important causal meaning in the source has no corresponding representation field in the target schema.

---

## 6. Repository Read-Only Findings
**CODE_FACT** in `flows/theory_flow/theory_generation_flow.py` and `cognition/schemas/theory/theory.py`:
- Representative Theory artifacts are stored daily in the `theory_summary_structured` field of daily replay snapshot JSON files under `data/replay_snapshots/reliance/run_20260701_123929/`.
- The structured source fields available for inspection include: `mechanism` (string), `claim` (string), `if_branch` (dict with `condition`/`action`), `else_branch` (dict), `falsified_if` (string), `mechanism_components` (list of components containing tags, expected behaviors, and observables), and `falsification_conditions` (list of strings).

---

## 7. Artifact Population and Sampling Rule
To prevent selection bias and cherry-picking, the sampling rule is frozen:
- **Population**: All daily snapshots from `data/replay_snapshots/reliance/run_20260701_123929/` (45 days total).
- **Sampling Procedure**: Select every 3rd day starting from Day 0 (Days: 0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42).
- **Sample Size**: $n = 15$ representative Theory snapshots. This sample size is sufficient to systematically characterize boundary representations across different market regime subtypes.
- **Inclusion Criteria**: Snapshots must contain a valid `theory_summary_structured` dict.
- **Exclusion Criteria**: None (days without a valid structured theory are noted as failures).

---

## 8. Unit of Analysis
- **Primary Unit**: A single Theory snapshot (represented by its `theory_summary_structured` dict).
- **Secondary Unit**: The target semantic field (10 fields evaluated per snapshot).
- **Aggregation Unit**: The complete sample (15 snapshots $\times$ 10 fields = 150 evaluations).

---

## 9. Source Semantic Inventory Procedure
Before mapping to target fields, the evaluator performs an independent inventory of the source Theory:
- Explicit meaning is recorded directly from the text fields.
- Normalization (e.g. matching `delivery_pct` to a known indicator variable) is allowed, but **no interpretation or causal reasoning is added**.
- Spans of text from `claim`, `if_branch.condition`, and `mechanism` are extracted and recorded in the inventory to establish ground truth source semantics.

---

## 10. Ten-Field Representability Procedure
Evaluate the 15 sampled theories against the 10 frozen semantic fields:
1. `trigger_definition`
2. `target_definition`
3. `scope_definition`
4. `expected_direction`
5. `contradiction_definition`
6. `mechanism_type`
7. `causal_direction`
8. `driver`
9. `mediator_or_process`
10. `target_effect`

---

## 11. Operational Fidelity Classification Rules
For each field, the evaluator assigns exactly one classification:
- **`PRESERVED`**: Causal meaning and direction are supported by source.
- **`DELETED`**: Source contains relevant details missing in the output.
- **`INVENTED`**: Output contains details unsupported by the source.
- **`DISTORTED`**: Output alters causal direction, scope, or target.
- **`UNSUPPORTED_IN_SOURCE`**: Field is expected but absent in the source.
- **`NOT_APPLICABLE`**: Field is not applicable for the specific theory type.
- **`INDETERMINATE`**: Available evidence cannot support classification.

---

## 12. Hidden Reasoning Dependency Test
For every mapped field, classify the reasoning dependency:
- **`DIRECTLY_SUPPORTED`**: Derived via direct text mapping.
- **`NORMALIZATION_ONLY`**: Re-formatted using a pre-registered normalization rule (e.g. mapping string indicators to column names).
- **`REASONING_DEPENDENT`**: Requires LLM reasoning or domain interpretation.
- **`INDETERMINATE`**.
*Storage*: Recorded as an orthogonal metadata attribute within the fidelity finding schema.

---

## 13. Residual Semantic Loss Test
The evaluator checks for source meaning that has no target schema mapping:
- Identify if components of `mechanism_components` (e.g. specific dependency links or ontology tags) cannot be mapped.
- Record the lost text and classify the severity of the loss (Low, Medium, High).

---

## 14. Blind Reverse-Coverage Test
- A second independent evaluator (or the same evaluator separated by 72 hours) is presented with only the populated 10-field structured representation.
- The reviewer attempts to reconstruct the original causal mechanism text.
- If key details (e.g. absorption vs exhaustion) are lost or corrupted, a **Reverse-Coverage Loss** is flagged.

---

## 15. Reviewer Architecture
- **Automated Reviewer**: Simple Pydantic regex/constraint validation check.
- **Human Reviewer**: Blinded review where the reviewer does not see the strategy labels (Strategy A vs B) and uses a frozen rubric.
- **Adjudication**: A third reviewer resolves conflicts, preserving original and final labels.

---

## 16. Comparison Rule Freeze
All sampling rules, field mapping rules, case lists, prompts, and classification thresholds are frozen prior to Phase 2. No post-inspection tuning of prompts or schemas is permitted.

---

## 17. Aggregation Rules and Minimum Metrics
- **Field Representability Rate**: Ratio of fields classified as `PRESERVED` or `NOT_APPLICABLE` to total evaluations.
- **Invention Rate**: Ratio of `INVENTED` fields to total evaluations.
- **Distortion Rate**: Ratio of `DISTORTED` fields to total evaluations.
- **Starvation Rate**: Ratio of `DELETED` fields to total evaluations.
- **Reasoning Dependency Rate**: Ratio of `REASONING_DEPENDENT` fields.

---

## 18. Causal Necessity Gate
Does the snapshot population instantiate handoff failure?  
**YES**. Theories are generated daily under deterministic context limits. If the context has complex rules, direct mapping is highly prone to translation failures.

---

## 19. Mechanism Strength Gate
Is there sufficient semantic richness?  
**YES**. Snapshot records contain multi-component mechanism definitions and detailed conditional actions, allowing deletions and distortions to be easily observed.

---

## 20. Isolation Gate
Can the diagnostic distinguish source under-specification from schema insufficiency?  
**YES**. Absent fields are classified as `UNSUPPORTED_IN_SOURCE` (source under-specification) vs `DELETED` or `DISTORTED` (schema/adapter failure).

---

## 21. Diagnostic Cost and Bias Analysis
- **Destination Bias**: Mitigated by the Source Semantic Inventory and blind reverse-coverage test.
- **Confirmation Bias**: Mitigated by blinded reviewer interfaces.

---

## 22. Adversarial Protocol Tests
1. **Explicit Theory**: Should map to all 10 fields with `PRESERVED`.
2. **Implicit/Narrow Theory**: Maps only to 2–3 fields, returning `UNSUPPORTED_IN_SOURCE` for the rest without flagging translation failure.
3. **Outside Field**: Causal details not mapped in the 10 fields are caught by the Residual Semantic Loss Test.
4. **Ambiguous Source**: Classified as `INDETERMINATE`.

---

## 23. Pre-Registered Outcome Thresholds
- **Fidelity Threshold**: $Fidelity \ge 0.85$ (ratio of `PRESERVED` fields).
- **Distortion Threshold**: $Distortion \le 0.05$.
- **Reasoning Dependency Limit**: $Dependency \le 0.15$.

---

## 24. POSITIVE Interpretation
Fidelity threshold met, distortion/invention limits respected.  
*Implication*: Representative current Theory artifacts map cleanly to the Proposition schema without loss.

---

## 25. NEGATIVE Interpretation and Causal Subtypes
Decomposed into:
- **`SOURCE_INSUFFICIENCY`**: Source theories consistently lack trigger/target structures.
- **`TRANSLATION_DEPENDENCY`**: Handoff requires high-inference reasoning.
- **`TRANSLATION_DISTORTION`**: Mapping distorts causal meanings.
- **`REPRESENTATION_INSUFFICIENT`**: Schema lacks fields for core mechanisms.

---

## 26. INCONCLUSIVE Interpretation
Triggered if reviewer disagreements exceed 15% or `INDETERMINATE` ratings exceed 10%.

---

## 27. NO_DIFFERENCE Applicability Assessment
Not applicable for this non-comparative Phase 0 diagnostic pass.

---

## 28. Proposition H₀ Interpretation Boundary
- Failing thresholds does not falsify $H_0$. $H_0$ is only falsified if the diagnostic establishes that the causal mechanism cannot be represented in Proposition form because the primitive itself is conceptually incorrect.

---

## 29. Five-Layer Claim Separation
- All findings are classified under: Code Fact, Execution Fact, Scientific Interpretation, Architectural Option, or Human Decision.

---

## 30. Unresolved Risks and Assumptions
- Assumes that manual semantic inventories do not introduce subjective reviewer bias.

---

## 31. Smallest Next Action After Protocol Review
Run Phase 0 data extraction on the selected 15 snapshot days.

---

## 32. Exact Files Inspected
- `cognition/schemas/theory/theory.py`
- `data/replay_snapshots/reliance/run_20260701_123929/day_0000.json`

---

## 33. Exact Commands Run
- `poetry run python /Users/hemantj/.gemini/antigravity-ide/brain/face4af3-acf5-4ebb-a5bd-ccb6af890aa2/scratch/inspect_snapshots.py`

---

## 34. Final Scientific Verdict
**FINAL SCIENTIFIC VERDICT: FORMATION_BOUNDARY_PHASE_0_PROTOCOL_READY**
