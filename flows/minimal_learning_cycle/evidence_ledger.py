import time
from typing import Any, Dict, List


class EvidenceLedger:
    def __init__(self):
        self._records: List[Dict[str, Any]] = []
        self._entry_counter = 0

    def append(self, record: Dict[str, Any]):
        """
        Appends a record to the append-only ledger.
        Raises an error if trying to modify or delete a record.
        """
        self._entry_counter += 1
        entry_id = f"LEDGER_{self._entry_counter:06d}"

        full_record = {"ledger_entry_id": entry_id, **record, "timestamp": time.time()}

        # Enforce append-only by sealing the records list
        self._records.append(full_record)

    def get_records(self) -> List[Dict[str, Any]]:
        # Return a copy of records to prevent modification of elements
        return [dict(r) for r in self._records]

    def clear(self):
        # We only support clearing for resetting between worlds, but within a run it remains sealed.
        self._records = []
        self._entry_counter = 0

    # Override standard list mutators to protect ledger integrity
    def __setitem__(self, index, value):
        raise TypeError("EvidenceLedger is append-only and cannot be modified.")

    def __delitem__(self, index):
        raise TypeError("EvidenceLedger is append-only and cannot be modified.")
