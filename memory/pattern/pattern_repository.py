import json
from pathlib import Path
from typing import Dict, List, Optional

from cognition.schemas.pattern.pattern import Pattern


class PatternRepository:
    """
    Handles persistence for Pattern entities.
    Persists to JSON files in data/patterns/ for longitudinal cognitive continuity.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = (
            Path(base_path)
            if base_path
            else Path(__file__).parent.parent.parent / "data" / "patterns"
        )
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.storage: Dict[str, Pattern] = {}
        self._initial_load()

    def _initial_load(self):
        """Loads existing patterns from disk into memory cache."""
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.storage[data["pattern_id"]] = Pattern(**data)
            except Exception as e:
                print(f"WARNING: Error loading pattern from {file_path}: {e}")

    def save(self, pattern: Pattern):
        """Persists the pattern state."""
        self.storage[pattern.pattern_id] = pattern
        file_path = self.base_path / f"{pattern.pattern_id}.json"
        with open(file_path, "w") as f:
            f.write(pattern.model_dump_json(indent=2))

    def get_all(self) -> List[Pattern]:
        """Returns all recorded patterns."""
        return list(self.storage.values())

    def get_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """Retrieves a pattern by its unique identifier."""
        return self.storage.get(pattern_id)

    def clear(self):
        """Clears cache and deletes all files in repository directory."""
        self.storage.clear()
        for file_path in self.base_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting file {file_path}: {e}")
