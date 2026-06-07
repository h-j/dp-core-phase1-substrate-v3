from typing import Any, Dict
from market.replay.replay_output import ReplayOutputMixin

class PersistenceCoordinator(ReplayOutputMixin):
    """Centralizes repository save operations and snapshotting."""
    
    def __init__(self, repositories: Dict[str, Any], replay_dir: Any):
        self.repos = repositories
        self.replay_dir = replay_dir

    def save_day(self, result: Any):
        """Orchestrates persistence of the day's cognition."""
        # PostgreSQL Persistence
        self.repos["observation"].save(result.observation) # Note: Replay wraps market_obs in ObservationEvent elsewhere but repo takes event
        self.repos["abstraction"].save(result.abstraction)
        self.repos["theory"].save(result.theory)
        self.repos["validation"].save(result.validation)
        self.repos["reflection"].save(result.reflection)
        self.repos["confidence"].save(result.confidence_state)

        if self.repos.get("market_outcome"):
            self.repos["market_outcome"].save(result.observation)

        if self.repos.get("transition_pressure"):
            self.repos["transition_pressure"].save(result.transition_pressure, date=result.date, day_index=result.day_index)

        if self.repos.get("prediction"):
            theory_id = str(getattr(result.theory, 'id', ''))
            reflection_id = str(getattr(result.reflection, 'id', ''))
            self.repos["prediction"].save(
                result.prediction,
                date=result.date,
                day_index=result.day_index,
                theory_id=theory_id,
                reflection_id=reflection_id
            )

        if self.repos.get("prediction_result") and result.prior_prediction_result:
            # Logic for prediction_id link is handled in executor via _prior_prediction_db_id
            pass 

        # Disk Snapshot
        self._save_snapshot(result.day_index, result.date, result.snapshot_data)

    def _save_snapshot(self, day_idx: int, date_str: str, snapshot_data: dict):
        # Re-implemented here for coordinator isolation, calling mixin behavior
        # Usually, Snapshots are for observability and debug.
        import json
        snapshot_file = self.replay_dir / "logs" / f"day_{day_idx:04d}_{date_str}.json"
        # Mixin logic expects a specific snapshot format
        # For now, delegating or re-implementing to maintain parity
        super()._save_snapshot(day_idx, date_str, snapshot_data)