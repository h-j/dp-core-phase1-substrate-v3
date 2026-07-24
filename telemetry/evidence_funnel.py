"""
Telemetry Substrate: Evidence Accumulation Funnel Tracker (PROMPT C2).

Tracks per-day funnel metrics without wall-clock fields for 100% byte stability:
- theories_active
- predicates_parsed_ok
- activation_evaluated
- activation_true
- terminal_state_resolved (SUPPORTED, CONTRADICTED, UNTRIGGERED, GROUNDED)
- resolutions_delivered_to_scored_engine
- beta_updates_applied
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class DailyFunnelRecord:
    def __init__(self, day_idx: int):
        self.day_idx = day_idx
        self.theories_active = 0
        self.predicates_parsed_ok = 0
        self.activation_evaluated = 0
        self.activation_true = 0
        self.supported_count = 0
        self.contradicted_count = 0
        self.untriggered_count = 0
        self.grounded_count = 0
        self.resolutions_delivered_to_scored_engine = 0
        self.beta_updates_applied = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_idx": self.day_idx,
            "theories_active": self.theories_active,
            "predicates_parsed_ok": self.predicates_parsed_ok,
            "activation_evaluated": self.activation_evaluated,
            "activation_true": self.activation_true,
            "terminal_state_resolved": {
                "SUPPORTED": self.supported_count,
                "CONTRADICTED": self.contradicted_count,
                "UNTRIGGERED": self.untriggered_count,
                "GROUNDED": self.grounded_count,
            },
            "resolutions_delivered_to_scored_engine": self.resolutions_delivered_to_scored_engine,
            "beta_updates_applied": self.beta_updates_applied,
        }


class EvidenceFunnel:
    """
    Append-only evidence accumulation funnel tracker.
    Byte-stable output without wall-clock timestamps.
    """

    def __init__(self):
        self._daily_records: Dict[int, DailyFunnelRecord] = {}

    def get_or_create_day(self, day_idx: int) -> DailyFunnelRecord:
        if day_idx not in self._daily_records:
            self._daily_records[day_idx] = DailyFunnelRecord(day_idx)
        return self._daily_records[day_idx]

    def record_active_theory(self, day_idx: int):
        rec = self.get_or_create_day(day_idx)
        rec.theories_active += 1

    def record_predicate_parsed(self, day_idx: int, parsed_ok: bool = True):
        rec = self.get_or_create_day(day_idx)
        if parsed_ok:
            rec.predicates_parsed_ok += 1

    def record_activation_evaluated(self, day_idx: int, activation_true: bool = False):
        rec = self.get_or_create_day(day_idx)
        rec.activation_evaluated += 1
        if activation_true:
            rec.activation_true += 1

    def record_terminal_resolution(self, day_idx: int, state: str):
        rec = self.get_or_create_day(day_idx)
        state_upper = state.upper()
        if state_upper == "SUPPORTED":
            rec.supported_count += 1
        elif state_upper == "CONTRADICTED":
            rec.contradicted_count += 1
        elif state_upper in ["UNTRIGGERED", "TRIGGERED"]:
            rec.untriggered_count += 1
        else:
            rec.grounded_count += 1

    def record_resolution_delivered(self, day_idx: int):
        rec = self.get_or_create_day(day_idx)
        rec.resolutions_delivered_to_scored_engine += 1

    def record_beta_update(self, day_idx: int):
        rec = self.get_or_create_day(day_idx)
        rec.beta_updates_applied += 1

    def get_summary_dict(self) -> Dict[str, Any]:
        totals = {
            "theories_active": 0,
            "predicates_parsed_ok": 0,
            "activation_evaluated": 0,
            "activation_true": 0,
            "supported_count": 0,
            "contradicted_count": 0,
            "untriggered_count": 0,
            "grounded_count": 0,
            "resolutions_delivered_to_scored_engine": 0,
            "beta_updates_applied": 0,
        }

        daily_list = []
        for day_idx in sorted(self._daily_records.keys()):
            r = self._daily_records[day_idx]
            d = r.to_dict()
            daily_list.append(d)
            totals["theories_active"] += r.theories_active
            totals["predicates_parsed_ok"] += r.predicates_parsed_ok
            totals["activation_evaluated"] += r.activation_evaluated
            totals["activation_true"] += r.activation_true
            totals["supported_count"] += r.supported_count
            totals["contradicted_count"] += r.contradicted_count
            totals["untriggered_count"] += r.untriggered_count
            totals["grounded_count"] += r.grounded_count
            totals["resolutions_delivered_to_scored_engine"] += r.resolutions_delivered_to_scored_engine
            totals["beta_updates_applied"] += r.beta_updates_applied

        return {
            "totals": totals,
            "daily_records": daily_list,
        }

    def generate_summary_table(self) -> str:
        s = self.get_summary_dict()
        t = s["totals"]

        table = "=========================================================================================\n"
        table += "EVIDENCE ACCUMULATION FUNNEL SUMMARY TABLE\n"
        table += "=========================================================================================\n"
        table += f"1. Active Theories Evaluated:                       {t['theories_active']}\n"
        table += f"2. Predicates Parsed OK:                            {t['predicates_parsed_ok']}\n"
        table += f"3. Activation Conditions Evaluated:                {t['activation_evaluated']}\n"
        table += f"4. Activation Conditions True:                     {t['activation_true']}\n"
        table += f"5. Terminal States Resolved:\n"
        table += f"   - SUPPORTED:                                     {t['supported_count']}\n"
        table += f"   - CONTRADICTED:                                  {t['contradicted_count']}\n"
        table += f"   - UNTRIGGERED:                                   {t['untriggered_count']}\n"
        table += f"   - GROUNDED / OTHER:                              {t['grounded_count']}\n"
        table += f"6. Resolutions Delivered to Scored Engine:         {t['resolutions_delivered_to_scored_engine']}\n"
        table += f"7. Beta Posterior Updates Applied:                 {t['beta_updates_applied']}\n"
        table += "=========================================================================================\n"

        return table


# Global instance helper for replay execution
_active_funnel: Optional[EvidenceFunnel] = None


def get_active_funnel() -> EvidenceFunnel:
    global _active_funnel
    if _active_funnel is None:
        _active_funnel = EvidenceFunnel()
    return _active_funnel


def reset_active_funnel() -> EvidenceFunnel:
    global _active_funnel
    _active_funnel = EvidenceFunnel()
    return _active_funnel
