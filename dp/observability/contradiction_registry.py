"""Persistent contradiction registry for replay.

Tracks contradiction objects across steps and computes longitudinal metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import json
import hashlib


@dataclass
class ContradictionRecord:
    id: str
    theory_id: str
    description: str
    created_at_step: int
    resolved_at_step: Optional[int] = None
    status: str = "active"
    age: int = 0
    severity: float = 0.0


class ContradictionRegistry:
    """Registry that persists contradiction objects and computes real metrics."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, ContradictionRecord] = {}
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text())
                for cid, rec in raw.items():
                    self.records[cid] = ContradictionRecord(**rec)
            except Exception:
                self.records = {}

    def _persist(self):
        with open(self.storage_path, "w") as f:
            json.dump(
                {cid: asdict(rec) for cid, rec in self.records.items()},
                f,
                indent=2,
                default=str,
            )

    def _normalize_description(self, description: str) -> str:
        return " ".join(description.strip().lower().split())

    def _record_id(self, theory_id: str, description: str, step: int) -> str:
        text = f"{theory_id}|{description}|{step}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def register_contradictions(
        self,
        theory_id: str,
        descriptions: List[str],
        severity: float,
        step: int,
    ) -> Dict[str, int]:
        """Register current contradictions and carry forward or resolve prior ones."""
        normalized_descriptions = [self._normalize_description(d) for d in descriptions]
        active_records = {
            rec.id: rec for rec in self.records.values() if rec.status != "resolved"
        }
        matched_ids = set()
        for rec in active_records.values():
            rec.age = max(rec.age, step - rec.created_at_step)

        for description in normalized_descriptions:
            existing = next(
                (
                    rec
                    for rec in active_records.values()
                    if rec.description == description
                ),
                None,
            )
            if existing:
                existing.age = max(existing.age, step - existing.created_at_step)
                existing.severity = max(existing.severity, severity)
                existing.status = "carried_forward" if existing.age > 0 else "active"
                matched_ids.add(existing.id)
            else:
                contradiction_id = self._record_id(theory_id, description, step)
                self.records[contradiction_id] = ContradictionRecord(
                    id=contradiction_id,
                    theory_id=theory_id,
                    description=description,
                    created_at_step=step,
                    status="active",
                    age=0,
                    severity=severity,
                )
                matched_ids.add(contradiction_id)

        resolved_count = 0
        for rec in active_records.values():
            if rec.id not in matched_ids:
                rec.status = "resolved"
                rec.resolved_at_step = step
                rec.age = max(rec.age, step - rec.created_at_step)
                resolved_count += 1

        self._persist()
        return {
            "new_contradictions": len(
                [
                    cid
                    for cid in matched_ids
                    if self.records[cid].created_at_step == step
                ]
            ),
            "resolved_contradictions": resolved_count,
            "active_contradictions": self.active_count(),
            "carried_forward_contradictions": self.carried_forward_count(),
        }

    def resolve_contradiction(self, contradiction_id: str, step: int) -> bool:
        rec = self.records.get(contradiction_id)
        if not rec or rec.status == "resolved":
            return False
        rec.status = "resolved"
        rec.resolved_at_step = step
        rec.age = max(rec.age, step - rec.created_at_step)
        self._persist()
        return True

    def resolve_for_theory(self, theory_id: str, step: int) -> int:
        resolved = 0
        for rec in self.records.values():
            if rec.theory_id == theory_id and rec.status != "resolved":
                rec.status = "resolved"
                rec.resolved_at_step = step
                rec.age = max(rec.age, step - rec.created_at_step)
                resolved += 1
        if resolved:
            self._persist()
        return resolved

    def carry_forward_contradiction(self, contradiction_id: str, step: int) -> bool:
        rec = self.records.get(contradiction_id)
        if not rec or rec.status == "resolved":
            return False
        rec.age += 1
        rec.status = "carried_forward" if rec.age > 0 else "active"
        self._persist()
        return True

    def active_count(self) -> int:
        return len([r for r in self.records.values() if r.status != "resolved"])

    def carried_forward_count(self) -> int:
        return len([r for r in self.records.values() if r.status == "carried_forward"])

    def resolved_count(self) -> int:
        return len([r for r in self.records.values() if r.status == "resolved"])

    def contradiction_half_life(self) -> float:
        durations = self.resolved_durations()
        return float(sum(durations) / len(durations)) if durations else 0.0

    def median_contradiction_half_life(self) -> float:
        durations = sorted(self.resolved_durations())
        if not durations:
            return 0.0
        midpoint = len(durations) // 2
        if len(durations) % 2:
            return float(durations[midpoint])
        return float((durations[midpoint - 1] + durations[midpoint]) / 2)

    def resolved_durations(self) -> List[int]:
        return [
            max(0, (r.resolved_at_step or r.created_at_step) - r.created_at_step)
            for r in self.records.values()
            if r.status == "resolved" and r.resolved_at_step is not None
        ]

    def oldest_unresolved_age(self) -> int:
        unresolved = [r.age for r in self.records.values() if r.status != "resolved"]
        return max(unresolved) if unresolved else 0

    def contradiction_resolution_rate(self) -> float:
        total = len(self.records)
        return float(self.resolved_count()) / total if total else 0.0

    def average_severity(self) -> float:
        if not self.records:
            return 0.0
        return float(sum(r.severity for r in self.records.values()) / len(self.records))

    def highest_severity(self) -> float:
        severities = [r.severity for r in self.records.values()]
        return max(severities) if severities else 0.0

    def all_active_contradictions(self) -> List[ContradictionRecord]:
        return [r for r in self.records.values() if r.status != "resolved"]

    def all_records(self) -> List[ContradictionRecord]:
        return list(self.records.values())

    def to_dict(self) -> Dict[str, Dict]:
        return {cid: asdict(rec) for cid, rec in self.records.items()}
