import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from cognition.schemas.experience.experience import (Experience,
                                                     ExperienceOutcome,
                                                     ExperienceStatus)


class ExperienceRepository:
    """
    Handles persistence for Experience entities.
    Persists to JSON files in data/experiences/ for longitudinal study.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = (
            Path(base_path)
            if base_path
            else Path(__file__).parent.parent.parent / "data" / "experiences"
        )
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.storage: Dict[str, Any] = {}
        self._initial_load()

    def _initial_load(self):
        """Loads existing experiences from disk into memory cache."""
        for file_path in self.base_path.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                try:
                    # Convert status string back to Enum
                    data["status"] = ExperienceStatus(data["status"])
                except ValueError:
                    # Handle cases where the status in the JSON file is not a valid ExperienceStatus enum member
                    print(
                        f"WARNING: Invalid ExperienceStatus '{data['status']}' found in {file_path}. Defaulting to ABANDONED."
                    )
                    data["status"] = ExperienceStatus.ABANDONED
                # Correctly instantiate ExperienceOutcome and Experience objects
                if "outcome" in data and isinstance(data["outcome"], dict):
                    data["outcome"] = ExperienceOutcome(**data["outcome"])
                self.storage[data["experience_id"]] = Experience(**data)

    def save(self, experience: Any):
        """Persists the experience state."""
        # Update memory cache
        self.storage[experience.experience_id] = experience

        # Persist to disk
        self.base_path.mkdir(parents=True, exist_ok=True)
        file_path = self.base_path / f"{experience.experience_id}.json"

        experience_data = asdict(experience)
        experience_data["status"] = experience.status.value

        with open(file_path, "w") as f:
            json.dump(experience_data, f, indent=2)

    def get_all(self) -> List[Any]:
        """Returns all recorded experiences."""
        return list(self.storage.values())

    def load(self) -> List[Experience]:
        """Reloads all experiences from the filesystem."""
        self.storage.clear()
        self._initial_load()
        return self.get_all()

    def load_by_lineage(
        self,
        lineage_id: str,
        status: Optional[ExperienceStatus] = None,
    ) -> Optional[Experience]:
        """Retrieves an experience by its associated lineage ID."""
        # Search memory cache first (always complete and in sync)
        for exp in self.storage.values():
            if exp.lineage_id == lineage_id and (
                status is None or exp.status == status
            ):
                return exp
        return None

    def list_experiences(self, status: Optional[str] = None) -> List[Experience]:
        """Returns filtered experiences from cache."""
        experiences = list(self.storage.values())
        if status:
            experiences = [e for e in experiences if e.status.value == status]
        return experiences

    def clear(self):
        """Clears memory cache and deletes all files in directory."""
        self.storage.clear()
        for file_path in self.base_path.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as e:
                print(f"WARNING: Error deleting file {file_path}: {e}")
