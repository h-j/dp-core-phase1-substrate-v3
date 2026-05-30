from dataclasses import dataclass, field
from typing import Dict

@dataclass
class RegimeSubtypeMemory:
    subtype: str
    first_seen: str | None = None
    last_seen: str | None = None
    seen_count: int = 0
    avg_usefulness: float = 0.0
    total_usefulness: float = 0.0
    falsified_count: int = 0
    resolution_counts: Dict[str, int] = field(default_factory=lambda: {
        "higher": 0,
        "lower": 0,
        "range_bound": 0,
        "uncertain": 0,
    })

class RegimeContinuityMemory:
    def __init__(self):
        self.records: Dict[str, RegimeSubtypeMemory] = {}

    def update(
        self,
        date: str,
        subtype: str,
        usefulness: float,
        actual_direction: str | None,
        falsified: bool,
    ):
        if subtype not in self.records:
            self.records[subtype] = RegimeSubtypeMemory(subtype=subtype, first_seen=date)
        
        rec = self.records[subtype]
        rec.seen_count += 1
        rec.last_seen = date
        rec.total_usefulness += usefulness
        rec.avg_usefulness = rec.total_usefulness / rec.seen_count
        
        if falsified:
            rec.falsified_count += 1
        
        if actual_direction and actual_direction in rec.resolution_counts:
            rec.resolution_counts[actual_direction] += 1

    def summary(self, subtype: str) -> dict:
        rec = self.records.get(subtype)
        if not rec:
            return {
                "subtype": subtype,
                "seen_count": 0,
                "avg_usefulness": 0.0,
                "last_seen": None,
                "historical_resolution": {"higher": 0, "lower": 0, "range_bound": 0, "uncertain": 0},
                "falsified_count": 0,
            }
        return {
            "subtype": rec.subtype,
            "seen_count": rec.seen_count,
            "avg_usefulness": round(rec.avg_usefulness, 3),
            "last_seen": rec.last_seen,
            "historical_resolution": rec.resolution_counts,
            "falsified_count": rec.falsified_count,
        }