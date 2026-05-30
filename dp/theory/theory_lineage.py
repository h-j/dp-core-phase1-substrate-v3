"""Theory lineage engine.

Treats theories as evolving objects and persists a JSON graph of evolving
records with lineage links, mutation history, and status transitions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Set


@dataclass
class TheoryRecord:
    id: str
    created_at_step: int
    parent_ids: List[str]
    status: str
    confidence: float
    abstraction: str
    confidence_state: Dict[str, float] = field(
        default_factory=lambda: {
            "empirical_confidence": 0.5,
            "regime_confidence": 0.5,
            "reflection_confidence": 0.5,
            "theoretical_coherence": 0.5,
            "contradiction_pressure": 0.0,
        }
    )
    contradictions: List[str] = field(default_factory=list)
    contradiction_count: int = 0
    mutation_reason: Optional[str] = None
    survival_steps: int = 0
    last_seen_step: int = 0
    mutation_count: int = 0
    retired_at_step: Optional[int] = None
    last_retired_step: Optional[int] = None
    revival_count: int = 0
    retirement_ages: List[int] = field(default_factory=list)
    revival_latencies: List[int] = field(default_factory=list)


class TheoryLineageEngine:
    """Lineage engine for evolving theory objects."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.theories: Dict[str, TheoryRecord] = {}
        self.debug = False
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text())
                for tid, rec in raw.items():
                    self.theories[tid] = TheoryRecord(**rec)
            except Exception:
                self.theories = {}

    def _persist(self):
        with open(self.storage_path, "w") as f:
            json.dump(
                {tid: asdict(rec) for tid, rec in self.theories.items()},
                f,
                indent=2,
                default=str,
            )

    def _token_set(self, text: str) -> Set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _similarity(self, a: str, b: str) -> float:
        a_tokens = self._token_set(a)
        b_tokens = self._token_set(b)
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

    def _record_id(self, seed: str, step: int) -> str:
        return hashlib.sha256(f"{seed}|{step}".encode()).hexdigest()[:16]

    def create_theory(
        self,
        tid: str,
        step: int,
        abstraction: str,
        confidence_state: Optional[Dict[str, float]] = None,
        parent_ids: Optional[List[str]] = None,
    ) -> TheoryRecord:
        parent_ids = parent_ids or []
        confidence_state = confidence_state or {
            "empirical_confidence": 0.5,
            "regime_confidence": 0.5,
            "reflection_confidence": 0.5,
            "theoretical_coherence": 0.5,
            "contradiction_pressure": 0.0,
        }
        rec = TheoryRecord(
            id=tid,
            created_at_step=step,
            parent_ids=parent_ids,
            status="active",
            confidence=float(confidence_state.get("empirical_confidence", 0.5)),
            confidence_state=confidence_state,
            abstraction=abstraction,
            contradictions=[],
            contradiction_count=0,
            mutation_reason=None,
            survival_steps=0,
            last_seen_step=step,
            mutation_count=0,
        )
        self.theories[tid] = rec
        self._persist()
        return rec

    def merge_theory(
        self,
        tid: str,
        new_abstraction: str,
        confidence_state: Dict[str, float],
        step: int,
    ) -> TheoryRecord:
        rec = self.theories.get(tid)
        if not rec:
            return self.create_theory(
                tid, step, new_abstraction, confidence_state=confidence_state
            )
        rec.abstraction = new_abstraction
        rec.confidence_state = {
            **rec.confidence_state,
            **confidence_state,
            "empirical_confidence": max(
                rec.confidence_state.get("empirical_confidence", 0.5),
                confidence_state.get("empirical_confidence", 0.5),
            ),
        }
        rec.confidence = float(rec.confidence_state["empirical_confidence"])
        rec.mutation_reason = "merged_duplicate"
        rec.last_seen_step = step
        self._persist()
        return rec

    def continue_theory(
        self,
        tid: str,
        new_abstraction: str,
        step: int,
        confidence_state: Dict[str, float],
    ) -> TheoryRecord:
        rec = self.theories.get(tid)
        if not rec:
            return self.create_theory(
                tid, step, new_abstraction, confidence_state=confidence_state
            )

        rec.abstraction = new_abstraction
        rec.confidence_state = {
            **rec.confidence_state,
            **confidence_state,
            "empirical_confidence": max(
                rec.confidence_state.get("empirical_confidence", 0.5),
                confidence_state.get("empirical_confidence", 0.5),
            ),
        }
        rec.confidence = float(rec.confidence_state["empirical_confidence"])
        rec.last_seen_step = step
        rec.mutation_reason = "continued"
        self._persist()
        return rec

    def mutate_theory(
        self,
        tid: str,
        new_abstraction: str,
        reason: str,
        step: int,
        confidence_state: Dict[str, float],
    ) -> TheoryRecord:
        parent = self.theories.get(tid)
        if not parent:
            return self.create_theory(
                tid, step, new_abstraction, confidence_state=confidence_state
            )

        parent.last_seen_step = step
        parent.mutation_count += 1
        if parent.mutation_count >= 2:
            parent.status = "dormant"

        child_id = self._record_id(tid + new_abstraction, step)
        child = TheoryRecord(
            id=child_id,
            created_at_step=step,
            parent_ids=[parent.id],
            status="active",
            confidence=float(confidence_state.get("empirical_confidence", 0.5)),
            confidence_state=confidence_state,
            abstraction=new_abstraction,
            contradictions=list(parent.contradictions),
            contradiction_count=parent.contradiction_count,
            mutation_reason=reason,
            survival_steps=parent.survival_steps,
            last_seen_step=step,
            mutation_count=0,
        )
        self.theories[child_id] = child
        self._persist()
        return child

    def evolve_theory(
        self,
        abstraction: str,
        confidence_state: Dict[str, float],
        step: int,
    ) -> Dict[str, Any]:
        """Compare a new abstraction against active and contradicted theories and evolve lineage."""
        # Include both active and contradicted theories for carry-forward/mutation pool
        active_theories = [
            rec
            for rec in self.theories.values()
            if rec.status in {"active", "contradicted"}
        ]
        best_match = None
        best_score = 0.0
        for rec in active_theories:
            score = self._similarity(rec.abstraction, abstraction)
            if score > best_score:
                best_score = score
                best_match = rec

        structural_shift = (
            self._has_structural_shift(best_match.abstraction, abstraction)
            if best_match
            else False
        )

        if self.debug:
            print(
                f"[Lineage] step={step} abstraction={abstraction!r} "
                f"best_match_id={getattr(best_match, 'id', None)} "
                f"best_score={best_score:.3f} "
                f"status={getattr(best_match, 'status', None)} "
                f"parents={getattr(best_match, 'parent_ids', None)} "
                f"structural_shift={structural_shift}"
            )

        if (
            best_match
            and best_score >= 0.30
            and not structural_shift
            and best_match.status == "active"
        ):
            rec = self.continue_theory(
                best_match.id,
                new_abstraction=abstraction,
                step=step,
                confidence_state=confidence_state,
            )
            if self.debug:
                print(
                    f"[Lineage] CONTINUE -> existing={best_match.id} "
                    f"confidence={rec.confidence:.3f} "
                    f"survival_steps={rec.survival_steps}"
                )
            self.update_survival(step)
            return {
                "record": rec,
                "created": False,
                "mutated": False,
                "merged": False,
                "continued": True,
                "parent_id": best_match.id,
            }

        if best_match and best_score >= 0.45 and structural_shift:
            rec = self.mutate_theory(
                best_match.id,
                new_abstraction=abstraction,
                reason=f"semantic_similarity_{best_score:.2f}",
                step=step,
                confidence_state=confidence_state,
            )
            if self.debug:
                print(
                    f"[Lineage] MUTATE -> parent={best_match.id} "
                    f"child={rec.id} reason=semantic_similarity_{best_score:.2f} "
                    f"confidence={rec.confidence:.3f} "
                    f"survival_steps={rec.survival_steps}"
                )
            self.update_survival(step)
            return {
                "record": rec,
                "created": False,
                "mutated": True,
                "merged": False,
                "continued": False,
                "parent_id": best_match.id,
            }

        if best_score < 0.30:
            new_id = self._record_id(abstraction, step)
            rec = self.create_theory(
                new_id,
                step,
                abstraction,
                confidence_state=confidence_state,
                parent_ids=[],
            )
            if self.debug:
                print(
                    f"[Lineage] NEW -> id={rec.id} abstraction={abstraction!r} "
                    f"confidence={rec.confidence:.3f}"
                )
            self.update_survival(step)
            return {
                "record": rec,
                "created": True,
                "mutated": False,
                "merged": False,
                "continued": False,
                "parent_id": None,
            }

        if (
            best_match
            and (structural_shift or best_score >= 0.32)
            and not (best_match.parent_ids and best_score < 0.45)
        ):
            rec = self.mutate_theory(
                best_match.id,
                new_abstraction=abstraction,
                reason=f"semantic_similarity_{best_score:.2f}",
                step=step,
                confidence_state=confidence_state,
            )
            if self.debug:
                print(
                    f"[Lineage] MUTATE -> parent={best_match.id} "
                    f"child={rec.id} reason=semantic_similarity_{best_score:.2f} "
                    f"confidence={rec.confidence:.3f} "
                    f"survival_steps={rec.survival_steps}"
                )
            self.update_survival(step)
            return {
                "record": rec,
                "created": False,
                "mutated": True,
                "merged": False,
                "continued": False,
                "parent_id": best_match.id,
            }

        new_id = self._record_id(abstraction, step)
        rec = self.create_theory(
            new_id,
            step,
            abstraction,
            confidence_state=confidence_state,
            parent_ids=[],
        )
        if self.debug:
            print(
                f"[Lineage] CREATE -> id={rec.id} abstraction={abstraction!r} "
                f"confidence={rec.confidence:.3f}"
            )
        self.update_survival(step)
        return {
            "record": rec,
            "created": True,
            "mutated": False,
            "merged": False,
            "parent_id": None,
        }

    def _has_structural_shift(self, prior: str, current: str) -> bool:
        prior_tokens = self._token_set(prior)
        current_tokens = self._token_set(current)
        opposed_terms = [
            (
                {"strengthened", "strongly", "participatory"},
                {"weakened", "deteriorated"},
            ),
            ({"lower", "closed_lower"}, {"higher", "extended_higher", "extended"}),
            ({"range", "range_bound", "bound"}, {"extended", "higher", "lower"}),
            ({"compressed", "stable"}, {"expanded", "high"}),
        ]
        return any(
            (prior_tokens & left and current_tokens & right)
            or (prior_tokens & right and current_tokens & left)
            for left, right in opposed_terms
        )

    def retire_theory(self, tid: str, step: int) -> Optional[TheoryRecord]:
        rec = self.theories.get(tid)
        if not rec:
            return None
        rec.status = "retired"
        rec.last_seen_step = step
        rec.retired_at_step = step
        rec.last_retired_step = step
        rec.retirement_ages.append(step - rec.created_at_step)
        self._persist()
        return rec

    def revive_theory(self, tid: str, step: int) -> Optional[TheoryRecord]:
        rec = self.theories.get(tid)
        if not rec:
            return None
        if rec.last_retired_step is not None:
            rec.revival_latencies.append(step - rec.last_retired_step)
        rec.status = "revived"
        rec.last_seen_step = step
        rec.retired_at_step = None
        rec.revival_count += 1
        self._persist()
        return rec

    def retire_stale_theories(
        self,
        step: int,
        contradiction_severity: float,
        current_record_id: Optional[str] = None,
        inactivity_threshold: int = 6,
        contradiction_threshold: int = 2,
    ) -> List[TheoryRecord]:
        """Retire weak stale theories using only current and prior replay state."""
        retired: List[TheoryRecord] = []
        candidates = [
            rec
            for rec in self.theories.values()
            if rec.status in {"active", "contradicted", "dormant", "revived"}
        ]
        for rec in sorted(candidates, key=lambda item: item.id):
            pressure = float(rec.confidence_state.get("contradiction_pressure", 0.0))
            empirical = float(rec.confidence_state.get("empirical_confidence", 0.5))
            stale_age = step - rec.last_seen_step
            superseded = rec.mutation_count >= 2 and stale_age >= 2
            should_retire = (
                rec.id != current_record_id
                and rec.retired_at_step is None
                and (
                    rec.contradiction_count >= contradiction_threshold
                    or pressure >= 0.52
                    or empirical <= 0.38
                    or stale_age >= inactivity_threshold
                    or (stale_age >= 4 and contradiction_severity >= 0.4)
                    or superseded
                )
            )
            if should_retire:
                retired_record = self.retire_theory(rec.id, step)
                if retired_record:
                    retired.append(retired_record)
        return retired

    def revive_matching_theories(
        self,
        abstraction: str,
        step: int,
        min_similarity: float = 0.55,
    ) -> List[TheoryRecord]:
        """Revive inactive theories when current evidence directly re-enters their topic."""
        revived: List[TheoryRecord] = []
        inactive = [
            rec
            for rec in self.theories.values()
            if rec.status in {"retired", "dormant"}
            and self._similarity(rec.abstraction, abstraction) >= min_similarity
        ]
        for rec in sorted(
            inactive,
            key=lambda item: (
                -self._similarity(item.abstraction, abstraction),
                item.id,
            ),
        )[:1]:
            revived_record = self.revive_theory(rec.id, step)
            if revived_record:
                revived.append(revived_record)
        return revived

    def link_parent_child(self, parent_id: str, child_id: str):
        parent = self.theories.get(parent_id)
        child = self.theories.get(child_id)
        if parent and child and parent_id not in child.parent_ids:
            child.parent_ids.append(parent_id)
            self._persist()

    def update_survival(self, step: int):
        for rec in self.theories.values():
            if rec.status in {"active", "contradicted", "revived"}:
                rec.survival_steps += 1
        self._persist()

    def active_theories(self) -> List[TheoryRecord]:
        return [
            rec
            for rec in self.theories.values()
            if rec.status in {"active", "contradicted", "revived"}
        ]

    def retrieve_active_theories(self) -> List[TheoryRecord]:
        return self.active_theories()

    def active_count(self) -> int:
        return len(self.active_theories())

    def contradicted_count(self) -> int:
        return len(
            [rec for rec in self.theories.values() if rec.status == "contradicted"]
        )

    def retired_count(self) -> int:
        return len([rec for rec in self.theories.values() if rec.status == "retired"])

    def revived_count(self) -> int:
        return sum(rec.revival_count for rec in self.theories.values())

    def average_retirement_age(self) -> float:
        ages = [age for rec in self.theories.values() for age in rec.retirement_ages]
        return float(sum(ages) / len(ages)) if ages else 0.0

    def average_revival_latency(self) -> float:
        latencies = [
            latency
            for rec in self.theories.values()
            for latency in rec.revival_latencies
        ]
        return float(sum(latencies) / len(latencies)) if latencies else 0.0

    def record_contradictions(
        self,
        tid: str,
        descriptions: List[str],
        step: int,
    ) -> Optional[TheoryRecord]:
        rec = self.theories.get(tid)
        if not rec or not descriptions:
            return rec
        for description in descriptions:
            if description not in rec.contradictions:
                rec.contradictions.append(description)
        rec.contradiction_count += len(descriptions)
        rec.status = "contradicted"
        rec.last_seen_step = step
        self._persist()
        return rec

    def total_mutation_count(self) -> int:
        return sum(rec.mutation_count for rec in self.theories.values())

    def average_theory_age(self) -> float:
        ages = [rec.survival_steps for rec in self.theories.values()]
        return float(sum(ages) / len(ages)) if ages else 0.0

    def longest_surviving_theory(self) -> int:
        ages = [rec.survival_steps for rec in self.theories.values()]
        return max(ages) if ages else 0

    def top_recurring_theory(self) -> Optional[str]:
        if not self.theories:
            return None
        return max(self.theories.values(), key=lambda rec: rec.survival_steps).id

    def family_analytics(self) -> Dict[str, Any]:
        """Compute deterministic longitudinal metrics by root theory family."""
        families: Dict[str, Dict[str, Any]] = {}
        for rec in self.theories.values():
            root_id = self._root_id(rec)
            family = families.setdefault(
                root_id,
                {
                    "root_id": root_id,
                    "children": [],
                    "mutation_count": 0,
                    "revival_count": 0,
                    "retirement_count": 0,
                    "survival_length": 0,
                    "contradiction_count": 0,
                    "contradiction_density": 0.0,
                    "avg_confidence": 0.0,
                    "_confidence_values": [],
                },
            )
            if rec.id != root_id:
                family["children"].append(rec.id)
            family["mutation_count"] += int(rec.mutation_count)
            family["revival_count"] += int(rec.revival_count)
            family["retirement_count"] += len(rec.retirement_ages)
            family["survival_length"] += int(rec.survival_steps)
            family["contradiction_count"] += int(rec.contradiction_count)
            family["_confidence_values"].append(float(rec.confidence))

        for family in families.values():
            survival = max(1, int(family["survival_length"]))
            family["children"] = sorted(set(family["children"]))
            family["contradiction_density"] = round(
                family["contradiction_count"] / survival,
                3,
            )
            values = family.pop("_confidence_values")
            family["avg_confidence"] = round(mean(values), 3) if values else 0.0

        def best_by(field_name: str) -> Optional[str]:
            if not families:
                return None
            return max(
                families.values(),
                key=lambda item: (
                    item[field_name],
                    item["survival_length"],
                    item["root_id"],
                ),
            )["root_id"]

        return {
            "families": families,
            "best_surviving_family": best_by("survival_length"),
            "most_revived_family": best_by("revival_count"),
            "highest_contradiction_family": best_by("contradiction_density"),
            "most_mutated_family": best_by("mutation_count"),
        }

    def _root_id(self, rec: TheoryRecord) -> str:
        current = rec
        seen = {rec.id}
        while current.parent_ids:
            parent_id = sorted(current.parent_ids)[0]
            if parent_id in seen or parent_id not in self.theories:
                break
            current = self.theories[parent_id]
            seen.add(current.id)
        return current.id

    def get_theory(self, tid: str) -> Optional[TheoryRecord]:
        return self.theories.get(tid)

    def to_graph(self) -> Dict[str, Any]:
        return {tid: asdict(rec) for tid, rec in self.theories.items()}


def default_lineage_path(base_dir: Path) -> Path:
    return base_dir / "theory_lineage.json"
