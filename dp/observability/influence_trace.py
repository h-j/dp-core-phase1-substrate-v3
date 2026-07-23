"""
Influence Trace Analysis Tool for Read-Side Provenance.

Command:
python -m dp.observability.influence_trace <ledger_path> <object_structural_id>

Calculates direct consultations and transitive multi-hop influence sets
from a consultation_ledger.jsonl artifact.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Set


def parse_consultation_ledger(ledger_path: Path) -> List[Dict]:
    """Parses append-only JSONL consultation ledger."""
    records = []
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger file not found: {ledger_path}")
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def compute_influence_set(records: List[Dict], target_object_id: str) -> Dict:
    """
    Computes direct consultations and transitive multi-hop influence set.

    Transitivity rule:
    1. Decision D directly consults target_object_id.
    2. Decision D's decision_id becomes a tainted structural object ID.
    3. Any subsequent decision D' that consults D (or a descendant structural ID matching lineage prefix) is tainted.
    """
    direct_consultations: Set[str] = set()
    consultation_records: List[Dict] = []
    decision_records: Dict[str, Dict] = {}

    for r in records:
        if r.get("kind") == "consultation":
            consultation_records.append(r)
            if r.get("object_structural_id") == target_object_id:
                direct_consultations.add(r["decision_id"])
        elif r.get("kind") == "decision":
            decision_records[r["decision_id"]] = r

    tainted_objects: Set[str] = {target_object_id}
    tainted_objects.update(direct_consultations)

    influenced_decisions: Set[str] = set(direct_consultations)

    # Transitive closure fixed-point iteration
    changed = True
    while changed:
        changed = False
        for c in consultation_records:
            dec_id = c.get("decision_id")
            obj_id = c.get("object_structural_id")

            # Check exact match or lineage matching (e.g. "0:theory:0" matches child "1:theory:0" lineage)
            is_tainted = obj_id in tainted_objects
            if not is_tainted and ":" in obj_id:
                # Lineage matching: if founding theory "0:theory:0" is tainted, child theory lineage matches
                founding_prefix = obj_id.split(":")[-1]
                for t in tainted_objects:
                    if t.endswith(f":{founding_prefix}"):
                        is_tainted = True
                        break

            if is_tainted and dec_id not in influenced_decisions:
                influenced_decisions.add(dec_id)
                tainted_objects.add(dec_id)
                changed = True

    return {
        "target_object_id": target_object_id,
        "direct_consultations": sorted(list(direct_consultations)),
        "influenced_decisions": sorted(list(influenced_decisions)),
        "total_influenced": len(influenced_decisions),
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m dp.observability.influence_trace <ledger_path> <target_object_id>")
        sys.exit(1)

    ledger_path = Path(sys.argv[1])
    target_object_id = sys.argv[2]

    records = parse_consultation_ledger(ledger_path)
    res = compute_influence_set(records, target_object_id)

    print(f"=== INFLUENCE TRACE FOR OBJECT: {res['target_object_id']} ===")
    print(f"Direct Consultations ({len(res['direct_consultations'])}):")
    for d in res["direct_consultations"]:
        print(f"  - {d}")
    print(f"\nFull Transitive Influenced Decisions ({res['total_influenced']}):")
    for d in res["influenced_decisions"]:
        print(f"  - {d}")


if __name__ == "__main__":
    main()
