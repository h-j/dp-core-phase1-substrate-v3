import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from experience.experience_engine import Experience, ExperienceStatus

class ExperienceRepository:
    """
    Handles persistence for Experience entities.
    Persists to JSON files in data/experiences/ for longitudinal study.
    """
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "data" / "experiences"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.storage: Dict[str, Any] = {}
        self._initial_load()

    def _initial_load(self):
        """Loads existing experiences from disk into memory cache."""
        for file_path in self.base_path.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Convert status string back to Enum
                data['status'] = ExperienceStatus(data['status'])
                self.storage[data['experience_id']] = Experience(**data)

    def save(self, experience: Any):
        """Persists the experience state."""
        # Update memory cache
        self.storage[experience.experience_id] = experience
        
        # Persist to disk
        file_path = self.base_path / f"{experience.experience_id}.json"
        experience_data = asdict(experience)
        # Serialize Enum value
        experience_data['status'] = experience.status.value
        
        with open(file_path, 'w') as f:
            json.dump(experience_data, f, indent=2)

    def get_all(self) -> List[Any]:
        """Returns all recorded experiences."""
        return list(self.storage.values())

    def load(self) -> List[Experience]:
        """Reloads all experiences from the filesystem."""
        self.storage.clear()
        self._initial_load()
        return self.get_all()

    def load_by_lineage(self, lineage_id: str) -> Optional[Experience]:
        """Retrieves an experience by its associated lineage ID."""
        # Search memory cache first
        for exp in self.storage.values():
            if exp.lineage_id == lineage_id:
                return exp
        
        # Fallback to reloading from disk if not found in cache
        self.load()
        for exp in self.storage.values():
            if exp.lineage_id == lineage_id:
                return exp
        return None