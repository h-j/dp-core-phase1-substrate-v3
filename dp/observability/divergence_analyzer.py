r"""
Four-Way Divergence & Influence Analysis Engine (PROMPT E1).


Aligns decisions strictly by structural decision_id ("{day}:{stage}:{ordinal}").
Calculates:
- Output Divergence: Same decision_id, different output_hash.
- Structural Divergence: decision_id present in only one run.
- PREDICTED INFLUENCE (P_trace)
- OBSERVED DIVERGENCE (D_obs = Output + Structural)
- VERIFIED INFLUENCE (P_trace ∩ D_obs)
- PRESENTED-BUT-INERT (P_trace \ D_obs)
- UNPREDICTED DIVERGENCE (D_obs \ P_trace)

Evaluates registered verdict:
- PASS: D_unpredicted is EMPTY AND Verified Influence >= 1.
- INSTRUMENTATION FAIL: D_unpredicted is NON-EMPTY.
- NULL: D_obs is EMPTY.
"""
from typing import Dict, List, Set, Any
from dp.observability.influence_trace import compute_influence_set


def analyze_divergence_and_influence(
    baseline_records: List[Dict[str, Any]],
    counterfactual_records: List[Dict[str, Any]],
    ablated_lineage_id: str,
    llm_stats: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Analyzes baseline vs counterfactual consultation ledgers and produces four-way report & verdict.
    """
    # 1. Taint propagation on BASELINE ledger
    influence_res = compute_influence_set(baseline_records, ablated_lineage_id)
    predicted_influence_set: Set[str] = set(influence_res.get("influenced_decisions", []))
    direct_consultations: Set[str] = set(influence_res.get("direct_consultations", []))

    # 2. Extract decisions by structural decision_id
    decisions_base: Dict[str, str] = {
        r["decision_id"]: r["output_hash"]
        for r in baseline_records
        if r.get("kind") == "decision"
    }

    decisions_cf: Dict[str, str] = {
        r["decision_id"]: r["output_hash"]
        for r in counterfactual_records
        if r.get("kind") == "decision"
    }

    all_decision_ids = set(decisions_base.keys()) | set(decisions_cf.keys())

    output_divergences: Set[str] = set()
    structural_divergences: Set[str] = set()

    for dec_id in sorted(all_decision_ids):
        in_base = dec_id in decisions_base
        in_cf = dec_id in decisions_cf

        if in_base and in_cf:
            if decisions_base[dec_id] != decisions_cf[dec_id]:
                output_divergences.add(dec_id)
        else:
            # Structural divergence: decision created or missing in counterfactual run
            structural_divergences.add(dec_id)

    observed_divergence_set: Set[str] = output_divergences | structural_divergences

    # 3. Four-Way Set Computation
    verified_influence_set = predicted_influence_set & observed_divergence_set
    presented_but_inert_set = predicted_influence_set - observed_divergence_set
    unpredicted_divergence_set = observed_divergence_set - predicted_influence_set

    # 4. Registered Verdict Evaluation
    if len(unpredicted_divergence_set) > 0:
        verdict = "INSTRUMENTATION FAIL"
        verdict_message = f"INSTRUMENTATION FAIL: Found {len(unpredicted_divergence_set)} unpredicted decision divergences ({sorted(unpredicted_divergence_set)}). Uninstrumented consultation read sites exist."
    elif len(observed_divergence_set) == 0:
        verdict = "NULL"
        verdict_message = "NULL: Divergence set D_obs is empty entirely — accumulated knowledge did not causally change reasoning in this bounded run."
    elif len(verified_influence_set) >= 1:
        verdict = "PASS"
        verdict_message = f"PASS: D_unpredicted set is EMPTY AND Verified Influence set is NON-EMPTY ({len(verified_influence_set)} decisions diverged as predicted)."
    else:
        verdict = "NULL"
        verdict_message = "NULL: No predicted decisions diverged."

    return {
        "verdict": verdict,
        "verdict_message": verdict_message,
        "ablated_lineage_id": ablated_lineage_id,
        "direct_consultations": sorted(list(direct_consultations)),
        "predicted_influence_set": sorted(list(predicted_influence_set)),
        "observed_divergence_set": sorted(list(observed_divergence_set)),
        "output_divergence_set": sorted(list(output_divergences)),
        "structural_divergence_set": sorted(list(structural_divergences)),
        "verified_influence_set": sorted(list(verified_influence_set)),
        "presented_but_inert_set": sorted(list(presented_but_inert_set)),
        "unpredicted_divergence_set": sorted(list(unpredicted_divergence_set)),
        "llm_stats": llm_stats or {},
    }
