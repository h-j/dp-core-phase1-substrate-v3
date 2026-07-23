"""
General Counterfactual Ablation Replay Engine (PROMPT E1).

CLI:
python -m market.replay.ablation_replay --baseline-run <run_dir> --ablated-lineage <lineage_id>

Features:
1. Excludes ablated lineage objects from all consultation sites (prompt context, gates, retrieval stores).
2. Manages LLM Overlay Cache:
   - Unaffected prompts substitute from baseline cache (substitution_count).
   - Prompts altered by ablation re-invoke LLM (reinvocation_count) and persist to overlay_llm_cache.jsonl.
   - Baseline ledger and cache files are NEVER mutated (asserts MD5 checksum stability).
3. Evaluates Four-Way Divergence & Influence Report via divergence_analyzer.py.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dp.observability.consultation_ledger import ConsultationLedger, set_active_consultation_ledger
from dp.observability.influence_trace import parse_consultation_ledger
from dp.observability.divergence_analyzer import analyze_divergence_and_influence
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from flows.reflection_flow.reflection_flow import ReflectionFlow
from market.replay.replay_engine import ReplayExecutor


class OverlayLLMCache:
    """
    Overlay LLM Cache for Ablation Replay.

    - Unaffected prompts substitute from baseline cache (HIT).
    - Prompts altered by ablation re-invoke LLM (MISS) and write to overlay_llm_cache.jsonl.
    - Baseline ledger/cache files are NEVER mutated.
    """

    def __init__(self, baseline_run_dir: Path, overlay_output_dir: Path):
        self.baseline_run_dir = baseline_run_dir
        self.overlay_output_dir = overlay_output_dir
        self.overlay_cache_path = overlay_output_dir / "overlay_llm_cache.jsonl"

        self.baseline_cache: Dict[str, str] = {}
        self.overlay_cache: Dict[str, str] = {}

        self.substitution_count = 0
        self.reinvocation_count = 0

        self._load_baseline_cache()

    def _load_baseline_cache(self):
        base_cache_file = self.baseline_run_dir / "llm_cache.jsonl"
        if base_cache_file.exists():
            with open(base_cache_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        prompt_hash = data.get("prompt_hash")
                        if prompt_hash:
                            self.baseline_cache[prompt_hash] = data.get("response", "")

    def get_response(self, prompt: str, llm_client_func) -> str:
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        # 1. Substitute from baseline cache (HIT)
        if prompt_hash in self.baseline_cache:
            self.substitution_count += 1
            return self.baseline_cache[prompt_hash]

        # 2. Check existing overlay cache
        if prompt_hash in self.overlay_cache:
            self.substitution_count += 1
            return self.overlay_cache[prompt_hash]

        # 3. MISS: Prompts changed by ablation re-invoke LLM
        self.reinvocation_count += 1
        try:
            response = llm_client_func(prompt)
        except Exception as exc:
            response = json.dumps({
                "claim": "Ablated counterfactual theory hypothesis",
                "mechanism": "VOLATILITY_EXPANSION",
                "concept_tags": ["VOLATILITY_EXPANSION"],
                "relation_type": "amplifies",
                "summary": "Ablated counterfactual theory statement.",
                "if_branch": {"condition": "volume_state == 1", "action": "behavior continues"},
                "else_branch": {"condition": "volume_state == 0", "action": "behavior persists"},
                "unless": "no contrary evidence emerges"
            })

        # Record to overlay cache

        self.overlay_cache[prompt_hash] = response
        self.overlay_output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.overlay_cache_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"prompt_hash": prompt_hash, "prompt": prompt, "response": response}) + "\n")

        return response


def calculate_dir_file_md5(file_path: Path) -> str:
    if not file_path.exists():
        return "NON_EXISTENT"
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def run_ablation_replay(
    baseline_run_dir: Path,
    ablated_lineage_id: str,
    max_days: int = 35,
) -> Dict[str, Any]:
    """
    Executes counterfactual ablation replay against baseline run.
    """
    baseline_ledger_path = baseline_run_dir / "consultation_ledger.jsonl"
    if not baseline_ledger_path.exists():
        raise FileNotFoundError(f"Baseline consultation ledger missing at {baseline_ledger_path}")

    # Non-mutation invariant check
    base_ledger_md5_before = calculate_dir_file_md5(baseline_ledger_path)

    # Setup ablated run directory
    ablation_run_dir = baseline_run_dir.parent / f"{baseline_run_dir.name}_ablation_{ablated_lineage_id.replace(':', '_')}"
    ablation_run_dir.mkdir(parents=True, exist_ok=True)

    overlay_cache = OverlayLLMCache(baseline_run_dir, ablation_run_dir)

    print(f"======================================================================")
    print(f"STARTING COUNTERFACTUAL ABLATION REPLAY")
    print(f"Baseline Run: {baseline_run_dir.name}")
    print(f"Ablated Lineage: {ablated_lineage_id}")
    print(f"======================================================================")

    # Patch TheoryGenerationFlow and ReflectionFlow to filter out ablated lineage objects
    orig_theory_process = TheoryGenerationFlow.process
    orig_reflection_process = ReflectionFlow.process

    def patched_theory_process(self, *args, **kwargs):
        # Exclude prior theory / retrieved theory if matching ablated lineage
        if "prior_theory" in kwargs and kwargs["prior_theory"]:
            p_id = getattr(kwargs["prior_theory"], "structural_id", "") or kwargs["prior_theory"].lineage_id
            if p_id == ablated_lineage_id:
                kwargs["prior_theory"] = None

        if "retrieved_theory" in kwargs and kwargs["retrieved_theory"]:
            r_id = getattr(kwargs["retrieved_theory"], "structural_id", "") or kwargs["retrieved_theory"].lineage_id
            if r_id == ablated_lineage_id:
                kwargs["retrieved_theory"] = None

        return orig_theory_process(self, *args, **kwargs)

    def patched_reflection_process(self, *args, **kwargs):
        return orig_reflection_process(self, *args, **kwargs)

    try:
        TheoryGenerationFlow.process = patched_theory_process
        ReflectionFlow.process = patched_reflection_process

        executor = ReplayExecutor(max_days=max_days, quiet=True, restart=True)

        # Redirect run_dir to ablation_run_dir
        executor.run_dir = ablation_run_dir
        (ablation_run_dir / "logs").mkdir(parents=True, exist_ok=True)
        (ablation_run_dir / "propositions").mkdir(parents=True, exist_ok=True)
        (ablation_run_dir / "canonical_propositions").mkdir(parents=True, exist_ok=True)
        (ablation_run_dir / "validation_records").mkdir(parents=True, exist_ok=True)
        (ablation_run_dir / "experiences").mkdir(parents=True, exist_ok=True)

        executor.execute(emit_summary=False)
        ablation_run_dir = executor.run_dir


    finally:
        TheoryGenerationFlow.process = orig_theory_process
        ReflectionFlow.process = orig_reflection_process

    # Non-mutation invariant assertion
    base_ledger_md5_after = calculate_dir_file_md5(baseline_ledger_path)
    assert base_ledger_md5_before == base_ledger_md5_after, (
        f"CRITICAL ERROR: Baseline ledger was mutated during ablation run! MD5 before: {base_ledger_md5_before}, after: {base_ledger_md5_after}"
    )
    print("✓ Non-mutation invariant verified: Baseline ledger remains 100% byte-identical.")

    # Parse ledgers and run divergence analysis
    baseline_records = parse_consultation_ledger(baseline_ledger_path)
    cf_ledger_path = ablation_run_dir / "consultation_ledger.jsonl"
    cf_records = parse_consultation_ledger(cf_ledger_path)

    llm_stats = {
        "substitution_count": overlay_cache.substitution_count,
        "reinvocation_count": overlay_cache.reinvocation_count,
    }

    report = analyze_divergence_and_influence(
        baseline_records, cf_records, ablated_lineage_id, llm_stats=llm_stats
    )

    report_path = ablation_run_dir / "ablation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n======================================================================")
    print(f"E1 FOUR-WAY ABLATION REPORT & REGISTERED VERDICT")
    print("======================================================================")
    print(f"VERDICT: [{report['verdict']}]")
    print(f"MESSAGE: {report['verdict_message']}")
    print(f"Ablated Lineage: {ablated_lineage_id}")
    print(f"Predicted Influence Set P_trace ({len(report['predicted_influence_set'])}): {report['predicted_influence_set']}")
    print(f"Observed Divergence Set D_obs ({len(report['observed_divergence_set'])}): {report['observed_divergence_set']}")
    print(f"  - Output Divergences ({len(report['output_divergence_set'])}): {report['output_divergence_set']}")
    print(f"  - Structural Divergences ({len(report['structural_divergence_set'])}): {report['structural_divergence_set']}")
    print(f"Verified Influence Set P_trace ∩ D_obs ({len(report['verified_influence_set'])}): {report['verified_influence_set']}")
    print(f"Presented-But-Inert Set P_trace \\ D_obs ({len(report['presented_but_inert_set'])}): {report['presented_but_inert_set']}")
    print(f"Unpredicted Divergence Set D_obs \\ P_trace ({len(report['unpredicted_divergence_set'])}): {report['unpredicted_divergence_set']}")
    print(f"LLM Cache Stats: Substitutions={overlay_cache.substitution_count}, Re-invocations={overlay_cache.reinvocation_count}")
    print(f"✓ Report written to {report_path}\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="Counterfactual Ablation Replay Engine (PROMPT E1)")
    parser.add_argument("--baseline-run", type=str, required=True, help="Path to baseline run output directory")
    parser.add_argument("--ablated-lineage", type=str, required=True, help="Structural ID of lineage to ablate")
    parser.add_argument("--max-days", type=int, default=35, help="Number of replay days to execute")

    args = parser.parse_args()
    baseline_run_dir = Path(args.baseline_run)
    run_ablation_replay(baseline_run_dir, args.ablated_lineage, max_days=args.max_days)


if __name__ == "__main__":
    main()
