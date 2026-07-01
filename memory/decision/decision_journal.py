import json
from pathlib import Path
from typing import Dict, List, Optional
from cognition.schemas.decision.decision_record import DecisionRecord


class DecisionJournal:
    """
    Chronological, persistent local journal for DecisionRecord entities.
    """

    def __init__(self, base_path: Optional[Path] = None):
        project_root = Path(__file__).parent.parent.parent
        self.base_path = Path(base_path) if base_path else project_root / "data"
        self.journal_path = self.base_path / "decision_journal"
        self.journal_path.mkdir(parents=True, exist_ok=True)
        
        self.records: Dict[str, DecisionRecord] = {}
        self.load_all()

    def load_all(self):
        """Loads all DecisionRecord files from disk into memory."""
        self.records.clear()
        for file_path in self.journal_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    record = DecisionRecord.from_dict(data)
                    self.records[record.id] = record
            except Exception as e:
                print(f"WARNING: Failed to load decision record {file_path}: {e}")

    def save(self, record: DecisionRecord):
        """Persists a DecisionRecord object to disk."""
        self.records[record.id] = record
        file_path = self.journal_path / f"{record.id}.json"
        with open(file_path, "w") as f:
            json.dump(record.to_dict(), f, indent=2)

    def get_all(self) -> List[DecisionRecord]:
        """Returns all records sorted chronologically by prediction_date."""
        sorted_records = sorted(
            self.records.values(),
            key=lambda x: (x.prediction_date or "", x.created_at),
        )
        return list(sorted_records)

    def clear(self):
        """Deletes all decision record files from disk and clears cache."""
        self.records.clear()
        if self.journal_path.exists():
            for file_path in self.journal_path.glob("*.json"):
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"WARNING: Failed to delete {file_path}: {e}")
