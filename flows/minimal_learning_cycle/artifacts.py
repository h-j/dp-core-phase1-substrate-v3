import csv
import json
import os
from typing import Any, Dict, List


class MLCArtifacts:
    @staticmethod
    def write_artifacts(
        directory: str,
        config: Dict[str, Any],
        world_registry: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]],
        propositions: List[Dict[str, Any]],
        erc_log: List[Dict[str, Any]],
        evidence_ledger: List[Dict[str, Any]],
        intrinsic_measurements: List[Dict[str, Any]],
        frozen_candidates: List[Dict[str, Any]],
        prospective_measurements: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]],
        belief_memory: List[Dict[str, Any]],
        baseline_results: Dict[str, Any],
        validity_gates: Dict[str, Any],
        metrics: Dict[str, Any],
        scientific_result: Any = None,
    ):
        os.makedirs(directory, exist_ok=True)

        def write_json(filename: str, data: Any):
            with open(os.path.join(directory, filename), "w") as f:
                json.dump(data, f, indent=2)

        def write_jsonl(filename: str, data: List[Any]):
            with open(os.path.join(directory, filename), "w") as f:
                for item in data:
                    f.write(json.dumps(item) + "\n")

        # Write all JSON/JSONL artifacts
        write_json("mlc_v0_1_config.json", config)
        write_json("mlc_v0_1_world_registry.json", world_registry)
        write_json("mlc_v0_1_ground_truth.json", ground_truth)
        write_json("mlc_v0_1_propositions.json", propositions)
        write_jsonl("mlc_v0_1_erc_log.jsonl", erc_log)
        write_jsonl("mlc_v0_1_evidence_ledger.jsonl", evidence_ledger)
        write_json("mlc_v0_1_intrinsic_measurements.json", intrinsic_measurements)
        write_json("mlc_v0_1_frozen_candidates.json", frozen_candidates)
        write_json("mlc_v0_1_prospective_measurements.json", prospective_measurements)
        write_json("mlc_v0_1_decisions.json", decisions)
        write_json("mlc_v0_1_belief_memory.json", belief_memory)
        write_json("mlc_v0_1_baseline_results.json", baseline_results)
        write_json("mlc_v0_1_validity_gates.json", validity_gates)
        write_json("mlc_v0_1_metrics.json", metrics)

        # Write scientific result artifacts if provided
        if scientific_result is not None:
            res_dict = (
                scientific_result.model_dump()
                if hasattr(scientific_result, "model_dump")
                else (
                    scientific_result.dict()
                    if hasattr(scientific_result, "dict")
                    else scientific_result
                )
            )
            write_json("mlc_v0_1_scientific_result.json", res_dict)

            hyp_results = {
                "H1": res_dict.get("h1_result"),
                "H2": res_dict.get("h2_result"),
                "H3": res_dict.get("h3_result"),
                "H4": res_dict.get("h4_result"),
                "H5": res_dict.get("h5_result"),
            }
            write_json("mlc_v0_1_hypothesis_results.json", hyp_results)

            protocol_md = """# MLC v0.1 Scientific Verdict Protocol

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
"""
            with open(
                os.path.join(directory, "mlc_v0_1_scientific_verdict_protocol.md"),
                "w",
            ) as f:
                f.write(protocol_md)

            issues = res_dict.get("unresolved_scientific_issues", [])
            if issues:
                issues_list = "\n".join(f"- {issue}" for issue in issues)
                issue_report_md = f"""# MLC v0.1 Scientific Verdict Issue Report

The following scientific ambiguities prevent complete deterministic evaluation:

{issues_list}

Please resolve these parameters to enable full significance-backed verdicts.
"""
                with open(
                    os.path.join(
                        directory, "mlc_v0_1_scientific_verdict_issue_report.md"
                    ),
                    "w",
                ) as f:
                    f.write(issue_report_md)

        # Write mlc_v0_1_results.csv
        # Combine metrics or run-level results
        csv_path = os.path.join(directory, "mlc_v0_1_results.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "world_id",
                    "family",
                    "seed",
                    "mlc_decision",
                    "oracle_decision",
                    "b2_decision",
                ]
            )
            for d in decisions:
                w_id = d["world_id"]
                # Find matching registry/oracle/b2 info
                reg = next((w for w in world_registry if w["world_id"] == w_id), {})
                gt = next((g for g in ground_truth if g["world_id"] == w_id), {})
                b2_dec = baseline_results["b2_decisions"].get(w_id, "NONE")
                writer.writerow(
                    [
                        w_id,
                        reg.get("family"),
                        reg.get("seed"),
                        d["decision"],
                        gt.get("expected_decision"),
                        b2_dec,
                    ]
                )

        # Write mlc_v0_1_summary_report.md
        with open(os.path.join(directory, "mlc_v0_1_summary_report.md"), "w") as f:
            f.write(
                f"""# MLC v0.1 Summary Report

## Validity Gate Status
"""
            )
            for gate, res in validity_gates.items():
                f.write(f"- **{gate}**: {res['status']} ({res['evidence']})\n")

            f.write(
                f"""
## Performance Metrics
- **Overall Decision Accuracy**: {metrics.get('overall_decision_accuracy', 0.0):.2%}
- **B2 Retrospective Decision Accuracy**: {metrics.get('b2_decision_accuracy', 0.0):.2%}
- **Catastrophic False Admission Rate**: {metrics.get('catastrophic_false_admission_rate', 0.0):.2%}
- **False Rejection Rate**: {metrics.get('false_rejection_rate', 0.0):.2%}
- **DEFER Precision**: {metrics.get('defer_precision', 0.0):.2%}
- **DEFER Recall**: {metrics.get('defer_recall', 0.0):.2%}
- **Compilation Rejection Count**: {metrics.get('compilation_rejection_count', 0)}
"""
            )

        # Get git hash
        import subprocess

        try:
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            git_hash = "unavailable"

        critical_files = [
            "mlc_v0_1_decisions.json",
            "mlc_v0_1_metrics.json",
            "mlc_v0_1_belief_memory.json",
            "mlc_v0_1_summary_report.md",
            "mlc_v0_1_results.csv",
        ]

        all_files = [
            "mlc_v0_1_config.json",
            "mlc_v0_1_world_registry.json",
            "mlc_v0_1_ground_truth.json",
            "mlc_v0_1_propositions.json",
            "mlc_v0_1_erc_log.jsonl",
            "mlc_v0_1_evidence_ledger.jsonl",
            "mlc_v0_1_intrinsic_measurements.json",
            "mlc_v0_1_frozen_candidates.json",
            "mlc_v0_1_prospective_measurements.json",
            "mlc_v0_1_decisions.json",
            "mlc_v0_1_belief_memory.json",
            "mlc_v0_1_baseline_results.json",
            "mlc_v0_1_validity_gates.json",
            "mlc_v0_1_metrics.json",
            "mlc_v0_1_results.csv",
            "mlc_v0_1_summary_report.md",
        ]

        if scientific_result is not None:
            critical_files.extend(
                [
                    "mlc_v0_1_scientific_result.json",
                    "mlc_v0_1_hypothesis_results.json",
                ]
            )
            all_files.extend(
                [
                    "mlc_v0_1_scientific_result.json",
                    "mlc_v0_1_hypothesis_results.json",
                    "mlc_v0_1_scientific_verdict_protocol.md",
                ]
            )
            if os.path.exists(
                os.path.join(directory, "mlc_v0_1_scientific_verdict_issue_report.md")
            ):
                all_files.append("mlc_v0_1_scientific_verdict_issue_report.md")

        import hashlib

        scientific_hashes = {}
        for fname in all_files:
            fpath = os.path.join(directory, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as bf:
                    file_hash = hashlib.sha256(bf.read()).hexdigest()
                if fname in critical_files:
                    scientific_hashes[fname] = file_hash

        import datetime

        manifest = {
            "run_id": os.path.basename(directory),
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "frozen_configuration": config,
            "configuration_hash": hashlib.sha256(
                json.dumps(config, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "worlds_configuration": world_registry,
            "artifact_inventory": all_files + ["run_manifest.json"],
            "scientific_artifact_hashes": scientific_hashes,
            "git_commit": git_hash,
        }

        write_json("run_manifest.json", manifest)
